"""
This file contains utility functions for the observation script for the ATA.
"""

import pandas as pd
import numpy as np
import os
import json
import re
import scipy
from astroquery.jplhorizons import Horizons
import astropy.units as u
from astropy.coordinates import Angle, EarthLocation, SkyCoord, AltAz
import astropy.constants as const
from astropy.time import Time
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


# Change this to reflect my 4 tunings
FREQ_RANGE = [1336, 2008, 4536, 8336] #MHz

# This file defines some useful tools to keep track of observed targets


def resolve_path_from_script(path_value: str, script_file: str = None, must_exist: bool = False) -> str:
    """Resolve absolute and script-relative filesystem paths.

    Resolution order for relative paths:
    1) Next to ``script_file`` (or this module when omitted)
    2) Parent directory of that script directory
    3) Absolute path from current working directory

    Args:
        path_value: Absolute or relative path text.
        script_file: ``__file__`` path for the caller requesting resolution.
            When omitted, this module's location is used.
        must_exist: If True, raise ``FileNotFoundError`` when unresolved.

    Returns:
        Normalized resolved path, or an empty string when ``path_value`` is blank.

    Raises:
        FileNotFoundError: When ``must_exist`` is True and no candidate exists.
    """
    path_text = str(path_value or "").strip()
    if not path_text:
        return ""

    if os.path.isabs(path_text):
        candidate = os.path.normpath(path_text)
        if must_exist and not os.path.exists(candidate):
            raise FileNotFoundError(f"Path does not exist: {candidate}")
        return candidate

    base_script_file = script_file or __file__
    script_dir = os.path.dirname(os.path.abspath(base_script_file))
    parent_dir = os.path.dirname(script_dir)

    candidates = [
        os.path.normpath(os.path.join(script_dir, path_text)),
        os.path.normpath(os.path.join(parent_dir, path_text)),
        os.path.normpath(os.path.abspath(path_text)),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    if must_exist:
        raise FileNotFoundError(f"Could not find '{path_value}'. Checked: {candidates}")

    return candidates[0]


def make_ods_project_tag(project_name: str = "survey", project_folder: str = "") -> str:
    """Build a filename-safe ODS project tag.

    Preference order:
    1) Basename of ``project_folder`` when provided (GUI browse mode)
    2) ``project_name`` fallback

    The returned tag is sanitized for filenames and has common operational
    suffixes removed when present.
    """
    folder_text = str(project_folder or "").strip()
    if folder_text:
        raw = os.path.basename(os.path.normpath(folder_text))
    else:
        raw = str(project_name or "survey")

    cleaned = re.sub(r"_(working|archive|ephemerides)$", "", str(raw), flags=re.IGNORECASE)
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned).strip("._-")
    return cleaned or "survey"


def normalize_hashpipe_targets(targets) -> dict:
    """Normalize hashpipe target dictionaries to ``{node: [streams]}`` form.

    Normalization rules:
    - Node keys are lowercased and stripped.
    - Stream containers must be iterable list/tuple/set values.
    - Streams are coerced to integers and filtered to ``0`` or ``1``.
    - Duplicate streams are removed and output is sorted.

    Args:
        targets: Candidate dictionary of ``node -> stream iterable``.

    Returns:
        Dictionary containing only valid nodes and streams.
    """
    normalized = {}
    if not isinstance(targets, dict):
        return normalized

    for node_name, streams in targets.items():
        node = str(node_name or "").strip().lower()
        if not node:
            continue
        if not isinstance(streams, (list, tuple, set)):
            continue

        cleaned_streams = []
        for stream in streams:
            try:
                stream_value = int(stream)
            except (TypeError, ValueError):
                continue
            if stream_value in (0, 1):
                cleaned_streams.append(stream_value)

        unique_streams = sorted(set(cleaned_streams))
        if unique_streams:
            normalized[node] = unique_streams

    return normalized


def _normalize_csv_key(value) -> str:
    """Normalize CSV keys for case-insensitive, whitespace-tolerant lookups."""
    if value is None:
        return ""
    return str(value).strip().lower()


_HMS_PATTERN = re.compile(r"(?P<h>\d+(?:\.\d+)?)h(?P<m>\d+(?:\.\d+)?)m(?P<s>\d+(?:\.\d+)?)s?", re.IGNORECASE)
_DMS_PATTERN = re.compile(r"(?P<d>\d+(?:\.\d+)?)d(?P<m>\d+(?:\.\d+)?)m(?P<s>\d+(?:\.\d+)?)s?", re.IGNORECASE)
_COLON_PATTERN = re.compile(r"(?P<a>\d+(?:\.\d+)?):(?P<m>\d+(?:\.\d+)?):(?P<s>\d+(?:\.\d+)?)")


def _coerce_sexagesimal_value(value, *, hours_mode: bool = False, strict_unit: bool = True, field_label: str = None):
    """Coerce a decimal, "H:M:S", "HhMmSs", or "DdMmSs" string into a float.

    The "h/m/s" and "d/m/s" suffixes are explicit unit markers. When one of
    them is present and disagrees with "hours_mode" (i.e. the column/header
    this value is destined for), the mismatch is either raised (strict_unit=True)
    or silently ignored and treated as unparsable (strict_unit=False), so a
    coordinate typed in the wrong unit for its column never gets silently
    reinterpreted as the wrong quantity.
    """
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "inf", "+inf", "-inf"}:
        return None

    try:
        numeric = float(text)
    except (TypeError, ValueError):
        numeric = None
    if numeric is not None:
        return numeric

    cleaned = "".join(text.split())
    sign = 1.0
    if cleaned.startswith("-"):
        sign = -1.0
        cleaned = cleaned[1:]
    elif cleaned.startswith("+"):
        cleaned = cleaned[1:]

    hms_match = re.fullmatch(_HMS_PATTERN, cleaned)
    dms_match = re.fullmatch(_DMS_PATTERN, cleaned)
    colon_match = re.fullmatch(_COLON_PATTERN, cleaned)

    if hms_match:
        explicit_unit = "hours"
        whole, minutes, seconds = hms_match.group("h"), hms_match.group("m"), hms_match.group("s")
    elif dms_match:
        explicit_unit = "degrees"
        whole, minutes, seconds = dms_match.group("d"), dms_match.group("m"), dms_match.group("s")
    elif colon_match:
        # "H:M:S" is ambiguous on its own; the caller's "hours_mode" decides the unit.
        explicit_unit = None
        whole, minutes, seconds = colon_match.group("a"), colon_match.group("m"), colon_match.group("s")
    else:
        return None

    whole_f = float(whole)
    minutes_f = float(minutes)
    seconds_f = float(seconds)
    if not (0 <= minutes_f < 60) or not (0 <= seconds_f < 60):
        return None

    requested_unit = "hours" if hours_mode else "degrees"
    if explicit_unit is not None and explicit_unit != requested_unit:
        label = f" for {field_label}" if field_label else ""
        message = (
            f"Coordinate '{text}'{label} is explicitly in {explicit_unit} (h/m/s or d/m/s suffix), "
            f"but was expected to be in {requested_unit}. Check that the value and its column header agree."
        )
        if strict_unit:
            raise ValueError(message)
        return None

    return sign * (whole_f + (minutes_f / 60.0) + (seconds_f / 3600.0))


def parse_hours_value(value, *, strict_unit: bool = True, field_label: str = None):
    """Parse a value as RA hours, accepting "HH:MM:SS.ss" or "HHhMMmSS.sss" strings.

    Raises "ValueError" when "strict_unit" is True and the value carries an
    explicit "d/m/s" (degrees) suffix instead of an "h/m/s" one.
    """
    parsed = _coerce_sexagesimal_value(value, hours_mode=True, strict_unit=strict_unit, field_label=field_label)
    return float(parsed) if parsed is not None else None


def parse_degrees_value(value, *, strict_unit: bool = True, field_label: str = None):
    """Parse a value as DEC degrees, accepting "+DD:MM:SS.ss" or "+DDdMMmSS.sss" strings.

    Raises "ValueError" when "strict_unit" is True and the value carries an
    explicit "h/m/s" (hours) suffix instead of a "d/m/s" one.
    """
    parsed = _coerce_sexagesimal_value(value, hours_mode=False, strict_unit=strict_unit, field_label=field_label)
    return float(parsed) if parsed is not None else None


def parse_positive_int_seconds(value):
    """Parse a positive integer number of seconds.

    Args:
        value: Candidate numeric/string value.

    Returns:
        Parsed positive integer, or ``None`` when missing/invalid/non-positive.
    """
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if pd.isna(value):
        return None

    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return None

    if parsed <= 0:
        return None
    return parsed


def is_valid_finite_float(value) -> bool:
    """Return True when a value can be parsed to a finite float."""
    try:
        if value is None or pd.isna(value):
            return False
        text = str(value).strip()
        if not text:
            return False
        # Non-strict: only checking whether this looks like *a* coordinate at all,
        # not whether its unit agrees with any particular column.
        parsed = _coerce_sexagesimal_value(text, hours_mode=True, strict_unit=False)
        if parsed is None:
            parsed = _coerce_sexagesimal_value(text, hours_mode=False, strict_unit=False)
        if parsed is not None:
            return bool(np.isfinite(parsed))
        return bool(np.isfinite(float(text)))
    except Exception:
        return False


