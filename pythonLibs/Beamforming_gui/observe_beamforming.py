"""Survey observation execution module.

This script accepts csvs with targets, then executes an observation with the ATA.
This script has several capabilities:
It re-orders targets based on current altitude, to ensure decreased atmospheric scattering
It also pushes all targets to ODS to ensure protection from SpaceX satellites.
Sun, Moon, and Planet avoidances can be turned on.
When an observation is finished, it will mark each target as observed.
If it reaches the end of the csv, it will attempt to cycle back through to make sure it didn't miss anything.
Start and End times can be configured before or during an observation.
"""

#TODO: Blayne - Bring in the new obs planning logic and target selection stuff.
# Find a better way to plan the whole session at the beginning, so there isn't as much waiting in the middle.

# CHANGE THESE VALUES FOR YOUR OBSERVATION ==========================================================================================================================================================

# NOTE: You can either change these values manually for your individualized script, or you can use the GUI.

PROJECT_NAME = 'testingtime'  # Name of the project. Used in file names and logging
PROJECT_FOLDER = ''  # Folder path for your project.
# NOTE: e.g. 'exotica' or 'p068'
# NOTE: This folder will have subfolders made inside of it. Make sure it's correct.

# Define scan length
# 300 seconds is 5 minutes
OBS_TIME = 5*60 #300 # In seconds
# The script will automatically add a short buffer so the system can handle it

# The csv_name variable defines the table of targets you want observed. Please ensure it is in the following format:
# NOTE: ID | Plaintext Name | Horizons Name | Solar System Flag | RA (hours) | DEC | RA (deg) | Obs Time |
# Please see the README for more details. Some aliases are allowed, but it is recommended to follow this guide.
CSV_NAME = 'demo_targets.csv'
# NOTE: e.g. 'exotica_targets.csv'

# This file has the ID, Plaintext Name, Solar System Flag, some identifying features if desired (e.g. columns for Sample Type), and columns for each frequency used.
# NOTE: FREQUENCY COLUMNS SHOULD BE NAMED LIKE: cfreq_1336mhz
OBSERVED_LIST = 'demo_observed.csv'
# NOTE: e.g. 'observed_exotica.csv'

# Here is where you will remove bad antennas from the observation
# Define antennas to remove
REMOVE_ANT = []
# NOTE: e.g. REMOVE_ANT = ["2b", "2l", "4e"]
# REMOVE_ANT = [] # For if no antennas need to be removed

SEFD_WEIGHTING = True # This is for antenna weighting. If False, it uses uniform weights. If True, it uses SEFD-based weights.

# ODS requires a 20 minute lead time before it can activate. If your observation is faster than that time, I would suggest adding the wait
# This will load your targets into the ODS database, then wait for that lead time to complete before beginning the actual observations
# ODS lead-time control is configured here for easy access.
# Default operation uses 20 minutes. Testing mode can optionally use a shorter lead.
ODS_LEAD_TIME_MINUTES = 20
TESTING_ODS_LEAD_TIME_MINUTES = 1

QUEUE_WAIT = True # Default is True.
ODS_PUSH = True

PREFER_RA_UNITS = 'deg' # hours or deg
# Don't worry about this, just tells the script which to try first.


# Set each to True to avoid.
MOON_AVOIDANCE = True # Avoid the moon
SUN_AVOIDANCE = True # Avoid the sun, KEEP ON!
PLANET_AVOIDANCE = False # Avoid the planets

# Working-table declination filter for sidereal (Solar System Flag == 0) sources.
# Any sidereal source with DEC below this limit is removed from the working copy.
DEC_LIMIT = -28.0

ALT_MIN = 21
#ALT_MIN = 16.5
ALT_MAX = 85

# Bright-body protection controls
# Keep Sun/Moon protection wider than planet protection by default.
MIN_SUN_MOON_SEPARATION_DEGREES = 10.0
MIN_PLANET_SEPARATION_DEGREES = 5.0
PLANET_HORIZONS_IDS = {
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
}
# Pluto is not included :(

SKIP_PAUSE_SECONDS = 10 # Define how long it waits before moving on to the next target after a skip

# How often to rebuild the LST-sorted target table during an observation (seconds)
REORDER_INTERVAL_SECONDS = 1*60*60 # 3600 seconds is 1 hour

REARRANGE_BY_LST = True # Rearrange the target list by local sidereal time

# End-of-list retry controls:
# - When the loop reaches the end without new observations, refresh target order and retry.
# - Keep this bounded so the script cannot spin forever when no targets are currently viable.
# - Set MAX_END_OF_LIST_RETRIES = "Max" for infinite retries, or use an integer for a fixed limit.
END_OF_LIST_RETRY_ENABLED = True
MAX_END_OF_LIST_RETRIES = "Max" # Number of times it will try to refresh (use "Max" for infinite retries)
END_OF_LIST_RETRY_WAIT_SECONDS = 30 # When the script reaches the very end, it will wait this time then refresh

# Only touch this if you're testing the code. This deactivates the hpguppi recording and the "mark as observed" function
RECORDING = False # For when you do or don't want to record in the GUI.
TESTING = True # For when not on the ATA or testing an observation. Default is True so the array isn't moved by accident.

MARKING = False # For marking as observed. Default is True.
SORT_BY_OBSERVED = True # If False, treat every target as unobserved in file-based checks and track only in-memory.
USE_TARGET_OBS_TIME_OVERRIDE = False # If True, use per-target "Obs Time" from target CSV when provided.
TESTING_OBS_TIME_SECONDS = 60 # Testing-mode scan duration; overrides per-target/default scan duration.

# Pacific timezone handling (Daylight Savings aware).
PACIFIC_TZ_NAME = "America/Los_Angeles"

ACTIVE_RECORDERS = {
    f"seti-node{i}": [0, 1] for i in range(1, 15)
}
# For 4 tunings

# Tracks whether recorder selection came explicitly from GUI config.
# - False: standalone/default behavior (fallback to full original recorder map)
# - True: honor GUI selection exactly (including an intentionally empty selection)
_ACTIVE_RECORDERS_EXPLICIT = False
# Tracks launch mode for antenna release semantics.
# - False: standalone script mode (release antennas on process exit via atexit)
# - True: GUI-controlled mode (do not release antennas on GUI process close)
_GUI_CONTROLLED = False
# Optional list of antennas checked in the GUI at run start.
# Standalone runs leave this empty.
GUI_SELECTED_ANTENNAS = []

DEFAULT_TUNING_RECORDER_MAPS = [
    {'seti-node1': [0,1], 'seti-node2': [0,1], 'seti-node3': [0,1], 'seti-node4': [0]},
    {'seti-node4': [1], 'seti-node5': [0,1], 'seti-node6': [0,1], 'seti-node7': [0,1]},
    {'seti-node8': [0,1], 'seti-node9': [0,1], 'seti-node10': [0,1], 'seti-node11': [0]},
    {'seti-node11': [1], 'seti-node12': [0,1], 'seti-node13': [0,1], 'seti-node14': [0,1]},
]
# Manually defining the seti nodes

TUNING_LABELS = ["LoA", "LoB", "LoC", "LoD"] # These are the headers for the recorders section. Might rename to 'tunings', but unsure.


# Target CSV column aliases for versatility.
TARGET_COLUMN_ALIASES = {
    "Plaintext Name": ["Plaintext Name", "Plaintext", "Plaintext_Name", "Name", "Target", "Target Name", "Source", "Source Name", "target_name"],
    "Horizons Name": ["Horizons Name", "Horizons_Name", "Horizons", "JPL Horizons", "Horizons ID", "JPL Name"],
    "ID": ["ID", "Id", "id", "Target ID", "Source ID", "ID#", "target_id"],
    "Solar System Flag": ["Solar System Flag", "SolarSystemFlag", "Solar System", "Solsys Flag", "solsys_flag", "Solar Flag"],
    "RA (hours)": ["RA (hours)", "RA hours", "RA_Hours", "RA (hr)", "RA hr", "target_ra_hours"],
    "RA (deg)": ["RA (deg)", "RA deg", "RA_Deg", "RA (degrees)", "RA degrees", "target_ra_deg"],
    "RA (solsys)": ["RA (solsys)", "RA_solsys", "RA Solsys", "Solar RA", "Solar System RA"],
    "DEC": ["DEC", "Dec", "dec", "DEC (deg)", "Dec (deg)","DEC (degree)", "Declination", "target_dec"],
    "DEC (solsys)": ["DEC (solsys)", "DEC_solsys", "DEC Solsys", "Solar DEC", "Solar System DEC"],
    "Obs Time": ["Obs Time", "ObsTime", "Observation Time", "Scan Time", "Duration", "obs_time"],
}

TARGET_REQUIRED_CANONICAL_COLUMNS = [
    "Plaintext Name",
    "ID",
    "Solar System Flag",
    "DEC",
]
# TODO: These are the columns you NEED in some way.
# ID is a unique index value per target. Each entry MUST be unique, or it will skip over.
# If you are observing one target several times, each observation needs its own unique ID.
# The Plaintext Name is the printout name for you. If you're observing an Horizons target, you'll need the Horizons column.
# Solar System Flag tells the script if it should use RA/DEC or query its coords with JPL Horizons.

TARGET_REQUIRED_RA_ANY_OF = ["RA (hours)", "RA (deg)"]
# Even if you only have solar system targets, your csv still needs (empty) RA/DEC columns so it has somewhere to put values to track.

# ============================================================================================================================================================================================

# ODS Settings
# ATA slew rate
ODS_SLEW_AZ_RATE_DEG_PER_SEC = 3.0
ODS_SLEW_EL_RATE_DEG_PER_SEC = 1.0
ODS_SLEW_CONSERVATIVE_MULTIPLIER = 1.30
ODS_SLEW_EXTRA_BUFFER_SECONDS = 30

# Budget additional time for the ODS reservation
ODS_ASSUME_LONG_SLEW_SECONDS = 240
ODS_ATA_OPERATIONS_SECONDS = 120

# Reserve a buffer on either side of the observation
ODS_RESERVATION_BUFFER_SECONDS = 5*60

ODS_WINDOW_EARLY_GRACE_SECONDS = 30
ODS_WINDOW_LATE_GRACE_SECONDS = 30

# If there's a mismatch, it will try to recover.
ODS_MISMATCH_RECOVERY_EXTRA_SECONDS = 120

# Repush threshold for ODS
ODS_FUTURE_DRIFT_REPUSH_THRESHOLD_SECONDS = 300


# Sort-by-observed toggle controls whether fully observed targets are skipped.
# - True  -> use observed-list checks and skip targets observed at all active frequencies
# - False -> bypass observed-list checks
BYPASS_OBSERVED_CHECK = (not SORT_BY_OBSERVED)
# Mainly just for faster testing, most people can disregard

# Global status callback (set by GUI)
_status_callback = None
_urgent_callback = None

_HORIZONS_ENABLED = True
_HORIZONS_WARNING_SHOWN = False

# -----------------------------------------------------------------------------------------------------------------------------------
# Now here's the *actual* script.

import utils_beamforming
import os

def set_status_callback(callback):
    """Register a status callback used by GUI integrations."""
    global _status_callback
    _status_callback = callback
    # Also register the same callback with utils_beamforming
    utils_beamforming.set_status_callback(callback)

def set_urgent_callback(callback):
    """Register an urgent-line callback used by GUI integrations."""
    global _urgent_callback
    _urgent_callback = callback


# Active tuning frequencies in MHz used across observation and ODS planning.
# Populate this from the actual selected tunings at runtime; do not assume a fixed
# four-frequency set for all observations.
active_tuning_freqs = []


# NOTE TODO: Blayne, fix this to update to new ODS requirements
# Especially need to make sure that it works for all 4 tunings
def _make_ods_bands_for_active_tunings(frequencies_mhz=None):
    """Builds dicts of the used bands for ODS."""
    if frequencies_mhz is None:
        frequencies_mhz = globals().get("active_tuning_freqs", []) or []

    parsed_freqs = []
    for freq_mhz in frequencies_mhz:
        try:
            freq_value = float(freq_mhz)
        except Exception:
            continue
        if not np.isfinite(freq_value) or freq_value <= 0:
            continue
        parsed_freqs.append(freq_value)

    if not parsed_freqs:
        return []

    bands = []
    for freq_mhz in parsed_freqs:
        bands.append({
            'freq_lower_hz': 1e6 * (freq_mhz - 345.0),
            'freq_upper_hz': 1e6 * (freq_mhz + 345.0),
        })
    return bands


def _log_status(message: str):
    '''Log status both to console and GUI if callback is set. '''
    print(message)
    if _status_callback:
        _status_callback(message)



def log_urgent(message: str, color: str = None):
    """Print message to both terminal and Urgent output line in GUI."""
    print(message)
    if _urgent_callback:
        try:
            _urgent_callback(message, color)
        except TypeError:
            _urgent_callback(message)




import atexit
import math
import numpy as np
import scipy
from astropy.constants import c
from astropy.coordinates import Angle, EarthLocation, SkyCoord, AltAz
import astropy.constants as consts
from astropy.time import Time
import astroquery
from astroquery.jplhorizons import Horizons
import astropy

import sys
import time
import argparse
import logging
import csv
import os
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import threading

from astropy import units as u
from astropy.coordinates import SkyCoord
import traceback

from utils_beamforming import mass_horizons_query
from utils_beamforming import is_observed
from utils_beamforming import mark_as_observed
from utils_beamforming import generate_ephemeris_files
from utils_beamforming import primary_beam_diameter
from utils_beamforming import synthesized_beam_diameter
from utils_beamforming import push_ods
from utils_beamforming import sleep_with_continuous_updates_seconds
from utils_beamforming import resolve_path_from_script
from utils_beamforming import normalize_hashpipe_targets
from utils_beamforming import _normalize_csv_key
from utils_beamforming import parse_hours_value
from utils_beamforming import parse_degrees_value
from utils_beamforming import parse_positive_int_seconds
from utils_beamforming import resolve_scan_duration_seconds
from utils_beamforming import estimate_ods_slew_seconds
from utils_beamforming import log_ods_reservation_vs_plan
from utils_beamforming import extract_horizons_id
from utils_beamforming import is_valid_finite_float
from utils_beamforming import parse_solar_system_flag
from utils_beamforming import query_horizons_instantaneous_position
from utils_beamforming import resolve_body_position

# Runtime globals (initialized in _initialize_runtime)
output_dir = None
output_dir2 = None
output_dir3 = None
obs_time_minutes = None
obs_time_hours = None
ods_lead_time_min = None
ods_lead_time_seconds = None
queue_length = None
time_step = None
query_time_step = None
diameter = None
obs_location = None
obs_start = None
hcro_obs_start = None
obs_start_name = None
obs_end = None
total_obs_time = None

# GUI/External control integration
_stop_event = threading.Event()
_stop_obs_event = threading.Event()
_interrupt_event = threading.Event()
_exit_event = threading.Event()
_gui_close_event = threading.Event()
_recording_active = False

observed_targets = []  # Ordered list of targets observed in this run
observed_target_ids_seen = set()  # Fast membership check keyed by normalized target ID
ant_list = None  # Tracks antennas reserved for this run so they can be released on Stop
# Per-run antenna snapshots used for reliable end-of-run reporting even after release.
ant_list_initial_active_snapshot = []
ant_list_used_snapshot = []
ant_list_removed_snapshot = []

# Transient per-reorder skip tracking. These lists are reset each time target
# order is refreshed so moving targets can be re-evaluated on the next pass.
skipped_altitude_targets = []
skipped_altitude_targets_seen = set()
skipped_sun_targets = []
skipped_sun_targets_seen = set()
skipped_moon_targets = []
skipped_moon_targets_seen = set()
skipped_planet_targets = []
skipped_planet_targets_seen = set()
skipped_data_targets = []
skipped_data_targets_seen = set()

try:
    PACIFIC_TZ = ZoneInfo(PACIFIC_TZ_NAME)
except Exception:
    # Fallback keeps runtime usable if zoneinfo data is unavailable.
    PACIFIC_TZ = timezone(timedelta(hours=-8))


def _to_pacific(dt_obj: datetime) -> datetime:
    """Convert datetime to America/Los_Angeles (DST-aware)."""
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
    return dt_obj.astimezone(PACIFIC_TZ)