def parse_solar_system_flag(flag_value):
    """Normalize Solar System Flag values to ``0`` or ``1``.

    Returns:
        ``0`` or ``1`` when valid, else ``None``.
    """
    try:
        parsed = int(float(flag_value))
    except Exception:
        return None
    if parsed in (0, 1):
        return parsed
    return None


def resolve_body_position(
    body_name: str,
    scan_start: str,
    obs_location,
    testing: bool = False,
    ata_sources_module=None,
    logger=None,
):
    """Resolve Sun/Moon RA/DEC in degrees using ATA first, Horizons fallback.

    Args:
        body_name: ``"sun"`` or ``"moon"``.
        scan_start: Observation timestamp string parseable by ``astropy.time.Time``.
        obs_location: Observatory location dict for Horizons query.
        testing: If True, skip ATA lookup and query Horizons directly.
        ata_sources_module: Optional ``ATATools.ata_sources`` module.
        logger: Optional callable for status/error lines.

    Returns:
        Dict with keys ``ra`` and ``dec`` in degrees, or ``None`` when unresolved.
    """
    body_key = str(body_name or "").strip().lower()
    body_horizons_ids = {
        "sun": "10",
        "moon": "301",
    }
    if body_key not in body_horizons_ids:
        return None

    sink = logger if callable(logger) else print

    if not testing and ata_sources_module is not None:
        try:
            ata_result = ata_sources_module.check_source(body_key)
            if isinstance(ata_result, dict) and is_valid_finite_float(ata_result.get("ra")) and is_valid_finite_float(ata_result.get("dec")):
                return {
                    "ra": float(ata_result["ra"]),
                    "dec": float(ata_result["dec"]),
                }
            sink(f"ATA {body_key} lookup returned unexpected payload. Falling back to Horizons.")
        except Exception as exc:
            sink(f"ATA {body_key} lookup failed: {exc}. Falling back to Horizons.")

    try:
        obj = Horizons(id=body_horizons_ids[body_key], location=obs_location, epochs=Time(scan_start).jd)
        eph = obj.ephemerides()
        return {
            "ra": float(eph["RA"][0]),
            "dec": float(eph["DEC"][0]),
        }
    except Exception as exc:
        sink(f"Horizons {body_key} lookup failed: {exc}")
        return None


def query_horizons_instantaneous_position(target_id, obs_location, epoch, logger=None):
    """Query a single instantaneous Horizons RA/DEC position in degrees.

    Args:
        target_id: Horizons identifier to query.
        obs_location: Observatory location dictionary for Horizons.
        epoch: Timestamp accepted by ``astropy.time.Time``.
        logger: Optional callable for status/error lines.

    Returns:
        Dict with keys ``ra`` and ``dec`` in degrees, or ``None`` on failure.
    """
    sink = logger if callable(logger) else print

    try:
        obj = Horizons(id=target_id, location=obs_location, epochs=Time(epoch).jd)
        eph = obj.ephemerides()
        if len(eph) == 0:
            sink(f"Horizons instantaneous lookup returned no rows for target {target_id}.")
            return None

        ra_deg = eph["RA"][0]
        dec_deg = eph["DEC"][0]
        if not is_valid_finite_float(ra_deg) or not is_valid_finite_float(dec_deg):
            sink(
                f"Horizons instantaneous lookup returned invalid coordinates for target {target_id}: "
                f"RA={ra_deg}, DEC={dec_deg}"
            )
            return None

        return {
            "ra": float(ra_deg),
            "dec": float(dec_deg),
        }
    except Exception as exc:
        sink(f"Horizons instantaneous lookup failed for target {target_id}: {exc}")
        return None


def resolve_scan_duration_seconds(
    target_df,
    row_index: int,
    default_obs_seconds,
    use_target_obs_time_override: bool = False,
    testing: bool = False,
    testing_obs_time_seconds: int = 60,
):
    """Resolve nominal/effective scan duration for a target row.

    Args:
        target_df: Target DataFrame that may include an ``Obs Time`` column.
        row_index: Row index for the active target.
        default_obs_seconds: Default scan duration fallback.
        use_target_obs_time_override: If True, uses row ``Obs Time`` when valid.
        testing: If True, forces effective duration to ``testing_obs_time_seconds``.
        testing_obs_time_seconds: Effective scan length used in testing mode.

    Returns:
        Dict with keys ``nominal_seconds``, ``effective_seconds``, and ``duration_source``.
    """
    default_seconds = parse_positive_int_seconds(default_obs_seconds) or 300
    nominal_seconds = default_seconds
    duration_source = "default OBS_TIME setting"

    if use_target_obs_time_override:
        if hasattr(target_df, "columns") and 'Obs Time' in target_df.columns:
            row_value = None
            try:
                row_value = target_df.iloc[row_index].get('Obs Time')
            except Exception:
                row_value = None

            parsed_row_seconds = parse_positive_int_seconds(row_value)
            if parsed_row_seconds is not None:
                nominal_seconds = parsed_row_seconds
                duration_source = 'target CSV column "Obs Time"'
            else:
                duration_source = 'default OBS_TIME setting ("Obs Time" blank/invalid)'
        else:
            duration_source = 'default OBS_TIME setting (no "Obs Time" column)'

    effective_seconds = int(testing_obs_time_seconds) if testing else nominal_seconds
    return {
        "nominal_seconds": nominal_seconds,
        "effective_seconds": effective_seconds,
        "duration_source": duration_source,
    }


def estimate_ods_slew_seconds(
    from_ra_deg,
    from_dec_deg,
    to_ra_deg,
    to_dec_deg,
    obs_location,
    obstime_utc=None,
    az_rate_deg_per_sec: float = 3.0,
    el_rate_deg_per_sec: float = 1.0,
    conservative_multiplier: float = 1.30,
    extra_buffer_seconds: int = 30,
):
    """Estimate conservative ODS slew time between two sky positions.

    Primary model uses Az/El deltas at the given observatory location and
    obstime. If transforms fail, a great-circle angular separation fallback is
    used.

    Args:
        from_ra_deg: Start right ascension in degrees.
        from_dec_deg: Start declination in degrees.
        to_ra_deg: End right ascension in degrees.
        to_dec_deg: End declination in degrees.
        obs_location: Dict containing ``lat``, ``lon``, and ``elevation``.
        obstime_utc: Optional UTC datetime for Az/El transform.
        az_rate_deg_per_sec: Azimuth slew rate.
        el_rate_deg_per_sec: Elevation slew rate.
        conservative_multiplier: Multiplier applied to raw slew estimate.
        extra_buffer_seconds: Fixed buffer added to final estimate.

    Returns:
        Non-negative integer slew estimate in seconds.
    """
    if from_ra_deg is None or from_dec_deg is None or to_ra_deg is None or to_dec_deg is None:
        return int(max(0, int(extra_buffer_seconds)))

    if obstime_utc is None:
        obstime_utc = datetime.now(timezone.utc)

    try:
        location = EarthLocation(lat=obs_location['lat'], lon=obs_location['lon'], height=obs_location['elevation'])
        aa = AltAz(location=location, obstime=Time(obstime_utc))

        from_coord = SkyCoord(ra=float(from_ra_deg) * u.deg, dec=float(from_dec_deg) * u.deg).transform_to(aa)
        to_coord = SkyCoord(ra=float(to_ra_deg) * u.deg, dec=float(to_dec_deg) * u.deg).transform_to(aa)

        az_delta = abs(float(to_coord.az.deg) - float(from_coord.az.deg))
        az_delta = min(az_delta, 360.0 - az_delta)
        el_delta = abs(float(to_coord.alt.deg) - float(from_coord.alt.deg))

        az_seconds = az_delta / max(float(az_rate_deg_per_sec), 1e-6)
        el_seconds = el_delta / max(float(el_rate_deg_per_sec), 1e-6)
        raw_slew_seconds = max(az_seconds, el_seconds)
    except Exception:
        try:
            from_coord = SkyCoord(ra=float(from_ra_deg) * u.deg, dec=float(from_dec_deg) * u.deg)
            to_coord = SkyCoord(ra=float(to_ra_deg) * u.deg, dec=float(to_dec_deg) * u.deg)
            angular_sep_deg = float(from_coord.separation(to_coord).deg)
            raw_slew_seconds = angular_sep_deg / 2.0
        except Exception:
            raw_slew_seconds = 0.0

    conservative_seconds = np.ceil(raw_slew_seconds * max(1.0, float(conservative_multiplier)))
    conservative_seconds += max(0, int(extra_buffer_seconds))
    return int(max(0, conservative_seconds))