def _ordinal_day(day: int) -> str:
    """Return day-of-month string with ordinal suffix (1st, 2nd, ...)."""
    d = int(day)
    if 10 <= (d % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
    return f"{d}{suffix}"


def _format_clock_local(dt_obj: datetime) -> str:
    """Format local time as h:mmam/pm (for example 8:13pm)."""
    hour24 = int(dt_obj.hour)
    hour12 = hour24 % 12
    if hour12 == 0:
        hour12 = 12
    ampm = "am" if hour24 < 12 else "pm"
    return f"{hour12}:{int(dt_obj.minute):02d}{ampm}"


def _format_minutes_label(total_seconds: int) -> str:
    """Format seconds as a human-readable minute label."""
    minutes = float(total_seconds) / 60.0
    if abs(minutes - round(minutes)) < 1e-9:
        value = f"{int(round(minutes))}"
    else:
        value = f"{minutes:.1f}"
    unit = "min" if abs(minutes - 1.0) < 1e-9 else "mins"
    return f"{value} {unit}"


def _format_ods_push_summary(
    res_start_utc: datetime,
    res_end_utc: datetime,
    obs_seconds: int,
) -> str:
    """Build an operator-friendly ODS push summary line."""
    start_local = _to_pacific(res_start_utc)
    end_local = _to_pacific(res_end_utc)
    date_label = f"{start_local.strftime('%B')} {_ordinal_day(start_local.day)}, {start_local.year}"

    reservation_seconds = max(0, int((res_end_utc - res_start_utc).total_seconds()))
    obs_label = _format_minutes_label(max(0, int(obs_seconds)))
    res_label = _format_minutes_label(reservation_seconds)

    return (
        f"Pushing ODS from {_format_clock_local(start_local)} to {_format_clock_local(end_local)} "
        f"(Obs length {obs_label}, Reservation length {res_label}) on {date_label}")


def _format_local_window_label(start_utc: datetime, end_utc: datetime) -> str:
    """Format a UTC window as a concise Pacific-local label for operators."""
    start_local = _to_pacific(start_utc)
    end_local = _to_pacific(end_utc)
    date_label = f"{start_local.strftime('%B')} {_ordinal_day(start_local.day)}, {start_local.year}"
    tz_label = start_local.strftime("%Z") or "local"
    return (
        f"{_format_clock_local(start_local)} to {_format_clock_local(end_local)} "
        f"{tz_label} on {date_label}")



def _build_active_tuning_maps(active_recorders: dict, explicit_selection: bool = False):
    """Build original d/LoA/LoB/LoC/LoD maps, then filter by selected active recorders/streams."""
    normalized = normalize_hashpipe_targets(active_recorders)

    d_full = {f"seti-node{i}": [0, 1] for i in range(1, 15)} # These are all the seti nodes. These are what record data.
    d_loa_full = {'seti-node1': [0,1], 'seti-node2': [0,1], 'seti-node3': [0,1], 'seti-node4': [0]}
    d_lob_full = {'seti-node4': [1], 'seti-node5': [0,1], 'seti-node6': [0,1], 'seti-node7': [0,1]}
    d_loc_full = {'seti-node8': [0,1], 'seti-node9': [0,1], 'seti-node10': [0,1], 'seti-node11': [0]}
    d_lod_full = {'seti-node11': [1], 'seti-node12': [0,1], 'seti-node13': [0,1], 'seti-node14': [0,1]}

    full_maps_by_index = {
        0: d_loa_full,
        1: d_lob_full,
        2: d_loc_full,
        3: d_lod_full,
    }

    # Standalone/default behavior: use full original structure when no explicit recorder selection was provided.
    # GUI behavior: when selection was explicit, honor it exactly and return no active maps.
    if not normalized:
        if explicit_selection:
            return [], [], {}
        active_maps = [d_loa_full, d_lob_full, d_loc_full, d_lod_full]
        active_indices = [0, 1, 2, 3]
        return active_maps, active_indices, d_full

    # Filter to selected recorder streams while preserving original LoA/LoB/LoC/LoD layout
    filtered_d = {}
    active_maps = []
    active_indices = []

    for tuning_index in range(4):
        tuning_map = full_maps_by_index[tuning_index]
        filtered_map = {}
        for node_name, streams in tuning_map.items():
            available_streams = normalized.get(node_name, [])
            kept_streams = [stream for stream in streams if stream in available_streams]
            if kept_streams:
                filtered_map[node_name] = kept_streams
                filtered_d.setdefault(node_name, [])
                for stream in kept_streams:
                    if stream not in filtered_d[node_name]:
                        filtered_d[node_name].append(stream)

        if filtered_map:
            active_maps.append(filtered_map)
            active_indices.append(tuning_index)

    for node_name in list(filtered_d.keys()):
        filtered_d[node_name] = sorted(filtered_d[node_name])

    return active_maps, active_indices, filtered_d


def _format_name_id_label(source_name: str, source_id) -> str:
    """Return a user-facing target label in the form ''(Name - ID###)''."""
    name_text = str(source_name or "Unknown").strip() or "Unknown"
    id_text = str(source_id or "?").strip() or "?"
    if id_text.endswith(".0") and id_text.replace(".", "", 1).isdigit():
        id_text = id_text.split(".", 1)[0]
    id_display = id_text if id_text.upper().startswith("ID") else f"ID{id_text}"
    return f"({name_text} - {id_display})"


def _normalize_target_id_key(source_id) -> str:
    """Return a stable, comparable key for target IDs across int/float/string forms."""
    raw = str(source_id or "").strip()
    if not raw:
        return ""
    try:
        numeric = float(raw)
        if math.isfinite(numeric):
            if numeric.is_integer():
                return str(int(numeric))
            return f"{numeric:g}"
    except Exception:
        pass
    return raw


def _is_wait_schedule_target(source_name: str, source_id) -> bool:
    """Return True when Plaintext Name is a case-insensitive 'wait' and ID is numeric zero.

    Accepts any representation of zero for the ID column (0, 0.0, 000, 0.00, etc.) so
    the check is robust against CSV readers that coerce bare integer strings to floats.
    Name matching is case-insensitive to support planner exports like 'WAIT'.
    """
    if str(source_name or "").strip().lower() != "wait":
        return False
    id_text = str(source_id or "").strip()
    if not id_text:
        return False
    try:
        return float(id_text) == 0.0
    except (ValueError, TypeError):
        return False


def _get_instantaneous_solar_system_coordinates(source_name: str, horizons_name, scan_start: str):
    """Resolve the current RA/DEC for a Solar System target without building an ephemeris."""
    horizons_id = extract_horizons_id(horizons_name)
    position = query_horizons_instantaneous_position(
        target_id=horizons_id,
        obs_location=obs_location,
        epoch=scan_start,
        logger=print,
    )
    if not isinstance(position, dict):
        return None, None, horizons_id
    return position.get("ra"), position.get("dec"), horizons_id


def _target_has_unobserved_frequency(observed_list_path: str, source_id, frequencies_mhz) -> bool:
    """Return True when any tracked frequency is still unobserved for the target."""
    freq_values = []
    for freq in (frequencies_mhz or []):
        try:
            freq_values.append(int(freq))
        except (TypeError, ValueError):
            continue

    if not freq_values:
        return True

    try:
        return any(is_observed(observed_list_path, source_id, freq) == 0 for freq in freq_values)
    except Exception:
        return True


def _get_optional_column_values(df: pd.DataFrame, column_name: str):
    """Return column values when present, else a length-matched list of None."""
    if df is None or not isinstance(df, pd.DataFrame):
        return [None] * 0
    lookup = {_normalize_csv_key(col): col for col in df.columns}
    actual = lookup.get(_normalize_csv_key(column_name))
    if actual is not None:
        return list(df[actual])
    return [None] * len(df)


def _normalize_preferred_ra_units() -> str:
    """Normalize PREFER_RA_UNITS to either 'hours' or 'deg'."""
    pref = str(PREFER_RA_UNITS or "deg").strip().lower()
    if pref in ("hours", "hour", "hr", "hrs", "h"):
        return "hours"
    if pref in ("deg", "degree", "degrees", "d"):
        return "deg"
    _log_status(f"Unrecognized PREFER_RA_UNITS='{PREFER_RA_UNITS}', defaulting to 'deg'.") # NOTE TODO: I don't think this is right actually
    return "deg"


def _resolve_sidereal_ra_pair(ra_hours_value, ra_deg_value, source_name: str = "", context: str = ""):
    """Resolve sidereal RA from either RA(hours) or RA(deg), returning both as floats."""
    ra_hours_ok = is_valid_finite_float(ra_hours_value)
    ra_deg_ok = is_valid_finite_float(ra_deg_value)

    if (not ra_hours_ok) and (not ra_deg_ok):
        return None

    where = f" ({context})" if str(context or "").strip() else ""

    if ra_hours_ok:
        try:
            parsed_ra_hours = parse_hours_value(ra_hours_value, field_label=f"RA(hours) for {source_name}{where}")
        except ValueError as exc:
            _log_status(f"Error: {exc}")
            return None
        ra_hours = float(parsed_ra_hours if parsed_ra_hours is not None else ra_hours_value)
    else:
        ra_hours = None

    if ra_deg_ok:
        try:
            parsed_ra_deg = parse_degrees_value(ra_deg_value, field_label=f"RA(deg) for {source_name}{where}")
        except ValueError as exc:
            _log_status(f"Error: {exc}")
            return None
        ra_deg = float(parsed_ra_deg if parsed_ra_deg is not None else ra_deg_value)
    else:
        ra_deg = None

    # Converts back and forth for degrees and hours.
    if ra_hours is None:
        ra_hours = ra_deg / 15.0
    if ra_deg is None:
        ra_deg = ra_hours * 15.0

    if ra_hours_ok and ra_deg_ok:
        derived_ra_deg = ra_hours * 15.0
        if abs(derived_ra_deg - ra_deg) > 1e-3:
            where = f" ({context})" if str(context or "").strip() else ""
            _log_status(
                f"Warning: RA(hours) and RA(deg) disagree for {source_name}{where}; "
                f"using RA(hours)={ra_hours:.6f} and RA(deg)={ra_deg:.6f} as provided.")

    return ra_hours, ra_deg


def _format_ra_preferred_text(ra_hours: float, ra_deg: float) -> str:
    """Format RA text according to PREFER_RA_UNITS while showing both units."""
    preferred = _normalize_preferred_ra_units()
    if preferred == "hours":
        return f"{ra_hours:.6f} hours ({ra_deg:.6f} degrees)"
    return f"{ra_deg:.6f} degrees ({ra_hours:.6f} hours)"


def _resolve_target_column_map(columns) -> dict:
    """Resolve canonical target-column names to available CSV headers using aliases."""
    column_values = [] if columns is None else list(columns)
    available = {_normalize_csv_key(col): col for col in column_values}
    resolved = {}
    for canonical, aliases in TARGET_COLUMN_ALIASES.items():
        for alias in aliases:
            alias_key = _normalize_csv_key(alias)
            if alias_key in available:
                resolved[canonical] = available[alias_key]
                break
    return resolved


def _format_alias_list(canonical_name: str) -> str:
    """Return a comma-separated alias list for a canonical target column name."""
    aliases = TARGET_COLUMN_ALIASES.get(canonical_name, [canonical_name])
    normalized = []
    seen = set()
    for alias in aliases:
        alias_text = str(alias).strip()
        if (not alias_text) or (alias_text in seen):
            continue
        seen.add(alias_text)
        normalized.append(alias_text)
    return ", ".join(normalized)


def _format_target_column_requirements() -> str:
    """Return a readable description of required target columns and accepted aliases."""
    lines = [
        "Required target columns (aliases accepted):",]
    for col in TARGET_REQUIRED_CANONICAL_COLUMNS:
        lines.append(f"- {col}: {_format_alias_list(col)}")

    lines.append("- At least one sidereal RA column is required:")
    for col in TARGET_REQUIRED_RA_ANY_OF:
        lines.append(f"  * {col}: {_format_alias_list(col)}")
    lines.append("- Plain 'RA' is not accepted because units are ambiguous.")
    lines.append("  Rename it to either 'RA (hours)' or 'RA (deg)' before running.")

    lines.append("Optional column:")
    lines.append(f"- Horizons Name: {_format_alias_list('Horizons Name')}")
    return "\n".join(lines)


def _validate_required_target_columns(target_df: pd.DataFrame, context_label: str = "Target CSV"):
    """Validate canonical required target columns after alias application."""
    if target_df is None or not isinstance(target_df, pd.DataFrame):
        return False, f"{context_label} data is not a valid pandas DataFrame."

    # Reject ambiguous RA headers early so operators must specify units.
    ambiguous_ra_headers = [
        col for col in target_df.columns
        if str(col).strip().lower() == "ra"]
    if ambiguous_ra_headers:
        message = (
            f"{context_label} column validation failed: ambiguous RA column header(s) "
            f"detected: {ambiguous_ra_headers}. "
            "Use unit-specific RA headers only: 'RA (hours)' or 'RA (deg)'. "
            "Please rename the RA column before continuing.\n"
            f"{_format_target_column_requirements()}")
        return False, message

    missing_required = [
        col for col in TARGET_REQUIRED_CANONICAL_COLUMNS
        if col not in target_df.columns]

    has_ra_column = any(col in target_df.columns for col in TARGET_REQUIRED_RA_ANY_OF)

    if (not missing_required) and has_ra_column:
        return True, ""

    problems = []
    if missing_required:
        problems.append(f"missing required columns: {missing_required}")
    if not has_ra_column:
        problems.append(
            "missing sidereal RA columns: at least one of "
            f"{TARGET_REQUIRED_RA_ANY_OF} is required")

    message = (
        f"{context_label} column validation failed ({'; '.join(problems)}). "
        f"Available columns: {target_df.columns.tolist()}\n"
        f"{_format_target_column_requirements()}")
    return False, message


def _apply_target_column_aliases(target_df: pd.DataFrame, log_aliases: bool = False):
    """Copy alias columns into canonical names so downstream logic uses stable headers."""
    if target_df is None or not isinstance(target_df, pd.DataFrame):
        return target_df, {}

    resolved = _resolve_target_column_map(target_df.columns)
    normalized_df = target_df.copy()

    for canonical, source_col in resolved.items():
        if canonical not in normalized_df.columns and source_col in normalized_df.columns:
            normalized_df[canonical] = normalized_df[source_col]
            if log_aliases:
                _log_status(f"Column alias mapped: '{source_col}' -> '{canonical}'")

    return normalized_df, resolved


def _warn_horizons_disabled_once(reason: str):
    """Emit a one-time GUI/console warning when Horizons lookups are disabled."""
    global _HORIZONS_WARNING_SHOWN
    if _HORIZONS_WARNING_SHOWN:
        return

    note = (
        "WARNING: Horizons Name column (or alias) not found. JPL Horizons queries are disabled for this run. "
        "Solar-system targets will use fallback coordinates when available and may be skipped otherwise. "
        "NOTE: revisit this no-Horizons behavior later.")
    detail = str(reason or "").strip()
    message = f"{note} ({detail})" if detail else note
    _log_status(message)
    log_urgent("Horizons disabled: missing Horizons Name column", color="#E69F00")
    _HORIZONS_WARNING_SHOWN = True


def _resolve_solar_system_coordinates_without_horizons(
    source_name: str,
    ra_solsys_value,
    dec_solsys_value,
    ra_hours_value,
    ra_deg_value,
    dec_value,
    context: str = "",):
    """Resolve Solar-System coordinates when Horizons lookups are unavailable."""
    if is_valid_finite_float(ra_solsys_value) and is_valid_finite_float(dec_solsys_value):
        return float(ra_solsys_value), float(dec_solsys_value)

    sidereal_pair = _resolve_sidereal_ra_pair(
        ra_hours_value,
        ra_deg_value,
        source_name=source_name,
        context=context or "solar-system fallback",)
    if sidereal_pair is None or (not is_valid_finite_float(dec_value)):
        return None, None

    _, resolved_ra_deg = sidereal_pair
    return float(resolved_ra_deg), float(dec_value)


def _validate_csv_columns_preflight(active_tuning_freqs) -> None:
    """Validate required CSV columns before queueing/push/wait can start."""
    try:
        target_df = pd.read_csv(CSV_NAME)
    except Exception as e:
        raise RuntimeError(f"Failed to read target CSV for preflight validation: {CSV_NAME} | {e}")

    target_df, _ = _apply_target_column_aliases(target_df, log_aliases=True)
    _log_status("Target CSV column requirements:\n" + _format_target_column_requirements())

    target_ok, target_validation_message = _validate_required_target_columns(
        target_df,
        context_label="Target CSV preflight",)
    if not target_ok:
        raise ValueError(target_validation_message)

    if "Horizons Name" not in target_df.columns:
        _warn_horizons_disabled_once(
            "No Horizons Name column (or alias) detected during preflight validation")

    # Observed-list schema is required only when we actively consult or update it.
    requires_observed_list = (not BYPASS_OBSERVED_CHECK) or bool(MARKING and RECORDING and (not TESTING))
    if not requires_observed_list:
        _log_status(
            "Preflight CSV validation: observed-list frequency-column check skipped "
            "(observed-list read/write not active in this run mode).")
        return

    try:
        observed_df = pd.read_csv(OBSERVED_LIST)
    except Exception as e:
        raise RuntimeError(f"Failed to read observed CSV for preflight validation: {OBSERVED_LIST} | {e}")

    observed_key_lookup = {_normalize_csv_key(col): col for col in observed_df.columns}
    observed_freq_keys = {
        _normalize_csv_key(col)
        for col in observed_df.columns
        if re.fullmatch(r"cfreq_\d+mhz", str(col).strip(), flags=re.IGNORECASE)}

    required_col_keys = {'id'}
    if observed_freq_keys:
        required_col_keys.update(observed_freq_keys)
    else:
        normalized_freqs = []
        for freq in (active_tuning_freqs or []):
            try:
                normalized_freqs.append(int(freq))
            except (TypeError, ValueError):
                continue
        if normalized_freqs:
            required_col_keys.update(
                _normalize_csv_key(f"cfreq_{freq}mhz") for freq in sorted(set(normalized_freqs)))

    missing_observed_cols = sorted(required_col_keys - observed_key_lookup.keys())
    if missing_observed_cols:
        raise ValueError(
            "Observed CSV missing required columns before run start. "
            f"Missing: {missing_observed_cols} | Required: {sorted(required_col_keys)} | "
            f"Available: {observed_df.columns.tolist()}")

    _log_status(
        "Preflight CSV validation passed: target and observed-list required columns are present.")


def _resolve_planned_slew_seconds(
    from_coords,
    to_ra_deg,
    to_dec_deg,
    reference_time_utc,) -> int:

    """Return conservative planned slew seconds with a long-slew floor."""
    long_slew_floor = max(0, int(ODS_ASSUME_LONG_SLEW_SECONDS))
    estimated_slew = 0

    if from_coords is not None:
        try:
            estimated_slew = estimate_ods_slew_seconds(
                from_coords[0],
                from_coords[1],
                to_ra_deg,
                to_dec_deg,
                obs_location=obs_location,
                obstime_utc=reference_time_utc,
                az_rate_deg_per_sec=ODS_SLEW_AZ_RATE_DEG_PER_SEC,
                el_rate_deg_per_sec=ODS_SLEW_EL_RATE_DEG_PER_SEC,
                conservative_multiplier=ODS_SLEW_CONSERVATIVE_MULTIPLIER,
                extra_buffer_seconds=ODS_SLEW_EXTRA_BUFFER_SECONDS,)
        except Exception:
            estimated_slew = 0

    return int(max(long_slew_floor, int(estimated_slew)))


def _get_conservative_pre_obs_seconds() -> int:
    """Return fixed conservative pre-observation budget (slew floor + ATA ops)."""
    return int(max(0, int(ODS_ASSUME_LONG_SLEW_SECONDS)) + max(0, int(ODS_ATA_OPERATIONS_SECONDS)))


def _ensure_target_ods_protection(
    source_name: str,
    reservation_key,
    ra_deg,
    dec_deg,
    scan_seconds: int,
    reservation_buffer: timedelta,
    ods_reservations_by_target: dict,
    pre_obs_seconds_override=None,):
    """Verify current target is inside its ODS reservation window; Recover if not.

    Returns:
    - (True, reason) when protected (existing window valid or recovery push succeeded)
    - (False, reason) when protection cannot be confirmed (caller may still continue)

    Policy note: the caller controls whether to continue or skip when False is
    returned. Current policy is continue observing but with warnings.
    """
    if not ODS_PUSH:
        return True, "ODS push disabled by ODS_PUSH=False"

    now_utc = datetime.now(timezone.utc) # NOTE: I need to see if this actually helps any
    key = str(reservation_key or "").strip() or str(source_name or "").strip()
    reservation = ods_reservations_by_target.get(key)

    early_grace = timedelta(seconds=max(0, int(ODS_WINDOW_EARLY_GRACE_SECONDS)))
    late_grace = timedelta(seconds=max(0, int(ODS_WINDOW_LATE_GRACE_SECONDS)))

    if pre_obs_seconds_override is None:
        pre_obs_seconds = _get_conservative_pre_obs_seconds()
    else:
        pre_obs_seconds = max(0, int(pre_obs_seconds_override))

    if reservation is not None:
        res_start_utc = reservation.get("res_start_utc")
        res_end_utc = reservation.get("res_end_utc")
        planned_obs_start_utc = now_utc + timedelta(seconds=pre_obs_seconds)
        planned_obs_end_utc = planned_obs_start_utc + timedelta(seconds=max(1, int(scan_seconds)))
        if isinstance(res_start_utc, datetime) and isinstance(res_end_utc, datetime):
            log_ods_reservation_vs_plan(
                source_name=source_name,
                res_start_utc=res_start_utc,
                res_end_utc=res_end_utc,
                planned_obs_start_utc=planned_obs_start_utc,
                planned_obs_end_utc=planned_obs_end_utc,
                context="pre-observation check",
                testing=TESTING,
                logger=_log_status,
            )

            # The observation window is covered if:
            # 1) Current wall clock or projected start is on/after reservation start (with early grace)
            # 2) Observation end from now (or projected end) is on/before reservation end (with late grace)
            start_ok = (planned_obs_start_utc >= (res_start_utc - early_grace)) or (now_utc >= (res_start_utc - early_grace))
            end_ok = (planned_obs_end_utc <= (res_end_utc + late_grace)) or ((now_utc + timedelta(seconds=max(1, int(scan_seconds)))) <= (res_end_utc + late_grace))

            if start_ok and end_ok:
                _log_status(
                    f"ODS window check OK for {source_name}: projected "
                    f"{_format_local_window_label(planned_obs_start_utc, planned_obs_end_utc)} "
                    f"within reserved {_format_local_window_label(res_start_utc, res_end_utc)}.")
                return True, "existing reservation covers projected observation window"
            _log_status(
                f"ODS window mismatch for {source_name}: projected operation "
                f"{_format_local_window_label(planned_obs_start_utc, planned_obs_end_utc)} not safely within "
                f"{_format_local_window_label(res_start_utc, res_end_utc)}. Attempting recovery push.")
        else:
            _log_status(f"ODS reservation for {source_name} is malformed. Attempting recovery push.")
    else:
        _log_status(f"No existing ODS reservation found for {source_name}. Attempting recovery push.")

    try:
        target_scan_seconds = max(1, int(scan_seconds))
    except Exception:
        target_scan_seconds = 1

    # Recovery window starts slightly before "now" and extends beyond
    # conservative pre-observation operations plus the scan.
    recovery_res_start_utc = now_utc - reservation_buffer
    recovery_res_end_utc = now_utc + timedelta(
        seconds=pre_obs_seconds + target_scan_seconds + max(0, int(ODS_MISMATCH_RECOVERY_EXTRA_SECONDS))) + reservation_buffer

    recovered_obs_start_utc = now_utc + timedelta(seconds=pre_obs_seconds)
    recovered_obs_end_utc = recovered_obs_start_utc + timedelta(seconds=target_scan_seconds)

    try:
        push_ok = push_ods(
            source=source_name,
            ra_deg=float(ra_deg),
            dec_deg=float(dec_deg),
            res_start_utc=recovery_res_start_utc,
            res_end_utc=recovery_res_end_utc,
            frequencies_mhz=globals().get("active_tuning_freqs", active_tuning_freqs),
            project_name=PROJECT_NAME,
            project_folder=PROJECT_FOLDER,)
        if not push_ok:
            _log_status(
                f"ODS recovery push failed for {source_name}: push_ods returned False | "
                f"target_ra_deg={float(ra_deg):.6f}, target_dec_deg={float(dec_deg):.6f}, "
                f"requested_window={_format_local_window_label(recovery_res_start_utc, recovery_res_end_utc)}")
            log_urgent(f"ODS protection FAILED for {source_name}; continuing observation unprotected", color="#D50000")
            return (False, "recovery push returned False for requested reservation window",)

        ods_reservations_by_target[key] = {
            "target_name": str(source_name),
            "res_start_utc": recovery_res_start_utc,
            "res_end_utc": recovery_res_end_utc,
            "obs_start_utc": recovered_obs_start_utc,
            "obs_end_utc": recovered_obs_end_utc,
            "scan_seconds": target_scan_seconds,
            "ra_deg": float(ra_deg),
            "dec_deg": float(dec_deg),
            "recovered": True,}
        log_ods_reservation_vs_plan(
            source_name=source_name,
            res_start_utc=recovery_res_start_utc,
            res_end_utc=recovery_res_end_utc,
            planned_obs_start_utc=recovered_obs_start_utc,
            planned_obs_end_utc=recovered_obs_end_utc,
            context="recovery repush",
            testing=TESTING,
            logger=_log_status,)
        _log_status(
            f"ODS recovery push succeeded for {source_name}: "
            f"{_format_local_window_label(recovery_res_start_utc, recovery_res_end_utc)}")
        log_urgent(f"ODS protection recovered for {source_name}", color="#E69F00")
        return True, "recovery push succeeded"
    except Exception as e:
        _log_status(
            f"ODS recovery push failed for {source_name}: {e} | "
            f"target_ra_deg={float(ra_deg):.6f}, target_dec_deg={float(dec_deg):.6f}, "
            f"requested_window={_format_local_window_label(recovery_res_start_utc, recovery_res_end_utc)}")
        log_urgent(f"ODS protection FAILED for {source_name}; continuing observation unprotected", color="#D50000")
        return False, f"recovery push raised exception: {e}"


def _refresh_drifting_future_ods_windows(
    current_source_key: str,
    ods_reservations_by_target: dict,
    reservation_buffer: timedelta,):
    """Detect future reservations drifting out of window and repush them.
    Will try its best to push ODS, but will still take data if it fails
    """
    if not ODS_PUSH:
        return

    now_utc = datetime.now(timezone.utc)
    pre_obs_seconds = _get_conservative_pre_obs_seconds()
    repush_threshold = timedelta(seconds=max(0, int(ODS_FUTURE_DRIFT_REPUSH_THRESHOLD_SECONDS)))

    for target_key, reservation in list((ods_reservations_by_target or {}).items()):
        if target_key == current_source_key:
            continue

        if not isinstance(reservation, dict):
            continue

        target_name = str(reservation.get("target_name") or target_key)

        res_start_utc = reservation.get("res_start_utc")
        res_end_utc = reservation.get("res_end_utc")
        ra_deg = reservation.get("ra_deg")
        dec_deg = reservation.get("dec_deg")
        scan_seconds = reservation.get("scan_seconds", OBS_TIME)

        needs_repush = False
        reason = None

        if not isinstance(res_start_utc, datetime) or not isinstance(res_end_utc, datetime):
            needs_repush = True
            reason = "missing or malformed reservation timestamps"
        # Trigger when window is near expiry (or already past), indicating drift.
        elif now_utc >= (res_end_utc - repush_threshold):
            needs_repush = True
            reason = (
                f"window nearing/past expiry (now={_to_pacific(now_utc).strftime('%Y-%m-%d %H:%M:%S %Z')}, "
                f"window={_format_local_window_label(res_start_utc, res_end_utc)})")

        if not needs_repush:
            continue

        if ra_deg is None or dec_deg is None:
            _log_status(
                f"Future ODS drift detected for {target_name} ({reason}) but missing RA/DEC; cannot repush.")
            continue

        try:
            scan_seconds = max(1, int(scan_seconds))
        except Exception:
            scan_seconds = max(1, int(parse_positive_int_seconds(OBS_TIME) or 300))

        # Repush near-now window to re-establish practical protection coverage.
        new_res_start_utc = now_utc - reservation_buffer
        new_res_end_utc = now_utc + timedelta(
            seconds=pre_obs_seconds + scan_seconds + max(0, int(ODS_MISMATCH_RECOVERY_EXTRA_SECONDS))) + reservation_buffer

        _log_status(
            f"Future ODS drift detected for {target_name}: {reason}. "
            f"Repushing updated window {_format_local_window_label(new_res_start_utc, new_res_end_utc)}.")
        try:
            push_ok = push_ods(
                source=target_name,
                ra_deg=float(ra_deg),
                dec_deg=float(dec_deg),
                res_start_utc=new_res_start_utc,
                res_end_utc=new_res_end_utc,
                frequencies_mhz=globals().get("active_tuning_freqs", active_tuning_freqs),
                project_name=PROJECT_NAME,
                project_folder=PROJECT_FOLDER,)
            if not push_ok:
                _log_status(f"Future ODS repush failed for {target_name}: push_ods returned False")
                continue
            reservation["target_name"] = target_name
            reservation["res_start_utc"] = new_res_start_utc
            reservation["res_end_utc"] = new_res_end_utc
            reservation["obs_start_utc"] = now_utc + timedelta(seconds=pre_obs_seconds)
            reservation["obs_end_utc"] = now_utc + timedelta(seconds=pre_obs_seconds + scan_seconds)
            reservation["scan_seconds"] = scan_seconds
            reservation["recovered"] = True
            log_ods_reservation_vs_plan(
                source_name=target_name,
                res_start_utc=new_res_start_utc,
                res_end_utc=new_res_end_utc,
                planned_obs_start_utc=reservation.get("obs_start_utc"),
                planned_obs_end_utc=reservation.get("obs_end_utc"),
                context="future-window repush",
                testing=TESTING,
                logger=_log_status,)
            _log_status(f"Future ODS repush succeeded for {target_name}.")
            log_urgent(f"Future ODS window refreshed for {target_name}", color="#E69F00")
        except Exception as e:
            _log_status(f"Future ODS repush failed for {target_name}: {e}")


def _ensure_obs_time_column(target_df):
    """Ensure target dataframe carries optional per-target "Obs Time" values when available."""
    if target_df is None or not isinstance(target_df, pd.DataFrame):
        return target_df
    if not USE_TARGET_OBS_TIME_OVERRIDE:
        return target_df
    if 'Obs Time' in target_df.columns:
        return target_df

    try:
        base_df = pd.read_csv(CSV_NAME)
    except Exception:
        return target_df

    if 'Plaintext Name' not in target_df.columns:
        return target_df
    if 'Plaintext Name' not in base_df.columns or 'Obs Time' not in base_df.columns:
        return target_df

    obs_time_by_name = (
        base_df[['Plaintext Name', 'Obs Time']]
        .drop_duplicates(subset=['Plaintext Name'], keep='first')
        .set_index('Plaintext Name')['Obs Time'])
    enriched_df = target_df.copy()
    enriched_df['Obs Time'] = enriched_df['Plaintext Name'].map(obs_time_by_name)
    return enriched_df


def _filter_working_target_table(target_df, active_tuning_freqs, context_label: str = "working"):
    """Build a filtered working target table while preserving full/archive tables unchanged."""
    if target_df is None or not isinstance(target_df, pd.DataFrame):
        return target_df

    working_df = target_df.copy()
    total_rows = len(working_df)

    solar_flags = pd.to_numeric(working_df.get('Solar System Flag'), errors='coerce')
    dec_values = pd.to_numeric(working_df.get('DEC'), errors='coerce')
    sidereal_low_dec_mask = (solar_flags == 0) & dec_values.notna() & (dec_values < float(DEC_LIMIT))

    removed_low_dec_count = int(sidereal_low_dec_mask.sum())
    if removed_low_dec_count > 0:
        working_df = working_df.loc[~sidereal_low_dec_mask].copy()

    keep_mask = []
    removed_observed_count = 0
    if not BYPASS_OBSERVED_CHECK:
        for _, row in working_df.iterrows():
            source_name = row.get('Plaintext Name')
            source_id = row.get('ID')
            if _is_wait_schedule_target(source_name, source_id):
                keep_mask.append(True)
                continue

            is_unobserved = _target_has_unobserved_frequency(
                OBSERVED_LIST,
                source_id,
                active_tuning_freqs,)
            keep_mask.append(bool(is_unobserved))
            if not is_unobserved:
                removed_observed_count += 1

        if keep_mask:
            working_df = working_df.loc[keep_mask].copy()

    working_df = working_df.reset_index(drop=True)
    _log_status(
        f"{context_label}: full_rows={total_rows}, "
        f"removed_dec_below_limit={removed_low_dec_count} (DEC<{DEC_LIMIT} for sidereal), "
        f"removed_already_observed={removed_observed_count}, "
        f"working_rows={len(working_df)}")
    return working_df


def _write_working_target_copy(target_df):
    """Persist the filtered working target table used by the live loop."""
    try:
        if not isinstance(output_dir, str) or not output_dir:
            return
        working_copy_path = os.path.join(output_dir, f"{PROJECT_NAME}_sources_working_filtered.csv")
        target_df.to_csv(working_copy_path, index=False)
        _log_status(
            f"Updated working target copy: {working_copy_path} "
            f"(source CSV from GUI/config: {CSV_NAME})")
    except Exception as exc:
        _log_status(f"Warning: could not write working target copy: {exc}")


def _write_full_archive_target_copy(target_df_full, snapshot_label: str = "current"):
    """Persist a complete/unfiltered archive copy of targets used for planning context."""
    try:
        if target_df_full is None or not isinstance(target_df_full, pd.DataFrame):
            return
        if not isinstance(output_dir2, str) or not output_dir2:
            return

        safe_label = str(snapshot_label or "current").strip().lower().replace(" ", "_")
        archive_copy_path = os.path.join(output_dir2, f"{PROJECT_NAME}_sources_archive_full_{safe_label}.csv")
        target_df_full.to_csv(archive_copy_path, index=False)
        _log_status(
            f"Updated full archive target copy: {archive_copy_path} "
            f"(rows={len(target_df_full)}, source CSV from GUI/config: {CSV_NAME})")
    except Exception as exc:
        _log_status(f"Warning: could not write full archive target copy: {exc}")


def _load_full_target_table_for_archive(log_aliases: bool = False):
    """Load a full, unfiltered target table from CSV for archival snapshots."""
    try:
        full_df = pd.read_csv(CSV_NAME)
    except Exception as exc:
        _log_status(f"Warning: could not read full target CSV for archive snapshot: {exc}")
        return None

    full_df = _ensure_obs_time_column(full_df)
    full_df, _ = _apply_target_column_aliases(full_df, log_aliases=log_aliases)
    return full_df


def _record_observed_target(source_name, source_id):
    """Append a newly observed target once, preserving observation order by unique ID."""
    target_id_key = _normalize_target_id_key(source_id)
    if not target_id_key:
        target_id_key = f"name:{str(source_name or '').strip().lower()}"
    if not target_id_key:
        return
    if target_id_key in observed_target_ids_seen:
        return
    observed_targets.append(_format_name_id_label(source_name, source_id))
    observed_target_ids_seen.add(target_id_key)


def _record_skipped_target(source_name, reason: str):
    """Track a skipped target by reason within the current reorder window."""
    name = str(source_name or "").strip()
    if not name:
        return

    skip_pause_seconds = SKIP_PAUSE_SECONDS

    def _pause_after_skip():
        # Catch stop/abort quickly during skip-heavy loops so requests are not deferred.
        _check_stop()
        time.sleep(skip_pause_seconds)
        _check_stop()

    reason_key = str(reason or "").strip().lower()
    if reason_key == "altitude":
        if name not in skipped_altitude_targets_seen:
            skipped_altitude_targets.append(name)
            skipped_altitude_targets_seen.add(name)
        _pause_after_skip()
        return

    if reason_key == "sun":
        if name not in skipped_sun_targets_seen:
            skipped_sun_targets.append(name)
            skipped_sun_targets_seen.add(name)
        _pause_after_skip()
        return

    if reason_key == "moon":
        if name not in skipped_moon_targets_seen:
            skipped_moon_targets.append(name)
            skipped_moon_targets_seen.add(name)
        _pause_after_skip()
        return

    if reason_key == "planet":
        if name not in skipped_planet_targets_seen:
            skipped_planet_targets.append(name)
            skipped_planet_targets_seen.add(name)
        _pause_after_skip()
        return

    if reason_key == "data":
        if name not in skipped_data_targets_seen:
            skipped_data_targets.append(name)
            skipped_data_targets_seen.add(name)
        _pause_after_skip()
        return

    _pause_after_skip()


def _clear_transient_skipped_targets():
    """Reset transient skip-tracking lists for the next reorder cycle."""
    skipped_altitude_targets.clear()
    skipped_altitude_targets_seen.clear()
    skipped_sun_targets.clear()
    skipped_sun_targets_seen.clear()
    skipped_moon_targets.clear()
    skipped_moon_targets_seen.clear()
    skipped_planet_targets.clear()
    skipped_planet_targets_seen.clear()
    skipped_data_targets.clear()
    skipped_data_targets_seen.clear()


def _log_transient_skipped_targets(prefix: str = "Skipped targets this reorder window"):
    """Log transient skipped-target lists for operator visibility."""
    _log_status(
        f"{prefix} | altitude={skipped_altitude_targets if skipped_altitude_targets else []}")
    _log_status(
        f"{prefix} | sun={skipped_sun_targets if skipped_sun_targets else []}")
    _log_status(
        f"{prefix} | moon={skipped_moon_targets if skipped_moon_targets else []}")
    _log_status(
        f"{prefix} | planet={skipped_planet_targets if skipped_planet_targets else []}")
    _log_status(
        f"{prefix} | data={skipped_data_targets if skipped_data_targets else []}")


def _get_planet_positions(scan_start: str):
    """Return best-effort planet RA/DEC dict in degrees for configured planets."""
    positions = {}
    if not PLANET_AVOIDANCE:
        return positions

    try:
        epoch_jd = Time(scan_start).jd
    except Exception:
        return positions

    for planet_name, planet_id in (PLANET_HORIZONS_IDS or {}).items():
        try:
            obj = Horizons(id=str(planet_id), location=obs_location, epochs=epoch_jd)
            eph = obj.ephemerides()
            positions[str(planet_name)] = {
                "ra": float(eph["RA"][0]),
                "dec": float(eph["DEC"][0]),}
        except Exception as e:
            _log_status(f"Planet position query failed for {planet_name} ({planet_id}): {e}")
    return positions


def _closest_planet_violation(ra_deg: float, dec_deg: float, scan_start: str):
    """Return (planet_name, separation_deg) when too close to a protected planet, else None."""
    if not PLANET_AVOIDANCE:
        return None

    planet_positions = _get_planet_positions(scan_start)
    if not planet_positions:
        return None

    target_coord = SkyCoord(ra=float(ra_deg) * u.deg, dec=float(dec_deg) * u.deg)
    threshold = float(MIN_PLANET_SEPARATION_DEGREES)
    closest_violation = None

    for planet_name, coords in planet_positions.items():
        try:
            planet_coord = SkyCoord(ra=float(coords["ra"]) * u.deg, dec=float(coords["dec"]) * u.deg)
            separation_deg = target_coord.separation(planet_coord).deg
            if separation_deg < threshold:
                if closest_violation is None or separation_deg < closest_violation[1]:
                    closest_violation = (planet_name, separation_deg)
        except Exception:
            continue

    return closest_violation


def _format_observed_targets():
    """Return the observed target list in display order."""
    return list(observed_targets)


def _normalize_antennas(values):
    """Normalize antenna labels into a unique, ordered lowercase list."""
    normalized = []
    seen = set()
    for ant in (values or []):
        name = str(ant).strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        normalized.append(name)
    return normalized


def _clear_observed_targets():
    """Reset ordered observed-target tracking for the next observation run."""
    observed_targets.clear()
    observed_target_ids_seen.clear()


def _log_observed_targets(prefix: str = "Targets observed this session", send_urgent: bool = False):
    """Log ordered observed-target summary, with optional urgent-line output."""
    ordered_targets = _format_observed_targets()
    summary_text = f"{prefix}: {ordered_targets if ordered_targets else []}"
    _log_status(summary_text)
    if send_urgent:
        log_urgent(summary_text, color="#0072B2")

# This prints at the end of every run
def _log_end_run_details(reason: str = "Observation script ending"):
    """Log end-of-run context for operators and GUI output."""
    try:
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        now_hcro = _to_pacific(datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception:
        now_utc = "unknown"
        now_hcro = "unknown"

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if str(PROJECT_FOLDER or "").strip():
            project_folder = os.path.abspath(PROJECT_FOLDER)
        else:
            project_folder = os.path.abspath(os.path.join(script_dir, "..", PROJECT_NAME))
    except Exception:
        project_folder = "unknown"

    requested_removed_antennas = _normalize_antennas(REMOVE_ANT)
    removed_antennas = _normalize_antennas(ant_list_removed_snapshot) or requested_removed_antennas
    used_antennas_live = _normalize_antennas(ant_list)
    used_antennas_snapshot = _normalize_antennas(ant_list_used_snapshot)
    if used_antennas_live:
        used_antennas = used_antennas_live
    elif used_antennas_snapshot:
        used_antennas = used_antennas_snapshot
    else:
        initial_active = _normalize_antennas(ant_list_initial_active_snapshot)
        removed_set = set(removed_antennas)
        used_antennas = [ant for ant in initial_active if ant not in removed_set]

    _log_status(f"{reason}")
    _log_status(f"Current time: {now_utc} | {now_hcro}")
    _log_status(f"Project folder: {project_folder}")
    _log_status(f"Used {len(used_antennas)} Antennas: {used_antennas}")
    _log_status(f"Removed {len(removed_antennas)} Antennas: {removed_antennas}")


# When the Pause button is pressed, this is pushed
def request_stop(reason: str = ""):
    """Request Stop for observing script. Will be caught at a convenient time and then exit."""
    label = f" ({reason})" if str(reason or "").strip() else ""
    _log_status(f"Stop requested{label}, will stop after the current scan completes.")
    log_urgent(f"Stop Requested{label}...", color = "#D55E00")
    _stop_obs_event.set()
    # Do NOT release antennas here. Antennas will be released when the stop is processed.
    # This protects hardware by only releasing when the actual scan is done.

def request_resume():
    """Clear a pending stop-after-current-scan request."""
    _log_status("Stop Cancelled through the GUI. Continuing observations.")
    log_urgent("Observation Resumed", color = "#009E73") # NOTE: See if there's a way to make this temporary
    _stop_obs_event.clear()

# When the Abort button is pressed, this is pushed.
def request_abort():
    """Trigger an immediate hard-abort and best-effort antenna release."""
    _log_status("Abort requested through the GUI, stopping everything immediately.")
    _log_end_run_details("Abort request received")
    _log_observed_targets("Targets observed this session")
    _exit_event.set()
    _stop_obs_event.set()
    _interrupt_event.set()
    # Attempt to release reserved antennas immediately on abort (best-effort)
    global ant_list
    try:
        if ant_list is not None and TESTING == False:
            antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list))
            ata_control.release_antennas(list(ant_list), False)
            _log_status(f"Abort requested | Released antennas: {antennas_for_log} (count={len(antennas_for_log)})")
            ant_list = None
        elif TESTING == True:
            antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list or []))
            _log_status(f"Abort requested | Released antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
            ant_list = None
    except Exception as e:
        _log_status(f"Error while releasing antennas on Abort: {e}")
    _clear_observed_targets()
    _log_status("Cleared observed target history after abort processing.")
    raise SystemExit(
        f"Abort requested by GUI at {_to_pacific(datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M %Z')}. Exiting immediately.")
    #sys.exit(0) # Closes everything completely NOTE: NEED TO EDIT AND CHANGE. STOP THE OBSERVATION, NOT THE GUI


def request_gui_close():
    """Mark an intentional GUI-close shutdown so final cleanup logs are suppressed."""
    _gui_close_event.set()

def clear_stop():
    """Clear all stop/interrupt/exit control events."""
    _stop_event.clear()
    _stop_obs_event.clear()
    _interrupt_event.clear()
    _exit_event.clear()
    _gui_close_event.clear()

def configure_and_run(cfg: dict = None):
    """Apply configuration and start observation flow in a background thread."""
    configure_from_dict(cfg)
    clear_stop()
    log_urgent("Script Running...", color = "#009E73")
    t = threading.Thread(target=_main_thread_wrapper, daemon=True)
    t.start()
    return t

# NOTE: This seems a little redundant, can probably be cleaned.
def _check_stop():
    """Check control events and terminate appropriately when requested."""
    global ant_list
    # If the event isn't set, it skips all these commands and keeps going.
    if _exit_event.is_set():
        # If antennas reserved, release them before exiting (best-effort)
        try:
            if ant_list is not None and TESTING == False:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list))
                ata_control.release_antennas(list(ant_list), False)
                _log_status(f"Exit requested | Released antennas: {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
            elif TESTING == True:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list or []))
                _log_status(f"Exit requested | Released antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
        except Exception as err:
            _log_status("Error releasing Antennas. Please run the following command from obs@control.")
            _log_status("python fxconf.py sagive bfa none [antnames]")
            _log_status(f"Error releasing antennas during forced exit: {err}")
        _log_observed_targets("Targets observed this session")
        _clear_observed_targets()
        _log_status("Cleared observed target history after abort processing.")
        raise SystemExit("Exit requested by GUI (hard abort)")
    if _interrupt_event.is_set():
        # If antennas reserved, release them before interrupting (best-effort)
        try:
            if ant_list is not None and TESTING == False:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list))
                ata_control.release_antennas(list(ant_list), False)
                _log_status(f"Interrupt requested | Released antennas: {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
            elif TESTING == True:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list or []))
                _log_status(f"Interrupt requested | Released antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
        except Exception as err:
            _log_status("Error releasing Antennas. Please run the following command from obs@control.")
            _log_status("python fxconf.py sagive bfa none [antnames]")
            _log_status("Check with fxconf.rb sals")
            _log_status(f"Error releasing antennas during interrupt: {err}")
        _log_observed_targets("Targets observed this session")
        _clear_observed_targets()
        _log_status("Cleared observed target history after abort processing.")
        raise KeyboardInterrupt("Interrupted by user (GUI abort)")

    if _stop_obs_event.is_set():
        if REMOVE_ANT:
            _log_status(f"REMOVE_ANT this session: {sorted(REMOVE_ANT)}")
        else:
            _log_status("REMOVE_ANT this session: []")
        log_urgent("Observation Stopped", color = "#D55E00")
        # Stop is being processed now; release reserved antennas before
        # raising the stop exception so hardware is cleaned up.
        try:
            if ant_list is not None and TESTING == False:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list))
                ata_control.release_antennas(ant_list, False)
                _log_status(f"Stop processing (_check_stop) | Released antennas: {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
            elif TESTING == True:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list or []))
                _log_status(f"Stop processing (_check_stop) | Released antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
        except Exception as err:
            _log_status("Error releasing Antennas. Please run the following command from obs@control.")
            _log_status("fxconf.rb sagive bfa none [antnames]")
            _log_status(f"Error releasing antennas during stop handling: {err}")
        _log_observed_targets("Targets observed this session")
        _clear_observed_targets()
        _log_status("Cleared observed target history after stop processing.")
        raise RuntimeError("Stop requested by user.")


def wait_with_stop(total_seconds: int, allow_stop: bool = True):
    """Sleep with continuous countdown that respects stop/exit/interrupt events.

    - If 'allow_stop' is True and a stop-after-current-scan request is set
      ('_stop_obs_event'), the wait will terminate early (return).
    - If '_exit_event' or '_interrupt_event' is set, the wait will terminate early.
    - If '_recording_active' is True, the wait ignores '_stop_obs_event' to
      allow a recording to finish undisturbed.
    """
    remaining_seconds = int(total_seconds)
    while remaining_seconds > 0:
        # Exit/interrupt take precedence and should end waits immediately
        if _exit_event.is_set() or _interrupt_event.is_set():
            _log_status(f"Wait interrupted by abort/exit request at time {_to_pacific(datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M %Z')}.")
            return
        # If a stop-after-current-scan was requested and we're allowed to stop,
        # and there is no active recording in progress, terminate the wait early.
        if allow_stop and _stop_obs_event.is_set() and (not _recording_active):
            _log_status(f"Wait interrupted by stop request at time {_to_pacific(datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M %Z')}.")
            return

        minutes, seconds = divmod(remaining_seconds, 60)
        message = f"{minutes:02d}:{seconds:02d} remaining"
        print(message, end="\r")
        if _status_callback:
            _status_callback(message)
        time.sleep(1)
        remaining_seconds -= 1

    final_message = f"Waited {total_seconds} second{'s' if total_seconds != 1 else ''}"
    print(final_message)
    if _status_callback:
        _status_callback(final_message)

def configure_from_dict(cfg: dict = None):
    """Apply GUI configs to override defaults"""
    global PROJECT_NAME, PROJECT_FOLDER, CSV_NAME, OBSERVED_LIST, REMOVE_ANT, ACTIVE_RECORDERS
    global _ACTIVE_RECORDERS_EXPLICIT, _GUI_CONTROLLED, GUI_SELECTED_ANTENNAS
    global QUEUE_WAIT, ODS_PUSH, REORDER_INTERVAL_SECONDS, REARRANGE_BY_LST, RECORDING, TESTING, MARKING, SORT_BY_OBSERVED, BYPASS_OBSERVED_CHECK, OBS_TIME
    global USE_TARGET_OBS_TIME_OVERRIDE
    if not cfg:
        _ACTIVE_RECORDERS_EXPLICIT = False
        _GUI_CONTROLLED = False
        GUI_SELECTED_ANTENNAS = []
        return
    # Any non-empty config dict is treated as GUI/external control unless explicitly overridden.
    _GUI_CONTROLLED = bool(cfg.get("GUI_CONTROLLED", True))
    PROJECT_NAME = cfg.get("PROJECT_NAME", PROJECT_NAME)
    PROJECT_FOLDER = cfg.get("PROJECT_FOLDER", PROJECT_FOLDER)
    CSV_NAME = cfg.get("CSV_NAME", CSV_NAME)
    OBSERVED_LIST = cfg.get("OBSERVED_LIST", OBSERVED_LIST)
    REMOVE_ANT = cfg.get("REMOVE_ANT", REMOVE_ANT)
    GUI_SELECTED_ANTENNAS = _normalize_antennas(cfg.get("GUI_SELECTED_ANTENNAS", []))
    OBS_TIME = int(cfg.get("OBS_TIME", OBS_TIME))
    ODS_PUSH = bool(cfg.get("ODS_PUSH", ODS_PUSH))
    QUEUE_WAIT = bool(cfg.get("QUEUE_WAIT", QUEUE_WAIT))
    REORDER_INTERVAL_SECONDS = int(cfg.get("REORDER_INTERVAL_SECONDS", REORDER_INTERVAL_SECONDS))
    REARRANGE_BY_LST = bool(cfg.get("REARRANGE_BY_LST", REARRANGE_BY_LST))
    RECORDING = bool(cfg.get("RECORDING", RECORDING))
    TESTING = bool(cfg.get("TESTING", TESTING))
    SORT_BY_OBSERVED = bool(cfg.get("SORT_BY_OBSERVED", SORT_BY_OBSERVED))
    MARKING = bool(cfg.get("MARKING", MARKING))
    if (not SORT_BY_OBSERVED) and MARKING:
        _log_status("Sort by observed list is OFF; disabling file-based mark-as-observed for this run.")
        MARKING = False
    USE_TARGET_OBS_TIME_OVERRIDE = bool(cfg.get("USE_TARGET_OBS_TIME_OVERRIDE", USE_TARGET_OBS_TIME_OVERRIDE))
    if "ACTIVE_RECORDERS" in cfg:
        _ACTIVE_RECORDERS_EXPLICIT = True
        ACTIVE_RECORDERS = normalize_hashpipe_targets(cfg.get("ACTIVE_RECORDERS", {}))
    else:
        _ACTIVE_RECORDERS_EXPLICIT = False
        ACTIVE_RECORDERS = normalize_hashpipe_targets(ACTIVE_RECORDERS) or {
            f"seti-node{i}": [0, 1] for i in range(1, 15)
        }
    BYPASS_OBSERVED_CHECK = (not SORT_BY_OBSERVED)

# Logging setup
log_file = None
archive_log_file = None
archive_log_path = None
_orig_stdout = None
_orig_stderr = None

class Tee(object):
    """Simple multi-stream writer that mirrors output to multiple file-like objects."""

    def __init__(self, *files):
        """Store output streams to mirror writes/flush calls."""
        self.files = files
    def write(self, obj):
        """Write text to each configured stream."""
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        """Flush each configured stream."""
        for f in self.files:
            f.flush()

def _start_logging():
    """Start terminal tee logging to working and archive output files."""
    global log_file, archive_log_file, archive_log_path, _orig_stdout, _orig_stderr

    if log_file is not None:
        return

    _orig_stdout = sys.stdout
    _orig_stderr = sys.stderr

    log_path = os.path.join(output_dir, "terminal_output.txt")
    archive_log_path = os.path.abspath(os.path.join(output_dir2, f"terminal_output_{obs_start_name}.txt"))
    log_file = open(log_path, "w", encoding="utf-8")
    archive_log_file = open(archive_log_path, "w", encoding="utf-8")
    sys.stdout = Tee(sys.stdout, log_file, archive_log_file)
    sys.stderr = Tee(sys.stderr, log_file, archive_log_file)

    _log_status(f"Terminal text archival started. Archive path: {archive_log_path}")
    _log_startup_stop_state()


def _describe_stop_request_state() -> str:
    """Print if a stop has been requested and by which method."""
    active_methods = []
    if _stop_obs_event.is_set():
        active_methods.append("stop-after-current-scan (_stop_obs_event)")
    if _interrupt_event.is_set():
        active_methods.append("interrupt/abort (_interrupt_event)")
    if _exit_event.is_set():
        active_methods.append("hard-exit/abort (_exit_event)")
    if _stop_event.is_set():
        active_methods.append("legacy stop event (_stop_event)")

    if not active_methods:
        return "No stop requested (all stop/abort events clear)."

    return "Stop is currently requested via: " + ", ".join(active_methods)


def _log_startup_stop_state():
    """Log startup timestamp and stop-request state when logging begins."""
    try:
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        now_hcro = _to_pacific(datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M:%S %Z')
        _log_status(f"Logging startup time: {now_utc} | {now_hcro}")
    except Exception:
        _log_status("Logging startup time: unknown")

    _log_status(f"Startup stop-request status: {_describe_stop_request_state()}")

def _stop_logging():
    """Stop tee logging, restore std streams, and close opened log files."""
    global log_file, archive_log_file, archive_log_path, _orig_stdout, _orig_stderr

    if log_file is None:
        return

    if _orig_stdout is not None:
        sys.stdout = _orig_stdout
    if _orig_stderr is not None:
        sys.stderr = _orig_stderr

    if log_file:
        log_file.close()
        log_file = None
    if archive_log_file:
        archive_log_file.close()
        archive_log_file = None

    _log_status(f"Terminal text archival stopped. Archive path: {archive_log_path}")

def _initialize_runtime():
    """Initialize derived runtime state, validate files, and import ATA deps."""
    global OBS_TIME, CSV_NAME, OBSERVED_LIST
    global output_dir, output_dir2, output_dir3
    global obs_time_minutes, obs_time_hours
    global ods_lead_time_min, ods_lead_time_seconds, queue_length
    global time_step, query_time_step
    global diameter, obs_location
    global obs_start, hcro_obs_start, obs_start_name, obs_end, total_obs_time

    effective_default_scan_seconds = TESTING_OBS_TIME_SECONDS if TESTING else (parse_positive_int_seconds(OBS_TIME) or 300)
    if TESTING == True:
        _log_status(
            f"TESTING mode active: all scans will run for {TESTING_OBS_TIME_SECONDS} seconds. "
            f"Configured/default OBS_TIME remains {OBS_TIME} seconds for non-testing runs.")

    log_urgent("Script Running...", color = "#009E73")

    # Resolve CSV and observed list paths so reading works whether run from
    # 'rfsoc_obs_scripts' or 'rfsoc_obs_scripts/survey_gui_code' (or GUI).
    # Use non-strict resolution here so the GUI can override values and so
    # running the script in TESTING mode can create lightweight templates.
    resolved_csv = resolve_path_from_script(CSV_NAME, script_file=__file__, must_exist=False)
    resolved_observed = resolve_path_from_script(OBSERVED_LIST, script_file=__file__, must_exist=False)

    # If files are missing, provide helpful behavior:
    # - In TESTING mode: create minimal template files so the script can run
    # - Otherwise: raise a clear FileNotFoundError
    if not os.path.exists(resolved_csv):
        if TESTING:
            template_cols = ['ID', 'Plaintext Name', 'Horizons Name', 'Solar System Flag',
                             'RA (hours)', 'DEC', 'RA (deg)', 'RA (solsys)', 'DEC (solsys)']
            try:
                pd.DataFrame(columns=template_cols).to_csv(resolved_csv, index=False)
                _log_status(f"Created template target CSV for TESTING at: {resolved_csv}")
            except Exception:
                raise RuntimeError(f"Unable to create testing template CSV at: {resolved_csv}")
        else:
            raise FileNotFoundError(f"Target CSV not found at resolved path: {resolved_csv}")

    if not os.path.exists(resolved_observed):
        if TESTING:
            try:
                pd.DataFrame(columns=['ID']).to_csv(resolved_observed, index=False)
                _log_status(f"Created empty observed-list CSV for TESTING at: {resolved_observed}")
            except Exception:
                raise RuntimeError(f"Unable to create testing observed-list CSV at: {resolved_observed}")
        else:
            raise FileNotFoundError(f"Observed list CSV not found at resolved path: {resolved_observed}")

    # Update globals so the rest of the code uses the resolved paths
    CSV_NAME = resolved_csv
    OBSERVED_LIST = resolved_observed

    _log_status("The following are the user inputs for this observation script:")
    _log_status(f"Project Name: {PROJECT_NAME}")
    _log_status(f"Configured default observation time (seconds): {OBS_TIME}")
    _log_status(f"Effective default scan time this run (seconds): {effective_default_scan_seconds}")
    _log_status(f"Target List CSV: {CSV_NAME}")
    _log_status("CSV file columns:")
    try:
        target_preview_df = pd.read_csv(CSV_NAME)
        _log_status(target_preview_df.columns.tolist())
        target_preview_df, target_preview_map = _apply_target_column_aliases(target_preview_df, log_aliases=False)
        global _HORIZONS_ENABLED
        _HORIZONS_ENABLED = "Horizons Name" in target_preview_df.columns
        if not _HORIZONS_ENABLED:
            _warn_horizons_disabled_once(
                "No Horizons Name column (or alias) detected in target CSV")
    except Exception as e:
        # Provide a clearer message for common pandas errors (missing file or wrong format)
        if isinstance(e, FileNotFoundError):
            raise FileNotFoundError(f"Target CSV not found at resolved path: {CSV_NAME}") from e
        # pandas.ParserError is common when file isn't a CSV (e.g. accidentally a .py)
        import pandas as _pd
        if isinstance(e, _pd.errors.ParserError):
            raise RuntimeError(f"Error parsing target CSV at {CSV_NAME}: {e}\nCheck that the file is a valid CSV and not a different file type like .xlsx.") from e
        raise
    _log_status(f"Observed List CSV: {OBSERVED_LIST}")
    try:
        _log_status(pd.read_csv(OBSERVED_LIST).columns.tolist())
    except Exception as e:
        # Provide a clearer message for common pandas errors (missing file or wrong format)
        if isinstance(e, FileNotFoundError):
            raise FileNotFoundError(f"Observed list CSV not found at resolved path: {OBSERVED_LIST}") from e
        import pandas as _pd
        if isinstance(e, _pd.errors.ParserError):
            raise RuntimeError(f"Error parsing observed list CSV at {OBSERVED_LIST}: {e}\nCheck that the file is a valid CSV and not a different file type like .xlsx.") from e
        raise

    # Validate CSV name agreement between target CSV and observed list CSV
    _log_status("\nValidating CSV name agreement...")
    if TESTING:
        _log_status(
            "Testing mode active: skipping strict target/observed-list name agreement validation. "
            "Wait entries and alternate observed-list layouts are allowed in this mode.")
    else:
        try:
            import utils_beamforming
            validation_result = utils_beamforming.validate_csv_name_agreement(
                CSV_NAME, OBSERVED_LIST, raise_on_error=False)

            if validation_result['agreement']:
                _log_status("All target names match between target CSV and observed list CSV")
            else:
                _log_status("\n" + "="*70)
                _log_status("WARNING: CSV NAME MISMATCH DETECTED")
                _log_status("="*70)

                if validation_result['missing_in_observed']:
                    _log_status(f"\n{len(validation_result['missing_in_observed'])} target(s) in TARGET CSV but NOT in OBSERVED CSV:")
                    for name in validation_result['missing_in_observed']:
                        _log_status(f"  - {name}")
                    _log_status("\nThese targets will fail when trying to mark as observed!")
                    _log_status("Add these entries to your observed list CSV.")

                if validation_result['extra_in_observed']:
                    _log_status(f"\n{len(validation_result['extra_in_observed'])} entry(ies) in OBSERVED CSV but NOT in TARGET CSV:")
                    for name in validation_result['extra_in_observed']:
                        _log_status(f"  - {name}")
                    _log_status("\nThese entries won't be used (not in target list).")

                _log_status("\n" + "="*70)
                _log_status("Please fix the CSV name mismatches before running observations.")
                _log_status("="*70 + "\n")

                # In non-testing mode, raise an error to prevent observation with mismatched CSVs
                if not TESTING and not BYPASS_OBSERVED_CHECK:
                    raise ValueError(
                        f"CSV name mismatch: {len(validation_result['missing_in_observed'])} "
                        f"targets missing from observed list. Fix the observed CSV before running.")
        except ImportError:
            _log_status("Warning: utils_beamforming module not available, skipping CSV validation")
        except Exception as e:
            _log_status(f"Warning: Could not validate CSV name agreement: {e}")
            if not TESTING:
                raise

    _log_status(f"\nAntennas to Remove: {REMOVE_ANT}")
    _log_status(f"Recording: {RECORDING}")
    _log_status(f"Testing Mode: {TESTING}")

    if TESTING == True:
        _log_status("TESTING MODE CURRENTLY ACTIVE. ANTENNAE WILL NOT RECORD")

    if TESTING == False:
        _log_status("Importing ATA specific functions and beginning script")
        # Expose these names at module scope so 'main()' and other functions
        # can use them whether the script is run standalone or via the GUI.
        global hpguppi_defaults, hpguppi_record, hpguppi_auxillary
        global ata_control, logger_defaults, snap_dada, snap_if, snap_config, ata_sources

        from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults
        from SNAPobs.snap_hpguppi import record_in as hpguppi_record
        from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary

        from ATATools import ata_control, logger_defaults
        from SNAPobs import snap_dada, snap_if, snap_config
        from ATATools import ata_sources
        print("Imported ATA functions.")

    # Get the rfsoc_obs_scripts directory (parent of survey_gui_code where this script lives)
    script_dir = os.path.dirname(os.path.abspath(__file__)) # survey_gui_code directory
    rfsoc_root = os.path.dirname(script_dir) # rfsoc_obs_scripts directory

    # Resolve project root directory.
    # GUI path mode: use PROJECT_FOLDER when provided.
    # Legacy mode: fall back to rfsoc_obs_scripts/<PROJECT_NAME>.
    project_folder_value = str(PROJECT_FOLDER or "").strip()
    if project_folder_value:
        candidates = [
            project_folder_value,
            os.path.join(script_dir, project_folder_value),
            os.path.join(rfsoc_root, project_folder_value),]
        resolved_project_root = None
        for candidate in candidates:
            if os.path.isdir(candidate):
                resolved_project_root = os.path.abspath(candidate)
                break
        if resolved_project_root is None:
            resolved_project_root = os.path.abspath(project_folder_value)
        project_root_dir = resolved_project_root
    else:
        project_root_dir = os.path.abspath(os.path.join(rfsoc_root, str(PROJECT_NAME).strip()))

    if os.path.normcase(os.path.normpath(project_root_dir)) == os.path.normcase(os.path.normpath(rfsoc_root)):
        raise ValueError(
            "Invalid project folder: rfsoc_obs_scripts cannot be used as the project folder. "
            "Please select a subfolder such as p068, survey, or testingtime.")

    os.makedirs(project_root_dir, exist_ok=True)
    _log_status(f"Project root directory set to: {project_root_dir}")

    # Create subdirectories within the project folder
    output_dir = os.path.join(project_root_dir, f"{PROJECT_NAME}_working", "")
    os.makedirs(output_dir, exist_ok=True)
    output_dir2 = os.path.join(project_root_dir, f"{PROJECT_NAME}_archive", "")
    os.makedirs(output_dir2, exist_ok=True)
    output_dir3 = os.path.join(project_root_dir, f"{PROJECT_NAME}_ephemerides", "")
    os.makedirs(output_dir3, exist_ok=True)

    obs_time_minutes = effective_default_scan_seconds / 60
    obs_time_hours = effective_default_scan_seconds / 3600

    ods_lead_time_min = int(ODS_LEAD_TIME_MINUTES)
    if TESTING == True:
        ods_lead_time_min = int(TESTING_ODS_LEAD_TIME_MINUTES)

    ods_lead_time_seconds = ods_lead_time_min * 60
    queue_length = -(-ods_lead_time_seconds // effective_default_scan_seconds) + 1

    # Testing-mode override: keep queue short for faster local/debug iterations.
    # This does not change whether ODS is used (that is still controlled by ODS_PUSH).
    if TESTING == True:
        queue_length = 3
        print(
            f"Testing mode is active (Testing={TESTING}), setting ODS queue length to "
            f"{queue_length} for faster testing.")

    print(f"ODS requires {ods_lead_time_min} minutes of lead time to activate. We will wait that long before the first observation.")
    print(f"Each target is currently set to observe for {obs_time_minutes:.2f} minutes.")
    print(f"Therefore, {queue_length} targets will be pre-loaded to ODS at a time.")

    time_step = '1m' # The ATA expects 1 minute time steps for ephemerides
    query_time_step = '6h' # For the large Horizons queries

    diameter = 6.1 * u.m # Dish diameter
    obs_location = {'lon': -121.4733, 'lat': 40.8177, 'elevation': 986} # NOTE: This is the location of HCRO

    obs_start = datetime.now(timezone.utc).replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
    hcro_obs_start = _to_pacific(datetime.now(timezone.utc).replace(second=0, microsecond=0)).strftime('%Y-%m-%d %H:%M %Z')
    obs_start_name = obs_start.replace(':', '-').replace(' ', 'T')
    obs_end = (pd.to_datetime(obs_start) + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M')

    total_obs_time = pd.to_datetime(obs_end) - pd.to_datetime(obs_start)
    _log_status(f"Observation beginning at {obs_start} (Or {hcro_obs_start} local time)")
    print(f"Each scan will last {effective_default_scan_seconds} seconds ({obs_time_minutes:.3} minutes or {obs_time_hours:.3} hours).")

def _main_thread_wrapper():
    """Execute initialization and main loop with centralized exception handling."""
    global ant_list
    try:
        _initialize_runtime()
        _start_logging()
        main()
    except SystemExit as e:
        _log_status(f"[Observing Script] SystemExit: {e}")
    except KeyboardInterrupt as e:
        _log_status(f"[Observing Script] KeyboardInterrupt: {e}")
    except RuntimeError as e:
        _log_status(f"[Observing Script] Exiting: {e}")
        # Stop was processed: release reserved antennas now (best-effort)
        try:
            if ant_list is not None and TESTING == False:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list))
                #_log_status(f"Stop processed | Releasing antennas: {antennas_for_log} (count={len(antennas_for_log)})")
                ata_control.release_antennas(list(ant_list), False)
                _log_status(f"Stop processed | Released antennas: {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
            elif TESTING == True:
                antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list or []))
                #_log_status(f"Stop processed | Releasing antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
                _log_status(f"Stop processed | Released antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
                ant_list = None
        except Exception as err:
            _log_status(f"Error releasing antennas after stop processed: {err}")
        log_urgent("Observation Stopped", color = "#FFFFFF")
    except Exception as e:
        if isinstance(e, FileNotFoundError):
            missing = getattr(e, "filename", None) or str(e)
            _log_status(f"[Observing Script] File not found: {missing}")
        else:
            _log_status(f"[Observing Script] Unhandled exception: {e}")
        print("[Observing Script] Full traceback (terminal/log):")
        traceback.print_exc()
        log_urgent("Run failed", color="#D50000")
    finally:
        if _gui_close_event.is_set():
            _log_status("GUI close requested: skipping final cleanup/release log output.")
        else:
            _log_observed_targets("Targets observed at script end")
            _clear_observed_targets()
            _log_end_run_details("Observation script ended")
            # Final cleanup: attempt to release antennas if reserved (best-effort)
            try:
                if ant_list is not None and TESTING == False:
                    antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list))
                    #_log_status(f"Final cleanup | Releasing antennas: {antennas_for_log} (count={len(antennas_for_log)})")
                    ata_control.release_antennas(list(ant_list), False)
                    _log_status(f"Final cleanup | Released antennas: {antennas_for_log} (count={len(antennas_for_log)})")
                    ant_list = None
                elif TESTING == True and ant_list:
                    antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list or []))
                    #_log_status(f"Final cleanup | Releasing antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
                    _log_status(f"Final cleanup | Released antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
                    ant_list = None
            except Exception as e:
                _log_status(f"Error releasing antennas during final cleanup: {e}")
        _stop_logging()

def build_rearranged_table(active_tuning_freqs=None):
    """Query Horizons and rebuild the target table ordered by current LST."""
    _log_status("Executing mass Horizons query...")
    location = EarthLocation(lat=obs_location['lat'],
                             lon=obs_location['lon'],
                             height=obs_location['elevation'])
    current_start = datetime.now(timezone.utc).replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
    current_end = (pd.to_datetime(current_start) + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M')
    current_start_name = current_start.replace(':', '-').replace(' ', 'T')

    obs_time_start = Time(current_start)
    lst = obs_time_start.sidereal_time('apparent', longitude=location.lon) # Outputs hours

    # Print LST in hours, degrees, and HH:MM:SS
    _log_status(f"Local Sidereal Time at {current_start} for longitude {location.lon}:")
    _log_status(f"LST (hours): {lst.hour:.4f}")
    _log_status(f"LST (degrees): {lst.deg:.2f}")
    _log_status(f"LST (HH:MM:SS): {lst.to_string(unit=u.hour, sep=':', pad=True, precision=0)}")

    # Query JPL Horizons once for relevant targets.
    # When SORT_BY_OBSERVED is enabled, trim out fully observed targets before
    # the mass query to reduce Horizons workload.
    target_list_df = pd.read_csv(CSV_NAME) # This csv has RA's for Sidereal and Solar targets in the same column, but the Horizons Name column differentiates.
    #print("Columns of target list:")
    #print(target_list_df.columns.tolist())

    query_target_df = target_list_df
    if not BYPASS_OBSERVED_CHECK:
        alias_df, _ = _apply_target_column_aliases(target_list_df, log_aliases=False)
        if ('Plaintext Name' in alias_df.columns) and ('ID' in alias_df.columns):
            keep_mask = []
            removed_observed_count = 0
            for _, row in alias_df.iterrows():
                source_name = row.get('Plaintext Name')
                source_id = row.get('ID')
                if _is_wait_schedule_target(source_name, source_id):
                    keep_mask.append(True)
                    continue

                is_unobserved = _target_has_unobserved_frequency(
                    OBSERVED_LIST,
                    source_id,
                    active_tuning_freqs,)
                keep_mask.append(bool(is_unobserved))
                if not is_unobserved:
                    removed_observed_count += 1

            if keep_mask:
                query_target_df = target_list_df.loc[keep_mask].copy()
            _log_status(
                "Mass Horizons query prefilter (observed-list): "
                f"input_rows={len(target_list_df)}, removed_already_observed={removed_observed_count}, "
                f"query_rows={len(query_target_df)}")
        else:
            _log_status(
                "Mass Horizons query prefilter skipped: target CSV is missing Plaintext Name/ID "
                "after alias mapping.")

    if len(query_target_df) == 0:
        _log_status(
            "Mass Horizons query skipped: no targets remain after observed-list prefilter.")
        return query_target_df.reset_index(drop=True)

    query_target_path = os.path.join(output_dir, f"{PROJECT_NAME}_mass_horizons_query_input.csv")
    query_target_df.to_csv(query_target_path, index=False)

    _check_stop()
    # Pass stop checker so GUI-triggered stop/abort can be handled during query.
    results_df = mass_horizons_query(target_list=query_target_path, output_dir=output_dir, obs_location=obs_location,
                                 obs_start=current_start, obs_end=current_end, time_step=query_time_step,
                                 stop_checker=_check_stop)
    results_df.to_csv(output_dir + "results_df.csv") # In case you want to save the results to a csv

    _log_status("Mass Horizons query complete. Building vertical-priority table from RA/DEC...")

    # NOTE ON BEHAVIOR CHANGE:
    # Previous logic sorted by RA and then rotated (wrapped) the table so the row closest to current LST appeared first.
    # Current logic instead ranks targets by *current altitude* at the observatory
    # location/time (highest altitude first = most vertical first).
    # Because this is a direct sort by altitude, there is no RA/LST wrap step.

    # Keep explicit LST unit variables for correctness/readability and diagnostics.
    # These values are now informational only for this vertical-priority mode.
    lst_ra_hours = lst.hour
    lst_ra_deg = lst.deg
    _log_status(f"LST for reference: {lst_ra_hours:.4f} hours | {lst_ra_deg:.2f} degrees")

    # Use each target's RA/DEC and the current observatory epoch to compute altitude "right now", then sort by altitude descending.
    # Top rows are the most vertical targets at this moment.
    dec_col = 'DEC' if 'DEC' in results_df.columns else ('DEC (deg)' if 'DEC (deg)' in results_df.columns else None)
    if dec_col is None:
        raise ValueError("Results table must include 'DEC' (or 'DEC (deg)') for vertical sorting.")

    if 'RA (deg)' in results_df.columns:
        ra_deg_values = pd.to_numeric(results_df['RA (deg)'], errors='coerce').values
    else:
        ra_deg_values = np.full(len(results_df), np.nan, dtype=float)

    if 'RA (hours)' in results_df.columns:
        ra_hours_values = pd.to_numeric(results_df['RA (hours)'], errors='coerce').values
        derived_ra_deg_values = ra_hours_values * 15.0
        ra_deg_values = np.where(np.isfinite(ra_deg_values), ra_deg_values, derived_ra_deg_values)

    if not np.isfinite(ra_deg_values).any():
        raise ValueError("Results table must include at least one usable RA column ('RA (deg)' or 'RA (hours)') for vertical sorting.")

    dec_deg_values = pd.to_numeric(results_df[dec_col], errors='coerce').values

    altitude_now_deg = np.full(len(results_df), -np.inf, dtype=float)
    valid_mask = np.isfinite(ra_deg_values) & np.isfinite(dec_deg_values)

    if np.any(valid_mask):
        observing_time = Time(current_start)
        aa = AltAz(location=location, obstime=observing_time)
        coords = SkyCoord(ra=ra_deg_values[valid_mask] * u.deg, dec=dec_deg_values[valid_mask] * u.deg)
        altitude_now_deg[valid_mask] = coords.transform_to(aa).alt.deg

    # Add a temporary altitude column for sorting, then remove it before saving.
    rearranged_tbl = results_df.copy()
    rearranged_tbl['_altitude_now_deg'] = altitude_now_deg
    rearranged_tbl = rearranged_tbl.sort_values(by='_altitude_now_deg', ascending=False, kind='mergesort').drop(columns=['_altitude_now_deg']).reset_index(drop=True)

    _log_status("Sorted by current altitude (most vertical first)")
    _log_status("First 3 rows:")
    _log_status(f"\n{rearranged_tbl.head(3)}")

    # Save the rearranged table (now vertical-priority order, not LST-wrap order).
    print(f"Saving rearranged table in vertical-priority order (LST reference: {lst})")

    # Archival copy
    rearranged_filename = f"{PROJECT_NAME}_sources_sorted_LSTstart_{current_start_name}.csv"
    rearranged_tbl.to_csv(os.path.join(output_dir2, rearranged_filename), index=False)

    # Working copy
    rearranged_tbl.to_csv(output_dir + f"{PROJECT_NAME}_sources_sorted_LSTstart.csv", index=False)

    _log_status(f"Vertical-priority table saved: {rearranged_filename}")
    return rearranged_tbl


# NOTE: MAIN
def main():
    """Run the end-to-end observation loop across queued survey targets."""
    _log_status("==================== Script Initiated ====================")
    _clear_observed_targets()
    _clear_transient_skipped_targets()

    _log_status("The following are the user inputs for this observation script:")
    _log_status(f"Project Name: {PROJECT_NAME}")
    _log_status(f"Observation Time (seconds): {OBS_TIME}")
    _log_status(f"\nCSV Name: {CSV_NAME}")
    # _log_status("CSV file columns:")
    # _log_status(pd.read_csv(CSV_NAME).columns.tolist())
    _log_status(f"Observed List: {OBSERVED_LIST}\n")
    _log_status(f"Remove Antennas: {REMOVE_ANT}")
    _log_status(f"Selected Recorders: {sorted(normalize_hashpipe_targets(ACTIVE_RECORDERS).keys())}")
    _log_status(f"Rearrange by LST: {REARRANGE_BY_LST}")
    _log_status(f"Recording: {RECORDING}")
    _log_status(f"Testing Mode: {TESTING}")
    _log_status(f"Use per-target Obs Time override: {USE_TARGET_OBS_TIME_OVERRIDE}")

    _check_stop()

    # Use module-level ant_list so Stop can release antennas
    global ant_list, ant_list_initial_active_snapshot, ant_list_used_snapshot, ant_list_removed_snapshot

    # Reset run snapshots before selecting antennas for this session.
    ant_list_initial_active_snapshot = []
    ant_list_used_snapshot = []
    ant_list_removed_snapshot = []

    if TESTING == False:
        _log_status("Getting antenna list and removing bad antennas")
        # Get antenna list and separate into 4 tunings
        ant_list = _normalize_antennas(snap_config.get_rfsoc_active_antlist())
        ant_list_initial_active_snapshot = list(ant_list)

        requested_removed = _normalize_antennas(REMOVE_ANT)
        ant_list_removed_snapshot = [ant for ant in requested_removed if ant in ant_list_initial_active_snapshot]
        if requested_removed: # Only process if list is not empty
            for ant in ant_list_removed_snapshot:
                if ant in ant_list:
                    ant_list.remove(ant)
                    _log_status(f"Antenna removed completely: {ant}")

            requested_not_active = [ant for ant in requested_removed if ant not in ant_list_initial_active_snapshot]
            if requested_not_active:
                _log_status(f"Requested removed antennas not in current SNAP active list: {requested_not_active}")

        ant_list_used_snapshot = _normalize_antennas(ant_list)
        if not ant_list:
            raise RuntimeError(
                "No active antennas remain after applying REMOVE_ANT. "
                "Check GUI antenna selections or REMOVE_ANT defaults before running.")
    if TESTING == True:
        _log_status("Testing turned on. Simulating antenna removal/reservation without ATA calls.")
        requested_removed = _normalize_antennas(REMOVE_ANT)
        simulated_active = _normalize_antennas(GUI_SELECTED_ANTENNAS)

        # In testing mode, use GUI-selected antennas as the simulated active set.
        # This keeps end-of-run reporting aligned with what would be reserved.
        if simulated_active:
            ant_list_initial_active_snapshot = list(simulated_active)
            ant_list_removed_snapshot = [ant for ant in requested_removed if ant in ant_list_initial_active_snapshot]
            requested_not_active = [ant for ant in requested_removed if ant not in ant_list_initial_active_snapshot]
            if requested_not_active:
                _log_status(f"Requested removed antennas not in simulated active list: {requested_not_active}")

            ant_list = [ant for ant in ant_list_initial_active_snapshot if ant not in set(ant_list_removed_snapshot)]
            ant_list_used_snapshot = _normalize_antennas(ant_list)
        else:
            ant_list_initial_active_snapshot = []
            ant_list_removed_snapshot = list(requested_removed)
            ant_list = []
            ant_list_used_snapshot = []
            _log_status(
                "Testing mode has no GUI_SELECTED_ANTENNAS; simulated reserved list is empty. "
                "Run from GUI or pass GUI_SELECTED_ANTENNAS in config to simulate antenna reservation.")

        _log_status(f"Antennas removed completely: {ant_list_removed_snapshot}")

    # Also report any antennas marked 'remove from calibration procedure' if a status map is available.
    try:
        observing_status_map = None
        # Prefer any status map defined in this module
        if 'OBSERVING_STATUS_BY_ANTENNA' in globals():
            observing_status_map = globals().get('OBSERVING_STATUS_BY_ANTENNA')
        # Fall back to a camel/case variant
        if not observing_status_map and 'observing_status_by_antenna' in globals():
            observing_status_map = globals().get('observing_status_by_antenna')
        # If not present locally, try to import from survey_gui if available (optional)
        if not observing_status_map:
            try:
                import beamforming_gui as _sg
                observing_status_map = getattr(_sg, 'OBSERVING_STATUS_BY_ANTENNA', None) or getattr(_sg, 'observing_status_by_antenna', None)
            except Exception:
                observing_status_map = None

        cal_removed = []
        if observing_status_map:
            for ant, st in (observing_status_map or {}).items():
                if st and isinstance(st, str) and 'calibration' in st.lower() and 'remove' in st.lower():
                    cal_removed.append(ant)

        if cal_removed:
            _log_status(f"Antennas removed from Calibration': {sorted(cal_removed)}")
        else:
            _log_status("Antennas removed from Calibration: []")
    except Exception:
        # Best-effort only; do not block observations on status reporting
        pass

    # Can also manually remove antennae if desired
    #ant_list.remove("2j") # As an example

    # For Exotica
    # Bands to Observe and Midpoints:
    # 1.000-1.672 GHz - 1.336 GHz
    # 1.672-2.344 GHz - 2.008 GHz
    # 4.200-4.872 GHz - 4.536 GHz
    # 8.000-8.672 GHz - 8.336 GHz

    # 1.000-1.672 GHz, 1.672-2.344 GHz, 4.200-4.872 GHz, and 8.000-8.672 GHz.
    _check_stop()

    if TESTING == False:
        # Define frequenies like above
        # This pulls frequencies from the ATA. Make sure it all agrees.
        freqs_a = [int(ata_control.get_sky_freq('a'))]*len(ant_list)
        freqs_b = [int(ata_control.get_sky_freq('b'))]*len(ant_list)
        freqs_c = [int(ata_control.get_sky_freq('c'))]*len(ant_list)
        freqs_d = [int(ata_control.get_sky_freq('d'))]*len(ant_list)

        _log_status(f"Center frequencies set to {freqs_a[0]} MHz, {freqs_b[0]} MHz, {freqs_c[0]} MHz, and {freqs_d[0]} MHz.")

        _check_stop()
        # Register and reserve antennas
        antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list))
        _log_status(f"About to reserve antennas: {antennas_for_log} (count={len(antennas_for_log)})")
        ata_control.reserve_antennas(ant_list)

        # Standalone script mode keeps legacy atexit release behavior.
        # GUI-controlled mode intentionally skips this so GUI close/X/Ctrl+C does not auto-release antennas.
        if not _GUI_CONTROLLED:
            atexit.register(ata_control.release_antennas, list(ant_list), False)
        else:
            _log_status("GUI-controlled mode: skipping atexit antenna release registration.")
        _log_status(f"Antennas reserved: {antennas_for_log} (count={len(antennas_for_log)})")
        _check_stop()
        # NOTE: Make sure that this will release all antennas upon finishing an observation, not just upon closing the GUI.

    if TESTING == True:
        antennas_for_log = sorted(str(ant).strip() for ant in list(ant_list or []))
        _log_status(f"About to reserve antennas (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
        _log_status("This is where the antennas would be reserved, the beamwidths would be defined, and the SETI nodes would be activated.")
        freqs_a = [1336]*4
        freqs_b = [2008]*4
        freqs_c = [4536]*4
        freqs_d = [8336]*4
        # I filled this in with Exotica ranges to save time. Should still be able to handle other values
        _log_status(f"Antennas reserved (simulated): {antennas_for_log} (count={len(antennas_for_log)})")
        _check_stop()

        _log_status(f"Center frequencies set to {freqs_a[0]} MHz, {freqs_b[0]} MHz, {freqs_c[0]} MHz, and {freqs_d[0]} MHz for testing.")

    _check_stop()
    active_tuning_maps, active_tuning_indices, d = _build_active_tuning_maps(
        ACTIVE_RECORDERS,
        explicit_selection=_ACTIVE_RECORDERS_EXPLICIT,)
    tuning_map_by_index = {
        tuning_index: tuning_map
        for tuning_index, tuning_map in zip(active_tuning_indices, active_tuning_maps)}

    d_loa = tuning_map_by_index.get(0, {})
    d_lob = tuning_map_by_index.get(1, {})
    d_loc = tuning_map_by_index.get(2, {})
    d_lod = tuning_map_by_index.get(3, {})
    selected_recorder_nodes = set(d.keys())
    _log_status(f"Recorder nodes in use: {selected_recorder_nodes if selected_recorder_nodes else []}")

    global active_tuning_freqs
    base_tuning_freqs = []
    for tuning_freq_list in (freqs_a, freqs_b, freqs_c, freqs_d):
        if tuning_freq_list:
            base_tuning_freqs.append(int(tuning_freq_list[0]))
        else:
            base_tuning_freqs.append(None)

    active_tuning_freqs = [
        base_tuning_freqs[tuning_index]
        for tuning_index in active_tuning_indices
        if tuning_index < len(base_tuning_freqs) and base_tuning_freqs[tuning_index] is not None]

    active_tuning_labels = [TUNING_LABELS[tuning_index] for tuning_index in active_tuning_indices if tuning_index < len(TUNING_LABELS)]
    _log_status(f"Tunings in use: {active_tuning_labels if active_tuning_labels else []}")
    if _ACTIVE_RECORDERS_EXPLICIT and not d:
        _log_status("Recorder selection was provided by GUI, but no valid recorder streams were selected.")

    # Fail fast on CSV schema issues before any queueing/ODS waiting can begin.
    _validate_csv_columns_preflight(active_tuning_freqs)

    if TESTING == False and all(freq_list for freq_list in (freqs_a, freqs_b, freqs_c, freqs_d)):
        f = np.array([freqs_a[0], freqs_b[0], freqs_c[0], freqs_d[0]]) / 1e3 # Put the frequencies into an array, convert to GHz
        primary_beamwidths = primary_beam_diameter(f)
        synthesized_beamwidths = synthesized_beam_diameter(f)
        separation = 5 * synthesized_beamwidths # Separation between on and off beams
        _log_status(f"Beam separation set to {separation} degrees and {synthesized_beamwidths} beamwidths.")
        _log_status(f"Primary beamwidths: {primary_beamwidths}")
    else:
        separation = np.array([])
        if TESTING == False:
            _log_status("No active recorder tunings selected. Recording-related actions will be skipped safely.")

    _check_stop()
    _log_status("=================== Acquiring source list ===================")


    # THIS IS WHERE THE COLUMNS ARE IMPORTANT IN THE CSV                                            ========================

    # NOTE TODO: This is where I need to implement the new scheduling system
    if REARRANGE_BY_LST and _HORIZONS_ENABLED:
        _log_status("Table Rearrange Enabled. Sorting target list by most vertical (based on LST).")
        rearranged_tbl = build_rearranged_table(active_tuning_freqs=active_tuning_freqs)
    elif REARRANGE_BY_LST and (not _HORIZONS_ENABLED):
        _warn_horizons_disabled_once(
            "LST reorder requires Horizons query path; falling back to CSV order for this run")
        _log_status("LST rearrange requested but Horizons is disabled. Using target CSV order as-is.")
        rearranged_tbl = pd.read_csv(CSV_NAME)
    else:
        _log_status("LST rearrange disabled. Using target CSV order as-is.")
        rearranged_tbl = pd.read_csv(CSV_NAME)

    # Keep archival snapshots sourced from the full CSV (unfiltered).
    archive_df_full = _load_full_target_table_for_archive(log_aliases=True)
    if isinstance(archive_df_full, pd.DataFrame):
        _write_full_archive_target_copy(archive_df_full, snapshot_label="initial")

    # Read in the reordered working table used by scheduler/loop logic.
    target_df_full = _ensure_obs_time_column(rearranged_tbl)
    target_df_full, target_col_map = _apply_target_column_aliases(target_df_full, log_aliases=True)
    horizons_available = "Horizons Name" in target_df_full.columns
    if not horizons_available:
        _warn_horizons_disabled_once(
            "Main loop running without Horizons Name column; JPL Horizons calls will be skipped")

    # Build and persist the filtered working copy used by the scheduler/loop.
    target_df = _filter_working_target_table(
        target_df_full,
        active_tuning_freqs=active_tuning_freqs,
        context_label="Initial target filter",)
    _write_working_target_copy(target_df)

    # Post-reorder guard: reuse the same required-column + alias validation used in preflight.
    target_ok, target_validation_message = _validate_required_target_columns(
        target_df,
        context_label="Reordered working target table",)
    if not target_ok:
        _log_status(f"ERROR: {target_validation_message}")
        raise ValueError(target_validation_message)

    plain_names = list(target_df['Plaintext Name'])
    horizons_name = list(target_df['Horizons Name']) if horizons_available else [None] * len(target_df)
    source_ids = list(target_df['ID'])
    solsys_flag = list(target_df['Solar System Flag'])

    ra_hours_list = _get_optional_column_values(target_df, 'RA (hours)') # RA in hours
    ra_deg_list = _get_optional_column_values(target_df, 'RA (deg)') # RA in degrees
    ra_solsys_list = _get_optional_column_values(target_df, 'RA (solsys)')
    dec_list = list(target_df['DEC']) # DEC always in degrees
    dec_solsys_list = _get_optional_column_values(target_df, 'DEC (solsys)')

    # Flag to track if this is the first time the queue has been pushed to ODS
    first_queue_pushed = True
    last_reorder_time = time.time()
    _log_status(f"Just acquired source list. The last LST reorder time set to {last_reorder_time} (time.time() function)")

    # Rolling-queue scheduling anchor
    # These variables describe the queue planner's timeline:
    # - next planned slot start (UTC)
    # - last queued coordinates (for inter-target slew estimates)
    # - reservation bookkeeping for sanity checks/repushes
    reservation_buffer = timedelta(seconds=max(0, int(ODS_RESERVATION_BUFFER_SECONDS)))
    ods_schedule_next_start_utc = None
    ods_schedule_last_coords = None
    pushed_targets = set()
    ods_reservations_by_target = {}

    _log_status(
        "ODS scheduler config: "
        f"Az rate={ODS_SLEW_AZ_RATE_DEG_PER_SEC} deg/s, "
        f"El rate={ODS_SLEW_EL_RATE_DEG_PER_SEC} deg/s, "
        f"conservative multiplier={ODS_SLEW_CONSERVATIVE_MULTIPLIER}, "
        f"slew extra buffer={ODS_SLEW_EXTRA_BUFFER_SECONDS}s, "
        f"reservation buffer={ODS_RESERVATION_BUFFER_SECONDS}s"
    )

    # Find the first queue_length targets that have not yet been observed
    # If they are in the solar system, query Horizons for their current RA/DEC
    # If they are sidereal, use the RA/DEC from the csv
    # Check altitude and distance from Sun
    # If the target is ready after those things, push ODS.
    # If it's the very first run, wait for the wait_time (30 mins)
    # After that wait time is done (and ONLY wait for the very first scan), begin observing
    # After that first target finishes, it should go back through the loop and send the next queue_length targets to ODS.
    # It should NOT have the wait time again because it should already be loaded.










    # Step 1: Begin the loop itself, starting with the top of the sorted table.
    # Use a bounded retry mode at end-of-list so moving targets can be retried after refresh without risking an infinite loop.
    i = 0
    end_of_list_retry_count = 0
    while True: # This while loop controls basically the whole thing.
        if i >= len(plain_names):
            _log_status("Reached end of current target table.")

            if not END_OF_LIST_RETRY_ENABLED:
                _log_status("End-of-list retry is disabled. Ending observation loop.")
                break

            has_transient_skips = bool(
                skipped_altitude_targets
                or skipped_sun_targets
                or skipped_moon_targets
                or skipped_planet_targets
                or skipped_data_targets)

            if not has_transient_skips:
                _log_status(
                    "No transient altitude/sun/moon skips are pending. "
                    "Ending observation loop without refresh retry.")
                break

            # Check retry limit (skip check if MAX_END_OF_LIST_RETRIES is "Max" for infinite retries)
            if str(MAX_END_OF_LIST_RETRIES).lower() != "max" and end_of_list_retry_count >= max(0, int(MAX_END_OF_LIST_RETRIES)):
                _log_status(
                    f"Reached max end-of-list retries ({MAX_END_OF_LIST_RETRIES}). "
                    "Ending observation loop to avoid refresh lock.")
                _log_transient_skipped_targets("Final transient skipped targets")
                break

            end_of_list_retry_count += 1
            retry_limit_str = "unlimited" if str(MAX_END_OF_LIST_RETRIES).lower() == "max" else str(MAX_END_OF_LIST_RETRIES)
            _log_status(
                f"End-of-list refresh retry {end_of_list_retry_count}/{retry_limit_str} "
                "starting.")
            _log_transient_skipped_targets("Skipped targets before end-of-list refresh")

            wait_seconds = max(0, int(END_OF_LIST_RETRY_WAIT_SECONDS))
            if wait_seconds > 0:
                _log_status(
                    f"Waiting {wait_seconds} seconds before retry refresh so moving targets can move.")
                _check_stop()
                wait_with_stop(wait_seconds, allow_stop=True)
                _check_stop()  # Process stop if triggered during end-of-list retry wait

            if REARRANGE_BY_LST and _HORIZONS_ENABLED:
                _log_status("End-of-list retry: rebuilding reordered target table.")
                rearranged_tbl = build_rearranged_table(active_tuning_freqs=active_tuning_freqs)
            elif REARRANGE_BY_LST and (not _HORIZONS_ENABLED):
                _warn_horizons_disabled_once(
                    "End-of-list reorder requested but Horizons is disabled; reloading CSV order")
                _log_status("End-of-list retry: Horizons disabled, reloading target CSV order as-is.")
                rearranged_tbl = pd.read_csv(CSV_NAME)
            else:
                _log_status("End-of-list retry: LST reorder disabled, reloading target CSV as-is.")
                rearranged_tbl = pd.read_csv(CSV_NAME)

            archive_df_full = _load_full_target_table_for_archive(log_aliases=False)
            if isinstance(archive_df_full, pd.DataFrame):
                _write_full_archive_target_copy(archive_df_full, snapshot_label="end_of_list_refresh")

            target_df_full = _ensure_obs_time_column(rearranged_tbl)
            target_df_full, target_col_map = _apply_target_column_aliases(target_df_full, log_aliases=False)
            horizons_available = "Horizons Name" in target_df_full.columns
            target_df = _filter_working_target_table(
                target_df_full,
                active_tuning_freqs=active_tuning_freqs,
                context_label="End-of-list refresh filter",)

            _write_working_target_copy(target_df)
            plain_names = list(target_df['Plaintext Name'])
            horizons_name = list(target_df['Horizons Name']) if horizons_available else [None] * len(target_df)
            source_ids = list(target_df['ID'])
            solsys_flag = list(target_df['Solar System Flag'])
            ra_hours_list = _get_optional_column_values(target_df, 'RA (hours)')
            ra_deg_list = _get_optional_column_values(target_df, 'RA (deg)')
            ra_solsys_list = _get_optional_column_values(target_df, 'RA (solsys)')
            dec_list = list(target_df['DEC'])
            dec_solsys_list = _get_optional_column_values(target_df, 'DEC (solsys)')
            i = 0
            last_reorder_time = time.time()

            _clear_transient_skipped_targets()
            _log_status("Reset transient altitude/sun/moon skipped-target lists after end-of-list refresh.")
            continue

        # Stop after current scan if requested
        _check_stop()

        elapsed_since_reorder = time.time() - last_reorder_time
        seconds_until_reorder = max(0, REORDER_INTERVAL_SECONDS - elapsed_since_reorder)
        # NOTE TODO: This statement prints over and over for some reason. Check on it.
        _log_status(f"Time since last LST reorder: {elapsed_since_reorder:.0f}s | Time until next reorder: {seconds_until_reorder:.0f}s")
        if REARRANGE_BY_LST and time.time() - last_reorder_time >= REORDER_INTERVAL_SECONDS:
            current_source = plain_names[i] if i < len(plain_names) else None
            _log_status("Rebuilding LST-sorted target table (hourly refresh).")
            _log_transient_skipped_targets("Skipped targets before periodic reorder reset")
            if _HORIZONS_ENABLED:
                rearranged_tbl = build_rearranged_table(active_tuning_freqs=active_tuning_freqs)
            else:
                _warn_horizons_disabled_once(
                    "Periodic reorder requested but Horizons is disabled; reloading CSV order")
                _log_status("Periodic reorder: Horizons disabled, reloading target CSV order as-is.")
                rearranged_tbl = pd.read_csv(CSV_NAME)
            archive_df_full = _load_full_target_table_for_archive(log_aliases=False)
            if isinstance(archive_df_full, pd.DataFrame):
                _write_full_archive_target_copy(archive_df_full, snapshot_label="periodic_refresh")

            target_df_full = _ensure_obs_time_column(rearranged_tbl)
            target_df_full, target_col_map = _apply_target_column_aliases(target_df_full, log_aliases=False)
            horizons_available = "Horizons Name" in target_df_full.columns
            target_df = _filter_working_target_table(
                target_df_full,
                active_tuning_freqs=active_tuning_freqs,
                context_label="Periodic refresh filter",)

            # NOTE: Make sure this section works with aliases
            _write_working_target_copy(target_df)
            plain_names = list(target_df['Plaintext Name'])
            horizons_name = list(target_df['Horizons Name']) if horizons_available else [None] * len(target_df)
            source_ids = list(target_df['ID'])
            solsys_flag = list(target_df['Solar System Flag'])
            ra_hours_list = _get_optional_column_values(target_df, 'RA (hours)') # RA in hours
            ra_deg_list = _get_optional_column_values(target_df, 'RA (deg)') # RA in degrees
            ra_solsys_list = _get_optional_column_values(target_df, 'RA (solsys)')
            dec_list = list(target_df['DEC']) # DEC always in degrees
            dec_solsys_list = _get_optional_column_values(target_df, 'DEC (solsys)')

            if current_source in plain_names:
                i = plain_names.index(current_source)
            else:
                i = 0

            last_reorder_time = time.time()
            _clear_transient_skipped_targets()
            _log_status("Reset transient altitude/sun/moon skipped-target lists after periodic reorder.")

        source = plain_names[i]
        source_id = source_ids[i]
        source_key = _normalize_target_id_key(source_id)
        source_identity_key = source_key if source_key else f"name:{str(source).strip().lower()}"
        source_label = _format_name_id_label(source, source_id)
        is_wait_marker_target = _is_wait_schedule_target(source, source_id)

        if is_wait_marker_target:
            _log_status(
                f"Schedule wait marker detected at {source_label}. "
                "This row will pause the queue and will not be marked as observed.")

        # Skip if already observed in this run (in-memory) or in the persistent observed list
        # NOTE TODO: Find a way to ignore this in some way to observe the same target over and over again
        if source_identity_key in observed_target_ids_seen:
            print(f"Target {source_label} already observed in this run (in-memory). Skipping.")
            _check_stop()
            i += 1
            continue

        # If persistent observed-list checking is enabled, consult it now and skip if fully observed
        if (not is_wait_marker_target) and (not BYPASS_OBSERVED_CHECK):
            freqs_check = list(active_tuning_freqs)
            if freqs_check:
                any_not_observed = _target_has_unobserved_frequency(OBSERVED_LIST, source_id, freqs_check)

                # If none of the bands are "not observed" (i.e., one of them has been observed before), skip
                if not any_not_observed:
                    print(f"Target {source_label} already observed in observed-list. Skipping.")
                    _check_stop()
                    i += 1
                    continue

        # Redefine the time and start of the loop for each iteration
        scan_start = datetime.now(timezone.utc).replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
        scan_end = (pd.to_datetime(scan_start) + timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M')
        ata_scan_start = _to_pacific(datetime.now(timezone.utc).replace(second=0, microsecond=0)).strftime('%Y-%m-%d %H:%M %Z')
        # Build these once per target-loop iteration and reuse in queue/main checks.
        current_scan_observing_location = EarthLocation(lat='40.8177', lon='-121.4733', height=986 * u.m)
        current_scan_observing_time = Time(scan_start)
        current_scan_altaz_frame = AltAz(
            location=current_scan_observing_location,
            obstime=current_scan_observing_time,)

        _check_stop()
        _log_status("\n==================== Top of the loop ====================")
        _log_status(f"Current time = {scan_start} UTC (Or {ata_scan_start} HCRO time)")
        _log_status(f"Current target: {i} - {source}\n")

        scan_timing = resolve_scan_duration_seconds(
            target_df,
            i,
            default_obs_seconds=OBS_TIME,
            use_target_obs_time_override=USE_TARGET_OBS_TIME_OVERRIDE,
            testing=TESTING,
            testing_obs_time_seconds=TESTING_OBS_TIME_SECONDS,)

        nominal_scan_seconds = int(scan_timing["nominal_seconds"])
        effective_scan_seconds = int(scan_timing["effective_seconds"])
        duration_source = scan_timing["duration_source"]
        if TESTING:
            _log_status(
                f"Scan timing for {source}: would use {nominal_scan_seconds}s from {duration_source}; "
                f"TESTING override active -> using {effective_scan_seconds}s.")
        else:
            _log_status(
                f"Scan timing for {source}: using {effective_scan_seconds}s from {duration_source}.")

        if is_wait_marker_target:
            # Always resolve per-row Obs Time for wait rows regardless of
            # USE_TARGET_OBS_TIME_OVERRIDE so scheduler-written durations are
            # honored even when the global override flag is off.
            wait_row_timing = resolve_scan_duration_seconds(
                target_df,
                i,
                default_obs_seconds=OBS_TIME,
                use_target_obs_time_override=True,
                testing=TESTING,
                testing_obs_time_seconds=TESTING_OBS_TIME_SECONDS,)

            effective_scan_seconds = int(wait_row_timing["effective_seconds"])
            _log_status(
                f"Schedule wait marker detected at {source_label}. "
                f"Wait duration: {effective_scan_seconds}s (from {wait_row_timing['duration_source']}). "
                "Queue planning will account for this wait before observing continues.")

        # Ensure the queue variable exists regardless of ODS_PUSH setting
        targets_to_queue = []

        if ODS_PUSH:
            _log_status("Beginning queue check...")
            # Step 2: Find next queue_length targets for queuing to ODS
            # This stage is a protection pre-pass:
            # - validate candidate targets
            # - compute planned slot timing
            # - push reservation windows before observing
            targets_to_queue = []
            queue_plan_entries = []
            queue_idx = i
            queue_count = 0
            while queue_idx < len(plain_names) and queue_count < queue_length:
                queue_source = plain_names[queue_idx]
                queue_source_id = source_ids[queue_idx]
                queue_source_key = _normalize_target_id_key(queue_source_id)
                queue_source_identity_key = (
                    queue_source_key if queue_source_key else f"name:{str(queue_source).strip().lower()}")

                queue_source_label = _format_name_id_label(queue_source, queue_source_id)
                print(f"Beginning queue check for target: {queue_source_label}")
                _check_stop()

                if _is_wait_schedule_target(queue_source, queue_source_id):
                    queue_wait_timing = resolve_scan_duration_seconds(
                        target_df,
                        queue_idx,
                        default_obs_seconds=OBS_TIME,
                        use_target_obs_time_override=USE_TARGET_OBS_TIME_OVERRIDE,
                        testing=TESTING,
                        testing_obs_time_seconds=TESTING_OBS_TIME_SECONDS,)

                    queue_wait_seconds = max(1, int(queue_wait_timing["effective_seconds"]))
                    queue_plan_entries.append(("wait", queue_wait_seconds, queue_source_label))
                    _log_status(
                        f"Queue planner accounted schedule wait row {queue_source_label} "
                        f"(+{queue_wait_seconds}s timeline offset).")
                    queue_idx += 1
                    continue

                # Step 2: Check if this target has been previously observed
                if BYPASS_OBSERVED_CHECK or (
                    _target_has_unobserved_frequency(OBSERVED_LIST, queue_source_id, active_tuning_freqs)):
                    print(f"Target {queue_source_label} has not yet been observed.")
                else:
                    print(f"Target {queue_source_label} already observed. Skipping queue candidate.")
                    _check_stop()
                    queue_idx += 1
                    continue

                # Get RA/DEC for this target
                queue_ra_deg = None
                queue_dec = None
                queue_flag = parse_solar_system_flag(solsys_flag[queue_idx])

                if queue_flag is None:
                    print(
                        f"Error: target {queue_source} has unexpected Solar System Flag "
                        f"value '{solsys_flag[queue_idx]}'. Soft-skipping until next refresh.")
                    _record_skipped_target(queue_source, "data")
                    queue_idx += 1
                    continue

                if queue_flag == 1:
                    this_horizons_name = horizons_name[queue_idx]
                    if horizons_available and str(this_horizons_name or "").strip():
                        print(f"Target {queue_source} is a Solar System target ({this_horizons_name}). Querying instantaneous Horizons coordinates.")
                        queue_ra_deg, queue_dec, queue_name_to_query = _get_instantaneous_solar_system_coordinates(
                            queue_source,
                            this_horizons_name,
                            scan_start,)
                        if (not is_valid_finite_float(queue_ra_deg)) or (not is_valid_finite_float(queue_dec)):
                            print(
                                f"Error querying instantaneous Horizons coordinates for {queue_source} "
                                f"({queue_name_to_query}). Soft-skipping until next refresh.")
                            _record_skipped_target(queue_source, "data")
                            queue_idx += 1
                            continue
                    else:
                        # NOTE: revisit no-Horizons Solar-System strategy.
                        queue_ra_deg, queue_dec = _resolve_solar_system_coordinates_without_horizons(
                            source_name=str(queue_source),
                            ra_solsys_value=ra_solsys_list[queue_idx],
                            dec_solsys_value=dec_solsys_list[queue_idx],
                            ra_hours_value=ra_hours_list[queue_idx],
                            ra_deg_value=ra_deg_list[queue_idx],
                            dec_value=dec_list[queue_idx],
                            context="queue solar fallback",)

                        if (not is_valid_finite_float(queue_ra_deg)) or (not is_valid_finite_float(queue_dec)):
                            print(
                                f"No Horizons Name / fallback coordinates available for Solar System target {queue_source}. "
                                "Soft-skipping until next refresh.")
                            _record_skipped_target(queue_source, "data")
                            queue_idx += 1
                            continue
                        _log_status(
                            f"Solar-system queue fallback active for {queue_source}: using non-Horizons coordinates. "
                            "NOTE: revisit no-Horizons Solar-System strategy.")
                else:
                    print(f"Target {queue_source} is a Sidereal target. Using RA/DEC from CSV.")
                    queue_ra_hours = ra_hours_list[queue_idx]
                    queue_ra_deg = ra_deg_list[queue_idx]
                    queue_dec = dec_list[queue_idx]

                    resolved_queue_ra = _resolve_sidereal_ra_pair(
                        queue_ra_hours,
                        queue_ra_deg,
                        source_name=str(queue_source),
                        context="queue",)
                    if resolved_queue_ra is None:
                        print(
                            f"Error: invalid sidereal RA for {queue_source} "
                            f"(RA_hours={queue_ra_hours}, RA_deg={queue_ra_deg}). "
                            "Soft-skipping until next refresh.")
                        _record_skipped_target(queue_source, "data")
                        queue_idx += 1
                        continue
                    queue_ra_hours, queue_ra_deg = resolved_queue_ra

                if (not is_valid_finite_float(queue_ra_deg)) or (not is_valid_finite_float(queue_dec)):
                    print(
                        f"Error: invalid RA/DEC for {queue_source} "
                        f"(RA={queue_ra_deg}, DEC={queue_dec}). Soft-skipping until next refresh.")
                    _record_skipped_target(queue_source, "data")
                    queue_idx += 1
                    continue

                queue_ra_deg = float(queue_ra_deg)
                queue_dec = float(queue_dec)

                # Check altitude
                coord = SkyCoord(ra=queue_ra_deg * u.deg, dec=queue_dec * u.deg)
                altaz_coord = coord.transform_to(current_scan_altaz_frame)
                queue_alt = altaz_coord.alt.value

                if not (ALT_MAX > queue_alt > ALT_MIN): # NOTE TODO: Set this to variables I can define at the top, in case this changes
                    _log_status(f"Target {queue_source} is out of altitude bounds ({queue_alt:.1f} degrees). Skipping.")
                    _record_skipped_target(queue_source, "altitude")
                    queue_idx += 1
                    continue



                # Sun separation (guarded by SUN_AVOIDANCE)
                if SUN_AVOIDANCE:
                    sun = resolve_body_position(
                        "sun",
                        scan_start=scan_start,
                        obs_location=obs_location,
                        testing=TESTING,
                        ata_sources_module=(None if TESTING else ata_sources),
                        logger=print,)

                    if not isinstance(sun, dict) or 'ra' not in sun or 'dec' not in sun:
                        print(
                            f"Error: could not determine Sun position for {queue_source}. "
                            "Soft-skipping until next refresh.")
                        _record_skipped_target(queue_source, "sun")
                        queue_idx += 1
                        continue
                    sun_ra = sun['ra']
                    sun_dec = sun['dec']
                    target_coord = SkyCoord(ra=queue_ra_deg * u.deg, dec=queue_dec * u.deg)
                    sun_coord = SkyCoord(ra=sun_ra * u.deg, dec=sun_dec * u.deg)
                    separation_from_sun = target_coord.separation(sun_coord).deg
                    print(f"Current separation from Sun for target {queue_source}: {separation_from_sun:.2f} degrees")

                    if separation_from_sun < MIN_SUN_MOON_SEPARATION_DEGREES:
                        print(
                            f"Target {queue_source} is too close to the Sun "
                            f"({separation_from_sun:.2f} degrees < {MIN_SUN_MOON_SEPARATION_DEGREES}). Skipping.")
                        _record_skipped_target(queue_source, "sun")
                        queue_idx += 1
                        continue

                # Moon separation (guarded by MOON_AVOIDANCE)
                if MOON_AVOIDANCE:
                    moon = resolve_body_position(
                        "moon",
                        scan_start=scan_start,
                        obs_location=obs_location,
                        testing=TESTING,
                        ata_sources_module=(None if TESTING else ata_sources),
                        logger=print,)

                    if not isinstance(moon, dict) or 'ra' not in moon or 'dec' not in moon:
                        print(
                            f"Error: could not determine Moon position for {queue_source}. "
                            "Soft-skipping until next refresh.")
                        _record_skipped_target(queue_source, "moon")
                        queue_idx += 1
                        continue
                    moon_ra = moon['ra']
                    moon_dec = moon['dec']
                    target_coord = SkyCoord(ra=queue_ra_deg * u.deg, dec=queue_dec * u.deg)
                    moon_coord = SkyCoord(ra=moon_ra * u.deg, dec=moon_dec * u.deg)
                    separation_from_moon = target_coord.separation(moon_coord).deg
                    print(f"Current separation from Moon for target {queue_source}: {separation_from_moon:.2f} degrees")

                    if separation_from_moon < MIN_SUN_MOON_SEPARATION_DEGREES:
                        print(
                            f"Target {queue_source} is too close to the Moon "
                            f"({separation_from_moon:.2f} degrees < {MIN_SUN_MOON_SEPARATION_DEGREES}). Skipping.")
                        _record_skipped_target(queue_source, "moon")
                        queue_idx += 1
                        continue

                if PLANET_AVOIDANCE:
                    # Check bright planets separation
                    closest_planet = _closest_planet_violation(queue_ra_deg, queue_dec, scan_start)
                    if closest_planet is not None:
                        planet_name, separation_deg = closest_planet
                        print(
                            f"Target {queue_source} is too close to {planet_name} "
                            f"({separation_deg:.2f} degrees < {MIN_PLANET_SEPARATION_DEGREES}). Skipping.")
                        _record_skipped_target(queue_source, "planet")
                        queue_idx += 1
                        continue

                # Count it toward the queue window
                queue_count += 1

                queue_scan_timing = resolve_scan_duration_seconds(
                    target_df,
                    queue_idx,
                    default_obs_seconds=OBS_TIME,
                    use_target_obs_time_override=USE_TARGET_OBS_TIME_OVERRIDE,
                    testing=TESTING,
                    testing_obs_time_seconds=TESTING_OBS_TIME_SECONDS,)
                queue_scan_seconds = int(queue_scan_timing["effective_seconds"])

                _check_stop()
                # Only push if this target has not already been pushed
                if queue_source_identity_key not in pushed_targets:
                    queue_target_entry = (
                        queue_idx,
                        queue_source,
                        queue_source_id,
                        queue_source_identity_key,
                        queue_ra_deg,
                        queue_dec,
                        queue_scan_seconds,)
                    targets_to_queue.append(queue_target_entry)
                    queue_plan_entries.append(("target", queue_target_entry))
                    _log_status(f"Target {queue_source_label} added to queue (new push).")
                else:
                    _log_status(
                        f"Target {queue_source_label} already pushed earlier by ID; "
                        "skipping duplicate push.")

                if queue_count >= queue_length:
                    _log_status(f"Reached queue length of {queue_length}. Proceeding with ODS push function.")
                    break

                queue_idx += 1

        _check_stop()
        if ODS_PUSH:
            if len(targets_to_queue) < queue_length:
                _log_status(f"Queue fill incomplete: only {len(targets_to_queue)}/{queue_length} targets met criteria after scanning the remaining list.")

            # Push all queued targets to ODS (outside inner loop, after targets are evaluated)
            if targets_to_queue:
                _log_status(f"Pushing {len(targets_to_queue)} queued target(s) to ODS...")
                _log_status(f"Queued targets are: {[t[1] for t in targets_to_queue]}")

            pushed_this_round = 0
            for queue_plan_entry in queue_plan_entries:
                _check_stop()

                queue_entry_type = queue_plan_entry[0]
                if queue_entry_type == "wait":
                    _, queued_wait_seconds, queued_wait_label = queue_plan_entry

                    # Initialize the ODS timeline anchor from wall clock only when it has
                    # not been set yet. For wait entries, do NOT re-anchor to now_utc once
                    # the timeline is running — doing so would reset the planned start
                    # position and misalign reservations for all following targets.
                    if ods_schedule_next_start_utc is None:
                        now_utc = datetime.now(timezone.utc)
                        if QUEUE_WAIT and first_queue_pushed:
                            ods_schedule_next_start_utc = now_utc + timedelta(seconds=ods_lead_time_seconds)
                        else:
                            ods_schedule_next_start_utc = now_utc

                    # Advance the planned timeline by the wait duration only. No wall-clock drift correction here; that is handled per-target below.
                    ods_schedule_next_start_utc = ods_schedule_next_start_utc + timedelta(seconds=queued_wait_seconds)
                    _log_status(
                        f"ODS queue timeline advanced by {queued_wait_seconds}s for schedule wait row "
                        f"{queued_wait_label}. "
                        f"Next target slot starts no earlier than "
                        f"{ods_schedule_next_start_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC.")
                    continue

                # NOTE TODO: Check what this is for and document it.
                _, target_entry = queue_plan_entry
                (
                    queue_idx,
                    queued_target,
                    queued_target_id,
                    queued_target_key,
                    queue_ra_deg,
                    queue_dec,
                    queue_scan_seconds,
                ) = target_entry
                queued_target_label = _format_name_id_label(queued_target, queued_target_id)

                if queued_target_key in pushed_targets:
                    continue

                now_utc = datetime.now(timezone.utc)
                if ods_schedule_next_start_utc is None:
                    if QUEUE_WAIT and first_queue_pushed:
                        ods_schedule_next_start_utc = now_utc + timedelta(seconds=ods_lead_time_seconds)
                    else:
                        ods_schedule_next_start_utc = now_utc
                elif ods_schedule_next_start_utc < now_utc:
                    ods_schedule_next_start_utc = now_utc

                # Budget a conservative pre-observation interval:
                # long slew floor + ATA operations overhead + scan.
                slew_seconds = _resolve_planned_slew_seconds(
                    from_coords=ods_schedule_last_coords,
                    to_ra_deg=queue_ra_deg,
                    to_dec_deg=queue_dec,
                    reference_time_utc=ods_schedule_next_start_utc,)
                ata_ops_seconds = max(0, int(ODS_ATA_OPERATIONS_SECONDS))

                obs_start_utc = ods_schedule_next_start_utc + timedelta(seconds=slew_seconds + ata_ops_seconds)
                obs_end_utc = obs_start_utc + timedelta(seconds=queue_scan_seconds)

                # Reservation is intentionally wider than planned scan slot.
                res_start_utc = obs_start_utc - reservation_buffer
                res_end_utc = obs_end_utc + reservation_buffer

                push_succeeded = False
                _log_status(
                    f"{_format_ods_push_summary(res_start_utc, res_end_utc, queue_scan_seconds)} "
                    f"for {queued_target_label}")
                try:
                    push_ok = push_ods(
                        source=queued_target,
                        ra_deg=queue_ra_deg,
                        dec_deg=queue_dec,
                        res_start_utc=res_start_utc,
                        res_end_utc=res_end_utc,
                        frequencies_mhz=active_tuning_freqs,
                        project_name=PROJECT_NAME,
                        project_folder=PROJECT_FOLDER,)
                    if push_ok:
                        _log_status(f"Successfully pushed {queued_target_label} to ODS.")
                        push_succeeded = True
                    else:
                        _log_status(
                            f"Failed to push {queued_target_label} to ODS: push_ods returned False | "
                            f"ra_deg={float(queue_ra_deg):.6f}, dec_deg={float(queue_dec):.6f}, "
                            f"obs_seconds={int(queue_scan_seconds)}, "
                            f"reservation={_format_local_window_label(res_start_utc, res_end_utc)}")
                except Exception as e:
                    _log_status(
                        f"Failed to push {queued_target_label} to ODS: {e} | "
                        f"ra_deg={float(queue_ra_deg):.6f}, dec_deg={float(queue_dec):.6f}, "
                        f"obs_seconds={int(queue_scan_seconds)}, "
                        f"reservation={_format_local_window_label(res_start_utc, res_end_utc)}")

                if not push_succeeded:
                    # Keep this target eligible for a later retry if ODS push failed.
                    continue

                pushed_targets.add(queued_target_key)
                _log_status(f"Pushed {queued_target_label} to ODS queue")
                pushed_this_round += 1
                ods_schedule_next_start_utc = obs_end_utc
                ods_schedule_last_coords = (queue_ra_deg, queue_dec)
                ods_reservations_by_target[queued_target_key] = {
                    "target_name": str(queued_target),
                    "res_start_utc": res_start_utc,
                    "res_end_utc": res_end_utc,
                    "obs_start_utc": obs_start_utc,
                    "obs_end_utc": obs_end_utc,
                    "scan_seconds": queue_scan_seconds,
                    "slew_seconds": slew_seconds,
                    "ata_ops_seconds": ata_ops_seconds,
                    "ra_deg": float(queue_ra_deg),
                    "dec_deg": float(queue_dec),
                    "recovered": False,}

                # Operator-facing comparison line: planned slot vs reserved window.
                log_ods_reservation_vs_plan(
                    source_name=queued_target_label,
                    res_start_utc=res_start_utc,
                    res_end_utc=res_end_utc,
                    planned_obs_start_utc=obs_start_utc,
                    planned_obs_end_utc=obs_end_utc,
                    context="queue scheduling",
                    testing=TESTING,
                    logger=_log_status,)

            if pushed_this_round == 0 and targets_to_queue:
                _log_status("No new ODS pushes were needed from this queue check (all targets were already queued).")

            # Only wait once, immediately after the first successful queue push batch.
            if pushed_this_round > 0 and first_queue_pushed and QUEUE_WAIT == True:
                _check_stop()
                _log_status(f"Waiting {ods_lead_time_min} minutes for ODS to activate...")
                wait_with_stop(ods_lead_time_seconds, allow_stop=True)
                _check_stop()  # Process stop if triggered during ODS activation wait
                _log_status("ODS activation wait complete.")
                first_queue_pushed = False
            elif pushed_this_round > 0 and first_queue_pushed:
                first_queue_pushed = False

            if pushed_this_round > 0:
                log_urgent("Queue push complete.", color="#0072B2")
                _log_status("All queued targets pushed to ODS. Beginning actual observations")
        else:
            _log_status("ODS_PUSH is False; skipping ODS queue checks and pushes.")
            targets_to_queue = []

        if is_wait_marker_target:
            wait_seconds = max(1, int(effective_scan_seconds))  # already resolved above with override=True
            _log_status(
                f"Executing schedule wait for {source_label}: {wait_seconds} seconds."
            )
            log_urgent(f"Schedule wait in progress ({wait_seconds}s)", color="#E69F00")
            _check_stop()
            wait_with_stop(wait_seconds, allow_stop=True)
            _check_stop()
            _log_status(f"Schedule wait complete for {source_label}.")
            i += 1
            continue


        # Step 3: Perform the actual observation
        # Now that the queue has been pushed to ODS, we can do the actual observation with the step by step ephemerides
        # Make sure that the queue deals with the first queue_length targets from the current index within the greater for loop, but that the observation only takes place with the current index target


        # If solar system flag = 1, use Horizons name and generate_ephemeris_files function.
        # ------------------------------------------------------------------------------------------------------------------------------
        _check_stop()
        current_flag = parse_solar_system_flag(solsys_flag[i])
        if current_flag is None:
            print(
                f"Error: target {source} has unexpected Solar System Flag value '{solsys_flag[i]}'. "
                "Soft-skipping until next refresh.")
            _record_skipped_target(source, "data")
            i += 1
            continue

        if current_flag == 1:
            _check_stop()

            this_horizons_name = horizons_name[i]
            if horizons_available and str(this_horizons_name or "").strip():
                name_to_query = extract_horizons_id(this_horizons_name)
                print(
                    f"Querying instantaneous Horizons coordinates for target {source} "
                    f"(ID: {source_ids[i]}) with name {name_to_query}")

                ra_deg, dec, resolved_horizons_id = _get_instantaneous_solar_system_coordinates(
                    source,
                    this_horizons_name,
                    scan_start,)

                if (not is_valid_finite_float(ra_deg)) or (not is_valid_finite_float(dec)):
                    print(
                        f"Error: Could not retrieve instantaneous RA/DEC for {source} "
                        f"(ID: {source_ids[i]}, Horizons: {resolved_horizons_id}). "
                        "Soft-skipping until next refresh.")
                    _record_skipped_target(source, "data")
                    i += 1
                    continue
            else:
                # NOTE: revisit no-Horizons Solar-System strategy.
                name_to_query = source
                ra_deg, dec = _resolve_solar_system_coordinates_without_horizons(
                    source_name=str(source),
                    ra_solsys_value=ra_solsys_list[i],
                    dec_solsys_value=dec_solsys_list[i],
                    ra_hours_value=ra_hours_list[i],
                    ra_deg_value=ra_deg_list[i],
                    dec_value=dec_list[i],
                    context="observe solar fallback",)

                if (not is_valid_finite_float(ra_deg)) or (not is_valid_finite_float(dec)):
                    print(
                        f"No Horizons Name / fallback coordinates available for Solar System target {source}. "
                        "Soft-skipping until next refresh.")
                    _record_skipped_target(source, "data")
                    i += 1
                    continue
                _log_status(
                    f"Solar-system observe fallback active for {source}: using non-Horizons coordinates. "
                    "NOTE: revisit no-Horizons Solar-System strategy.")

            ra_deg = float(ra_deg)
            dec = float(dec)
            ra_hours = ra_deg / 15.0

            # Check that the source is at an appropriate elevation
            coord = SkyCoord(ra_deg * u.deg, dec * u.deg) # Needs RA in degrees
            altaz_coord = coord.transform_to(current_scan_altaz_frame)
            alt = altaz_coord.alt.value


        # ------------------------------------------------------------------------------------------------------------------------------
        if current_flag == 0:
            _check_stop()
            # If not a solar system target, use RA and DEC from CSV
            _log_status(f"Target {source} is not a Solar System target. Using RA and DEC from CSV.")
            ra_hours = ra_hours_list[i] # In hours
            ra_deg = ra_deg_list[i] # In degrees
            dec = dec_list[i]

            # Accept either RA(hours) or RA(deg) for sidereal rows and derive the missing value.
            if (not is_valid_finite_float(dec)):
                _log_status(
                    f"Error: invalid Sidereal row values for {source} "
                    f"(RA_hours={ra_hours}, RA_deg={ra_deg}, DEC={dec}). "
                    "Soft-skipping until next refresh.")
                _record_skipped_target(source, "data")
                i += 1
                continue

            resolved_sidereal_ra = _resolve_sidereal_ra_pair(
                ra_hours,
                ra_deg,
                source_name=str(source),
                context="observe",)
            if resolved_sidereal_ra is None:
                print(
                    f"Error: invalid Sidereal row values for {source} "
                    f"(RA_hours={ra_hours}, RA_deg={ra_deg}, DEC={dec}). "
                    "Soft-skipping until next refresh.")
                _record_skipped_target(source, "data")
                i += 1
                continue

            old_ra_hours_ok = is_valid_finite_float(ra_hours)
            old_ra_deg_ok = is_valid_finite_float(ra_deg)
            ra_hours, ra_deg = resolved_sidereal_ra
            if (not old_ra_deg_ok) and old_ra_hours_ok:
                _log_status(
                    f"Info: RA (deg) missing for {source}; derived RA_deg={ra_deg:.6f} from RA_hours={ra_hours:.6f}.")
            if (not old_ra_hours_ok) and old_ra_deg_ok:
                _log_status(
                    f"Info: RA (hours) missing for {source}; derived RA_hours={ra_hours:.6f} from RA_deg={ra_deg:.6f}.")

            ra_hours = float(ra_hours)
            ra_deg = float(ra_deg)
            dec = float(dec)


            # Check that the source is at an appropriate elevation
            coord = SkyCoord(ra_deg * u.deg, dec * u.deg) # Needs RA in degrees
            altaz_coord = coord.transform_to(current_scan_altaz_frame)
            alt = altaz_coord.alt.value


        _check_stop()
        if (not is_valid_finite_float(ra_deg)) or (not is_valid_finite_float(dec)):
            print(
                f"Error: invalid RA/DEC for {source} after preprocessing "
                f"(RA={ra_deg}, DEC={dec}). Soft-skipping until next refresh.")
            _record_skipped_target(source, "data")
            i += 1
            continue

        ra_deg = float(ra_deg)
        dec = float(dec)
        _log_status(f"Current Altitude: {alt} degrees")
        # Need to check this. Make sure it's pulling RA/DEC from only Solsys OR Sidereal, not both
        if ALT_MAX > alt > ALT_MIN: # NOTE TODO: Make this bound to variables
            _log_status(f"Altitude is within bounds, tracking source {source}")
        else:
            _log_status(f"{source} is not within elevation bounds ({alt} not between {ALT_MIN} and {ALT_MAX}), so is being skipped.")
            _record_skipped_target(source, "altitude")
            i += 1
            continue



        # Sun and Moon protection (conditionally applied)
        if SUN_AVOIDANCE:
            # Check Sun separation
            sun = resolve_body_position(
                "sun",
                scan_start=scan_start,
                obs_location=obs_location,
                testing=TESTING,
                ata_sources_module=(None if TESTING else ata_sources),
                logger=print,)
            if not isinstance(sun, dict) or 'ra' not in sun or 'dec' not in sun:
                print(
                    f"Error: could not determine Sun position for {source}. "
                    "Soft-skipping until next refresh.")
                _record_skipped_target(source, "sun")
                i += 1
                continue
            sun_ra = sun['ra']
            sun_dec = sun['dec']
            target_coord = SkyCoord(ra=ra_deg * u.deg, dec=dec * u.deg)
            sun_coord = SkyCoord(ra=sun_ra * u.deg, dec=sun_dec * u.deg)
            separation_from_sun = target_coord.separation(sun_coord).deg
            print(f"Current separation from Sun for target {source}: {separation_from_sun:.2f} degrees")

            if separation_from_sun < MIN_SUN_MOON_SEPARATION_DEGREES:
                print(
                    f"Target {source} is too close to the Sun "
                    f"({separation_from_sun:.2f} degrees < {MIN_SUN_MOON_SEPARATION_DEGREES}). Skipping.")
                _record_skipped_target(source, "sun")
                i += 1
                continue

        if MOON_AVOIDANCE:
            # Check Moon separation
            moon = resolve_body_position(
                "moon",
                scan_start=scan_start,
                obs_location=obs_location,
                testing=TESTING,
                ata_sources_module=(None if TESTING else ata_sources),
                logger=print,)
            if not isinstance(moon, dict) or 'ra' not in moon or 'dec' not in moon:
                print(
                    f"Error: could not determine Moon position for {source}. "
                    "Soft-skipping until next refresh.")
                _record_skipped_target(source, "moon")
                i += 1
                continue
            moon_ra = moon['ra']
            moon_dec = moon['dec']
            target_coord = SkyCoord(ra=ra_deg * u.deg, dec=dec * u.deg)
            moon_coord = SkyCoord(ra=moon_ra * u.deg, dec=moon_dec * u.deg)
            separation_from_moon = target_coord.separation(moon_coord).deg
            print(f"Current separation from Moon for target {source}: {separation_from_moon:.2f} degrees")

            if separation_from_moon < MIN_SUN_MOON_SEPARATION_DEGREES:
                print(
                    f"Target {source} is too close to the Moon "
                    f"({separation_from_moon:.2f} degrees < {MIN_SUN_MOON_SEPARATION_DEGREES}). Skipping.")
                _record_skipped_target(source, "moon")
                i += 1
                continue

        if PLANET_AVOIDANCE:
            # Check bright planets separation
            closest_planet = _closest_planet_violation(ra_deg, dec, scan_start)
            if closest_planet is not None:
                planet_name, separation_deg = closest_planet
                print(
                    f"Target {source} is too close to {planet_name} "
                    f"({separation_deg:.2f} degrees < {MIN_PLANET_SEPARATION_DEGREES}). Skipping.")
                _record_skipped_target(source, "planet")
                i += 1
                continue


        _check_stop()
        _log_status(f"Target {source} passed checks. About to begin observation.")
        log_urgent(f"Beginning Observation...", color = "#009E73")

        if ODS_PUSH:
            # Before observing current target, refresh any queued future targets
            # whose reservation windows have drifted near/past expiry.
            _refresh_drifting_future_ods_windows(
                current_source_key=source_identity_key,
                ods_reservations_by_target=ods_reservations_by_target,
                reservation_buffer=reservation_buffer,)

            # Compare current time against this target's reserved window.
            # If mismatched, attempt an immediate recovery repush.
            target_protected, target_protection_reason = _ensure_target_ods_protection(
                source_name=source,
                reservation_key=source_identity_key,
                ra_deg=ra_deg,
                dec_deg=dec,
                scan_seconds=effective_scan_seconds,
                reservation_buffer=reservation_buffer,
                ods_reservations_by_target=ods_reservations_by_target,)
            if not target_protected: # NOTE TODO: Set this as a variable up top so the user can decide
                _log_status(
                    f"ODS protection could not be confirmed for {source}; "
                    f"reason: {target_protection_reason}; continuing observation anyway per policy.")
                log_urgent(f"Observing {source} without confirmed ODS protection", color="#D55E00")

        if TESTING == False:
            _log_status("Beginning tracking function based on solar system flag.")
            log_urgent(f"Tracking target {source}...", color = "#009E73")

            if current_flag == 1:
                _log_status(
                    f"Target {source} passed checks as a Solar System target. Generating full ephemeris for tracking.")
                az, el, ra, dec_track, safe_t = generate_ephemeris_files(
                    target_to_process=name_to_query,
                    id_to_process=source_ids[i],
                    output_dir=output_dir3,
                    output_dir2=output_dir2,
                    scan_start=scan_start,
                    scan_end=scan_end,
                    time_step=time_step,
                    obs_location=obs_location,)
                if ra is None or dec_track is None or safe_t is None:
                    _log_status(
                        f"Error: full ephemeris generation failed for {source} ({name_to_query}). "
                        "Skipping tracking for this pass.")
                    _record_skipped_target(source, "data")
                    i += 1
                    continue

                _check_stop()
                # Track source
                _log_status("Target is within the solar system, tracking using Horizons Ephemeris.")
                _log_status(f"Tracking source {source}...")
                # Use the actual ephemerides output directory (absolute path) created in _initialize_runtime
                eph_filepath = os.path.join(output_dir3, f"JPLH_{safe_t}.ephem")
                eph_id = ata_control.upload_ephemeris(eph_filepath)
                for ant in ant_list[:-1]:
                    ata_control.track_ephemeris(eph_id, [ant], wait=False)
                ata_control.track_ephemeris(eph_id, [ant_list[-1]], wait=True)
            if current_flag == 0:
                _log_status("Target is Sidereal, tracking using given RA/DEC.")
                _log_status(f"Tracking source {source}...")
                ata_control.make_and_track_ra_dec(ra_hours, dec, ant_list) # Wants RA Hours

        if TESTING == True:
            _log_status("Testing mode active, skipping actual tracking function.")
            if current_flag == 1:
                _log_status("Target is within the solar system, would be tracking using Horizons Ephemeris.")
            if current_flag == 0:
                _log_status("Target is Sidereal, would be tracking using given RA/DEC.")

        _check_stop()
        if ODS_PUSH:
            # Runtime guard: immediately before scan/recording, verify remaining
            # observation will still be protected and recover if setup delays drifted.
            runtime_protected, runtime_protection_reason = _ensure_target_ods_protection(
                source_name=source,
                reservation_key=source_identity_key,
                ra_deg=ra_deg,
                dec_deg=dec,
                scan_seconds=effective_scan_seconds,
                reservation_buffer=reservation_buffer,
                ods_reservations_by_target=ods_reservations_by_target,
                pre_obs_seconds_override=0,)
            if not runtime_protected:
                _log_status(
                    f"Runtime ODS protection could not be confirmed for {source}; "
                    f"reason: {runtime_protection_reason}; proceeding per policy.")
                log_urgent(f"Runtime ODS protection unresolved for {source}", color="#D55E00")


        _check_stop()
        if RECORDING == True and TESTING == False and d and active_tuning_maps and len(active_tuning_freqs) > 0:
            _check_stop()

            # BEGIN HPGUPPI RECORDING
            # Off beams need RA in HOURS
            # Define off beams
            _log_status("Beginning ATA Recording functions...")
            dec1 = np.atleast_1d(np.array(dec, dtype=float) + np.array(separation, dtype=float))
            if len(dec1) < 4:
                _log_status("Insufficient beam-separation offsets for LoA/LoB/LoC/LoD. Skipping this target safely.")
                i += 1
                continue

            _check_stop()
            global _recording_active
            _recording_active = True # NOTE: Antenna Weighting

            if SEFD_WEIGHTING:
                _log_status("SEFD weighting is active for this observation.")
            else:
                _log_status("Uniform weighting is active for this observation.")

            keyval_dict_loa = {'RA_OFF0': ra_hours, 'DEC_OFF0': dec,
                    'RA_OFF1': ra_hours, 'DEC_OFF1': float(dec1[0])}
            keyval_dict_lob = {'RA_OFF0': ra_hours, 'DEC_OFF0': dec,
                    'RA_OFF1': ra_hours, 'DEC_OFF1': float(dec1[1])}
            keyval_dict_loc = {'RA_OFF0': ra_hours, 'DEC_OFF0': dec,
                    'RA_OFF1': ra_hours, 'DEC_OFF1': float(dec1[2])}
            keyval_dict_lod = {'RA_OFF0': ra_hours, 'DEC_OFF0': dec,
                    'RA_OFF1': ra_hours, 'DEC_OFF1': float(dec1[3])}

            if d_loa:
                hpguppi_auxillary.publish_keyval_dict_to_redis(
                        keyval_dict_loa, d_loa, postproc=False)
                _log_status(f"Published LoA keyvals to recorders: {sorted(d_loa.keys())}")
            if d_lob:
                hpguppi_auxillary.publish_keyval_dict_to_redis(
                        keyval_dict_lob, d_lob, postproc=False)
                _log_status(f"Published LoB keyvals to recorders: {sorted(d_lob.keys())}")
            if d_loc:
                hpguppi_auxillary.publish_keyval_dict_to_redis(
                        keyval_dict_loc, d_loc, postproc=False)
                _log_status(f"Published LoC keyvals to recorders: {sorted(d_loc.keys())}")
            if d_lod:
                hpguppi_auxillary.publish_keyval_dict_to_redis(
                        keyval_dict_lod, d_lod, postproc=False)
                _log_status(f"Published LoD keyvals to recorders: {sorted(d_lod.keys())}")


            if SEFD_WEIGHTING:
                if d_loa:
                    hpguppi_auxillary.publish_keyval_dict_to_redis(
                            {'CALWGHTP': "/opt/mnt/share/weights_a.bin"}, d_loa, postproc=False)
                    _log_status(f"Published LoA keyvals to recorders: {sorted(d_loa.keys())}")
                if d_lob:
                    hpguppi_auxillary.publish_keyval_dict_to_redis(
                            {'CALWGHTP': "/opt/mnt/share/weights_b.bin"}, d_lob, postproc=False)
                    _log_status(f"Published LoB keyvals to recorders: {sorted(d_lob.keys())}")
                if d_loc:
                    hpguppi_auxillary.publish_keyval_dict_to_redis(
                            {'CALWGHTP': "/opt/mnt/share/weights_c.bin"}, d_loc, postproc=False)
                    _log_status(f"Published LoC keyvals to recorders: {sorted(d_loc.keys())}")
                if d_lod:
                    hpguppi_auxillary.publish_keyval_dict_to_redis(
                            {'CALWGHTP': "/opt/mnt/share/weights_d.bin"}, d_lod, postproc=False)
                    _log_status(f"Published LoD keyvals to recorders: {sorted(d_lod.keys())}")
            _check_stop()

            wait_with_stop(20, allow_stop=True)

            obs_start_in = 10

            _log_status("REMOVED POST PROCESSING BLOCK, USE AT OWN RISK")
            _log_status("Sleeping for 60 seconds instead...")
            #hpguppi_record.block_until_post_processing_waiting(d)
            #print('Post proc is done for\n', d)
            _check_stop()
            wait_with_stop(60, allow_stop=True)

            # Begin new observation of target
            _check_stop()
            _log_status(f"\nStarting new observation of {source}")
            # log_urgent(f"Starting new observation of {source}...", color = "#009E73")
            hpguppi_record.record_in(obs_start_in, effective_scan_seconds + 5, hashpipe_targets = d) # NOTE: ATA recording function - Actual observation
            # Start recording -- record_in does NOT block
            _log_status("\n")
            if current_flag == 1:
                _log_status(
                    f"Source {source} is in the solar system. Currently at RA: "
                    f"{_format_ra_preferred_text(ra_hours, ra_deg)} and DEC: {dec} degrees.")
            if current_flag == 0:
                _log_status(
                    f"Source {source} is Sidereal with RA: "
                    f"{_format_ra_preferred_text(ra_hours, ra_deg)} and DEC: {dec} degrees.")

            _log_status(f"It is currently {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC or {_to_pacific(datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M:%S %Z')} local time.")
            _log_status(f"========================= Recording of {source} (index {i}) for {effective_scan_seconds} seconds started =========================")
            log_urgent(f"Observing {source}...", color = "#009E73")
            sleep_with_continuous_updates_seconds(effective_scan_seconds + obs_start_in + 10)

            _log_status(f"Observation of {source} (ID: {source_ids[i]}) completed")
            log_urgent(f"Scan of {source} completed.", color = "#0072B2")
            _record_observed_target(source, source_id)
            _log_observed_targets("Targets observed so far")
            wait_with_stop(5, allow_stop=True) # A little buffer to make sure it really stopped observing.


            _recording_active = False
            # I kept this separated just in case. Redundant, but doesn't really matter
            # Can rename later so we can observe and record, but not mark as observed.
            if MARKING == True and SORT_BY_OBSERVED:
                _log_status("Marking as observed")
                freqs = list(active_tuning_freqs)
                for freq in freqs:
                    mark_as_observed(OBSERVED_LIST, source_id, freq, source_name=source)
                    _log_status(f"{source_label} has been successfully marked as observed at {freq}MHz")
            elif MARKING == True and (not SORT_BY_OBSERVED):
                _log_status("Sort by observed list is OFF. Skipping file-based mark-as-observed; keeping internal-only observed tracking.")

            if TESTING == True:
                _log_status("Temporarilty removed marking as observed due to testing mode.")

            _log_status(
                f"\nIt is currently {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC "
                f"or {_to_pacific(datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M:%S %Z')} local time.")
            _log_status(f"Observation cycle complete for {source}. If you'd like to end this session, please do so now.")
            _log_status("============================================================\n")
            _check_stop()
            wait_with_stop(30, allow_stop=True)
            _check_stop()

        if RECORDING == True and TESTING == True:
            _log_status("Recording requested but Testing Mode is active. Skipping recorder actions safely.")
            _record_observed_target(source, source_id)
            _log_observed_targets("Targets observed so far")
            _check_stop()
            wait_with_stop(30, allow_stop=True)
            _check_stop()

        if RECORDING == True and TESTING == False and (not d or not active_tuning_maps or len(active_tuning_freqs) == 0):
            _log_status("Recording requested but no active recorder nodes/tunings are selected. Skipping recording for this target safely.")
            _record_observed_target(source, source_id)
            _log_observed_targets("Targets observed so far")
            _check_stop()
            wait_with_stop(30, allow_stop=True)
            _check_stop()

        if RECORDING == False:
            _log_status("Recording disabled. This will not record and will not mark as observed.")
            _log_status("This is where observation would have taken place.")
            no_record_wait_seconds = 30 if TESTING else effective_scan_seconds
            _log_status(f"Waiting {no_record_wait_seconds}s to simulate this observation's duration.")
            wait_with_stop(no_record_wait_seconds, allow_stop=True)
            _check_stop()
            _log_status(f"\nObservation cycle is complete for {source}. If you'd like to end this session, please do so now.")
            _log_status("============================================================\n")
            _record_observed_target(source, source_id)
            _log_observed_targets("Targets observed so far")
            _check_stop()


        if TESTING:
            _log_status(
                f"Completed scan timing for {source}: nominal(non-testing) {nominal_scan_seconds}s, "
                f"actual(TESTING) {effective_scan_seconds}s.")
        else:
            _log_status(f"Completed scan timing for {source}: {effective_scan_seconds}s.")

        if ODS_PUSH and source_identity_key in ods_reservations_by_target:
            ods_reservations_by_target.pop(source_identity_key, None)

        i += 1


if __name__ == "__main__":
    _main_thread_wrapper()