def log_ods_reservation_vs_plan(
    source_name: str,
    res_start_utc,
    res_end_utc,
    planned_obs_start_utc=None,
    planned_obs_end_utc=None,
    context: str = "comparison",
    testing: bool = False,
    logger=None,
) -> str:
    """Log planned slot vs reserved ODS window using a standard operator format.

    Args:
        source_name: Target/source name.
        res_start_utc: Reservation start datetime.
        res_end_utc: Reservation end datetime.
        planned_obs_start_utc: Planned observation start datetime, when known.
        planned_obs_end_utc: Planned observation end datetime, when known.
        context: Short context label (for example ``queue scheduling``).
        testing: Whether to label output as TESTING mode.
        logger: Callable receiving the formatted message. Defaults to ``print``.

    Returns:
        The formatted log message string.
    """
    mode_label = "TESTING" if testing else "NON-TESTING"

    try:
        pacific_tz = ZoneInfo("America/Los_Angeles")
    except Exception:
        pacific_tz = timezone(timedelta(hours=-8))

    def _to_pacific(dt_obj: datetime) -> datetime:
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(pacific_tz)

    def _fmt_clock(dt_obj: datetime) -> str:
        local_dt = _to_pacific(dt_obj)
        clock = local_dt.strftime('%I:%M%p').lstrip('0').lower()
        return f"{clock} {local_dt.strftime('%Z')}"

    def _fmt_local_window(start_dt: datetime, end_dt: datetime) -> str:
        start_local = _to_pacific(start_dt)
        end_local = _to_pacific(end_dt)
        if start_local.date() == end_local.date():
            date_text = start_local.strftime('%b %d, %Y')
            return f"{_fmt_clock(start_dt)} - {_fmt_clock(end_dt)} on {date_text}"
        return (
            f"{_fmt_clock(start_dt)} ({start_local.strftime('%b %d, %Y')}) - "
            f"{_fmt_clock(end_dt)} ({end_local.strftime('%b %d, %Y')})"
        )

    reserved_local = _fmt_local_window(res_start_utc, res_end_utc)

    if isinstance(planned_obs_start_utc, datetime) and isinstance(planned_obs_end_utc, datetime):
        planned_local = _fmt_local_window(planned_obs_start_utc, planned_obs_end_utc)
        message = (
            f"[{mode_label}] ODS {context} for {source_name}: "
            f"planned {planned_local} vs reserved {reserved_local}"
        )
    else:
        message = (
            f"[{mode_label}] ODS {context} for {source_name}: "
            f"planned slot unavailable vs reserved {reserved_local}"
        )

    sink = logger if callable(logger) else print
    sink(message)
    return message


def parse_title_text(prop):
    """Extract plain text from Notion ``title`` or ``rich_text`` payloads.

    Args:
        prop: Notion property dictionary.

    Returns:
        Concatenated plain-text value, or an empty string when unavailable.
    """
    if not isinstance(prop, dict):
        return ""

    title_items = prop.get("title", [])
    if title_items:
        return "".join(item.get("plain_text", "") for item in title_items).strip()

    rich_text_items = prop.get("rich_text", [])
    if rich_text_items:
        return "".join(item.get("plain_text", "") for item in rich_text_items).strip()

    return ""


def _normalize_notion_property_title(title: str) -> str:
    """Normalize Notion property titles for resilient matching."""
    text = str(title or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def get_notion_property(properties: dict, *candidate_titles: str) -> dict:
    """Return a Notion property payload by title, tolerant to casing/punctuation.

    Args:
        properties: Notion ``page['properties']`` dictionary.
        *candidate_titles: One or more title variants to try.

    Returns:
        Matching property dictionary, or ``{}`` when no match is found.
    """
    if not isinstance(properties, dict):
        return {}

    normalized_key_map = {
        _normalize_notion_property_title(key): value
        for key, value in properties.items()
    }

    for title in candidate_titles:
        normalized_title = _normalize_notion_property_title(title)
        if normalized_title in normalized_key_map:
            match = normalized_key_map.get(normalized_title)
            if isinstance(match, dict):
                return match

    # Fuzzy fallback: match when candidate text is contained in a property title
    # or vice versa (for cases like "status" vs "observing status").
    for title in candidate_titles:
        normalized_title = _normalize_notion_property_title(title)
        if not normalized_title:
            continue
        title_tokens = set(normalized_title.split())
        for normalized_key, value in normalized_key_map.items():
            if not isinstance(value, dict):
                continue
            if normalized_title in normalized_key or normalized_key in normalized_title:
                return value
            key_tokens = set(normalized_key.split())
            if title_tokens and key_tokens and title_tokens.issubset(key_tokens):
                return value

    return {}

# Index, Antenna, Active Array?, Observing Status
def parse_active_value(prop):
    """Interpret a Notion property payload as an active-array boolean flag.

    Args:
        prop: Notion property dictionary.

    Returns:
        True when property indicates active/enabled state; otherwise False.
    """
    if not isinstance(prop, dict):
        return False

    if "checkbox" in prop:
        return bool(prop.get("checkbox"))

    formula_prop = prop.get("formula") or {}
    if isinstance(formula_prop, dict):
        if "boolean" in formula_prop:
            return bool(formula_prop.get("boolean"))
        formula_string = str(formula_prop.get("string", "")).strip().lower()
        if formula_string in {"true", "yes", "active", "enabled", "1"}:
            return True

    select_name = (prop.get("select") or {}).get("name", "")
    status_name = (prop.get("status") or {}).get("name", "")
    text_value = parse_title_text(prop)

    candidate = (select_name or status_name or text_value).strip().lower()
    candidate = " ".join(candidate.split())
    return candidate in {"true", "yes", "active", "active array", "enabled", "1"}


def parse_observing_status(prop):
    """Extract normalized observing-status text from a Notion property payload.

    Args:
        prop: Notion property dictionary.

    Returns:
        Lowercased and whitespace-normalized status text.
    """
    if not isinstance(prop, dict):
        return ""

    # Preferred path for current Notion schema: multi_select status tags.
    multi_select_items = prop.get("multi_select") or []
    if isinstance(multi_select_items, list):
        names = []
        for item in multi_select_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip().lower()
            if name:
                names.append(" ".join(name.split()))
        if names:
            # Use first tag for compatibility with existing single-status logic.
            return names[0]

    select_name = (prop.get("select") or {}).get("name", "")
    status_name = (prop.get("status") or {}).get("name", "")
    formula_string = str((prop.get("formula") or {}).get("string", "")).strip().lower()
    text_value = parse_title_text(prop)

    value = (select_name or status_name or formula_string or text_value).strip().lower()
    return " ".join(value.split())







def _normalize_target_id_text(target_id_value):
    """Normalize target ID values for stable matching across CSV type differences."""
    if target_id_value is None or pd.isna(target_id_value):
        return ""

    try:
        if isinstance(target_id_value, (int, np.integer)):
            return str(int(target_id_value))
        if isinstance(target_id_value, float) and np.isfinite(target_id_value):
            if float(target_id_value).is_integer():
                return str(int(target_id_value))
    except Exception:
        pass

    text = str(target_id_value).strip()
    if re.fullmatch(r"\d+\.0+", text):
        return text.split(".", 1)[0]
    return text


def _format_name_id_label(source_name, target_id_text: str) -> str:
    """Return a user-facing target label in the form ``(Name - ID###)``."""
    name_text = str(source_name or "Unknown").strip() or "Unknown"
    id_text = str(target_id_text or "?").strip() or "?"
    id_display = id_text if id_text.upper().startswith("ID") else f"ID{id_text}"
    return f"({name_text} - {id_display})"


# Need to rewrite these two definitions to work with my files.
# Also, currently 0 means unobserved and 1 means observed. Need to make sure they agree
def is_observed(observed_list, target_id, freq_mhz):
    """
    Check if a source has been observed at a specific frequency.

    Args:
        observed_list: Path to observed list CSV
        target_id: Unique target ID (must match 'ID' column)
        freq_mhz: Frequency in MHz (int)

    Returns:
        1 if observed, 0 if not observed

    Raises:
        ValueError: If target ID not found or frequency column missing
    """
    if not isinstance(freq_mhz, int):
        raise TypeError(f"Frequency must be an integer (MHz), got {type(freq_mhz).__name__}")

    normalized_target_id = _normalize_target_id_text(target_id)
    if not normalized_target_id:
        raise ValueError(f"Target ID must be provided, got: {target_id}")

    try:
        source_entries = pd.read_csv(observed_list)
    except FileNotFoundError:
        raise FileNotFoundError(f"Observed list not found: {observed_list}")
    except pd.errors.ParserError as e:
        raise RuntimeError(f"Failed to parse observed list CSV: {e}")

    cfreq_name = f"cfreq_{freq_mhz}mhz"
    column_lookup = {_normalize_csv_key(col): col for col in source_entries.columns}
    id_col = column_lookup.get('id')
    cfreq_col = column_lookup.get(_normalize_csv_key(cfreq_name))

    # Check if frequency column exists
    if cfreq_col is None:
        raise ValueError(f"Frequency column not found: '{cfreq_name}'. Available columns: {source_entries.columns.tolist()}")

    if id_col is None:
        raise ValueError(f"Observed CSV missing required 'ID' column. Found: {source_entries.columns.tolist()}")

    id_series = source_entries[id_col].map(_normalize_target_id_text)
    row = source_entries.loc[id_series == normalized_target_id]

    if row.empty:
        available_ids = [i for i in source_entries[id_col].map(_normalize_target_id_text).tolist() if i]
        raise ValueError(f"Target ID '{normalized_target_id}' not found in observed list. Available IDs: {available_ids}")

    # Return the observation status
    return int(row[cfreq_col].values[0])

def mark_as_observed(observed_list, target_id, freq_mhz, source_name=None):
    """
    Mark a target as observed at a specific frequency.

    Args:
        observed_list: Path to observed list CSV
        target_id: Unique target ID (must match 'ID' column)
        freq_mhz: Frequency in MHz (int)
        source_name: Optional display name for logging

    Raises:
        ValueError: If target ID not found or frequency column missing
        RuntimeWarning: If target was already marked as observed
    """
    if not isinstance(freq_mhz, int):
        raise TypeError(f"Frequency must be an integer (MHz), got {type(freq_mhz).__name__}")

    normalized_target_id = _normalize_target_id_text(target_id)
    if not normalized_target_id:
        raise ValueError(f"Target ID must be provided, got: {target_id}")

    try:
        source_entries = pd.read_csv(observed_list)
    except FileNotFoundError:
        raise FileNotFoundError(f"Observed list not found: {observed_list}")
    except pd.errors.ParserError as e:
        raise RuntimeError(f"Failed to parse observed list CSV: {e}")

    cfreq_name = f"cfreq_{freq_mhz}mhz"
    column_lookup = {_normalize_csv_key(col): col for col in source_entries.columns}
    id_col = column_lookup.get('id')
    cfreq_col = column_lookup.get(_normalize_csv_key(cfreq_name))

    # Check if frequency column exists
    if cfreq_col is None:
        raise ValueError(f"Frequency column not found: '{cfreq_name}'. Available columns: {source_entries.columns.tolist()}")

    if id_col is None:
        raise ValueError(f"Observed CSV missing required 'ID' column. Found: {source_entries.columns.tolist()}")

    id_series = source_entries[id_col].map(_normalize_target_id_text)
    mask = id_series == normalized_target_id
    if not mask.any():
        available_ids = [i for i in source_entries[id_col].map(_normalize_target_id_text).tolist() if i]
        raise ValueError(f"Target ID '{normalized_target_id}' not found in observed list. Available IDs: {available_ids}")

    row_index = source_entries.index[mask][0]
    resolved_name = source_name
    plain_name_col = column_lookup.get('plaintext name')
    if not resolved_name and plain_name_col is not None:
        resolved_name = source_entries.at[row_index, plain_name_col]
    target_label = _format_name_id_label(resolved_name, normalized_target_id)

    # Check current status
    current_val = source_entries.loc[mask, cfreq_col].values[0]

    if current_val == 0:
        # Mark as observed
        source_entries.loc[mask, cfreq_col] = 1
        source_entries.to_csv(observed_list, index=False)
        print(f"Marked {target_label} as observed at {freq_mhz} MHz")
    elif current_val == 1:
        print(f"WARNING: {target_label} was already marked as observed at {freq_mhz} MHz")


def validate_csv_name_agreement(target_csv_path, observed_csv_path, raise_on_error=False):
    """
    Check that all targets in the target CSV exist in the observed CSV.

    This prevents the case where typos or formatting mismatches cause targets
    to never be marked as observed.

    Args:
        target_csv_path: Path to target CSV file
        observed_csv_path: Path to observed list CSV file
        raise_on_error: If True, raise an exception on mismatch; if False, warn and return

    Returns:
        dict with keys:
            'agreement': bool - True if all target names match
            'missing_in_observed': list - Target names not in observed list
            'extra_in_observed': list - Names in observed list not in targets
            'message': str - Human-readable summary
    """
    try:
        target_df = pd.read_csv(target_csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read target CSV: {e}")

    try:
        observed_df = pd.read_csv(observed_csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read observed CSV: {e}")

    # Check for required column
    if 'Plaintext Name' not in target_df.columns:
        raise ValueError(f"Target CSV missing 'Plaintext Name' column. Found: {target_df.columns.tolist()}")
    if 'Plaintext Name' not in observed_df.columns:
        raise ValueError(f"Observed CSV missing 'Plaintext Name' column. Found: {observed_df.columns.tolist()}")

    target_names = set(target_df['Plaintext Name'].dropna())
    observed_names = set(observed_df['Plaintext Name'].dropna())

    missing_in_observed = sorted(target_names - observed_names)
    extra_in_observed = sorted(observed_names - target_names)

    agreement = (len(missing_in_observed) == 0 and len(extra_in_observed) == 0)

    message_parts = []
    if agreement:
        message_parts.append("CSV names agree perfectly")
    else:
        message_parts.append("CSV name disagreement detected:")
        if missing_in_observed:
            message_parts.append(f"  - {len(missing_in_observed)} targets in TARGET CSV but NOT in OBSERVED CSV:")
            for name in missing_in_observed[:5]:
                message_parts.append(f"      '{name}'")
            if len(missing_in_observed) > 5:
                message_parts.append(f"      ... and {len(missing_in_observed) - 5} more")
        if extra_in_observed:
            message_parts.append(f"  - {len(extra_in_observed)} entries in OBSERVED CSV but NOT in TARGET CSV:")
            for name in extra_in_observed[:5]:
                message_parts.append(f"      '{name}'")
            if len(extra_in_observed) > 5:
                message_parts.append(f"      ... and {len(extra_in_observed) - 5} more")

    message = "\n".join(message_parts)

    if not agreement:
        if raise_on_error:
            raise ValueError(message)
        else:
            print("WARNING")
            print(message)

    return {
        'agreement': agreement,
        'missing_in_observed': missing_in_observed,
        'extra_in_observed': extra_in_observed,
        'message': message
    }








def extract_horizons_id(target_value):
    """Extract a JPL Horizons identifier from flexible target text.

    Normalization steps applied in order:
      1. Non-string or missing values are returned unchanged.
      2. If the value is ';'-joined (e.g. '899; A899_UB' from ATA filenames that
         encode both the asteroid number and provisional designation), the first
         non-empty part is used — the asteroid number is the most reliable
         Horizons lookup key.
      3. If the value contains a '(DESIGNATION)' group, the LAST such group is
         used (e.g. '15 Eunomia (A851 OA)' -> 'A851 OA', or
         '153P/Ikeya-Zhang [2002] (74) - default' -> '74').
      4. Underscores are replaced with spaces, because ATA filenames substitute
         underscores for spaces (e.g. 'A851_OA' -> 'A851 OA').

    Args:
        target_value: Target identifier text or object.

    Returns:
        Parsed Horizons ID when present; otherwise the original value (or
        unchanged non-string input).
    """
    if not isinstance(target_value, str) or pd.isna(target_value):
        return target_value

    text = target_value.strip()
    if not text:
        return target_value

    # Handle ';'-joined "number; designation" pairs from parsed ATA filenames.
    if ';' in text:
        parts = [p.strip() for p in text.split(';') if p.strip()]
        if parts:
            text = parts[0]

    # Extract the LAST '(...)' group anywhere in the string, so names like
    # '153P/Ikeya-Zhang [2002] (74) - default' yield '74'.
    m = re.search(r'\(([^)]+)\)(?=[^()]*$)', text)
    if m:
        return m.group(1).strip().replace('_', ' ')

    return text.replace('_', ' ')


def _query_horizons_single_target(target_id, location, query_start, query_end, time_step, max_retries=2, stop_checker=None):
    """
    Query Horizons for a single target with retry logic.

    Retry model:
    - ``max_retries`` controls how many full attempts are made.
    - Each attempt tries the provided ``time_step`` first, then falls back to
      ``60m`` and ``1h``.
    - A short linear backoff is applied between attempts.

    Args:
        target_id: Horizons object identifier.
        location: Observatory location dictionary for Horizons.
        query_start: Query start timestamp.
        query_end: Query end timestamp.
        time_step: Preferred Horizons step string.
        max_retries: Number of full attempts to perform (minimum 1).
        stop_checker: Optional cooperative stop callback.

    Returns (ra_deg, dec_deg) or (np.nan, np.nan) on failure.
    """
    time_steps_to_try = [time_step, '60m', '1h']

    try:
        total_attempts = max(1, int(max_retries))
    except Exception:
        total_attempts = 2

    for attempt_idx in range(total_attempts):
        if callable(stop_checker):
            stop_checker()
        if attempt_idx > 0:
            delay_seconds = min(10 * attempt_idx, 60)
            print(
                f"  Retry attempt {attempt_idx + 1}/{total_attempts} "
                f"after {delay_seconds}s delay..."
            )
            time.sleep(delay_seconds)

        for step in time_steps_to_try:
            if callable(stop_checker):
                stop_checker()
            try:
                obj = Horizons(id=target_id, location=location,
                              epochs={'start': query_start, 'stop': query_end, 'step': step})
                eph = obj.ephemerides()

                # Extract RA and DEC from first row
                ra_deg = eph['RA'][0]
                dec_deg = eph['DEC'][0]
                print(f"  Successfully queried Horizons: RA={ra_deg:.4f}°, DEC={dec_deg:.4f}°")
                return ra_deg, dec_deg

            except Exception as e:
                error_msg = str(e).split('\n')[0][:100]  # First line of error, truncated
                if step != time_steps_to_try[-1]:
                    continue  # Try next time step in this attempt
                if attempt_idx < total_attempts - 1:
                    print(
                        f"  Attempt {attempt_idx + 1}/{total_attempts} failed "
                        f"for target {target_id}: {error_msg}"
                    )
                else:
                    print(
                        f"  Query failed after {total_attempts} attempt(s) "
                        f"for target {target_id}: {error_msg}"
                    )

    return np.nan, np.nan

def mass_horizons_query(target_list, output_dir, obs_location, obs_start, obs_end, time_step, stop_checker=None, max_retries=2):
    """
    Query JPL Horizons for RA and DEC for all targets in the target list.

    Args:
        target_list: Path to CSV file with target information
        output_dir: Directory to save results
        obs_location: Observatory location dict {'lon': float, 'lat': float, 'elevation': float}
        obs_start: Observation start time (string, format '%Y-%m-%d %H:%M')
        obs_end: Observation end time (string, format '%Y-%m-%d %H:%M')
        time_step: Time step for ephemeris (string, e.g. '1m', '6h')
        stop_checker: Optional callable invoked periodically to allow cooperative
            stop/abort handling (for example from a GUI). If None, query runs
            normally with no stop checks.
        max_retries: Number of full Horizons retry attempts per target.

    Returns:
        DataFrame with columns: ID, Plaintext Name, Horizons Name, Solar System Flag, RA (deg), DEC, RA (hours)
    """
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)

    if callable(stop_checker):
        stop_checker()
    print("Beginning Horizons query process...")
    print(f"  Location: {obs_location}")
    print(f"  Time range: {obs_start} to {obs_end}")
    print(f"  Time step: {time_step}")
    print("=" * 70)

    # Load and validate target CSV
    try:
        target_df = pd.read_csv(target_list)
    except FileNotFoundError:
        raise FileNotFoundError(f"Target list not found: {target_list}")
    except pd.errors.ParserError as e:
        raise RuntimeError(f"Failed to parse target CSV: {e}\nCheck that {target_list} is a valid CSV file.")

    # Validate required columns
    required_cols = ['ID', 'Plaintext Name', 'Horizons Name', 'Solar System Flag',
                     'RA (deg)', 'DEC']
    missing_cols = [col for col in required_cols if col not in target_df.columns]
    if missing_cols:
        raise ValueError(f"Target CSV missing required columns: {missing_cols}\nFound columns: {target_df.columns.tolist()}")

    print(f"Target CSV loaded: {len(target_df)} targets")
    print(f"Columns: {target_df.columns.tolist()}\n")

    # Build results incrementally (avoids slow pd.concat in loop)
    results_data = []
    failed_targets = []

    for idx, row in target_df.iterrows():
        if callable(stop_checker):
            stop_checker()
        target_name = row['Plaintext Name']
        horizons_name = row['Horizons Name']
        target_id = row['ID']

        # Skip NaN targets
        if pd.isna(horizons_name):
            print(f"[{idx+1}/{len(target_df)}] {target_name:30s} [SKIP] (no Horizons Name)")
            results_data.append({
                'ID': target_id,
                'Plaintext Name': target_name,
                'Horizons Name': horizons_name,
                'Solar System Flag': row.get('Solar System Flag', 0),
                'RA (deg)': row['RA (deg)'],
                'DEC': row['DEC'],
                'RA (hours)': row['RA (deg)'] / 15 if not pd.isna(row['RA (deg)']) else np.nan
            })
            continue

        # Extract ID from parentheses if present
        horizons_id = extract_horizons_id(horizons_name)

        print(f"[{idx+1}/{len(target_df)}] {target_name:30s} (ID: {horizons_id})")

        # Query Horizons
        ra_deg, dec_deg = _query_horizons_single_target(
            horizons_id,
            obs_location,
            obs_start,
            obs_end,
            time_step,
            max_retries=max_retries,
            stop_checker=stop_checker,
        )

        # Use queried results if valid, otherwise keep CSV values
        if not pd.isna(ra_deg) and not pd.isna(dec_deg):
            use_ra = ra_deg
            use_dec = dec_deg
        else:
            use_ra = row['RA (deg)']
            use_dec = row['DEC']
            if pd.isna(use_ra) or pd.isna(use_dec):
                failed_targets.append((target_name, horizons_id))

        # Convert RA to hours
        ra_hours = use_ra / 15 if not pd.isna(use_ra) else np.nan

        results_data.append({
            'ID': target_id,
            'Plaintext Name': target_name,
            'Horizons Name': horizons_name,
            'Solar System Flag': row.get('Solar System Flag', 0),
            'RA (deg)': use_ra,
            'DEC': use_dec,
            'RA (hours)': ra_hours
        })

    # Create results DataFrame from accumulated data (much faster than loop concatenation)
    results_df = pd.DataFrame(results_data)

    # Save results
    output_path = os.path.join(output_dir, 'HorizonsOutput.csv')
    results_df.to_csv(output_path, index=False)

    print("\n" + "=" * 70)
    print(f"Horizons query complete. Results saved to: {output_path}")
    if failed_targets:
        print(f"[WARNING] {len(failed_targets)} targets could not be queried:")
        for name, hid in failed_targets[:5]:  # Show first 5
            print(f"  - {name} ({hid})")
        if len(failed_targets) > 5:
            print(f"  ... and {len(failed_targets) - 5} more")
    print("=" * 70 + "\n")

    return results_df

# Example usage:
# results_df = mass_horizons_query(target_list, output_dir, obs_location, obs_start, obs_end, time_step)







# Still need to tweak this
# generate_ephemeris_files creates ephemeris files for a list of targets using JPL Horizons.
# It queries Horizons for each target, interpolates the ephemeris data, and saves the results as .ephem files.
# To use:
# targets_to_process: list/Series of Horizons target names
# id_names_to_process: list/Series of IDs corresponding to targets
# output_dir: directory to save the working ephemeris file
# output_dir2: directory to archive all generated ephemeris files
# scan_start, scan_end: observation time range (strings)
# location: observer location code (string)
# TFMT: time format string (default "%Y-%m-%dT%H:%M")
# TFMT="%Y-%m-%dT%H:%M"

def generate_ephemeris_files(target_to_process, id_to_process, output_dir, output_dir2,
                             scan_start, scan_end, time_step, obs_location):
    """
    Generate ephemeris files for a single target.

    Creates two copies of ATA-compatible .ephem files:
    - Working copy in output_dir with filename JPLH_{target_name}.ephem
    - Archive copy in output_dir2 with timestamp-tagged filename

    .ephem file format (tab/space-separated columns):
    1. TAI time (nanoseconds since epoch) - integer
    2. Azimuth (degrees) - float (5 decimals)
    3. Elevation (degrees) - float (5 decimals)
    4. Inverse radius - float (scientific notation, 10 decimals; all zeros for ATA use)

    Returns:
        (az, el, ra, dec, safe_t) if successful; (None, None, None, None, None) on failure
    """
    print("Generating ephemeris file for the ATA to use:")

    t = target_to_process
    this_id_name = str(id_to_process).replace(" ", "_")
    safe_t = str(t).replace(" ", "_")
    scan_start_name = scan_start.replace(':', '-').replace(' ', 'T')

    # Skip if target name is NaN
    if pd.isna(t):
        print(f"  Skipping NaN target (ID: {id_to_process})")
        return None, None, None, None, None

    target_id = id_to_process
    print(f"  Processing: {t} (ID: {target_id})")

    # Try multiple step formats in case of errors
    time_steps_to_try = [time_step, '60m', '1h']
    eph = None

    for step in time_steps_to_try:
        try:
            print(f"    Querying Horizons with step={step}...")
            obj = Horizons(id=t, location=obs_location,
                          epochs={'start': scan_start, 'stop': scan_end, 'step': step})
            eph = obj.ephemerides()
            print(f"    Ephemeris query successful")
            break  # Success, exit loop

        except ValueError as e:
            # ValueError often means bad time step format; try next one
            if step != time_steps_to_try[-1]:
                continue  # Try next step
            print(f"    ValueError: {str(e)[:80]}")

        except Exception as e:
            error_str = str(e)[:100]
            print(f"    Query failed: {error_str}")
            if step != time_steps_to_try[-1]:
                continue  # Try next step

    # Check if we got results
    if eph is None or len(eph) == 0:
        print(f"  Skipping {t}: ephemeris query returned no data")
        return None, None, None, None, None

    # Check for minimum data points (need at least 2 for interpolation)
    if len(eph) < 2:
        print(f"  Skipping {t}: ephemeris has only {len(eph)} point(s), need at least 2")
        return None, None, None, None, None

    # Check for required columns
    required_cols = ['datetime_jd', 'AZ', 'EL', 'RA', 'DEC']
    missing_cols = [col for col in required_cols if col not in eph.colnames]
    if missing_cols:
        print(f"  Skipping {t}: missing columns in ephemeris: {missing_cols}")
        return None, None, None, None, None

    try:
        # Convert JD to TAI seconds
        unixTime = (eph['datetime_jd'] - 2440587.5) * 86400
        taiSec = np.int64(np.round((unixTime + 37)*1e9))  # Adding leap second offset

        # Check for duplicate time values (would cause interpolation to fail)
        if len(np.unique(taiSec)) < len(taiSec):
            print(f"  Warning: found duplicate timestamps in ephemeris, removing...")
            unique_indices = np.concatenate([[True], np.diff(taiSec) != 0])
            taiSec = taiSec[unique_indices]
            eph = eph[unique_indices]

            if len(taiSec) < 2:
                print(f"  Skipping {t}: not enough unique timestamps after deduplication")
                return None, None, None, None, None

        # Create interpolators
        az_interp = scipy.interpolate.interp1d(taiSec, eph['AZ'])
        el_interp = scipy.interpolate.interp1d(taiSec, eph['EL'])
        ra_interp = scipy.interpolate.interp1d(taiSec, eph['RA'])
        dec_interp = scipy.interpolate.interp1d(taiSec, eph['DEC'])

        # Generate grid of interpolated points
        ata_tai_grid = np.arange(taiSec[0], taiSec[-1], 25*1e9)

        if len(ata_tai_grid) == 0:
            print(f"  Skipping {t}: ephemeris time span too short")
            return None, None, None, None, None

        # Interpolate
        az = az_interp(ata_tai_grid)
        el = el_interp(ata_tai_grid)
        ra_deg = ra_interp(ata_tai_grid)
        dec = dec_interp(ata_tai_grid)

        # Convert RA to hours
        ra = ra_deg / 360 * 24

        # Prepare file data
        inv_rad = np.zeros_like(az)
        eph_file_np = np.column_stack([ata_tai_grid, az, el, inv_rad])

        # Save archival copy
        archive_path = os.path.join(output_dir2, f"JPLH_{this_id_name}_{safe_t}_{scan_start_name}.ephem")
        try:
            np.savetxt(archive_path, eph_file_np, fmt='%i   %.5f  %.5f  %.10E')
            print(f"    Archived to: {os.path.basename(archive_path)}")
        except Exception as e:
            print(f"    Failed to save archive: {e}")

        # Save working copy
        output_ephem = os.path.join(output_dir, f"JPLH_{safe_t}.ephem")
        try:
            np.savetxt(output_ephem, eph_file_np, fmt='%i   %.5f  %.5f  %.10E')
            print(f"    Saved working ephemeris: {os.path.basename(output_ephem)}")
        except Exception as e:
            print(f"    Failed to save working ephemeris: {e}")
            return None, None, None, None, None

        return az, el, ra, dec, safe_t

    except Exception as e:
        print(f"  Error processing ephemeris: {str(e)[:100]}")
        return None, None, None, None, None





# Global status callback (set by GUI)
_status_callback = None

def set_status_callback(callback):
    # External API: GUI can register a callback to receive status updates.
    # Allows text to be printed to the GUI and the normal terminal
    global _status_callback
    _status_callback = callback

def sleep_with_continuous_updates_seconds(total_seconds: int):
    remaining_seconds = total_seconds

    while remaining_seconds > 0:
        minutes, seconds = divmod(remaining_seconds, 60)
        message = f"{minutes:02d}:{seconds:02d} remaining"
        print(message, end="\r")

        # Also log to GUI if callback is set
        if _status_callback:
            _status_callback(message)

        time.sleep(1)
        remaining_seconds -= 1

    final_message = f"Waited {total_seconds} second{'s' if total_seconds != 1 else ''}"
    print(final_message)
    if _status_callback:
        _status_callback(final_message)

def countdown_sleep(total_seconds, interval=1):
    # Sleep with periodic countdown display, updates only when minute changes
    remaining = total_seconds
    last_minute = int(remaining / 60) + 1  # Start higher so first minute prints
    while remaining > 0:
        current_minute = int(remaining / 60)
        if current_minute != last_minute:
            message = f"Waiting for ODS... {current_minute}:00 remaining"
            print(message)
            if _status_callback:
                _status_callback(message)
            last_minute = current_minute
        time.sleep(min(interval, remaining))
        remaining -= interval
    final_message = "Wait complete!"
    print(final_message)
    if _status_callback:
        _status_callback(final_message)



def primary_beam_diameter(center_freq):
    # Constants
    c = const.c # Speed of light
    d = 6.1 * u.m # Antenna diameter
    center_freq = center_freq * u.GHz # Assume user input in GHz
    lambda_ = c / center_freq # Wavelength
    # Primary beam diameter
    pb_diam = Angle ((1.22 * lambda_ / d) * u.radian)
    return pb_diam.degree

def synthesized_beam_diameter(center_freq):
    # Synthesized beam diameter
    sb_diam = Angle ((3.5 * 1.2 / center_freq) * u.arcmin) # Assume user input in GHz
    return sb_diam.degree




# ODS protection from ASP
def OG_push_ASP_ods(ra_deg, dec_deg, length_hours=12):
    """
    NOTE: this only applies to ASP observations
    """
    from odsutils import ods_engine
    from datetime import datetime, timedelta, timezone

    ods = ods_engine.ODS(conlog='ERROR', defaults='$ods_defaults_ata_B.json')

    asp_ra_coord_deg  = ra_deg  # RA of ASP at the middle of the night
    asp_dec_coord_deg = dec_deg # DEC of ASP at the middle of the night

    #info = check.check_radec(ra_deg*24./360, dec_deg)

    dt_now = datetime.utcnow()
    dt_end = dt_now + timedelta(hours=length_hours)

    #if info['set_time'] < dt_end:
    #    print(f"source will set before {length_hours}")
    #    dt_end = info['set_time'] + timedelta(hours = 1) #just do 1 hour after elevation=16

    cfg = {
            'src_id': 'ASP',
            'src_ra_j2000_deg': asp_ra_coord_deg,
            'src_dec_j2000_deg': asp_dec_coord_deg,
            'src_start_utc': dt_now.isoformat(),
            'src_end_utc': dt_end.isoformat()
        }
    ods.add(cfg)
    ods.update_by_elevation()
    try:
        ods.post_ods("/opt/mnt/share/ods_project/ods_ASP.json")
        ods.assemble_ods("/opt/mnt/share/ods_project", post_to="/opt/mnt/share/ods_upload/ods.json")
    except:  #anything
        pass


def new_ASP_push_ods(ra_deg, dec_deg, length_hours=12):
    """
    NOTE: this only applies to ASP observations
    """
    from odsutils import ods_engine
    from datetime import datetime, timedelta, timezone

    ods = ods_engine.ODS(conlog='ERROR', defaults='$ods_defaults_ata_B.json')

    asp_ra_coord_deg  = ra_deg  # RA of ASP at the middle of the night
    asp_dec_coord_deg = dec_deg # DEC of ASP at the middle of the night

    #info = check.check_radec(ra_deg*24./360, dec_deg)

    dt_now = datetime.utcnow()
    dt_end = dt_now + timedelta(hours=length_hours)

    #if info['set_time'] < dt_end:
    #    print(f"source will set before {length_hours}")
    #    dt_end = info['set_time'] + timedelta(hours = 1) #just do 1 hour after elevation=16

    cfg = {
            'src_id': 'ASP',
            'src_ra_j2000_deg': asp_ra_coord_deg,
            'src_dec_j2000_deg': asp_dec_coord_deg,
            'src_start_utc': dt_now.isoformat(),
            'src_end_utc': dt_end.isoformat()
        }
    ods.add(cfg)
    ods.update_by_elevation()
    try:
        ods.post_ods("/opt/mnt/share/ods_project/ods_ASP.json")
        ods.assemble_ods("/opt/mnt/share/ods_project", post_to="/opt/mnt/share/ods_upload/ods.json")
    except:  #anything
        pass




def push_ods(
    source,
    ra_deg,
    dec_deg,
    res_start_utc=None,
    res_end_utc=None,
    frequencies_mhz=None,
    bands=None,
    project_name="survey",
    project_folder="",
    length_hours=12,
    defaults=None,
    ods_rados="/opt/mnt/share/ods_project",
    ods_upload="/opt/mnt/share/ods_upload/ods.json",
    ods_assembly=True,
    project=None,
):
    """Post one observation to ODS using ods_engine API following Standard_Version_B.

    Keeps reservation time window (res_start_utc, res_end_utc) and frequency bands
    (frequencies_mhz / bands) strictly separate.

    Parameters:
        source: Target name or identifier.
        ra_deg: Target right ascension in degrees (float).
        dec_deg: Target declination in degrees (float).
        res_start_utc: Reservation start timestamp (datetime, Time, or ISO string).
        res_end_utc: Reservation end timestamp (datetime, Time, or ISO string).
        frequencies_mhz: List of center frequencies in MHz (e.g. [1336, 2008, 4536, 8336]).
        bands: List of band dicts [{'freq_lower_hz': ..., 'freq_upper_hz': ...}].
        project_name: Project tag used for ODS filenames.
        project_folder: Path to project directory for local testing/storage.
        length_hours: Duration in hours if res_start_utc/res_end_utc are omitted.
        defaults: Optional path to ODS defaults JSON file.
        ods_rados: Project directory for ODS JSON records.
        ods_upload: Destination JSON file for assembled ODS records.
        ods_assembly: Whether to assemble and deduplicate records into ods_upload.
        project: Alias for project_name.
    """
    if project is not None and project_name == "survey":
        project_name = project

    # Handle parameter order fallback: if res_start_utc was passed as bands container
    if bands is None and isinstance(res_start_utc, (list, tuple, dict)):
        bands = res_start_utc
        res_start_utc = None

    # Resolve reservation start and end times
    now_dt = datetime.now(timezone.utc)
    if res_start_utc is not None:
        if isinstance(res_start_utc, datetime):
            dt_start = res_start_utc if res_start_utc.tzinfo else res_start_utc.replace(tzinfo=timezone.utc)
            dt_start_utc = dt_start.astimezone(timezone.utc)
        elif isinstance(res_start_utc, str):
            try:
                dt_start_utc = datetime.fromisoformat(res_start_utc.replace('Z', '+00:00'))
                if dt_start_utc.tzinfo is None:
                    dt_start_utc = dt_start_utc.replace(tzinfo=timezone.utc)
            except Exception:
                dt_start_utc = now_dt
        else:
            dt_start_utc = now_dt
    else:
        dt_start_utc = now_dt

    if res_end_utc is not None:
        if isinstance(res_end_utc, datetime):
            dt_end = res_end_utc if res_end_utc.tzinfo else res_end_utc.replace(tzinfo=timezone.utc)
            dt_end_utc = dt_end.astimezone(timezone.utc)
        elif isinstance(res_end_utc, str):
            try:
                dt_end_utc = datetime.fromisoformat(res_end_utc.replace('Z', '+00:00'))
                if dt_end_utc.tzinfo is None:
                    dt_end_utc = dt_end_utc.replace(tzinfo=timezone.utc)
            except Exception:
                dt_end_utc = dt_start_utc + timedelta(hours=max(1, int(length_hours or 12)))
        else:
            dt_end_utc = dt_start_utc + timedelta(hours=max(1, int(length_hours or 12)))
    else:
        dt_end_utc = dt_start_utc + timedelta(hours=max(1, int(length_hours or 12)))

    if dt_end_utc <= dt_start_utc:
        dt_end_utc = dt_start_utc + timedelta(hours=max(1, int(length_hours or 12)))

    # Resolve frequency bands
    resolved_bands = []
    if bands is not None:
        raw_bands = [bands] if isinstance(bands, dict) else list(bands)
        for b in raw_bands:
            if isinstance(b, dict) and 'freq_lower_hz' in b and 'freq_upper_hz' in b:
                resolved_bands.append({
                    'freq_lower_hz': float(b['freq_lower_hz']),
                    'freq_upper_hz': float(b['freq_upper_hz']),
                })
    elif frequencies_mhz is not None:
        raw_freqs = [frequencies_mhz] if not isinstance(frequencies_mhz, (list, tuple, set)) else list(frequencies_mhz)
        for f in raw_freqs:
            try:
                freq_val = float(f)
                if np.isfinite(freq_val) and freq_val > 0:
                    resolved_bands.append({
                        'freq_lower_hz': float(1e6 * (freq_val - 345.0)),
                        'freq_upper_hz': float(1e6 * (freq_val + 345.0)),
                    })
            except Exception:
                continue

    if not resolved_bands:
        for freq_mhz in FREQ_RANGE:
            resolved_bands.append({
                'freq_lower_hz': float(1e6 * (float(freq_mhz) - 345.0)),
                'freq_upper_hz': float(1e6 * (float(freq_mhz) + 345.0)),
            })

    # Initialize ODS engine
    try:
        from odsutils import ods_engine, DATA_PATH
    except Exception as exc:
        print(f"ODS engine not available: 'odsutils' import failed: {exc}")
        return False

    defaults_path = None
    if defaults and os.path.exists(str(defaults)):
        defaults_path = str(defaults)
    elif DATA_PATH:
        candidate = os.path.join(DATA_PATH, 'ods_defaults_ata_B.json')
        if os.path.exists(candidate):
            defaults_path = candidate

    try:
        if defaults_path:
            ods = ods_engine.ODS(conlog='ERROR', defaults=defaults_path)
        else:
            ods = ods_engine.ODS(conlog='ERROR')
    except Exception as exc:
        print(f"Failed to initialize ODS engine: {exc}")
        return False

    # Resolve target project directory and upload path
    project_tag = make_ods_project_tag(project_name=project_name, project_folder=project_folder)
    clean_source = re.sub(r'[^A-Za-z0-9._-]+', '_', str(source or 'survey_target')).strip('._-') or 'target'

    on_ata_share = os.path.isdir("/opt/mnt/share/ods_project") and os.path.isdir("/opt/mnt/share/ods_upload")
    if on_ata_share:
        project_dir = "/opt/mnt/share/ods_project"
        upload_target = "/opt/mnt/share/ods_upload/ods.json"
    else:
        base_dir = project_folder if (project_folder and os.path.isdir(project_folder)) else os.getcwd()
        project_dir = os.path.join(base_dir, "ods_project")
        upload_dir = os.path.join(base_dir, "ods_upload")
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(upload_dir, exist_ok=True)
        upload_target = os.path.join(upload_dir, "ods.json")

    target_file = os.path.join(project_dir, f"ods_{project_tag}_{clean_source}.json")

    dt_start_str = dt_start_utc.replace(tzinfo=None).isoformat(timespec='seconds')
    dt_end_str = dt_end_utc.replace(tzinfo=None).isoformat(timespec='seconds')

    # Build and add records for all bands
    for band in resolved_bands:
        cfg = {
            'src_id': clean_source,
            'src_ra_j2000_deg': float(ra_deg),
            'src_dec_j2000_deg': float(dec_deg),
            'src_start_utc': dt_start_str,
            'src_end_utc': dt_end_str,
            'freq_lower_hz': float(band['freq_lower_hz']),
            'freq_upper_hz': float(band['freq_upper_hz']),
        }
        ods.add(cfg)

    try:
        ods.update_by_elevation()
    except Exception:
        pass

    try:
        ods.post_ods(target_file)
    except Exception as exc:
        print(f"Failed to post target ODS file ({target_file}): {exc}")
        return False

    # Assemble and deduplicate across all project files
    if ods_assembly:
        try:
            import glob
            all_entries = []
            seen = set()
            for fp in glob.glob(os.path.join(project_dir, "ods_*.json")):
                try:
                    with open(fp, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        for entry in data.get("ods_data", []):
                            dedup_key = (
                                str(entry.get("src_id")),
                                str(entry.get("src_start_utc")),
                                str(entry.get("src_end_utc")),
                                round(float(entry.get("freq_lower_hz", 0)), 1),
                                round(float(entry.get("freq_upper_hz", 0)), 1),
                            )
                            if dedup_key not in seen:
                                seen.add(dedup_key)
                                all_entries.append(entry)
                except Exception:
                    continue

            all_entries.sort(key=lambda x: str(x.get("src_start_utc", "")))
            os.makedirs(os.path.dirname(os.path.abspath(upload_target)), exist_ok=True)
            with open(upload_target, "w", encoding="utf-8") as fh:
                json.dump({"ods_data": all_entries}, fh, indent=2)
        except Exception as exc:
            print(f"Warning: could not assemble ODS to {upload_target}: {exc}")

    return True





# How ODS is pushed according to "/home/sonata/ods_files/online_ods_mon.txt"
# site_id,site_lat_deg,site_lon_deg,site_el_m,src_id,src_is_pulsar_bool,corr_integ_time_sec,src_ra_j2000_deg,src_dec_j2000_deg,src_radius,src_start_utc,src_end_utc,slew_sec,trk_rate_dec_deg_per_sec,trk_rate_ra_deg_per_sec,freq_lower_hz,freq_upper_hz,notes
# ATA,40.817431,-121.470736,1019.222,3c286,None,1.0,202.784529,30.5091553,None,2025-09-25T01:36:30,2025-09-25T01:46:30,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,3c286,None,1.0,202.784529,30.5091553,None,2025-09-26T01:39:37,2025-09-26T01:49:37,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,3c286,None,1.0,202.784529,30.5091553,None,2025-09-26T01:39:41,2025-09-26T01:49:41,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,3c286,None,1.0,202.784529,30.5091553,None,2025-09-29T18:59:01,2025-09-29T19:09:01,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,3c286,None,1.0,202.784529,30.5091553,None,2025-09-29T19:03:20,2025-09-29T19:13:20,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,3c286,None,1.0,202.784529,30.5091553,None,2025-09-30T00:03:53,2025-09-30T00:13:53,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,3c286,None,1.0,202.784529,30.5091553,None,2025-09-30T00:07:30,2025-09-30T00:17:30,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,ASP,None,1.0,6.30798370937331,2.7266575798254244,None,2025-09-30T03:16:18,2025-09-30T13:10:18,30,0,0,1990000000.0,1995000000.0,None


# Duplicate pushes
# site_id,site_lat_deg,site_lon_deg,site_el_m,src_id,src_is_pulsar_bool,corr_integ_time_sec,src_ra_j2000_deg,src_dec_j2000_deg,src_radius,src_start_utc,src_end_utc,slew_sec,trk_rate_dec_deg_per_sec,trk_rate_ra_deg_per_sec,freq_lower_hz,freq_upper_hz,notes
# ATA,40.817431,-121.470736,1019.222,M51a_b,None,1,202.469583,47.195278,None,2026-09-15T22:19:45,2026-09-15T23:19:45,30,0,0,1990000000,1995000000,None
# ATA,40.817431,-121.470736,1019.222,M51a_b,None,1.0,202.469583,47.195278,None,2026-09-15T22:19:45,2026-09-15T23:19:45,30,0,0,1990000000.0,1995000000.0,None
# ATA,40.817431,-121.470736,1019.222,M51a,None,1,202.469583,47.195278,None,2026-09-15T22:19:46,2026-09-15T23:19:46,30,0,0,1990000000,1995000000,None
# ATA,40.817431,-121.470736,1019.222,M51a,None,1.0,202.469583,47.195278,None,2026-09-15T22:19:46,2026-09-15T23:19:46,30,0,0,1990000000.0,1995000000.0,None















# class Standard_Version_B:
#     """
#     Contains elements defining the ODS standard for Version B as at Sept 2025
#     """
#     fields = {
#         'site_id': str,
#         'site_lat_deg': float,
#         'site_lon_deg': float,
#         'site_el_m': float,
#         'src_id': str,
#         'corr_integ_time_sec': float,
#         'src_ra_j2000_deg': float,
#         'src_dec_j2000_deg': float,
#         'src_start_utc': str,
#         'src_end_utc': str,
#         'slew_sec': float,
#         'trk_rate_dec_deg_per_sec': float,
#         'trk_rate_ra_deg_per_sec': float,
#         'freq_lower_hz': float,
#         'freq_upper_hz': float,
#         'version': str,
#         'dish_diameter_m': float,
#         'subarray': int,
#     }

#     sort_order_time = ['src_start_utc', 'src_end_utc', 'site_id', 'site_lat_deg', 'site_lon_deg', 'site_el_m',
#                        'src_id', 'corr_integ_time_sec', 'src_ra_j2000_deg', 'src_dec_j2000_deg', 'slew_sec',
#                        'trk_rate_dec_deg_per_sec', 'trk_rate_ra_deg_per_sec', 'freq_lower_hz', 'freq_upper_hz',
#                        'version', 'dish_diameter_m', 'subarray']

#     def __init__(self):
#         self.transfer_keys = {
#             'observatory': 'site_id',
#             'lat': 'site_lat_deg',
#             'lon': 'site_lon_deg',
#             'ele': 'site_el_m',
#             'source': 'src_id',
#             'ra': 'src_ra_j2000_deg',
#             'dec': 'src_dec_j2000_deg',
#             'start': 'src_start_utc',
#             'stop': 'src_end_utc'
#         }
#         self.meta_fields = {'data_key': 'ods_data',
#                             'time_fields': ['src_start_utc', 'src_end_utc']}


# def push_ods(source, ra_deg, dec_deg, res_start_utc, res_end_utc,
#              defaults=None,
#              ods_rados="/opt/mnt/share/ods_project/ods_rados.json",
#              ods_upload="/opt/mnt/share/ods_upload/ods.json",
#              ods_assembly=True):
#     """
#     Post one observation to the ODS using the ods_engine API following Standard_Version_B.

#     Required parameters: source, ra_deg, dec_deg, res_start_utc, res_end_utc
#     """
#     try:
#         from odsutils import ods_engine, DATA_PATH
#     except Exception:
#         try:
#             from odsutils import ods_engine
#             DATA_PATH = None
#         except Exception:
#             print("ODS engine not available: 'odsutils' / 'ods_engine' package not installed.")
#             return

#     import os.path as op
#     from datetime import timezone

#     # Resolve defaults file
#     if defaults is None and DATA_PATH:
#         candidate = op.join(DATA_PATH, 'ods_defaults_ata_B.json')
#         if op.exists(candidate):
#             defaults = candidate

#     defaults_dict = {}
#     if defaults and op.exists(defaults):
#         try:
#             with open(defaults, 'r', encoding='utf-8') as fh:
#                 defaults_dict = json.load(fh)
#         except Exception as e:
#             print(f"Warning: failed to read defaults file {defaults}: {e}")

#     std = Standard_Version_B()

#     # Helper to coerce values to expected types when possible
#     def _coerce(key, value):
#         expected = std.fields.get(key)
#         if value is None:
#             return None
#         if expected is None:
#             return value
#         try:
#             return expected(value)
#         except Exception:
#             return value

#     # Build the ODS record using defaults where available and sensible fallbacks
#     ods_record = {}
#     # Frequency defaults from FREQ_RANGE (MHz) -> Hz
#     try:
#         freqs_hz = sorted([int(f) * 1_000_000 for f in FREQ_RANGE])
#         freq_lower_default, freq_upper_default = freqs_hz[0], freqs_hz[-1]
#     except Exception:
#         freq_lower_default, freq_upper_default = 0, 0

#     fallbacks = {
#         'site_id': 'ATA',
#         'site_lat_deg': float(defaults_dict.get('site_lat_deg', 40.817431)),
#         'site_lon_deg': float(defaults_dict.get('site_lon_deg', -121.470736)),
#         'site_el_m': float(defaults_dict.get('site_el_m', 1819.222)),
#         'corr_integ_time_sec': float(defaults_dict.get('corr_integ_time_sec', 1.0)),
#         'slew_sec': float(defaults_dict.get('slew_sec', 30.0)),
#         'trk_rate_dec_deg_per_sec': float(defaults_dict.get('trk_rate_dec_deg_per_sec', 0.0)),
#         'trk_rate_ra_deg_per_sec': float(defaults_dict.get('trk_rate_ra_deg_per_sec', 0.0)),
#         'freq_lower_hz': float(defaults_dict.get('freq_lower_hz', freq_lower_default)),
#         'freq_upper_hz': float(defaults_dict.get('freq_upper_hz', freq_upper_default)),
#         'version': str(defaults_dict.get('version', 'v1.0.0')),
#         'dish_diameter_m': float(defaults_dict.get('dish_diameter_m', 6.1)),
#         'subarray': int(defaults_dict.get('subarray', 0)),
#     }

#     for key in std.fields:
#         if key in ('src_id', 'src_ra_j2000_deg', 'src_dec_j2000_deg', 'src_start_utc', 'src_end_utc'):
#             # will set below from function args
#             ods_record[key] = None
#             continue
#         if key in defaults_dict:
#             ods_record[key] = _coerce(key, defaults_dict.get(key))
#         else:
#             ods_record[key] = fallbacks.get(key)

#     # Set required source/time fields
#     ods_record['src_id'] = str(source)
#     ods_record['src_ra_j2000_deg'] = float(ra_deg)
#     ods_record['src_dec_j2000_deg'] = float(dec_deg)
#     try:
#         ods_record['src_start_utc'] = res_start_utc.astimezone(timezone.utc).isoformat()
#         ods_record['src_end_utc'] = res_end_utc.astimezone(timezone.utc).isoformat()
#     except Exception:
#         ods_record['src_start_utc'] = str(res_start_utc)
#         ods_record['src_end_utc'] = str(res_end_utc)

#     # Instantiate ODS engine
#     try:
#         if defaults and op.exists(defaults):
#             ods = ods_engine.ODS(defaults=defaults, conlog='ERROR')
#         else:
#             ods = ods_engine.ODS(conlog='ERROR')
#     except Exception as e:
#         print(f"Failed to initialize ODS engine: {e}")
#         return

#     try:
#         ods.add(ods_record)
#         try:
#             ods.update_by_elevation()
#         except Exception:
#             pass

#         if ods_assembly:
#             try:
#                 ods.assemble_ods(ods_rados, post_to=ods_upload)
#                 print(f"ODS assembled and posted for source {source}.")
#                 return True
#             except Exception:
#                 try:
#                     ods.post_ods(ods_upload)
#                     print(f"ODS posted for source {source} to {ods_upload}.")
#                     return True
#                 except Exception as e:
#                     print(f"Failed to assemble/post ODS: {e}")
#                     return False
#         else:
#             try:
#                 ods.post_ods(ods_upload)
#                 print(f"ODS posted for source {source} to {ods_upload}.")
#                 return True
#             except Exception as e:
#                 print(f"Failed to post ODS: {e}")
#                 return False
#     except Exception as e:
#         print(f"Error while creating/posting ODS for {source}: {e}")
#         return False

#     # Done







