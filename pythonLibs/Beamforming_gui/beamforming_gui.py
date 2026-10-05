"""Beamforming Survey GUI.

This module provides a CustomTkinter-based interface for configuring and running
survey observations, selecting antennas, loading status from Notion, and
managing runtime controls such as stop/resume/abort and scheduled auto-stop for the ATA.
"""

#  ==========================================================================================================================================================

# These are defaults to automatically load into the GUI
PROJECT_NAME = 'testingtime' # Project Folder
OBSERVE_MODULE_NAME = 'observe_survey' # Python module name (without .py) used by the GUI to run observations.
OBS_TIME = 300 # Length of time spent on each target in seconds. Default is 300 sec (5 mins)
CSV_NAME = 'demo_targets.csv' # List of targets
OBSERVED_LIST = 'demo_survey.csv' # List of targets with columns marking if it has been observed yet.
#REMOVE_ANT = ['1c', '2c']
REMOVE_ANT = ['']
QUEUE_WAIT = True # Wait for ODS to activate before beginning observation
ODS_PUSH = True # Push reservation requests to ODS
REORDER_INTERVAL_SECONDS = 600 # 3600 # 1 hour # Reorder targets by Local Sidereal Time every N seconds.
REARRANGE_BY_LST = True # If True, rearranges targets by LST
RECORDING = False # If True, it will record data with the ATA
TESTING = True # Used when on a local machine. If True, it won't use ATA specific functions
MARKING = False # Whether or not the script will mark as observed.
SORT_BY_OBSERVED = True # If False, bypass observed-list sorting/filtering and use internal tracking only.
USE_TARGET_OBS_TIME_OVERRIDE = False # If True, uses per-target "Obs Time" values from CSV when present.
README_FILE_NAME = "Beamforming_GUI_README.txt" # The location of the README text


MAIN_WINDOW_IMAGE_PATH = "totality.ico"
README_WINDOW_IMAGE_PATH = "totality.ico"
# Optional path for icons. Doesn't seem to work on VNC. Accepts .ico or .png

README_TEXT = """Welcome to the Beamforming Survey GUI!

This Graphical User Interface is designed to make observations more accessible and user friendly.
If there are any issues, bugs, or comments for improvement, please reach out to Blayne Griffin.

Later in the script, this is supposed to call forth a .txt file for the README.
If you're reading this, please contact Blayne Griffin at bgriffin@seti.org so this can be fixed.

""" # This is redefined later to pull from the .txt file.

NOTION_PULL = True # Determines if the GUI will pull antennas from Notion or use the full list

GUI_BOX_SIZES = {
    "config": (460, 500),
    # "config": (460, 445),
    "options": (300, 220),
    "antennas": (270, 450),
    "console": (300, 245),
    "run_confirmation": (700, 390),
} # In pixels. Width then height.

GUI_WINDOW_SIZE = (1000, 530)  # Overall GUI window size in pixels. Width then height.

GUI_INPUT_SIZES = {
    "text_entry": 280,
    "browse_button": 80,
    "obs_time_entry": 120,
} # Default sizes for entry sections

GUI_BUTTON_SIZES = {
    "antennas_panel": 150,
    "recorders_panel": 150,
    "refresh_antennas": 170,
    "run": 90,
    "stop": 150,
    "resume": 90,
    "abort": 90,
    "readme": 100,
} # Default button sizes

GUI_POPUP_SIZES = {
    "antennas": (420, 520),
    "recorders": (700, 400),
    "readme": (640, 420),
} # Popup sizes

GUI_LAYOUT = {
    "antenna_columns": 4,
    "antenna_column_minsize": 66,
    "antenna_status_wraplength": 290,
} # Layout settings

APP_FONT_FAMILY = "DejaVu Sans" # This font is in both Windows and Ubuntu, which is why it was chosen

# Fonts used throughout the CustomTkinter UI (family, size, optional weight)
TITLE_FONT = (APP_FONT_FAMILY, 14, "bold")
NORMAL_FONT = (APP_FONT_FAMILY, 12)
SMALL_FONT = (APP_FONT_FAMILY, 10)
# NOTE: The fonts are still weird on Ubuntu, check to make sure that everything is legible while on VNC

BUTTON_CORNER_RADIUS = 0
BUTTON_FONT = (APP_FONT_FAMILY, 11)
CHECKBOX_CORNER_RADIUS = 0
# I tried making rounded buttons, but Ubuntu didn't like that.
# But if that's ever fixed, we can change these settings to bring it back.

TITLE_TEXT_COLOR = "#FFFFFF"
NORMAL_TEXT_COLOR = "#FFFFFF"
SMALL_TEXT_COLOR = "#FFFFFF"
ALERT_TEXT_COLOR = "#D50000"
# Default colors for text

UI_BG_COLOR = "#1F1F1F"
UI_PANEL_COLOR = "#2A2A2A"
UI_PANEL_ALT_COLOR = "#262626"
UI_BORDER_COLOR = "#3A3A3A"
UI_ENTRY_COLOR = "#303030"
UI_MUTED_TEXT_COLOR = "#B8B8B8"
# Default GUI colors

# Notion observing-status strings used to classify and style antennas.
# Edit these values if Notion wording changes.
# X is purple, Y is orange
STATUS_CLEAR_TO_USE = "clear to use"
STATUS_XPOL_HARDWARE_ISSUE = "x-pol hardware issue"
STATUS_YPOL_HARDWARE_ISSUE = "y-pol hardware issue"
STATUS_REMOVE_FROM_ALL_SCRIPTS = "remove from all scripts"
STATUS_REMOVE_FROM_CALIBRATION_PROCEDURE = "remove from calibration procedure"
STATUS_KEEP_AN_EYE = "keep an eye"
STATUS_NOT_APPLICABLE = "n/a"

STATUS_COLOR_BY_VALUE = {
    STATUS_CLEAR_TO_USE: "#009E73",
    STATUS_XPOL_HARDWARE_ISSUE: "#CC79A7",
    STATUS_YPOL_HARDWARE_ISSUE: "#F0E442",
    STATUS_REMOVE_FROM_ALL_SCRIPTS: "#D50000",
    STATUS_REMOVE_FROM_CALIBRATION_PROCEDURE: "#CC79A7",
    STATUS_KEEP_AN_EYE: "#F0E442",
    STATUS_NOT_APPLICABLE: UI_MUTED_TEXT_COLOR,
}

STATUS_LEGEND_ITEMS = [
    (STATUS_REMOVE_FROM_ALL_SCRIPTS, "Remove from all scripts"),
    (STATUS_XPOL_HARDWARE_ISSUE, "X-pol Hardware Issue"),
    (STATUS_YPOL_HARDWARE_ISSUE, "Y-pol Hardware Issue"),
    # (STATUS_REMOVE_FROM_CALIBRATION_PROCEDURE, "Remove from Calibration (legacy: affects X and Y)"),
    # (STATUS_KEEP_AN_EYE, "Keep an Eye (legacy alias for Y-pol)"),
    (STATUS_CLEAR_TO_USE, "Clear to Use"),
    (STATUS_NOT_APPLICABLE, "N/A"),
]

# List all antennas in the active array. These correspond to the checkboxes.
# If the Notion pull fails, it falls back to ALL antennas
# NOTE: REMOVE THIS, HAVE IT JUST FALL BACK TO SNAPobs
DEFAULT_ANTENNAS = ['1a', '1b', '1c', '1d', '1e', '1f', '1g', '1h', '1j', '1k',
                    '2a', '2b', '2c', '2d', '2e', '2f', '2g', '2h', '2j', '2k', '2l', '2m',
                    '3c', '3d', '3e', '3f', '3g', '3h', '3j', '3l',
                    '4e', '4f', '4g', '4h', '4j', '4k', '4l',
                    '5b', '5c', '5e', '5g', '5h']
# It will first try to pull from Notion. If that fails it will pull from SNAPobs as it has before.
# If that somehow fails, it will fall back to listing ALL antennas.
# Actual non-testing observations will break if SNAP fails.

DEFAULT_RECORDERS = {
    f"seti-node{i}": [0, 1] for i in range(1, 15)
}

# Recorder source policy (intended behavior):
# 1) On GUI startup and Recorder Panel refresh, always attempt ATA/SNAPobs import first.
# 2) If ATA validation succeeds, populate recorder selections from the standard
#    calibration-style map (seti-node1..14 with streams [0,1]) to keep a stable
#    28-stream layout in four columns (LoA..LoD).
# 3) If ATA import/validation fails, fall back to mock test-node1..14 streams [0,1]
#    so local/offline runs can still open and use the Recorder Panel.
#
# Recorder panel controls:
# - Select All: checks all currently displayed recorder streams.
# - Refresh: re-runs ATA-first load logic and redraws the panel with updated source data.

RECORDER_TUNING_LABELS = ["LoA", "LoB", "LoC", "LoD"]

# Stream-level mapping used by both GUI display and active-tuning filtering.
DEFAULT_TUNING_RECORDER_MAPS = [
    {'seti-node1': [0,1], 'seti-node2': [0,1], 'seti-node3': [0,1], 'seti-node4': [0]},
    {'seti-node4': [1], 'seti-node5': [0,1], 'seti-node6': [0,1], 'seti-node7': [0,1]},
    {'seti-node8': [0,1], 'seti-node9': [0,1], 'seti-node10': [0,1], 'seti-node11': [0]},
    {'seti-node11': [1], 'seti-node12': [0,1], 'seti-node13': [0,1], 'seti-node14': [0,1]},
]

if TESTING == False:
    # Keep startup import side effects minimal; SNAPobs is loaded on-demand
    # in antenna fallback logic so failures can be surfaced cleanly in the GUI.
    pass

# All antennas:
# ['1a', '1b', '1c', '1d', '1e', '1f', '1g', '1h', '1j', '1k',
# '2a', '2b', '2c', '2d', '2e', '2f', '2g', '2h', '2j', '2k', '2l', '2m',
# '3c', '3d', '3e', '3f', '3g', '3h', '3j', '3l',
# '4e', '4f', '4g', '4h', '4j', '4k', '4l',
# '5b', '5c', '5e', '5g', '5h', 'antenna 43']


# ============================================================================================================================================================================================

import os

NOTION_TOKEN = os.environ.get("NOTION_TOKEN") # Talk to Sofia if this messes up
NOTION_DISH_STATUS_ID = os.environ.get("NOTION_DISH_STATUS_ID") # This links to the Dish Status Page in Notion
# Tokens for pulling ATA dish status from Notion
# Used in beamforming and correlation GUI scripts

# DON'T EDIT THESE!
# This defines where the Notion section pulls from, and its associated access token.

# Begin section to pull from Notion
NOTION_SORTS = [{"property": "Antenna", "direction": "ascending"}]
# Property = Antenna means that this is the column being looked at

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


# White = "#FFFFFF"
# Black = "#000000"

COLORBLIND_FRIENDLY_PALETTE = [
    "#0072B2",  # Blue
    "#E69F00",  # Orange
    "#009E73",  # Green
    "#D55E00",  # Vermillion
    "#D50000",  # Red
    "#CC79A7",  # Reddish purple
    "#F0E442",  # Yellow
    "#56B4E9",  # Sky blue
    "#000000",  # Black
    "#999999",  # Gray
    "#332288",  # Indigo
    "#88CCEE",  # Light blue
    "#44AA99",  # Teal
    "#117733",  # Dark green
    "#DDCC77",  # Sand
    "#CC6677",  # Rose
    "#882255",  # Plum
]
# print(COLORBLIND_FRIENDLY_PALETTE)
# This was just for me as I was making the script. I tried to make the colors colorblind friendly.

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import customtkinter as ctk
import os
import importlib
import requests
import re
import sys
import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from utils_beamforming import resolve_path_from_script
from utils_beamforming import parse_title_text
from utils_beamforming import parse_active_value
from utils_beamforming import parse_observing_status
from utils_beamforming import get_notion_property
from utils_beamforming import normalize_hashpipe_targets
from utils_beamforming import make_ods_project_tag

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
# Consider adding a Light/Dark mode toggle. Not required though


def _strip_wrapping_quotes(text: str) -> str:
    '''STRIP WRAPPING QUOTES: Remove common wrapping quotes from a string, if present.'''
    # Currently used to load the README without any wrapping quotes.
    stripped = text.strip()
    wrappers = (
        ('"""', '"""'),
        ("'''", "'''"),
        ('"', '"'),
        ("'", "'"),
    )
    for left, right in wrappers:
        if stripped.startswith(left) and stripped.endswith(right) and len(stripped) >= len(left) + len(right):
            return stripped[len(left):-len(right)].strip()
    return text


def _normalize_observing_status(value: str) -> str:
    """Return canonical observing status text for robust, case-insensitive matching."""
    raw = str(value or "").strip().lower()
    normalized = re.sub(r"\s+", " ", raw)
    aliases = {
        "xpol hardware issue": STATUS_XPOL_HARDWARE_ISSUE,
        "x pol hardware issue": STATUS_XPOL_HARDWARE_ISSUE,
        STATUS_XPOL_HARDWARE_ISSUE: STATUS_XPOL_HARDWARE_ISSUE,
        "ypol hardware issue": STATUS_YPOL_HARDWARE_ISSUE,
        "y pol hardware issue": STATUS_YPOL_HARDWARE_ISSUE,
        STATUS_YPOL_HARDWARE_ISSUE: STATUS_YPOL_HARDWARE_ISSUE,
        STATUS_KEEP_AN_EYE: STATUS_YPOL_HARDWARE_ISSUE,
        STATUS_REMOVE_FROM_ALL_SCRIPTS: STATUS_REMOVE_FROM_ALL_SCRIPTS,
        STATUS_REMOVE_FROM_CALIBRATION_PROCEDURE: STATUS_REMOVE_FROM_CALIBRATION_PROCEDURE,
        STATUS_CLEAR_TO_USE: STATUS_CLEAR_TO_USE,
        STATUS_NOT_APPLICABLE: STATUS_NOT_APPLICABLE,
        "na": STATUS_NOT_APPLICABLE,
        "n a": STATUS_NOT_APPLICABLE,
    }
    return aliases.get(normalized, normalized)


def _collect_pol_hardware_issues(observing_status_by_antenna: dict) -> dict:
    """Collect X/Y polarization hardware issue groups from canonical status values."""
    x_pol_issues = []
    y_pol_issues = []

    for antenna in DEFAULT_ANTENNAS:
        status_text = _normalize_observing_status((observing_status_by_antenna or {}).get(antenna, ""))
        if status_text == STATUS_XPOL_HARDWARE_ISSUE:
            x_pol_issues.append(antenna)
        elif status_text == STATUS_YPOL_HARDWARE_ISSUE:
            y_pol_issues.append(antenna)
        elif status_text == STATUS_REMOVE_FROM_CALIBRATION_PROCEDURE:
            # Backward compatibility with legacy single-status calibration removal.
            x_pol_issues.append(antenna)
            y_pol_issues.append(antenna)

    return {
        "x_pol_issues": x_pol_issues,
        "y_pol_issues": y_pol_issues,
    }


def _load_readme_text(default_text: str) -> str:
    '''LOAD README: Load README text from disk. If unavailable, keep the in-script fallback.'''
    readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), README_FILE_NAME)
    try:
        with open(readme_path, "r", encoding="utf-8") as readme_file:
            file_text = readme_file.read()
    except OSError:
        return default_text

    if not file_text.strip():
        return default_text

    return _strip_wrapping_quotes(file_text)


def _apply_window_image(window, image_path: str) -> bool:
    '''APPLY WINDOW IMAGE: Apply icon/image to a Tk window. Returns True on success, False on failure.
    This is meant to give the window a little icon, but Ubuntu doesn't seem to like it.'''
    resolved = resolve_path_from_script(image_path, script_file=__file__, must_exist=False)
    if not resolved:
        return False
    if not os.path.exists(resolved):
        return False

    try:
        ext = os.path.splitext(resolved)[1].lower()
        if ext == ".ico":
            window.iconbitmap(resolved)
            return True

        image = tk.PhotoImage(file=resolved)
        window.iconphoto(True, image)
        window._window_icon_image = image
        return True
    except Exception:
        return False


def _insert_inline_markup(tk_text, text: str):
    '''INSERT INLINE MARKUP: Render simple inline markup for the README: **bold** and __underline__.'''
    parts = re.split(r"(\*\*[^*]+\*\*|__[^_]+__)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            tk_text.insert("end", part[2:-2], ("readme_bold",))
        elif part.startswith("__") and part.endswith("__") and len(part) >= 4:
            tk_text.insert("end", part[2:-2], ("readme_underline",))
        else:
            tk_text.insert("end", part)


def _render_readme_markup(readme_textbox, content: str):
    '''RENDER README MARKUP: Render README markdown-like content into a CTk textbox with tags.'''
    tk_text = readme_textbox._textbox
    tk_text.configure(state="normal")
    tk_text.delete("1.0", "end")

    tk_text.tag_configure("readme_h1", font=("Arial", 16, "bold"), spacing1=8, spacing3=6)
    tk_text.tag_configure("readme_h2", font=("Arial", 13, "bold"), spacing1=6, spacing3=4)
    tk_text.tag_configure("readme_bold", font=("Arial", 12, "bold"))
    tk_text.tag_configure("readme_underline", underline=1)
    tk_text.tag_configure("readme_bullet", lmargin1=10, lmargin2=28)

    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("# "):
            tk_text.insert("end", stripped[2:] + "\n", ("readme_h1",))
            continue
        if stripped.startswith("## "):
            tk_text.insert("end", stripped[3:] + "\n", ("readme_h2",))
            continue
        if stripped.startswith(("- ", "* ")):
            tk_text.insert("end", "• ", ("readme_bullet",))
            _insert_inline_markup(tk_text, stripped[2:])
            tk_text.insert("end", "\n", ("readme_bullet",))
            continue

        _insert_inline_markup(tk_text, line)
        tk_text.insert("end", "\n")

    tk_text.configure(state="disabled")

# This is a default if pulling from README.txt fails.
README_TEXT = _load_readme_text(README_TEXT)





class AntennaSourceError(RuntimeError):
    """Raised when Notion antenna loading fails and SNAPobs fallback is unavailable."""


def _show_startup_antenna_warning(message: str):
    """Show a blocking startup warning dialog for fatal antenna source failures."""
    text = str(message or "Unknown antenna source error").strip()
    if not text:
        text = "Unknown antenna source error"

    try:
        popup_root = tk.Tk()
        popup_root.withdraw()
        messagebox.showerror(
            "Antenna Source Error",
            (
                "Failed to load antennas from SNAPobs after Notion failed.\n\n"
                f"{text}\n\n"
                "Observations are blocked until this is fixed."
            ),
        )
        popup_root.destroy()
    except Exception:
        # Best-effort warning only.
        pass


def _get_snap_active_antennas_or_raise(reason_context: str):
    """Load active antennas from SNAPobs or raise a fatal source error."""
    context = str(reason_context or "Notion fallback required").strip()
    try:
        from SNAPobs import snap_config
    except Exception as exc:
        raise AntennaSourceError(
            f"{context}. Could not import SNAPobs.snap_config ({exc})."
        ) from exc

    try:
        snap_list = snap_config.get_rfsoc_active_antlist()
    except Exception as exc:
        raise AntennaSourceError(
            f"{context}. SNAPobs get_rfsoc_active_antlist failed ({exc})."
        ) from exc

    normalized = [str(ant).strip().lower() for ant in (snap_list or []) if str(ant).strip()]
    if not normalized:
        raise AntennaSourceError(
            f"{context}. SNAPobs get_rfsoc_active_antlist returned no active antennas."
        )

    active_from_snap = [ant for ant in DEFAULT_ANTENNAS if ant in normalized]
    if not active_from_snap:
        active_from_snap = normalized
    return active_from_snap

# NOTION PULL:
def get_notion_data():
    """Query Notion and return active/observing antenna lists and status mapping."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DISH_STATUS_ID}/query"
    antenna_state = {}

    payload = {
        "sorts": NOTION_SORTS,
        "page_size": 100,
    }

    while True:
        response = requests.post(url, headers=NOTION_HEADERS, json=payload, timeout=15)
        response.raise_for_status()

        data = response.json()
        for page in data.get("results", []):
            properties = page.get("properties", {})
            antenna_prop = get_notion_property(properties, "Antenna", "Dish", "Ant")
            active_prop = get_notion_property(properties, "Active Array?", "Active Array", "Active")
            status_prop = get_notion_property(properties, "Observing Status", "Status", "Observing")

            antenna = parse_title_text(antenna_prop)
            active_array = parse_active_value(active_prop)
            observing_status = parse_observing_status(status_prop)

            observing_allowed = active_array

            antenna_key = antenna.strip().lower()
            if antenna_key:
                antenna_state[antenna_key] = {
                    "active": bool(active_array),
                    "clear_to_use": observing_allowed,
                    "observing_status": observing_status,
                }

        if not data.get("has_more"):
            break

        payload["start_cursor"] = data.get("next_cursor")

    active_array = [antenna for antenna in DEFAULT_ANTENNAS if antenna_state.get(antenna, {}).get("active")]
    observing_array = [antenna for antenna in DEFAULT_ANTENNAS if antenna_state.get(antenna, {}).get("clear_to_use")]
    observing_status_by_antenna = {
        antenna: antenna_state.get(antenna, {}).get("observing_status", "")
        for antenna in DEFAULT_ANTENNAS
    }
    return active_array, observing_array, observing_status_by_antenna


def load_antennas_from_notion_or_fallback():
    """Load antenna state from Notion, or return safe fallback antenna data."""
    if not NOTION_PULL:
        return (
            DEFAULT_ANTENNAS.copy(),
            DEFAULT_ANTENNAS.copy(),
            {antenna: STATUS_CLEAR_TO_USE for antenna in DEFAULT_ANTENNAS},
            "Antenna source: Fallback default (NOTION_PULL=False)"
        )

    notion_issue = None
    try:
        active_array, observing_array, observing_status_by_antenna = get_notion_data()
        if active_array:
            return (
                active_array,
                observing_array,
                observing_status_by_antenna,
                f"Notion Antenna Pull: Active_Array ({len(active_array)} loaded) | Observing_Array ({len(observing_array)} loaded)"
            )
        notion_issue = "Notion Active_Array empty"
    except Exception as exc:
        notion_issue = f"Notion error: {exc}"

    if not TESTING:
        active_from_snap = _get_snap_active_antennas_or_raise(notion_issue)
        return (
            active_from_snap,
            active_from_snap.copy(),
            {antenna: STATUS_CLEAR_TO_USE for antenna in active_from_snap},
            f"Antenna source: SNAPobs active list ({len(active_from_snap)} loaded) - {notion_issue}"
        )

    return (
        DEFAULT_ANTENNAS.copy(),
        DEFAULT_ANTENNAS.copy(),
        {antenna: STATUS_CLEAR_TO_USE for antenna in DEFAULT_ANTENNAS},
        f"Antenna source: Fallback default ({notion_issue})"
    )

ANTENNA_LOAD_FATAL_MESSAGE = ""
try:
    ANTENNAS, Observing_Array, OBSERVING_STATUS_BY_ANTENNA, ANTENNA_SOURCE_STATUS = load_antennas_from_notion_or_fallback()
except AntennaSourceError as exc:
    ANTENNAS = DEFAULT_ANTENNAS.copy()
    Observing_Array = DEFAULT_ANTENNAS.copy() #NOTE: This is something I need to clean up.
    OBSERVING_STATUS_BY_ANTENNA = {antenna: STATUS_CLEAR_TO_USE for antenna in DEFAULT_ANTENNAS}
    ANTENNA_SOURCE_STATUS = f"Antenna source: BLOCKED - FATAL ({exc})"
    ANTENNA_LOAD_FATAL_MESSAGE = str(exc)
    print(f"FATAL ANTENNA SOURCE ERROR: {ANTENNA_LOAD_FATAL_MESSAGE}")
    _show_startup_antenna_warning(ANTENNA_LOAD_FATAL_MESSAGE)

print(f"Antenna Source Status: {ANTENNA_SOURCE_STATUS}")
# Consider pulling from the antenna status (on control.hcro.org) window currently in Workspace 1


# Define the GUI window itself                                             ===================================
class SurveyConfigGUI(ctk.CTk):
    """Main survey configuration window and observation control surface."""

    def __init__(self):
        """Initialize window state, runtime flags, and all GUI widgets."""
        super().__init__()
        # Enforce consistent font metrics and scaling on program start so the GUI looks the same for Windows and Ubuntu
        try:
            # Set Tk scaling to a neutral value (affects font/widget scaling).
            try:
                self.tk.call("tk", "scaling", 1.0)
            except Exception:
                pass

            import tkinter.font as tkfont
            try:
                f = tkfont.nametofont("TkDefaultFont")
                f.configure(family=APP_FONT_FAMILY, size=12)
            except Exception:
                pass
            try:
                f = tkfont.nametofont("TkTextFont")
                f.configure(family=APP_FONT_FAMILY, size=12)
            except Exception:
                pass
            try:
                f = tkfont.nametofont("TkMenuFont")
                f.configure(family=APP_FONT_FAMILY, size=12)
            except Exception:
                pass
            try:
                f = tkfont.nametofont("TkHeadingFont")
                f.configure(family=APP_FONT_FAMILY, size=14, weight="bold")
            except Exception:
                pass
        except Exception:
            # Best-effort only; failure should not stop GUI.
            pass
        self._install_error_handlers()
        self.title("Beamforming Survey Graphical User Interface")
        self.protocol("WM_DELETE_WINDOW", self._on_close_gui)
        self.geometry(f"{GUI_WINDOW_SIZE[0]}x{GUI_WINDOW_SIZE[1]}") # First number is width, second is height.
        self.configure(fg_color=UI_BG_COLOR)
        # Apply icon from top-level config. Re-apply shortly after startup because CustomTkinter can set its own default icon during initialization.
        _apply_window_image(self, MAIN_WINDOW_IMAGE_PATH)
        self.after(200, lambda: _apply_window_image(self, MAIN_WINDOW_IMAGE_PATH))
        # Show the full antenna list in the GUI, then gray out unavailable antennas.
        self.current_antennas = list(DEFAULT_ANTENNAS)
        self.active_antennas = set(ANTENNAS)
        self.observing_antennas = set(Observing_Array)
        self.observing_status_by_antenna = dict(OBSERVING_STATUS_BY_ANTENNA)
        self._antenna_load_blocked = bool(ANTENNA_LOAD_FATAL_MESSAGE)
        self._worker_thread = None
        self._is_running = False
        self._run_state_poll_id = None
        self._lockable_widgets = []
        self._antenna_checkbox_widgets = []
        self._recorder_checkbox_widgets = []
        self._observe_module = None
        self._observe_module_name = None
        self._advanced_options_panel = None
        self._queue_wait_adv_chk = None
        self._target_obs_time_override_chk = None
        self.recorder_vars = {}
        self._recorder_source_status = ""
        self._recorder_targets = {}
        self._recorder_tuning_columns = {label: [] for label in RECORDER_TUNING_LABELS}
        self._load_recorders_from_ata_or_fallback(preserve_selection=False, announce=False)
        self.start_after_value = tk.StringVar(value="")
        self.stop_after_value = tk.StringVar(value="")
        self.stop_at_hour_value = tk.StringVar(value="12")
        self.stop_at_minute_value = tk.StringVar(value="00")
        self.stop_at_second_value = tk.StringVar(value="00")
        self.stop_at_timezone_value = tk.StringVar(value="PST")
        self._is_start_scheduled = False
        self._scheduled_start_after_id = None
        self._scheduled_start_target_time = None
        self._scheduled_start_brief = ""
        self._scheduled_start_description = ""
        self._scheduled_start_run_configuration = None
        self._scheduled_start_remove_ant_list = []
        self._pending_start_after_duration = None
        self._pending_start_after_brief = ""
        self._scheduled_stop_after_id = None
        self._scheduled_stop_description = ""
        self._scheduled_stop_brief = ""
        self._scheduled_stop_type = None  # Tracks which schedule is active: "after", "at", or None
        self._scheduled_stop_target_time = None  # Target datetime when stop will execute
        self._pending_stop_after_duration = None  # Duration in seconds for "Stop After" (set but not running yet)
        self._pending_stop_after_brief = None  # Brief description of pending stop after
        self._pending_stop_at_hour = None  # Hour for pending "Stop At" (set but not running yet)
        self._pending_stop_at_minute = None  # Minute for pending "Stop At" (set but not running yet)
        self._pending_stop_at_second = None  # Second for pending "Stop At" (set but not running yet)
        self._pending_stop_at_timezone = None  # Timezone for pending "Stop At" (set but not running yet)
        self._pending_stop_at_brief = None  # Brief description of pending stop at
        self._schedule_stop_after_btn = None
        self._schedule_stop_at_btn = None
        self._clear_scheduled_stop_btn = None
        self._advanced_schedule_status_label = None
        self._confirmation_panel = None
        self._run_confirmation_panel = None
        self._start_after_entry = None
        self._schedule_start_after_btn = None
        self._clear_scheduled_start_btn = None
        self._stop_after_entry = None
        self._stop_at_hour_menu = None
        self._stop_at_minute_menu = None
        self._stop_at_second_menu = None
        self._stop_at_timezone_entry = None
        self.ods_push = tk.BooleanVar(value=ODS_PUSH)
        self._ods_push_btn = None
        self.use_target_obs_time_override = tk.BooleanVar(value=USE_TARGET_OBS_TIME_OVERRIDE)
        self.scheduled_stop_display = tk.StringVar(value="")
        self._scheduled_stop_label = None
        self.scheduled_start_display = tk.StringVar(value="")
        self._scheduled_start_label = None
        self.advanced_start_status = tk.StringVar(value="No start delay configured.")
        self.advanced_schedule_status = tk.StringVar(value="No stop scheduled.")
        self._build_ui()
        if self._antenna_load_blocked:
            warning = (
                "Cannot run observations: SNAPobs active-antenna fallback failed. "
                f"{ANTENNA_LOAD_FATAL_MESSAGE}"
            )
            self._set_urgent_status("Antenna loading failed - run blocked", color=ALERT_TEXT_COLOR)
            self._update_status(f"ERROR: {warning}")
            try:
                self.run_btn.configure(state="disabled")
            except Exception:
                pass
        # Hook into configured observe module to receive status updates for terminal output.
        self._load_observe_module(raise_on_error=False)

    def _install_error_handlers(self):
        """Install global exception hooks so runtime issues surface in the GUI."""
        self._previous_sys_excepthook = sys.excepthook
        self._previous_threading_excepthook = getattr(threading, "excepthook", None)

        def _sys_excepthook(exc_type, exc_value, exc_traceback):
            if exc_type is KeyboardInterrupt:
                if callable(self._previous_sys_excepthook):
                    self._previous_sys_excepthook(exc_type, exc_value, exc_traceback)
                return
            self._report_error("Unhandled exception", exc_type, exc_value, exc_traceback)

        def _threading_excepthook(args):
            self._report_error(
                f"Unhandled exception in thread '{args.thread.name}'",
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
            )

        sys.excepthook = _sys_excepthook
        if hasattr(threading, "excepthook"):
            threading.excepthook = _threading_excepthook

    def report_callback_exception(self, exc, val, tb):
        """Override Tk callback exception handling to route errors to the GUI reporter."""
        self._report_error("GUI callback error", exc, val, tb)

    def _build_gui_error_summary(self, context_message: str, exc_value=None) -> str:
        """Build a concise, user-facing summary string for GUI error messages."""
        base = str(context_message or "Error").strip()
        if exc_value is None:
            return base

        if isinstance(exc_value, FileNotFoundError):
            missing = getattr(exc_value, "filename", None) or str(exc_value)
            return f"{base}: file not found ({missing})"

        detail = str(exc_value).strip().splitlines()[0] if str(exc_value).strip() else ""
        if not detail:
            return base

        if len(detail) > 180:
            detail = detail[:177] + "..."
        return f"{base}: {detail}"

    def _report_error(self, context_message: str, exc_type=None, exc_value=None, exc_traceback=None):
        """Publish an error summary to urgent/status lines and show an error dialog."""
        summary = self._build_gui_error_summary(context_message, exc_value)

        self._set_urgent_status(summary, color=ALERT_TEXT_COLOR)
        self._update_status(f"ERROR: {summary}")

        def show_error_popup():
            messagebox.showerror("Error", summary)

        try:
            self.after(0, show_error_popup)
        except Exception:
            pass

    def _resolve_user_selected_file(self, raw_path: str) -> str:
        """Resolve a user-entered file path using absolute and script-relative candidates."""
        value = str(raw_path or "").strip()
        if not value:
            return ""

        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_parent = os.path.dirname(script_dir)
        candidates = [
            value,
            os.path.join(script_dir, value),
            os.path.join(script_parent, value),
        ]

        for candidate in candidates:
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)

        return ""

    def _resolve_project_folder(self, raw_path: str) -> str:
        """Resolve a user-selected project folder to an absolute, existing directory."""
        value = str(raw_path or "").strip()
        if not value:
            return ""

        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_parent = os.path.dirname(script_dir)
        candidates = [
            value,
            os.path.join(script_dir, value),
            os.path.join(script_parent, value),
        ]

        for candidate in candidates:
            if os.path.isdir(candidate):
                return os.path.abspath(candidate)

        return ""

    def _is_rfsoc_root_folder(self, folder_path: str) -> bool:
        """Return True when the provided folder is the rfsoc_obs_scripts root."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            rfsoc_root = os.path.abspath(os.path.dirname(script_dir))
            return os.path.normcase(os.path.normpath(folder_path)) == os.path.normcase(os.path.normpath(rfsoc_root))
        except Exception:
            return False

    def _build_run_confirmation_content(self, run_configuration: dict):
        """Build primary and secondary run-confirmation lines for the custom panel."""
        remove_antennas = sorted(run_configuration.get("REMOVE_ANT") or [])
        selected_recorders = normalize_hashpipe_targets(run_configuration.get("ACTIVE_RECORDERS") or {})
        recorder_stream_count = sum(len(streams) for streams in selected_recorders.values())
        ods_project_tag = str(run_configuration.get("ODS_PROJECT_TAG", "")).strip()

        primary_lines = [
            ("Project Folder", str(run_configuration.get("PROJECT_FOLDER", ""))),
            ("Target List CSV", str(run_configuration.get("CSV_NAME", ""))),
            ("Observed List CSV", str(run_configuration.get("OBSERVED_LIST", ""))),
            ("Removed Antennas", str(remove_antennas if remove_antennas else [])),
        ]

        secondary_lines = [
            f"Project Name: {run_configuration.get('PROJECT_NAME', '')}",
            f"ODS Filename Tag (from folder): {ods_project_tag or '(auto)'}",
            f"Observation Time (sec): {run_configuration.get('OBS_TIME', '')}",
            f"Recording: {bool(run_configuration.get('RECORDING', False))}",
            f"Testing Mode: {bool(run_configuration.get('TESTING', False))}",
            f"Push ODS: {bool(run_configuration.get('ODS_PUSH', False))}",
            f"Queue Wait: {bool(run_configuration.get('QUEUE_WAIT', False))}",
            f"Mark Observed: {bool(run_configuration.get('MARKING', False))}",
            f"Sort by observed list: {bool(run_configuration.get('SORT_BY_OBSERVED', True))}",
            (
                "Target order mode: Dynamic refresh/rearrange (LST)"
                if bool(run_configuration.get('REARRANGE_BY_LST', False))
                else "Target order mode: Predetermined CSV schedule (no on-the-fly reorder)"
            ),
            f"Use per-target Obs Time override: {bool(run_configuration.get('USE_TARGET_OBS_TIME_OVERRIDE', False))}",
            f"Start After delay: {run_configuration.get('START_AFTER_BRIEF', 'None')}",
            f"Recorder streams selected: {recorder_stream_count}",
        ]
        return primary_lines, secondary_lines

    def _format_duration_brief(self, seconds: int) -> str:
        """Format a second count into a compact human-readable duration string."""
        try:
            total = int(seconds)
        except Exception:
            return "0s"
        if total <= 0:
            return "0s"

        hours = total // 3600
        mins = (total % 3600) // 60
        secs = total % 60

        if hours > 0:
            return f"{hours}h {mins}m"
        if mins > 0:
            return f"{mins}m {secs}s"
        return f"{secs}s"

    def _show_run_confirmation_panel(self, run_configuration: dict, confirm_callback):
        """Show a bold, high-visibility run confirmation panel before starting observations."""
        panel = getattr(self, "_run_confirmation_panel", None)
        if panel is not None and panel.winfo_exists():
            try:
                panel.destroy()
            except Exception:
                pass

        primary_lines, secondary_lines = self._build_run_confirmation_content(run_configuration)

        try:
            panel_w, panel_h = GUI_BOX_SIZES.get("run_confirmation", (700, 390))
            panel = ctk.CTkFrame(
                self,
                corner_radius=10,
                border_width=3,
                border_color="#F0E442",
                fg_color=UI_PANEL_COLOR,
                width=panel_w,
                height=panel_h,
            )
            panel.place(relx=0.5, rely=0.5, anchor="center")
            try:
                panel.pack_propagate(False)
            except Exception:
                pass
            try:
                panel.grid_propagate(False)
            except Exception:
                pass
            try:
                panel.lift()
                panel.focus_set()
            except Exception:
                pass

            self._run_confirmation_panel = panel

            content = ctk.CTkFrame(panel, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=16, pady=14)

            scroll_area = ctk.CTkScrollableFrame(content, fg_color="transparent")
            scroll_area.pack(fill="both", expand=True, pady=(0, 10))

            ctk.CTkLabel(
                scroll_area,
                text="CONFIRM OBSERVATION SETTINGS",
                font=(APP_FONT_FAMILY, 20, "bold"),
                text_color="#F0E442",
            ).pack(anchor="w", pady=(0, 10))

            ctk.CTkLabel(
                scroll_area,
                text="Review these required fields before continuing:",
                font=(APP_FONT_FAMILY, 14, "bold"),
                text_color=TITLE_TEXT_COLOR,
            ).pack(anchor="w", pady=(0, 10))

            for key, value in primary_lines:
                row = ctk.CTkFrame(scroll_area, fg_color="transparent")
                row.pack(fill="x", anchor="w", pady=(0, 6))
                ctk.CTkLabel(
                    row,
                    text=f"{key}:",
                    font=(APP_FONT_FAMILY, 16, "bold"),
                    text_color="#FFFFFF",
                    width=220,
                    anchor="w",
                ).pack(side="left")
                ctk.CTkLabel(
                    row,
                    text=value,
                    font=(APP_FONT_FAMILY, 16, "bold"),
                    text_color="#FFFFFF",
                    wraplength=max(420, panel_w - 260),
                    justify="left",
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

            ctk.CTkFrame(scroll_area, height=1, fg_color=UI_BORDER_COLOR).pack(fill="x", pady=(8, 8))

            ctk.CTkLabel(
                scroll_area,
                text="Additional options",
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
            ).pack(anchor="w", pady=(0, 4))

            ctk.CTkLabel(
                scroll_area,
                text="\n".join(secondary_lines),
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
                justify="left",
                anchor="w",
            ).pack(anchor="w")

            footer = ctk.CTkFrame(content, fg_color="transparent")
            footer.pack(side="bottom", fill="x", pady=(4, 0))

            def on_cancel():
                try:
                    panel.destroy()
                except Exception:
                    pass
                self._run_confirmation_panel = None
                self._set_urgent_status("Run cancelled")
                self._update_status("Run cancelled before start.")

            def on_confirm():
                try:
                    panel.destroy()
                except Exception:
                    pass
                self._run_confirmation_panel = None
                confirm_callback()

            ctk.CTkButton(
                footer,
                text="Cancel",
                command=on_cancel,
                width=170,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            ).pack(side="left")

            ctk.CTkButton(
                footer,
                text="Confirm and Start",
                command=on_confirm,
                width=220,
                fg_color="#009E73",
                text_color="white",
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            ).pack(side="right")
        except Exception as exc:
            self._update_status(f"ERROR: Failed to show run confirmation panel: {exc}")
            messagebox.showerror("Run Confirmation Error", f"Failed to show run confirmation: {exc}")

    def _validate_run_configuration(self):
        """Validate run inputs and return normalized values plus a list of errors."""
        errors = []

        project_folder = self._resolve_project_folder(self.project.get())
        if not project_folder:
            errors.append("Project folder must be an existing directory. Please use Browse to select one.")
        elif self._is_rfsoc_root_folder(project_folder):
            errors.append("Project folder cannot be rfsoc_obs_scripts. Select a subfolder (for example: p000, survey, testingtime).")

        project_name = os.path.basename(project_folder.rstrip("/\\")) if project_folder else ""
        if not project_name:
            errors.append("Could not derive a valid project name from the selected project folder.")

        ods_project_tag = make_ods_project_tag(project_name=project_name, project_folder=project_folder)
        if not ods_project_tag:
            errors.append("Could not derive a valid ODS filename tag from the selected project folder.")

        try:
            obs_time_seconds = int(self.obs_time_entry.get().strip())
            if obs_time_seconds <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            obs_time_seconds = None
            errors.append("Observation time must be a positive integer (seconds).")

        csv_path = self._resolve_user_selected_file(self.csv_name.get())
        if not csv_path:
            errors.append(f"Target CSV file not found: {self.csv_name.get()}")

        sort_by_observed = bool(self.sort_by_observed.get())
        marking_enabled = bool(self.marking.get())
        requires_observed_list = sort_by_observed or marking_enabled

        observed_path = ""
        if requires_observed_list:
            observed_path = self._resolve_user_selected_file(self.observed.get())
            if not observed_path:
                errors.append(f"Observed list file not found: {self.observed.get()}")

            # Validate that target CSV and observed list CSV have matching names
            # (Detailed validation also happens in observe_survey.py at runtime)
            if csv_path and observed_path and os.path.isfile(csv_path) and os.path.isfile(observed_path):
                try:
                    import utils_beamforming
                    validation_result = utils_beamforming.validate_csv_name_agreement(csv_path, observed_path, raise_on_error=False)
                    if not validation_result['agreement']:
                        mismatch_count = len(validation_result['missing_in_observed'])
                        errors.append(f"CSV name mismatch: {mismatch_count} target(s) in target CSV but not in observed list. See terminal output for details.")
                        self._update_status(f"CSV mismatch detected: {mismatch_count} target(s) missing from observed list")
                except ImportError:
                    pass  # utils_beamforming not available, will be checked at runtime
                except Exception as e:
                    self._update_status(f"Could not validate CSV names: {str(e)[:80]}")
        else:
            observed_path = str(self.observed.get() or "").strip()

        return {
            "errors": errors,
            "project_name": project_name,
            "project_folder": project_folder,
            "ods_project_tag": ods_project_tag,
            "obs_time_seconds": obs_time_seconds,
            "csv_path": csv_path,
            "observed_path": observed_path,
        }

    def _show_configuration_errors(self, errors):
        """Display configuration validation errors in GUI status and popup dialog."""
        self._set_urgent_status("Configuration check failed", color=ALERT_TEXT_COLOR)
        self._update_status("ERROR: Configuration check failed.")
        for error in errors:
            self._update_status(f"- {error}")
        messagebox.showerror("Configuration Error", "\n".join(errors))

    def _bind_observe_callbacks(self):
        """Attach status and urgent callbacks to the loaded observe module."""
        if self._observe_module is None:
            return
        # Normal Status Console Update
        if hasattr(self._observe_module, "set_status_callback"):
            self._observe_module.set_status_callback(self._update_status)
        # Urgent output line for important messages
        if hasattr(self._observe_module, "set_urgent_callback"):
            def _urgent_wrapper(message, color=None):
                try:
                    self._set_urgent_status(message, color)
                except TypeError:
                    try:
                        self._set_urgent_status(message)
                    except Exception:
                        pass

            self._observe_module.set_urgent_callback(_urgent_wrapper)

    def _load_observe_module(self, raise_on_error: bool):
        """Import the configured observing module and bind GUI callbacks.

        Args:
            raise_on_error: If True, raises RuntimeError when import fails.
        """
        configured_module_name = str(OBSERVE_MODULE_NAME or "").strip()
        if configured_module_name.endswith(".py"):
            configured_module_name = configured_module_name[:-3]

        module_name = configured_module_name.lower()
        if not module_name:
            msg = "Observe module name is required. Set OBSERVE_MODULE_NAME at the top of this script."
            if raise_on_error:
                raise RuntimeError(msg)
            return None

        if self._observe_module is not None and self._observe_module_name == module_name:
            return self._observe_module

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name != module_name:
                raise
            msg = f"Could not import {module_name}. Expected file: {module_name}.py"
            if raise_on_error:
                self._set_urgent_status("Observe module not found", color=ALERT_TEXT_COLOR)
                raise RuntimeError(msg) from exc
            return None

        self._observe_module = module
        self._observe_module_name = module_name
        self._bind_observe_callbacks()
        return module

    def _build_ui(self):
        """Build the full GUI layout: configuration, options, status, and controls."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)

        # This is the left column for project/run configuration inputs.
        left = ctk.CTkFrame(main_frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsw", padx=(0,16))

        # This is the main configuration box for filenames and observation timing.
        input_box = ctk.CTkFrame(
            left,
            corner_radius=10,
            border_width=1,
            border_color=UI_BORDER_COLOR,
            fg_color=UI_PANEL_COLOR
        )
        config_w, config_h = GUI_BOX_SIZES["config"]
        input_box.configure(width=config_w, height=config_h)
        input_box.pack(anchor="nw", pady=(0,12), fill="x")
        input_box.pack_propagate(False)

        ctk.CTkLabel(
            input_box,
            text="Configuration",
            font=TITLE_FONT,
            text_color=TITLE_TEXT_COLOR
        ).pack(anchor="w", padx=10, pady=(8,2))

        config_container = ctk.CTkFrame(input_box, width=config_w, height=config_h, fg_color="transparent")
        config_container.pack(fill="both", expand=True, padx=10, pady=(0,8))
        config_container.pack_propagate(False)

        # Define project folder
        ctk.CTkLabel(
            config_container,
            text="Project Folder (MAKE SURE THIS IS ACCURATE. Subfolders will be created here.)",
            font=NORMAL_FONT,
            text_color=NORMAL_TEXT_COLOR
        ).pack(anchor="w", pady=(0,2))
        project_row = ctk.CTkFrame(config_container, fg_color="transparent")
        project_row.pack(anchor="w", pady=(0,6))
        self.project = tk.StringVar(value=PROJECT_NAME)
        ctk.CTkEntry(
            project_row,
            textvariable=self.project,
            width=GUI_INPUT_SIZES["text_entry"],
            fg_color=UI_ENTRY_COLOR,
            border_color=UI_BORDER_COLOR,
            text_color=NORMAL_TEXT_COLOR
        ).pack(side="left")
        self.project_entry = project_row.winfo_children()[-1]
        self._lockable_widgets.append(self.project_entry)
        self.browse_project_btn = ctk.CTkButton(project_row, text="Browse", command=self._browse_project, width=GUI_INPUT_SIZES["browse_button"], corner_radius=BUTTON_CORNER_RADIUS, font=BUTTON_FONT)
        self.browse_project_btn.pack(side="left", padx=6)
        self._lockable_widgets.append(self.browse_project_btn)
        ctk.CTkLabel(
            config_container,
            text="ODS files use: ods_<folder_tag>_<source>.json",
            font=SMALL_FONT,
            text_color=SMALL_TEXT_COLOR
        ).pack(anchor="w")

        # Define target CSV
        ctk.CTkLabel(
            config_container,
            text="Target CSV (e.g. survey_targets.csv)",
            font=NORMAL_FONT,
            text_color=NORMAL_TEXT_COLOR
        ).pack(anchor="w", pady=(4,2))
        csv_row = ctk.CTkFrame(config_container, fg_color="transparent")
        csv_row.pack(anchor="w", pady=(0,2))
        self.csv_name = tk.StringVar(value=CSV_NAME)
        ctk.CTkEntry(
            csv_row,
            textvariable=self.csv_name,
            width=GUI_INPUT_SIZES["text_entry"],
            fg_color=UI_ENTRY_COLOR,
            border_color=UI_BORDER_COLOR,
            text_color=NORMAL_TEXT_COLOR
        ).pack(side="left")
        self.csv_entry = csv_row.winfo_children()[-1]
        self._lockable_widgets.append(self.csv_entry)
        self.browse_csv_btn = ctk.CTkButton(csv_row, text="Browse", command=self._browse_csv, width=GUI_INPUT_SIZES["browse_button"], corner_radius=BUTTON_CORNER_RADIUS, font=BUTTON_FONT)
        self.browse_csv_btn.pack(side="left", padx=6)
        self._lockable_widgets.append(self.browse_csv_btn)
        # Format note for Target CSV
        ctk.CTkLabel(
            config_container,
            text="Check README for Format",
            # text="Format: ID | Plaintext Name | Horizons Name | Solsys Flag | RA (hours) | DEC | RA (deg) | RA (solsys) | DEC (solsys)",
            font=SMALL_FONT,
            text_color=SMALL_TEXT_COLOR
        ).pack(anchor="w")

        # Define observed list CSV. Can be the same file as the target list.
        ctk.CTkLabel(
            config_container,
            text="Observed List CSV (e.g. survey_observed.csv)",
            font=NORMAL_FONT,
            text_color=NORMAL_TEXT_COLOR
        ).pack(anchor="w", pady=(4,2))
        obs_row = ctk.CTkFrame(config_container, fg_color="transparent")
        obs_row.pack(anchor="w", pady=(0,2))
        self.observed = tk.StringVar(value=OBSERVED_LIST)
        ctk.CTkEntry(
            obs_row,
            textvariable=self.observed,
            width=GUI_INPUT_SIZES["text_entry"],
            fg_color=UI_ENTRY_COLOR,
            border_color=UI_BORDER_COLOR,
            text_color=NORMAL_TEXT_COLOR
        ).pack(side="left")
        self.observed_entry = obs_row.winfo_children()[-1]
        self._lockable_widgets.append(self.observed_entry)
        self.browse_observed_btn = ctk.CTkButton(obs_row, text="Browse", command=self._browse_observed, width=GUI_INPUT_SIZES["browse_button"], corner_radius=BUTTON_CORNER_RADIUS, font=BUTTON_FONT)
        self.browse_observed_btn.pack(side="left", padx=6)
        self._lockable_widgets.append(self.browse_observed_btn)
        # Format note for Observed List CSV
        ctk.CTkLabel(
            config_container,
            text="Check README for Format",
            # text="Format: ID | Plaintext Name | Solsys Flag | cfreq_1336mhz | cfreq_2008mhz | cfreq_4536mhz | cfreq_8336mhz | cfreq_####mhz...",
            font=SMALL_FONT,
            text_color=SMALL_TEXT_COLOR
        ).pack(anchor="w")

        # Define Observation Time
        ctk.CTkLabel(
            config_container,
            text="Observation Time per Target (sec)",
            font=NORMAL_FONT,
            text_color=NORMAL_TEXT_COLOR
        ).pack(anchor="w", pady=(4,2))
        self.obs_time = tk.IntVar(value=OBS_TIME)
        self.obs_time_entry = ctk.CTkEntry(
            config_container,
            textvariable=self.obs_time,
            width=GUI_INPUT_SIZES["obs_time_entry"],
            fg_color=UI_ENTRY_COLOR,
            border_color=UI_BORDER_COLOR,
            text_color=NORMAL_TEXT_COLOR
        )
        self.obs_time_entry.pack(anchor="w", pady=(0,2))
        self._lockable_widgets.append(self.obs_time_entry)
        ctk.CTkLabel(
            config_container,
            text="Default: 300 seconds (5 minutes)",
            font=SMALL_FONT,
            text_color=SMALL_TEXT_COLOR
        ).pack(anchor="w")

        panel_button_row = ctk.CTkFrame(config_container, fg_color="transparent")
        panel_button_row.pack(anchor="w", fill="x", pady=(6, 0))

        # "Choose Antennas" popup removed in favor of the inline panel because Ubuntu was weird
        self.antennas_inline_btn = ctk.CTkButton(
            panel_button_row,
            text="Antenna Panel",
            command=self._toggle_inline_antennas,
            width=GUI_BUTTON_SIZES["antennas_panel"],
            fg_color="#0072B2",
            text_color="white",
            corner_radius=BUTTON_CORNER_RADIUS,
            font=BUTTON_FONT,
        )
        self.antennas_inline_btn.pack(side="left", padx=(0, 6))
        self._lockable_widgets.append(self.antennas_inline_btn)

        self.recorders_inline_btn = ctk.CTkButton(
            panel_button_row,
            text="Recorder Panel",
            command=self._toggle_inline_recorders,
            width=GUI_BUTTON_SIZES["recorders_panel"],
            fg_color="#0072B2",
            text_color="white",
            corner_radius=BUTTON_CORNER_RADIUS,
            font=BUTTON_FONT,
        )
        self.recorders_inline_btn.pack(side="left")
        self._lockable_widgets.append(self.recorders_inline_btn)

        status_box = ctk.CTkFrame(
            left,
            corner_radius=10,
            border_width=1,
            border_color=UI_BORDER_COLOR,
            fg_color=UI_PANEL_COLOR,
        )
        status_box.pack(anchor="nw", fill="x")
        self._build_status_mapping_section(status_box)

        self.ant_vars = {}
        self.ant_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        self._render_antenna_checkboxes()

        # This is the right column for toggles and status output.
        right = ctk.CTkFrame(main_frame, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        # Options box: Check boxes for other parts of the observation
        options_box = ctk.CTkFrame(right, corner_radius=10, border_width=1, border_color=UI_BORDER_COLOR, fg_color=UI_PANEL_COLOR)
        options_w, options_h = GUI_BOX_SIZES["options"]
        options_box.configure(width=options_w, height=options_h)
        options_box.pack(anchor="nw", pady=(0,12), fill="x")
        options_box.pack_propagate(False)

        ctk.CTkLabel(
            options_box,
            text="Options",
            font=TITLE_FONT,
            text_color=TITLE_TEXT_COLOR
        ).pack(anchor="w", padx=10, pady=(8,2))

        options_container = ctk.CTkFrame(options_box, width=options_w, height=options_h, fg_color="transparent")
        options_container.pack(fill="both", expand=True, padx=10, pady=(0,8))
        options_container.pack_propagate(False)

        # Check if the user does or doesn't want to actually record the observation.
        self.recording = tk.BooleanVar(value=RECORDING)
        self.recording_chk = ctk.CTkCheckBox(
            options_container,
            text="Record Data",
            variable=self.recording,
            text_color=NORMAL_TEXT_COLOR,
            corner_radius=CHECKBOX_CORNER_RADIUS,
        )
        self.recording_chk.pack(anchor="w", pady=(0,4))
        self._lockable_widgets.append(self.recording_chk)

        # Check box to mark the targets as observed as you go.
        self.marking = tk.BooleanVar(value=MARKING)
        self.marking_chk = ctk.CTkCheckBox(
            options_container,
            text="Mark Target as Observed After Scan",
            variable=self.marking,
            text_color=NORMAL_TEXT_COLOR,
            corner_radius=CHECKBOX_CORNER_RADIUS,
        )
        self.marking_chk.pack(anchor="w", pady=(0,4))
        self._lockable_widgets.append(self.marking_chk)

        self.sort_by_observed = tk.BooleanVar(value=SORT_BY_OBSERVED)
        self.sort_by_observed_chk = ctk.CTkCheckBox(
            options_container,
            text="Sort by observed list",
            variable=self.sort_by_observed,
            text_color=NORMAL_TEXT_COLOR,
            corner_radius=CHECKBOX_CORNER_RADIUS,
        )
        self.sort_by_observed_chk.pack(anchor="w", pady=(0,4))
        self._lockable_widgets.append(self.sort_by_observed_chk)

        self.rearrange_by_lst = tk.BooleanVar(value=REARRANGE_BY_LST)
        self.rearrange_by_lst_chk = ctk.CTkCheckBox(
            options_container,
            text="Dynamic refresh/rearrange by LST (OFF = follow CSV schedule order)",
            variable=self.rearrange_by_lst,
            text_color=NORMAL_TEXT_COLOR,
            corner_radius=CHECKBOX_CORNER_RADIUS,
        )
        self.rearrange_by_lst_chk.pack(anchor="w", pady=(0,4))
        self._lockable_widgets.append(self.rearrange_by_lst_chk)

        self.testing = tk.BooleanVar(value=TESTING)
        self.testing_chk = ctk.CTkCheckBox(
            options_container,
            text="Testing Mode",
            variable=self.testing,
            text_color=NORMAL_TEXT_COLOR,
            corner_radius=CHECKBOX_CORNER_RADIUS,
        )
        self.testing_chk.pack(anchor="w", pady=(0,6))
        self._lockable_widgets.append(self.testing_chk)

        # Advanced options container (includes ODS Wait)
        self.queue_wait = tk.BooleanVar(value=QUEUE_WAIT)

        # Frame to hold Advanced Options button and scheduled stop status
        advanced_row = ctk.CTkFrame(options_container, fg_color="transparent")
        advanced_row.pack(anchor="w", pady=(2,4), fill="x")

        self.advanced_options_btn = ctk.CTkButton(
            advanced_row,
            text="Advanced Options",
            command=self._toggle_inline_advanced_options,
            width=160,
            fg_color="#0072B2",
            text_color="white",
            corner_radius=BUTTON_CORNER_RADIUS,
            font=BUTTON_FONT,
        )
        self.advanced_options_btn.pack(side="left")

        # Scheduled stop status label
        self._scheduled_stop_label = ctk.CTkLabel(
            advanced_row,
            textvariable=self.scheduled_stop_display,
            font=SMALL_FONT,
            text_color="#E69F00"
        )
        self._scheduled_stop_label.pack(side="left", padx=(8, 0))

        console_header = ctk.CTkFrame(right, fg_color="transparent")
        console_header.pack(fill="x")

        ctk.CTkLabel(
            console_header,
            text="Status Console",
            font=TITLE_FONT,
            text_color=TITLE_TEXT_COLOR
        ).pack(side="left")

        ctk.CTkButton(
            console_header,
            text="Clear Console",
            command=self._confirm_clear_console,
            corner_radius=BUTTON_CORNER_RADIUS,
            font=BUTTON_FONT,
        ).pack(side="right")

        # Put the console Text and its scrollbar inside a dedicated frame so the scrollbar sits directly beside the console
        console_row = ctk.CTkFrame(right, fg_color="transparent")
        console_row.pack(anchor="nw", pady=6, fill="both", expand=True)

        console_frame = ctk.CTkFrame(console_row, corner_radius=10, border_width=1, border_color=UI_BORDER_COLOR, fg_color=UI_PANEL_ALT_COLOR)
        console_frame.pack(side="left", fill="both", expand=True)
        console_w, console_h = GUI_BOX_SIZES["console"]
        console_frame.configure(width=console_w, height=console_h)
        console_frame.pack_propagate(False)

        self.status_text = ctk.CTkTextbox(
            console_frame,
            height=console_h,
            width=console_w,
            wrap="word",
            fg_color=UI_ENTRY_COLOR,
            text_color=NORMAL_TEXT_COLOR
        )
        self.status_text.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        self.status_text.configure(state="disabled")

        # Urgent single-line output (below console)
        # Always show the urgent/action line (renamed to 'urgent').
        self.urgent_var = None
        self.urgent_label = None

        # Bottom control panel: action output + run/stop/abort + close/readme.
        bottom_box = ctk.CTkFrame(
            main_frame,
            corner_radius=10,
            border_width=1,
            border_color=UI_BORDER_COLOR,
            fg_color=UI_PANEL_COLOR
        )
        bottom_box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        bottom_box.grid_columnconfigure(0, weight=1)

        bottom_controls = ctk.CTkFrame(bottom_box, fg_color="transparent")
        bottom_controls.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        bottom_controls.grid_columnconfigure(0, weight=1)
        bottom_controls.grid_columnconfigure(1, weight=0)
        bottom_controls.grid_columnconfigure(2, weight=1)

        # Bottom single-line urgent status (previously called 'action')
        self.urgent_var = tk.StringVar(value="(idle)")
        self.urgent_label = ctk.CTkLabel(
            bottom_controls,
            textvariable=self.urgent_var,
            font=TITLE_FONT,
            text_color=UI_MUTED_TEXT_COLOR
        )
        self.urgent_label.grid(row=0, column=0, sticky="w")

        btns = ctk.CTkFrame(bottom_controls, fg_color="transparent")
        btns.grid(row=0, column=1)

        self.run_btn = ctk.CTkButton(btns, text="Run", fg_color="#009E73", text_color="white", command=self._on_run, width=GUI_BUTTON_SIZES["run"], corner_radius=BUTTON_CORNER_RADIUS, font=BUTTON_FONT)
        self.run_btn.pack(side="left") # Run button
        self._lockable_widgets.append(self.run_btn)
        self.stop_btn = ctk.CTkButton(btns, text="Request Stop", fg_color="#E69F00", text_color="white", command=self._on_stop, width=GUI_BUTTON_SIZES["stop"], corner_radius=BUTTON_CORNER_RADIUS, font=BUTTON_FONT)
        self.resume_btn = ctk.CTkButton(btns, text="Resume", fg_color="#009E73", text_color="white", command=self._on_resume, width=GUI_BUTTON_SIZES["resume"], corner_radius=BUTTON_CORNER_RADIUS, font=BUTTON_FONT)
        self.abort_btn = ctk.CTkButton(btns, text="ABORT", fg_color="#D50000", text_color="white", command=self._on_abort, width=GUI_BUTTON_SIZES["abort"], corner_radius=BUTTON_CORNER_RADIUS, font=BUTTON_FONT)
        self.abort_btn.pack(side="left", padx=(0, 12)) # Abort everything and close the GUI
        self._set_stop_resume_buttons(stop_requested=False)

        # Close and README buttons at bottom-right of the bottom control panel
        readme_corner = ctk.CTkFrame(bottom_controls, fg_color="transparent")
        readme_corner.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(
            readme_corner,
            text="Close GUI",
            fg_color="#0072B2",
            text_color="white",
            command=self._on_close_gui,
            corner_radius=BUTTON_CORNER_RADIUS,
            font=BUTTON_FONT,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            readme_corner,
            text="README",
            fg_color="#009E73",
            text_color="white",
            width=GUI_BUTTON_SIZES["readme"],
            command=self._open_readme_window,
            corner_radius=BUTTON_CORNER_RADIUS,
            font=BUTTON_FONT,
        ).pack(side="left")

    def _confirm_clear_console(self):
        """Prompt for confirmation and clear the status console when approved."""
        if messagebox.askyesno("Clear Console", "Are you sure you want to clear the status console?"):
            self.status_text.configure(state="normal")
            self.status_text.delete("1.0", tk.END)
            self.status_text.configure(state="disabled")

    def _update_status(self, message: str):
        """Append a status message to the console, collapsing duplicate timer lines."""
        def append():
            at_bottom = self.status_text.yview()[1] >= 0.99
            message_text = str(message).rstrip("\n")

            self.status_text.configure(state="normal")

            if self._is_live_timer_message(message_text):
                last_line = self.status_text.get("end-2l linestart", "end-2l lineend").strip()
                if self._is_live_timer_message(last_line) and self._timer_signature(last_line) == self._timer_signature(message_text):
                    self.status_text.delete("end-2l linestart", "end-2l lineend")
                    self.status_text.insert("end-2l linestart", message_text)
                else:
                    self.status_text.insert(tk.END, message_text + "\n")
            else:
                self.status_text.insert(tk.END, message_text + "\n")

            if at_bottom:
                self.status_text.see(tk.END)
            self.status_text.configure(state="disabled")
        # Ensure UI updates happen on main thread
        self.after(0, append)

    def _is_live_timer_message(self, message: str) -> bool:
        """Return True when a status line matches the live countdown timer format."""
        text = str(message or "").strip()
        return bool(re.match(r"^\d{1,2}:\d{2}(?::\d{2})?\s+remaining$", text, flags=re.IGNORECASE))

    def _timer_signature(self, message: str) -> str:
        """Return a normalized timer suffix used to detect timer-line replacement."""
        text = str(message or "").strip().lower()
        return re.sub(r"^\d{1,2}:\d{2}(?::\d{2})?\s+", "", text)

    def _set_urgent_status(self, message: str, color: str = None):
        """Set the bottom urgent status line text and optional text color."""
        def set_line():
            # Update the bottom urgent line and optionally its color.
            if self.urgent_var is None or self.urgent_label is None:
                return
            try:
                self.urgent_var.set(message)
            except Exception:
                return
            try:
                if color:
                    self.urgent_label.configure(text_color=color)
                else:
                    self.urgent_label.configure(text_color=UI_MUTED_TEXT_COLOR)
            except Exception:
                pass

        self.after(0, set_line)

    def _get_antenna_visuals(self, name: str):
        """Return style/state metadata for a single antenna checkbox."""
        is_active = name in self.active_antennas
        observing_status = _normalize_observing_status(self.observing_status_by_antenna.get(name, ""))

        if not is_active or observing_status == STATUS_NOT_APPLICABLE:
            base_color = UI_BORDER_COLOR
        else:
            base_color = STATUS_COLOR_BY_VALUE.get(observing_status, STATUS_COLOR_BY_VALUE[STATUS_CLEAR_TO_USE])

        border_color = base_color if is_active else UI_BORDER_COLOR
        is_disabled = (not is_active) or (observing_status == STATUS_NOT_APPLICABLE)
        return is_active, observing_status, base_color, border_color, is_disabled

    def _render_antenna_checkboxes(self, preserve_previous: bool = True):
        """Render antenna checkboxes and keep shared checkbox state in sync."""
        for widget in self.ant_grid.winfo_children():
            widget.destroy()
        self._antenna_checkbox_widgets = []
        create_main_widgets = bool(self.ant_grid.winfo_manager())

        previous_values = {name: var.get() for name, var in self.ant_vars.items()} if preserve_previous else {}
        self.ant_vars = {}
        # Keep a compact layout so all antennas stay visible in the fixed panel.
        cols = GUI_LAYOUT["antenna_columns"]
        for col in range(cols):
            self.ant_grid.grid_columnconfigure(col, minsize=GUI_LAYOUT["antenna_column_minsize"])
        for i, name in enumerate(self.current_antennas):
            is_active, observing_status, base_color, border_color, is_disabled = self._get_antenna_visuals(name)

            # By default, mark antennas that are in the active array as checked.
            # Then uncheck any explicitly marked for removal by Notion or the global REMOVE_ANT.
            if preserve_previous:
                default_checked = previous_values.get(name, name not in REMOVE_ANT)
            else:
                default_checked = bool(is_active)

            if observing_status == STATUS_REMOVE_FROM_ALL_SCRIPTS or name in (REMOVE_ANT or []):
                default_checked = False

            var = tk.BooleanVar(value=default_checked)
            self.ant_vars[name] = var
            # Keep global REMOVE_ANT in sync whenever a checkbox changes
            try:
                var.trace_add("write", lambda *a, _n=name: self._update_global_REMOVE_ANT())
            except Exception:
                try:
                    var.trace("w", lambda *a, _n=name: self._update_global_REMOVE_ANT())
                except Exception:
                    pass

            if not create_main_widgets:
                continue

            checkbox_kwargs = {
                "text": name,
                "variable": var,
                "font": SMALL_FONT,
                "width": 60,
                "checkbox_width": 20,
                "checkbox_height": 20,
                "corner_radius": CHECKBOX_CORNER_RADIUS,
                "text_color": NORMAL_TEXT_COLOR if is_active else UI_MUTED_TEXT_COLOR,
                "fg_color": base_color,
                "hover_color": base_color,
                "border_color": border_color,
            }
            if observing_status == STATUS_YPOL_HARDWARE_ISSUE and is_active:
                checkbox_kwargs["checkmark_color"] = "#000000"

            chk = ctk.CTkCheckBox(
                self.ant_grid,
                **checkbox_kwargs,
            )

            if is_disabled:
                chk.configure(state="disabled")

            chk.grid(row=i//cols, column=i % cols, sticky="w", padx=1, pady=1)
            self._antenna_checkbox_widgets.append(chk)

        if self._is_running:
            for widget in self._antenna_checkbox_widgets:
                widget.configure(state="disabled")

    def _update_global_REMOVE_ANT(self):
        """Synchronize global REMOVE_ANT from current antenna checkbox selections."""
        global REMOVE_ANT
        try:
            remove_list = [name for name, var in self.ant_vars.items() if (name in self.active_antennas and not var.get())]
            REMOVE_ANT = remove_list
            # Optionally show concise status
            try:
                self._set_urgent_status(f"Removed antennas: {', '.join(REMOVE_ANT) if REMOVE_ANT else '(none)'}")
            except Exception:
                pass
        except Exception:
            pass

    def _build_antenna_legend(self, parent):
        """Create the antenna color legend that explains Notion observing statuses."""
        for status_value, legend_text in STATUS_LEGEND_ITEMS:
            legend_row = ctk.CTkFrame(parent, fg_color="transparent")
            legend_row.pack(anchor="w", padx=10, pady=(0, 0))

            color = STATUS_COLOR_BY_VALUE.get(status_value, UI_MUTED_TEXT_COLOR)
            ctk.CTkLabel(
                legend_row,
                text="■",
                font=NORMAL_FONT,
                text_color=color,
            ).pack(side="left", padx=(0, 2))
            ctk.CTkLabel(
                legend_row,
                text=legend_text,
                font=NORMAL_FONT,
                text_color=color,
            ).pack(side="left")

    def _build_status_mapping_section(self, parent):
        """Show editable Notion status rules and their matching colors."""
        ctk.CTkLabel(
            parent,
            text="Notion Status Mapping",
            font=TITLE_FONT,
            text_color=TITLE_TEXT_COLOR,
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            parent,
            text="Edit STATUS_* values near the top of this file to change matching rules.",
            font=SMALL_FONT,
            text_color=SMALL_TEXT_COLOR,
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 4))

        for status_value, legend_text in STATUS_LEGEND_ITEMS:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(anchor="w", padx=10, pady=(0, 1), fill="x")

            color = STATUS_COLOR_BY_VALUE.get(status_value, UI_MUTED_TEXT_COLOR)
            ctk.CTkLabel(
                row,
                text="■",
                font=NORMAL_FONT,
                text_color=color,
                width=14,
            ).pack(side="left", padx=(0, 2))
            ctk.CTkLabel(
                row,
                text=f"{legend_text}: '{status_value}'",
                font=SMALL_FONT,
                text_color=NORMAL_TEXT_COLOR,
                anchor="w",
            ).pack(side="left")

    def _build_antenna_selection_grid(self, parent):
        """Build the antenna checkbox grid used by the inline antenna panel."""
        self._antenna_checkbox_widgets = []
        ant_container = ctk.CTkFrame(parent, fg_color="transparent")
        ant_container.pack(fill="both", expand=True, padx=10, pady=(0,8))

        ant_grid = ctk.CTkFrame(ant_container, fg_color="transparent")
        ant_grid.pack(anchor="nw", fill="both", expand=True)

        cols = GUI_LAYOUT["antenna_columns"]
        for col in range(cols):
            ant_grid.grid_columnconfigure(col, minsize=GUI_LAYOUT["antenna_column_minsize"])

        for i, name in enumerate(self.current_antennas):
            is_active, observing_status, base_color, border_color, is_disabled = self._get_antenna_visuals(name)
            var = self.ant_vars.get(name)
            if var is None:
                continue

            checkbox_kwargs = {
                "text": name,
                "variable": var,
                "font": SMALL_FONT,
                "width": 60,
                "checkbox_width": 16,
                "checkbox_height": 16,
                "corner_radius": CHECKBOX_CORNER_RADIUS,
                "text_color": NORMAL_TEXT_COLOR if is_active else UI_MUTED_TEXT_COLOR,
                "fg_color": base_color,
                "hover_color": base_color,
                "border_color": border_color,
            }
            if observing_status == STATUS_YPOL_HARDWARE_ISSUE and is_active:
                checkbox_kwargs["checkmark_color"] = "#000000"

            chk = ctk.CTkCheckBox(
                ant_grid,
                **checkbox_kwargs,
            )
            if is_disabled or self._is_running:
                chk.configure(state="disabled")

            chk.grid(row=i//cols, column=i % cols, sticky="w", padx=1, pady=1)
            self._antenna_checkbox_widgets.append(chk)

    def _build_recorder_tuning_columns(self, active_targets: dict):
        """Build ordered stream labels by tuning column (LoA..LoD).

        Notes:
        - The visual layout is fixed to the calibration/exotica-style 4-column map.
        - Prefix is inferred from available node names (typically seti-node or test-node)
          so the same layout works for both ATA-validated and fallback recorder sources.
        """
        columns = {label: [] for label in RECORDER_TUNING_LABELS}
        normalized_targets = normalize_hashpipe_targets(active_targets)

        prefix = "seti-node"
        node_names = list(normalized_targets.keys())
        if any(name.startswith("seti-node") for name in node_names):
            prefix = "seti-node"
        elif any(name.startswith("test-node") for name in node_names):
            prefix = "test-node"
        else:
            for name in node_names:
                match = re.match(r"^(.*?)(\d+)$", name)
                if match:
                    prefix = match.group(1)
                    break

        layout = [
            [(1, [0, 1]), (2, [0, 1]), (3, [0, 1]), (4, [0])],
            [(4, [1]), (5, [0, 1]), (6, [0, 1]), (7, [0, 1])],
            [(8, [0, 1]), (9, [0, 1]), (10, [0, 1]), (11, [0])],
            [(11, [1]), (12, [0, 1]), (13, [0, 1]), (14, [0, 1])],
        ]

        for index, column_layout in enumerate(layout):
            if index >= len(RECORDER_TUNING_LABELS):
                break
            tuning_label = RECORDER_TUNING_LABELS[index]
            entries = []
            for node_number, streams in column_layout:
                node = f"{prefix}{node_number}".lower()
                available_streams = normalized_targets.get(node, [])
                for stream in streams:
                    if stream in available_streams:
                        entries.append(f"{node}.{stream}")
            columns[tuning_label] = entries

        return columns

    def _mock_recorder_targets(self) -> dict:
        """Return calibration-style fallback recorder targets: seti-node1..14 with both streams."""
        return normalize_hashpipe_targets(DEFAULT_RECORDERS)

    def _extract_hashpipe_targets_from_module(self, module_obj) -> dict:
        """Best-effort extraction of hashpipe target dict(s) from SNAPobs defaults module."""
        candidates = []
        for attr_name in dir(module_obj):
            if attr_name.startswith("__"):
                continue
            try:
                attr_value = getattr(module_obj, attr_name)
            except Exception:
                continue
            if isinstance(attr_value, dict):
                normalized = normalize_hashpipe_targets(attr_value)
                if normalized:
                    candidates.append(normalized)

        if not candidates:
            return {}

        merged = {}
        for candidate in candidates:
            for node_name, streams in candidate.items():
                merged.setdefault(node_name, set())
                merged[node_name].update(streams)

        merged = {node_name: sorted(streams) for node_name, streams in merged.items() if streams}

        # Keep previous behavior as a guardrail and prefer whichever contains more node coverage.
        largest_single = max(candidates, key=lambda item: len(item.keys()))
        if len(merged.keys()) >= len(largest_single.keys()):
            return merged
        return largest_single

    def _load_recorders_from_ata_or_fallback(self, preserve_selection: bool, announce: bool):
        """Load recorder targets using ATA-first policy with deterministic fallback.

        Behavior:
        - First, attempt ATA/SNAPobs import as a validation step.
        - If successful, use the fixed calibration-style seti-node map
          (seti-node1..14, streams [0,1]) for stable GUI coverage.
        - If ATA fails, use mock test-node1..14 streams [0,1].

        Args:
            preserve_selection: Keep existing checkbox state where stream labels match.
            announce: If True, write source-status text to the status console.
        """
        previous_values = {name: bool(var.get()) for name, var in (self.recorder_vars or {}).items()}

        source_status = ""
        active_targets = {}
        try:
            from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults

            extracted = self._extract_hashpipe_targets_from_module(hpguppi_defaults)
            # Match current_calibration_gui.py behavior by ensuring a stable
            # seti-node map is always available, while still honoring ATA
            # defaults when they provide explicit hashpipe targets.
            active_targets = extracted or normalize_hashpipe_targets(DEFAULT_RECORDERS)
            if not active_targets:
                raise RuntimeError("No valid hashpipe target dictionary found in SNAPobs defaults")

            source_status = (
                f"Recorder source: ATA/SNAPobs defaults loaded "
                f"({len(active_targets)} nodes)"
            )
        except Exception as exc:
            active_targets = self._mock_recorder_targets()
            source_status = f"Recorder source: Fallback standard map ({len(active_targets)} nodes) - {exc}"

        tuning_columns = self._build_recorder_tuning_columns(active_targets)

        self.recorder_vars = {}
        for tuning_label in RECORDER_TUNING_LABELS:
            for stream_label in tuning_columns.get(tuning_label, []):
                initial_value = previous_values.get(stream_label, True) if preserve_selection else True
                self.recorder_vars[stream_label] = tk.BooleanVar(value=bool(initial_value))

        self._recorder_targets = active_targets
        self._recorder_tuning_columns = tuning_columns
        self._recorder_source_status = source_status

        print(source_status)
        if announce:
            try:
                self._update_status(source_status)
            except Exception:
                pass

    def _refresh_recorders(self):
        """Re-pull recorder targets (ATA-first) and redraw the inline panel if open.

        This is an active reload operation, not just a visual repaint.
        """
        self._load_recorders_from_ata_or_fallback(preserve_selection=True, announce=True)

        if getattr(self, "_recorder_inline_panel", None) is not None and self._recorder_inline_panel.winfo_exists():
            try:
                self._recorder_inline_panel.destroy()
            except Exception:
                pass
            self._recorder_inline_panel = None
            self.recorders_inline_btn.configure(text="Recorder Panel")
            self._toggle_inline_recorders()
        else:
            self._set_urgent_status("Recorder targets refreshed")

    def _selected_recorders_dict(self):
        """Return selected recorder targets in hashpipe-target dictionary format."""
        selected = {}
        for stream_label, var in (self.recorder_vars or {}).items():
            try:
                if not bool(var.get()):
                    continue
            except Exception:
                continue

            stream_text = str(stream_label or "").strip().lower()
            if "." not in stream_text:
                continue
            node_name, stream_suffix = stream_text.rsplit(".", 1)
            try:
                stream_value = int(stream_suffix)
            except ValueError:
                continue
            if stream_value not in (0, 1):
                continue
            selected.setdefault(node_name, [])
            if stream_value not in selected[node_name]:
                selected[node_name].append(stream_value)

        for node_name in list(selected.keys()):
            selected[node_name] = sorted(selected[node_name])

        return selected

    def _select_all_recorders(self):
        """Check all currently visible recorder stream checkboxes in the panel."""
        try:
            for stream_label, var in (self.recorder_vars or {}).items():
                try:
                    var.set(True)
                except Exception:
                    continue
            selected_nodes = len(self._selected_recorders_dict())
            self._set_urgent_status(f"Recorder streams selected across {selected_nodes} nodes")
        except Exception:
            pass

    def _build_recorder_selection_grid(self, parent):
        """Build recorder stream selection grid in 4 tuning columns (LoA/LoB/LoC/LoD)."""
        self._recorder_checkbox_widgets = []
        recorder_container = ctk.CTkFrame(parent, fg_color="transparent")
        recorder_container.pack(fill="both", expand=True, padx=10, pady=(0,8))

        recorder_grid = ctk.CTkFrame(recorder_container, fg_color="transparent")
        recorder_grid.pack(anchor="nw", fill="both", expand=True)

        cols = len(RECORDER_TUNING_LABELS)
        for col_index in range(cols):
            recorder_grid.grid_columnconfigure(col_index, minsize=170, weight=1)

        for col_index, tuning_label in enumerate(RECORDER_TUNING_LABELS):
            column_frame = ctk.CTkFrame(recorder_grid, fg_color="transparent")
            column_frame.grid(row=0, column=col_index, sticky="n", padx=8, pady=0)

            ctk.CTkLabel(
                column_frame,
                text=tuning_label,
                font=TITLE_FONT,
                text_color=TITLE_TEXT_COLOR,
            ).pack(anchor="center", pady=(0, 4))

            ctk.CTkFrame(column_frame, height=1, fg_color=UI_BORDER_COLOR).pack(fill="x", pady=(0, 6))

            for stream_label in self._recorder_tuning_columns.get(tuning_label, []):
                var = self.recorder_vars.get(stream_label)
                if var is None:
                    var = tk.BooleanVar(value=True)
                    self.recorder_vars[stream_label] = var

                checkbox = ctk.CTkCheckBox(
                    column_frame,
                    text=stream_label,
                    variable=var,
                    font=SMALL_FONT,
                    corner_radius=CHECKBOX_CORNER_RADIUS,
                    text_color=NORMAL_TEXT_COLOR,
                    fg_color="#009E73",
                    hover_color="#009E73",
                    border_color="#009E73",
                    checkbox_width=18,
                    checkbox_height=18,
                )
                if self._is_running:
                    try:
                        checkbox.configure(state="disabled")
                    except Exception:
                        pass

                checkbox.pack(anchor="w", pady=2)
                self._recorder_checkbox_widgets.append(checkbox)

    def _toggle_inline_recorders(self):
        """Toggle the centered inline recorder panel used for recorder selection."""
        if getattr(self, "_recorder_inline_panel", None) is not None and self._recorder_inline_panel.winfo_exists():
            try:
                self._recorder_inline_panel.destroy()
            except Exception:
                pass
            self._recorder_inline_panel = None
            self.recorders_inline_btn.configure(text="Recorder Panel")
            return

        try:
            self._load_recorders_from_ata_or_fallback(preserve_selection=True, announce=True)

            panel_w, panel_h = GUI_POPUP_SIZES.get("recorders", (360, 440))
            panel = ctk.CTkFrame(
                self,
                corner_radius=10,
                border_width=1,
                border_color=UI_BORDER_COLOR,
                fg_color=UI_PANEL_COLOR,
                width=panel_w,
                height=panel_h,
            )

            try:
                self.update_idletasks()
                win_w = max(self.winfo_width(), GUI_WINDOW_SIZE[0])
                win_h = max(self.winfo_height(), GUI_WINDOW_SIZE[1])
            except Exception:
                win_w, win_h = GUI_WINDOW_SIZE

            # Place Recorder Panel to the right of the Antenna Panel when available.
            if getattr(self, "_antenna_inline_panel", None) is not None and self._antenna_inline_panel.winfo_exists():
                try:
                    antenna_x = self._antenna_inline_panel.winfo_x()
                    antenna_y = self._antenna_inline_panel.winfo_y()
                    antenna_w = self._antenna_inline_panel.winfo_width()
                    place_x = min(max(8, antenna_x + antenna_w + 10), max(8, win_w - panel_w - 8))
                    place_y = min(max(8, antenna_y), max(8, win_h - panel_h - 8))
                    panel.place(x=place_x, y=place_y)
                except Exception:
                    panel.place(relx=0.5, rely=0.5, anchor="center")
            else:
                panel.place(relx=0.5, rely=0.5, anchor="center")

            try:
                panel.pack_propagate(False)
            except Exception:
                pass
            try:
                panel.grid_propagate(False)
            except Exception:
                pass
            try:
                panel.configure(border_width=2, border_color="#888888")
            except Exception:
                pass
            try:
                panel.lift()
                panel.focus_set()
            except Exception:
                pass

            self._recorder_inline_panel = panel

            content = ctk.CTkFrame(panel, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=8, pady=8)

            inline_header = ctk.CTkFrame(content, fg_color="transparent")
            inline_header.pack(fill="x", padx=4, pady=(2,6))
            ctk.CTkLabel(
                inline_header,
                text="Recorder Panel (hashpipe targets)",
                font=TITLE_FONT,
                text_color=TITLE_TEXT_COLOR
            ).pack(side="left", anchor="w")

            self._build_recorder_selection_grid(content)

            source_status_row = ctk.CTkFrame(content, fg_color="transparent")
            source_status_row.pack(fill="x", padx=4, pady=(2, 4))
            ctk.CTkLabel(
                source_status_row,
                text=self._recorder_source_status,
                font=SMALL_FONT,
                text_color=UI_MUTED_TEXT_COLOR,
                wraplength=410,
                justify="left",
            ).pack(anchor="w")

            footer = ctk.CTkFrame(content, fg_color="transparent")
            footer.pack(side="bottom", fill="x", padx=4, pady=(6,2))

            right_actions = ctk.CTkFrame(footer, fg_color="transparent")
            right_actions.pack(side="right")

            select_all_btn = ctk.CTkButton(
                right_actions,
                text="Select All",
                command=self._select_all_recorders,
                width=100,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            select_all_btn.pack(side="left", padx=(0,6))
            if self._is_running:
                try:
                    select_all_btn.configure(state="disabled")
                except Exception:
                    pass

            refresh_btn = ctk.CTkButton(
                right_actions,
                text="Refresh",
                command=self._refresh_recorders,
                width=100,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            refresh_btn.pack(side="left", padx=(0,6))
            if self._is_running:
                try:
                    refresh_btn.configure(state="disabled")
                except Exception:
                    pass

            ctk.CTkButton(
                right_actions,
                text="Close",
                command=self._toggle_inline_recorders,
                width=100,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            ).pack(side="left")

            self.recorders_inline_btn.configure(text="Hide Recorder Panel")
            self._update_status("Recorder panel opened")
        except Exception as exc:
            self._update_status(f"ERROR: Failed to open inline recorder panel: {exc}")
            messagebox.showerror("Inline Recorder Error", f"Failed to show inline recorder panel: {exc}")

    def _select_active_antennas(self):
        """Check all active antennas while leaving inactive/disabled entries unchanged."""
        try:
            for name, var in (self.ant_vars or {}).items():
                # Determine visuals/state for this antenna
                is_active, observing_status, base_color, border_color, is_disabled = self._get_antenna_visuals(name)
                # Only check antennas that are active and not disabled
                try:
                    if is_active and not is_disabled:
                        var.set(True)
                except Exception:
                    pass
            # Keep global REMOVE_ANT in sync with the new selections
            try:
                self._update_global_REMOVE_ANT()
            except Exception:
                pass
        except Exception:
            pass

    def _toggle_inline_antennas(self):
        """Toggle the centered inline antenna panel used for antenna selection.

        The antenna selector is intentionally inline-only.
        Ubuntu didn't like the popup, but it seems happy with an 'inline' panel
        """

        if getattr(self, "_antenna_inline_panel", None) is not None and self._antenna_inline_panel.winfo_exists():
            # Close inline panel
            try:
                self._antenna_inline_panel.destroy()
            except Exception:
                pass
            self._antenna_inline_panel = None
            # Clear stored inline content reference and sync global remove list
            self._antenna_inline_content = None
            try:
                self._update_global_REMOVE_ANT()
            except Exception:
                pass
            self.antennas_inline_btn.configure(text="Antenna Panel")
            return

        # Build inline panel below the config area
        try:
            # Define the panel's size
            panel_w, panel_h = GUI_POPUP_SIZES.get("antennas", (420, 520))
            panel = ctk.CTkFrame(
                self,
                corner_radius=10,
                border_width=1,
                border_color=UI_BORDER_COLOR,
                fg_color=UI_PANEL_COLOR,
                width=panel_w,
                height=panel_h,
            )

            try:
                self.update_idletasks()
                win_w = max(self.winfo_width(), GUI_WINDOW_SIZE[0])
                win_h = max(self.winfo_height(), GUI_WINDOW_SIZE[1])
            except Exception:
                win_w, win_h = GUI_WINDOW_SIZE

            # x = max(8, (win_w - popup_w) // 2)
            # y = max(8, (win_h - popup_h) // 2)
            # Center the inline panel in the main window so it is reliably visible

            panel.place(relx=0.5, rely=0.5, anchor="center")
            # Prevent child widgets from forcing the panel to resize
            # Used to flicker in size when refreshing, this prevents that
            try:
                panel.pack_propagate(False)
            except Exception:
                pass
            try:
                panel.grid_propagate(False)
            except Exception:
                pass
            # Make border slightly more visible so the inline panel stands out.
            try:
                panel.configure(border_width=2, border_color="#888888")
            except Exception:
                pass
            # Ensure the inline panel is on top of the main GUI so it's visible
            try:
                panel.lift()
                panel.focus_set()
            except Exception:
                pass
            panel.update_idletasks()
            # Log visibly so users know the panel was created.
            try:
                self._update_status("Antennas panel opened")
            except Exception:
                print("Antennas panel opened")
            self._antenna_inline_panel = panel
            content = ctk.CTkFrame(panel, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=8, pady=8)
            # Keep reference to inline content so refresh can rebuild it
            self._antenna_inline_content = content
            # Header with a refresh and close button so the inline panel can always be refreshed/hidden
            inline_header = ctk.CTkFrame(content, fg_color="transparent")
            inline_header.pack(fill="x", padx=4, pady=(2,6))
            ctk.CTkLabel(
                inline_header,
                text="Antenna Panel (Press Refresh and Choose Antennas)", # This is the title of the Antenna panel
                font=TITLE_FONT,
                text_color=TITLE_TEXT_COLOR
            ).pack(side="left")

            # Build the legend for the Antenna panel
            self._build_antenna_legend(content)
            self._build_antenna_selection_grid(content)
            try:
                self._update_global_REMOVE_ANT()
            except Exception:
                pass

            # Put buttons at the bottom of the panel
            footer = ctk.CTkFrame(content, fg_color="transparent")
            footer.pack(side="bottom", fill="x", padx=4, pady=(6,2))

            right_actions = ctk.CTkFrame(footer, fg_color="transparent")
            right_actions.pack(side="right")

            # Button to select all active antennas (leaves disabled ants unchecked)
            select_active_btn = ctk.CTkButton(
                right_actions,
                text="Select All Active",
                command=self._select_active_antennas,
                width=120,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            select_active_btn.pack(side="left", padx=(0,6))
            if self._is_running:
                try:
                    select_active_btn.configure(state="disabled")
                except Exception:
                    pass

            # Refresh antennas from Notion
            refresh_btn = ctk.CTkButton(
                right_actions,
                text="Refresh from Notion",
                command=self._refresh_antennas_from_notion,
                width=GUI_BUTTON_SIZES["refresh_antennas"],
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            refresh_btn.pack(side="left")
            if self._is_running:
                try:
                    refresh_btn.configure(state="disabled")
                except Exception:
                    pass

            # Close the antenna panel
            ctk.CTkButton(
                right_actions,
                text="Close",
                command=self._toggle_inline_antennas,
                width=100,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            ).pack(side="left", padx=(6,0))

            self.antennas_inline_btn.configure(text="Hide Antenna Panel")
        except Exception as exc:
            self._update_status(f"ERROR: Failed to open inline antenna panel: {exc}")
            messagebox.showerror("Inline Antennas Error", f"Failed to show inline antenna panel: {exc}")


    def _set_config_controls_enabled(self, enabled: bool):
        """Lock or unlock lockable widgets when running to prevent errors"""
        state = "normal" if enabled else "disabled"

        for widget in self._lockable_widgets:
            try:
                widget.configure(state=state)
            except Exception:
                continue

        if self._queue_wait_adv_chk is not None:
            try:
                self._queue_wait_adv_chk.configure(state=state)
            except Exception:
                pass

        if self._ods_push_btn is not None:
            try:
                self._ods_push_btn.configure(state=state)
            except Exception:
                pass

        if self._target_obs_time_override_chk is not None:
            try:
                self._target_obs_time_override_chk.configure(state=state)
            except Exception:
                pass

        # Keep Advanced Options window enabled during runs so auto-stop scheduling remains available.
        try:
            self.advanced_options_btn.configure(state="normal")
        except Exception:
            pass

        for widget in self._antenna_checkbox_widgets:
            try:
                widget.configure(state=state)
            except Exception:
                continue

        for widget in self._recorder_checkbox_widgets:
            try:
                widget.configure(state=state)
            except Exception:
                continue

    def _set_running_state(self, running: bool):
        """Set running state and update dependent control/schedule UI state."""
        self._is_running = running
        self._set_config_controls_enabled(not running)
        self._update_scheduled_stop_display()

    def _set_start_scheduled_state(self, scheduled: bool):
        """Track whether a delayed start is armed and lock config controls accordingly."""
        self._is_start_scheduled = bool(scheduled)
        if self._is_running:
            return
        self._set_config_controls_enabled(not self._is_start_scheduled)
        self._update_scheduled_start_display()

    def _set_stop_resume_buttons(self, stop_requested: bool):
        """Show either Stop or Resume button to match requested stop state."""
        if stop_requested:
            if self.stop_btn.winfo_manager():
                self.stop_btn.pack_forget()
            if not self.resume_btn.winfo_manager():
                self.resume_btn.pack(side="left", padx=8, before=self.abort_btn)
        else:
            if self.resume_btn.winfo_manager():
                self.resume_btn.pack_forget()
            if not self.stop_btn.winfo_manager():
                self.stop_btn.pack(side="left", padx=8, before=self.abort_btn)

    def _start_run_state_monitor(self):
        """Start polling worker-thread state to detect run completion."""
        if self._run_state_poll_id is not None:
            return
        self._poll_run_state()

    def _poll_run_state(self):
        """Poll worker-thread health and reset UI state when run ends."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._run_state_poll_id = self.after(500, self._poll_run_state)
            return

        self._run_state_poll_id = None
        if self._is_running:
            self._set_running_state(False)
            self._set_stop_resume_buttons(stop_requested=False)
            self._cancel_scheduled_stop(show_status=False)
            self._cancel_pending_stop_after()

    def _parse_stop_after_seconds(self, raw_value: str) -> int:
        """Parse 'Stop After' commands such as '8h', '1h 30m', or integer seconds."""
        text = str(raw_value or "").strip().lower()
        if not text:
            raise ValueError("Stop After value cannot be empty.")

        if re.fullmatch(r"\d+", text):
            seconds = int(text)
            if seconds <= 0:
                raise ValueError("Stop After must be greater than zero.")
            return seconds

        unit_seconds = { # Define common inputs and their corresponding seconds
            "s": 1,
            "sec": 1,
            "secs": 1,
            "second": 1,
            "seconds": 1,
            "m": 60,
            "min": 60,
            "mins": 60,
            "minute": 60,
            "minutes": 60,
            "h": 3600,
            "hr": 3600,
            "hrs": 3600,
            "hour": 3600,
            "hours": 3600,
            "d": 86400,
            "day": 86400,
            "days": 86400,
        }

        matches = re.findall(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)", text)
        consumed = "".join(f"{value}{unit}" for value, unit in matches)
        if not matches or consumed.replace(" ", "") != re.sub(r"\s+", "", text):
            raise ValueError("Use formats like '8 hours', '1h 30m', '1.5 hours', or seconds as an integer (e.g., 28800).")

        total_seconds = 0
        for value_text, unit in matches:
            unit_key = unit.strip().lower()
            if unit_key not in unit_seconds:
                raise ValueError(f"Unsupported duration unit: {unit}")
            total_seconds += float(value_text) * unit_seconds[unit_key]

        total_seconds = int(total_seconds)
        if total_seconds <= 0:
            raise ValueError("Stop After must be greater than zero.")
        return total_seconds

    def _parse_start_after_seconds(self, raw_value: str) -> int:
        """Parse 'Start After' commands such as '4h', '1h 30m', or integer seconds."""
        try:
            return self._parse_stop_after_seconds(raw_value)
        except ValueError as exc:
            raise ValueError(str(exc).replace("Stop After", "Start After")) from exc

    def _set_pending_start_after(self, duration_seconds: int, brief_description: str):
        """Store a pending Start-After delay to apply on the next Run action."""
        self._cancel_scheduled_start(show_status=False)
        self._cancel_pending_start_after()

        if duration_seconds is None or duration_seconds <= 0:
            self._set_urgent_status("Invalid start delay", color=ALERT_TEXT_COLOR)
            return

        self._pending_start_after_duration = max(1, int(duration_seconds))
        self._pending_start_after_brief = str(brief_description or "")
        self._set_urgent_status(f"Start After set: {self._pending_start_after_brief}")
        self._update_status(
            f"Start After {self._pending_start_after_duration}s configured: "
            "next Run will begin after this delay"
        )
        self._update_start_controls_state()

    def _cancel_pending_start_after(self):
        """Clear any pending Start-After delay not yet armed by Run."""
        self._pending_start_after_duration = None
        self._pending_start_after_brief = ""
        self._update_start_controls_state()

    def _schedule_start_request(self, delay_seconds: float, run_configuration: dict, remove_ant_list: list, brief: str):
        """Arm delayed observation start and store immutable run configuration."""
        if delay_seconds is None or delay_seconds <= 0:
            raise ValueError("Start delay must be greater than zero")

        self._cancel_scheduled_start(show_status=False)

        delay_seconds = max(float(delay_seconds), 0.001)
        delay_ms = int(delay_seconds * 1000)
        local_target = datetime.now().astimezone() + timedelta(seconds=delay_seconds)

        self._scheduled_start_run_configuration = dict(run_configuration)
        self._scheduled_start_remove_ant_list = list(remove_ant_list or [])
        self._scheduled_start_brief = str(brief or self._format_duration_brief(delay_seconds))
        self._scheduled_start_description = (
            f"Start After {self._scheduled_start_brief} "
            f"(at {local_target.strftime('%Y-%m-%d %H:%M:%S %Z')})"
        )
        self._scheduled_start_target_time = local_target
        self._scheduled_start_after_id = self.after(delay_ms, self._execute_scheduled_start)
        self._set_start_scheduled_state(True)

        self._set_urgent_status(f"Start scheduled: {self._scheduled_start_brief}")
        self._update_status(f"Observation start scheduled: {self._scheduled_start_description}")
        self._update_start_controls_state()

    def _cancel_scheduled_start(self, show_status: bool = True):
        """Cancel any armed delayed-start callback and reset start metadata."""
        if self._scheduled_start_after_id is not None:
            try:
                self.after_cancel(self._scheduled_start_after_id)
            except Exception:
                pass

        self._scheduled_start_after_id = None
        self._scheduled_start_target_time = None
        self._scheduled_start_brief = ""
        self._scheduled_start_description = ""
        self._scheduled_start_run_configuration = None
        self._scheduled_start_remove_ant_list = []
        self._set_start_scheduled_state(False)
        if show_status:
            self._set_urgent_status("Scheduled start cleared")
            self._update_status("Scheduled start cleared")
        self._update_start_controls_state()

    def _execute_scheduled_start(self):
        """Start the observation run when delayed-start timer fires."""
        run_configuration = self._scheduled_start_run_configuration
        remove_ant_list = list(self._scheduled_start_remove_ant_list or [])
        description = self._scheduled_start_description or "scheduled start"

        self._scheduled_start_after_id = None
        self._scheduled_start_target_time = None
        self._scheduled_start_brief = ""
        self._scheduled_start_description = ""
        self._scheduled_start_run_configuration = None
        self._scheduled_start_remove_ant_list = []
        self._set_start_scheduled_state(False)
        self._update_start_controls_state()

        if self._is_running:
            self._set_urgent_status("Scheduled start skipped (already running)", color=ALERT_TEXT_COLOR)
            self._update_status(f"Scheduled start skipped (already running): {description}")
            return

        if not isinstance(run_configuration, dict):
            self._set_urgent_status("Scheduled start failed", color=ALERT_TEXT_COLOR)
            self._update_status("Scheduled start failed: missing run configuration")
            return

        self._set_urgent_status(f"Auto-starting: {description}")
        self._update_status(f"Scheduled start triggered: {description}")
        self._start_observation_run(run_configuration, remove_ant_list)

    def _update_scheduled_start_display(self):
        """Refresh the one-line scheduled-start display using local wall time."""
        if self._scheduled_start_after_id is None or self._scheduled_start_target_time is None:
            self.scheduled_start_display.set("")
            return

        try:
            local_str = self._scheduled_start_target_time.strftime("%H:%M")
            self.scheduled_start_display.set(f"Start Scheduled at {local_str} local")
        except Exception:
            self.scheduled_start_display.set(f"Start Scheduled: {self._scheduled_start_brief}")

    def _on_schedule_start_after(self):
        """Handle Start-After UI action by storing a delay for the next Run."""
        if self._is_running:
            self._set_urgent_status("Cannot schedule Start After while running", color=ALERT_TEXT_COLOR)
            messagebox.showwarning("Already Running", "Start delay can only be configured before a run begins.")
            return

        if self._is_start_scheduled:
            self._set_urgent_status("A delayed start is already armed", color=ALERT_TEXT_COLOR)
            messagebox.showwarning("Start Already Scheduled", "A delayed start is already armed. Clear it first.")
            return

        raw_value = self.start_after_value.get().strip()
        if not raw_value:
            return

        try:
            seconds = self._parse_start_after_seconds(raw_value)
        except ValueError as exc:
            self._set_urgent_status("Invalid Start After value", color=ALERT_TEXT_COLOR)
            messagebox.showerror("Start After Error", str(exc))
            return

        brief = self._format_duration_brief(seconds)
        full_desc = f"Next Run will start {seconds} seconds ({brief}) after you confirm Run."
        self._show_schedule_confirmation(
            "Start After",
            raw_value,
            brief,
            full_desc,
            lambda: self._set_pending_start_after(seconds, brief),
        )

    def _on_clear_scheduled_start(self):
        """Clear pending or armed delayed-start state after confirmation."""
        has_pending = self._pending_start_after_duration is not None
        has_armed = self._scheduled_start_after_id is not None
        if not has_pending and not has_armed:
            self._set_urgent_status("No scheduled start to clear", color=ALERT_TEXT_COLOR)
            return

        if has_armed:
            brief = self._scheduled_start_brief or "configured"
            full_desc = self._scheduled_start_description or "Delayed start is armed"
        else:
            brief = self._pending_start_after_brief or "configured"
            full_desc = (
                "Pending: next Run will start after "
                f"{self._pending_start_after_duration} seconds"
            )

        self._show_schedule_confirmation(
            "Clear Scheduled Start",
            brief,
            brief,
            f"This will clear the delayed start: {full_desc}",
            lambda: (self._cancel_scheduled_start(show_status=True), self._cancel_pending_start_after()),
        )

    def _update_start_controls_state(self):
        """Enable/disable Start-After controls based on pending/armed state."""
        has_pending = self._pending_start_after_duration is not None
        has_armed = self._scheduled_start_after_id is not None
        has_any_start_delay = has_pending or has_armed

        if self._schedule_start_after_btn is not None:
            try:
                self._schedule_start_after_btn.configure(state="disabled" if has_any_start_delay else "normal")
            except Exception:
                pass

        if self._clear_scheduled_start_btn is not None:
            try:
                self._clear_scheduled_start_btn.configure(state="normal" if has_any_start_delay else "disabled")
            except Exception:
                pass

        if self._start_after_entry is not None:
            try:
                self._start_after_entry.configure(state="normal")
            except Exception:
                pass

        if has_armed:
            message = f"Delayed start armed: {self._scheduled_start_description or self._scheduled_start_brief}"
        elif has_pending:
            message = (
                "Delayed start pending: next Run begins after "
                f"{self._pending_start_after_brief or str(self._pending_start_after_duration) + 's'}"
            )
        else:
            message = "No start delay configured."
        self.advanced_start_status.set(message)
        self._update_scheduled_start_display()

    def _start_observation_run(self, run_configuration: dict, remove_ant_list: list):
        """Start observation immediately from a prepared run configuration."""
        if self._antenna_load_blocked:
            warning = (
                "Observation start blocked because SNAPobs fallback antenna loading failed. "
                f"{ANTENNA_LOAD_FATAL_MESSAGE or 'Unknown antenna source failure.'}"
            )
            print(f"FATAL ANTENNA SOURCE ERROR: {ANTENNA_LOAD_FATAL_MESSAGE or 'Unknown antenna source failure.'}")
            self._set_urgent_status("Observation blocked: antenna source failure", color=ALERT_TEXT_COLOR)
            self._update_status(f"ERROR: {warning}")
            messagebox.showerror("Antenna Source Error", warning)
            return

        self._set_urgent_status("Script Running...")
        self._set_stop_resume_buttons(stop_requested=False)

        try:
            module = self._load_observe_module(raise_on_error=True)
            self._worker_thread = module.configure_and_run(run_configuration)
            self._set_running_state(True)
            # Activate any pending "Stop After" or "Stop At" settings now that the run has started
            self._activate_pending_stop_after()
            self._activate_pending_stop_at()
            self._start_run_state_monitor()
            # Print antenna removal information for logging and quick visibility now that the run has started.
            try:
                global REMOVE_ANT
                print(f"Global REMOVE_ANT: {REMOVE_ANT}")
                self._update_status(f"Global REMOVE_ANT: {', '.join(REMOVE_ANT) if REMOVE_ANT else '(none)'}")

                print(f"GUI-selected REMOVE_ANT for this run: {remove_ant_list}")
                self._update_status(f"GUI-selected REMOVE_ANT for this run: {', '.join(remove_ant_list) if remove_ant_list else '(none)'}")

                pol_issues = _collect_pol_hardware_issues(self.observing_status_by_antenna or {})
                x_pol_issues = pol_issues["x_pol_issues"]
                y_pol_issues = pol_issues["y_pol_issues"]
                print(f"Antennas marked '{STATUS_XPOL_HARDWARE_ISSUE}': {x_pol_issues}")
                print(f"Antennas marked '{STATUS_YPOL_HARDWARE_ISSUE}': {y_pol_issues}")
                self._update_status(f"X-pol hardware issues: {', '.join(x_pol_issues) if x_pol_issues else '(none)'}")
                self._update_status(f"Y-pol hardware issues: {', '.join(y_pol_issues) if y_pol_issues else '(none)'}")
            except Exception:
                pass
            messagebox.showinfo("Started", "Observation has begun. Please monitor for updates and/or errors.")
        except Exception as exc:
            self._set_running_state(False)
            self._report_error("Failed to start observation", type(exc), exc, exc.__traceback__)

    def _resolve_timezone_info(self, raw_timezone: str):
        """Resolve timezone aliases or IANA names into a ZoneInfo object and name."""
        tz_text = str(raw_timezone or "").strip()
        if not tz_text:
            raise ValueError("Timezone is required. Use UTC, PST/PDT, MST/MDT, CST/CDT, EST/EDT, or IANA format like America/Los_Angeles.")

        aliases = {
            "UTC": "UTC",
            "GMT": "UTC",
            "PST": "America/Los_Angeles",
            "PDT": "America/Los_Angeles",
            "MST": "America/Denver",
            "MDT": "America/Denver",
            "CST": "America/Chicago",
            "CDT": "America/Chicago",
            "EST": "America/New_York",
            "EDT": "America/New_York",
        }
        zone_name = aliases.get(tz_text.upper(), tz_text)
        try:
            return ZoneInfo(zone_name), zone_name
        except Exception as exc:
            raise ValueError(
                f"Unknown timezone '{tz_text}'. Check spelling. Valid: UTC, PST/PDT, MST/MDT, CST/CDT, EST/EDT, or IANA like America/Los_Angeles."
            ) from exc

    def _set_pending_stop_after(self, duration_seconds: int, brief_description: str):
        """Store a pending 'Stop After' request to activate when a run begins."""
        # First cancel any existing scheduled/pending stops to avoid conflicts
        self._cancel_scheduled_stop(show_status=False)
        self._cancel_pending_stop_after()

        # Validate inputs
        if duration_seconds is None or duration_seconds <= 0:
            self._set_urgent_status("Invalid stop duration", color=ALERT_TEXT_COLOR)
            return

        self._pending_stop_after_duration = max(1, int(duration_seconds))  # Ensure at least 1 second
        self._pending_stop_after_brief = str(brief_description or "")
        self._set_urgent_status(f"Stop After set (will start when run begins): {brief_description}")
        self._update_status(f"Stop After {self._pending_stop_after_duration}s scheduled: will activate when observation begins")
        self._update_schedule_controls_state()

    def _activate_pending_stop_after(self):
        """Activate a pending Stop-After setting now that observation is running."""
        if self._pending_stop_after_duration is None:
            return

        duration = self._pending_stop_after_duration
        brief = self._pending_stop_after_brief or f"{duration}s"
        full_desc = f"in {duration} seconds (from start of observation)"

        # Clear pending state
        self._pending_stop_after_duration = None
        self._pending_stop_after_brief = None

        # Schedule the stop request
        self._schedule_stop_request(duration, f"Stop After {full_desc}", brief, schedule_type="after")

    def _cancel_pending_stop_after(self):
        """Clear any pending Stop-After request not yet activated."""
        self._pending_stop_after_duration = None
        self._pending_stop_after_brief = None
        self._update_schedule_controls_state()

    def _set_pending_stop_at(self, hour: int, minute: int, second: int, timezone_str: str, brief_description: str):
        """Store a pending Stop-At time to resolve and activate when run starts."""
        # First cancel any existing scheduled/pending stops to avoid conflicts
        self._cancel_scheduled_stop(show_status=False)
        self._cancel_pending_stop_after()
        self._cancel_pending_stop_at()

        # Validate inputs
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            self._set_urgent_status("Invalid stop time values", color=ALERT_TEXT_COLOR)
            return

        self._pending_stop_at_hour = int(hour)
        self._pending_stop_at_minute = int(minute)
        self._pending_stop_at_second = int(second)
        self._pending_stop_at_timezone = str(timezone_str or "")
        self._pending_stop_at_brief = str(brief_description or "")
        self._set_urgent_status(f"Stop At set (will calculate when run begins): {brief_description}")
        self._update_status(f"Stop At {brief_description} pending: will calculate delay when observation begins")
        self._update_schedule_controls_state()

    def _activate_pending_stop_at(self):
        """Activate a pending Stop-At setting by recalculating delay from current time."""
        if self._pending_stop_at_hour is None:
            return

        try:
            tzinfo, zone_name = self._resolve_timezone_info(self._pending_stop_at_timezone)
            hour = self._pending_stop_at_hour
            minute = self._pending_stop_at_minute
            second = self._pending_stop_at_second
            brief = self._pending_stop_at_brief or f"{hour:02d}:{minute:02d}:{second:02d} {zone_name}"

            # Recalculate target time based on current time
            now_local = datetime.now(tzinfo)
            target_local = now_local.replace(hour=hour, minute=minute, second=second, microsecond=0)

            if target_local <= now_local:
                target_local = target_local + timedelta(days=1)

            now_utc = datetime.now(timezone.utc)
            target_utc = target_local.astimezone(timezone.utc)
            delay_seconds = (target_utc - now_utc).total_seconds()

            if delay_seconds <= 0:
                delay_seconds = 1  # Failsafe: at least schedule for 1 second from now

            local_target = target_utc.astimezone()
            full_desc = (
                f"Stop At {target_local.strftime('%Y-%m-%d %H:%M:%S')} {zone_name} "
                f"(local {local_target.strftime('%Y-%m-%d %H:%M:%S %Z')})"
            )

            # Clear pending state
            self._cancel_pending_stop_at()

            # Schedule the stop request
            self._schedule_stop_request(delay_seconds, full_desc, brief, schedule_type="at")
        except Exception as exc:
            self._set_urgent_status(f"Error activating pending Stop At command: {exc}", color=ALERT_TEXT_COLOR)
            self._update_status(f"ERROR: Failed to activate pending Stop At command: {exc}")
            self._cancel_pending_stop_at()

    def _cancel_pending_stop_at(self):
        """Clear any pending Stop-At request not yet activated."""
        self._pending_stop_at_hour = None
        self._pending_stop_at_minute = None
        self._pending_stop_at_second = None
        self._pending_stop_at_timezone = None
        self._pending_stop_at_brief = None
        self._update_schedule_controls_state()

    def _on_clear_scheduled_stop(self):
        """Show confirmation and clear active/pending scheduled stop settings."""
        # Check if there's an active scheduled stop
        if self._scheduled_stop_after_id is None and self._pending_stop_after_duration is None and self._pending_stop_at_hour is None:
            self._set_urgent_status("No scheduled stop to clear", color=ALERT_TEXT_COLOR)
            return

        # Determine what to show in the confirmation
        if self._pending_stop_after_duration is not None:
            brief = self._pending_stop_after_brief or "unknown"
            full_desc = f"Pending: will stop in {self._pending_stop_after_duration} seconds after run starts"
        elif self._pending_stop_at_hour is not None:
            brief = self._pending_stop_at_brief or "unknown"
            full_desc = f"Pending: will stop at {brief}"
        else:
            brief = self._scheduled_stop_brief or "unknown"
            full_desc = self._scheduled_stop_description or "unknown"

        self._show_schedule_confirmation(
            "Clear Scheduled Stop",
            brief,
            brief,
            f"This will clear the scheduled stop: {full_desc}",
            lambda: (self._cancel_scheduled_stop(show_status=True), self._cancel_pending_stop_after(), self._cancel_pending_stop_at())
        )

    def _cancel_scheduled_stop(self, show_status: bool = True):
        """Cancel any active scheduled auto-stop callback and reset schedule metadata."""
        if self._scheduled_stop_after_id is not None:
            try:
                self.after_cancel(self._scheduled_stop_after_id)
            except Exception:
                pass
        self._scheduled_stop_after_id = None
        self._scheduled_stop_description = ""
        self._scheduled_stop_brief = ""
        self._scheduled_stop_type = None
        self._scheduled_stop_target_time = None
        if show_status:
            self._set_urgent_status("Scheduled stop cleared")
            self._update_status("Scheduled stop cleared")
        self._update_schedule_controls_state()
        self._update_scheduled_stop_display()

    def _schedule_stop_request(self, delay_seconds: float, description: str, brief: str, schedule_type: str = None):
        """Schedule a delayed stop-after-scan request and update schedule status fields."""
        try:
            # Validate inputs
            if delay_seconds is None or delay_seconds < 0:
                raise ValueError("Delay must be non-negative")
            if not description or not brief:
                raise ValueError("Description and brief must be non-empty")

            self._cancel_scheduled_stop(show_status=False)
            delay_seconds = max(float(delay_seconds), 0.001)  # Ensure at least 1ms
            delay_ms = int(delay_seconds * 1000)
            self._scheduled_stop_description = str(description)
            self._scheduled_stop_brief = str(brief)
            self._scheduled_stop_type = schedule_type  # Track whether this is "after" or "at"
            # Calculate and store the target time when the stop will execute
            self._scheduled_stop_target_time = datetime.now().astimezone() + timedelta(seconds=delay_seconds)
            self._scheduled_stop_after_id = self.after(delay_ms, self._execute_scheduled_stop)

            self._set_urgent_status(f"Stop scheduled: {brief}")
            self._update_status(f"Scheduled Stop After This Scan: {description}")
            self._update_schedule_controls_state()
            self._update_scheduled_stop_display()
        except Exception as exc:
            self._set_urgent_status(f"Error scheduling stop: {exc}", color=ALERT_TEXT_COLOR)
            self._update_status(f"ERROR: Failed to schedule stop: {exc}")

    def _execute_scheduled_stop(self):
        """Execute the scheduled stop request when its timer callback is triggered."""
        description = self._scheduled_stop_description or "scheduled request"
        self._scheduled_stop_after_id = None
        self._scheduled_stop_description = ""
        self._scheduled_stop_brief = ""
        self._scheduled_stop_type = None
        self._scheduled_stop_target_time = None

        if not self._is_running:
            self._set_urgent_status("Scheduled stop skipped (not running)", color=ALERT_TEXT_COLOR)
            self._update_status(f"Scheduled stop skipped (not running): {description}")
            self._update_schedule_controls_state()
            self._update_scheduled_stop_display()
            return

        self._update_status(f"Scheduled stop triggered: {description}")
        self._submit_stop_after_scan(trigger_source="scheduled", show_popup=False, reason_detail=description)
        self._update_schedule_controls_state()
        self._update_scheduled_stop_display()

    def _update_scheduled_stop_display(self):
        """Refresh the one-line scheduled-stop display using Pacific/UTC wall times."""
        if not self._is_running or self._scheduled_stop_after_id is None or self._scheduled_stop_target_time is None:
            self.scheduled_stop_display.set("")
            return

        # Convert target time to Pacific local time and UTC.
        try:
            pacific_tz = ZoneInfo("America/Los_Angeles")
            utc_tz = ZoneInfo("UTC")

            # Convert to Pacific and UTC.
            target_pacific = self._scheduled_stop_target_time.astimezone(pacific_tz)
            target_utc = self._scheduled_stop_target_time.astimezone(utc_tz)

            # Format times (HH:MM)
            pacific_str = target_pacific.strftime("%H:%M")
            pacific_abbrev = target_pacific.strftime("%Z")
            utc_str = target_utc.strftime("%H:%M")

            # Display format: "Stop Scheduled at HH:MM PDT/PST / HH:MM UTC"
            self.scheduled_stop_display.set(f"Stop Scheduled at {pacific_str} {pacific_abbrev} / {utc_str} UTC")
        except Exception:
            # Fallback if timezone conversion fails
            self.scheduled_stop_display.set(f"Stop Scheduled: {self._scheduled_stop_brief}")

    def _submit_stop_after_scan(self, trigger_source: str = "manual", show_popup: bool = True, reason_detail: str = "") -> bool:
        """Submit a stop-after-current-scan request through the observing module."""
        if self._observe_module is None:
            if show_popup:
                messagebox.showwarning("No Active Module", "No observe module is currently loaded.")
            self._update_status("Stop request failed: no active observe module loaded")
            return False

        try:
            reason = str(reason_detail or trigger_source or "").strip()
            try:
                self._observe_module.request_stop(reason=reason)
            except TypeError:
                # Fallback for modules that don't yet accept a reason parameter
                self._observe_module.request_stop()
            # Safety: once a stop has been processed, clear any future auto-stop
            # state so it cannot affect a later user/session.
            self._cancel_scheduled_stop(show_status=False)
            self._cancel_pending_stop_after()
            self._set_stop_resume_buttons(stop_requested=True)
            if trigger_source == "manual":
                urgent_msg = "Stop Requested..."
            else:
                urgent_msg = f"Stop Requested ({reason})" if reason else f"Stop Requested ({trigger_source})"
            self._set_urgent_status(urgent_msg)
            self._update_status(f"Stop requested after this scan: ({trigger_source}) {reason_detail}".rstrip())
            if show_popup:
                messagebox.showinfo("Stop", "Stop requested. Observation will stop after the current scan.")
            return True
        except Exception as exc:
            self._set_urgent_status("Stop request failed", color=ALERT_TEXT_COLOR)
            self._update_status(f"Stop request failed ({trigger_source}): {exc}")
            if show_popup:
                messagebox.showerror("Error", f"Stop failed: {exc}")
            return False

    def _on_schedule_stop_after(self):
        """Handle Stop-After UI action, validate input, and stage/schedule request."""
        # Check if something is already scheduled and warn the user
        if self._scheduled_stop_after_id is not None or self._pending_stop_after_duration is not None or self._pending_stop_at_hour is not None:
            existing_brief = self._scheduled_stop_brief or self._pending_stop_after_brief or self._pending_stop_at_brief or "unknown"
            self._set_urgent_status(f"A stop is already scheduled: {existing_brief}", color=ALERT_TEXT_COLOR)
            messagebox.showwarning(
                "Stop Already Scheduled",
                f"A stop is already scheduled ({existing_brief}). Please clear it first before scheduling a new one."
            )
            return

        raw_value = self.stop_after_value.get().strip()
        if not raw_value:
            return

        try:
            seconds = self._parse_stop_after_seconds(raw_value)
        except ValueError as exc:
            self._set_urgent_status("Invalid Stop After value", color=ALERT_TEXT_COLOR)
            messagebox.showerror("Stop After Error", str(exc))
            return

        target_local = datetime.now().astimezone() + timedelta(seconds=seconds)
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            brief = f"{hours}h {mins}m"
        elif mins > 0:
            brief = f"{mins}m {secs}s"
        else:
            brief = f"{secs}s"

        # PROTECTION: If script is already running, schedule immediately. Otherwise, set as pending.
        if self._is_running:
            full_desc = f"Will stop {seconds} seconds from now"
            self._show_schedule_confirmation(
                "Stop After",
                self.stop_after_value.get(),
                brief,
                full_desc,
                lambda: self._schedule_stop_request(seconds, f"Stop After {full_desc}", brief, schedule_type="after")
            )
        else:
            full_desc = f"Will stop {seconds} seconds after the script begins"
            self._show_schedule_confirmation(
                "Stop After",
                self.stop_after_value.get(),
                brief,
                full_desc,
                lambda: self._set_pending_stop_after(seconds, brief)
            )

    def _on_schedule_stop_at(self):
        """Handle Stop-At UI action, validate time fields, and stage/schedule request."""
        # Check if something is already scheduled and warn the user
        if self._scheduled_stop_after_id is not None or self._pending_stop_after_duration is not None or self._pending_stop_at_hour is not None:
            existing_brief = self._scheduled_stop_brief or self._pending_stop_after_brief or self._pending_stop_at_brief or "unknown"
            self._set_urgent_status(f"A stop is already scheduled: {existing_brief}", color=ALERT_TEXT_COLOR)
            messagebox.showwarning(
                "Stop Already Scheduled",
                f"A stop is already scheduled ({existing_brief}). Please clear it first before scheduling a new one."
            )
            return

        if not self.stop_at_hour_value.get().strip() or \
           not self.stop_at_minute_value.get().strip() or \
           not self.stop_at_second_value.get().strip() or \
           not self.stop_at_timezone_value.get().strip():
            return

        try:
            tzinfo, zone_name = self._resolve_timezone_info(self.stop_at_timezone_value.get())
            hour = int(self.stop_at_hour_value.get())
            minute = int(self.stop_at_minute_value.get())
            second = int(self.stop_at_second_value.get())

            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError("Invalid time values: hour must be 0-23, minute/second must be 0-59.")

            now_local = datetime.now(tzinfo)
            target_local = now_local.replace(hour=hour, minute=minute, second=second, microsecond=0)

            if target_local <= now_local:
                target_local = target_local + timedelta(days=1)

            now_utc = datetime.now(timezone.utc)
            target_utc = target_local.astimezone(timezone.utc)
            delay_seconds = (target_utc - now_utc).total_seconds()

            if delay_seconds <= 0:
                raise ValueError("Stop At time must be in the future.")
        except ValueError as exc:
            self._set_urgent_status("Invalid Stop At value", color=ALERT_TEXT_COLOR)
            messagebox.showerror("Stop At Error", str(exc))
            return

        local_target = target_utc.astimezone()
        brief = f"{hour:02d}:{minute:02d}:{second:02d} {zone_name}"
        full_desc = (
            f"Stop At {target_local.strftime('%Y-%m-%d %H:%M:%S')} {zone_name} "
            f"(local {local_target.strftime('%Y-%m-%d %H:%M:%S %Z')})"
        )

        user_input = f"{hour:02d}:{minute:02d}:{second:02d} {zone_name}"

        # PROTECTION: If script is already running, schedule immediately with current calculated delay.
        # Otherwise, set as pending and recalculate delay when run starts.
        if self._is_running:
            self._show_schedule_confirmation(
                "Stop At",
                user_input,
                brief,
                full_desc,
                lambda: self._schedule_stop_request(delay_seconds, full_desc, brief, schedule_type="at")
            )
        else:
            self._show_schedule_confirmation(
                "Stop At",
                user_input,
                brief,
                full_desc,
                lambda: self._set_pending_stop_at(hour, minute, second, self.stop_at_timezone_value.get(), brief)
            )

    def _refresh_antennas_from_notion(self):
        """Refresh antenna data from Notion/fallback sources and recheck antenna boxes."""
        global ANTENNAS, Observing_Array, OBSERVING_STATUS_BY_ANTENNA, ANTENNA_SOURCE_STATUS, ANTENNA_LOAD_FATAL_MESSAGE
        self._set_urgent_status("Refreshing antennas from Notion...")
        try:
            antennas, observing_array, observing_status_by_antenna, source_status = load_antennas_from_notion_or_fallback()
            ANTENNAS = antennas
            Observing_Array = observing_array
            OBSERVING_STATUS_BY_ANTENNA = observing_status_by_antenna
            ANTENNA_SOURCE_STATUS = source_status
            ANTENNA_LOAD_FATAL_MESSAGE = ""
            self._antenna_load_blocked = False

            self.current_antennas = list(DEFAULT_ANTENNAS)
            self.active_antennas = set(antennas)
            self.observing_antennas = set(observing_array)
            self.observing_status_by_antenna = dict(observing_status_by_antenna)
            # On refresh, reset checkboxes from Notion state:
            # Check all Active Array antennas, then uncheck any marked "remove from all scripts".
            self._render_antenna_checkboxes(preserve_previous=False)
            # If inline content is visible, update it in place.
            try:
                inline_content = getattr(self, "_antenna_inline_content", None)
                if inline_content is not None and inline_content.winfo_exists():
                    # Update existing inline header buttons (don't rebuild the whole panel)
                    try:
                        # Update any refresh/select buttons to disabled when running
                        for w in inline_content.winfo_children():
                            # look for header frame widgets and their children
                            for child in w.winfo_children():
                                if isinstance(child, ctk.CTkButton):
                                    try:
                                        if self._is_running:
                                            child.configure(state="disabled")
                                        else:
                                            child.configure(state="normal")
                                    except Exception:
                                        pass
                    except Exception:
                        pass

                    # Update checkbox widgets in-place so the inline panel retains layout
                    try:
                        def _iter_descendants(widget):
                            for ch in widget.winfo_children():
                                yield ch
                                yield from _iter_descendants(ch)

                        for widget in _iter_descendants(inline_content):
                            if isinstance(widget, ctk.CTkCheckBox):
                                try:
                                    name = widget.cget("text")
                                except Exception:
                                    continue
                                is_active, observing_status, base_color, border_color, is_disabled = self._get_antenna_visuals(name)
                                var = self.ant_vars.get(name)
                                # bind variable if available
                                try:
                                    if var is not None:
                                        widget.configure(variable=var)
                                except Exception:
                                    pass
                                # set variable state according to refreshed Notion data
                                try:
                                    if is_active and observing_status != STATUS_REMOVE_FROM_ALL_SCRIPTS:
                                        if var is not None:
                                            var.set(True)
                                    else:
                                        if var is not None:
                                            var.set(False)
                                except Exception:
                                    pass
                                # update visual styling and enabled/disabled state
                                try:
                                    widget.configure(
                                        text_color=NORMAL_TEXT_COLOR if is_active else UI_MUTED_TEXT_COLOR,
                                        fg_color=base_color,
                                        hover_color=base_color,
                                        border_color=border_color,
                                    )
                                    if is_disabled or self._is_running:
                                        widget.configure(state="disabled")
                                    else:
                                        widget.configure(state="normal")
                                except Exception:
                                    pass
                    except Exception:
                        pass
            except Exception:
                pass
            # Ensure global REMOVE_ANT matches refreshed state
            try:
                self._update_global_REMOVE_ANT()
            except Exception:
                pass
            print(source_status)
            self._set_urgent_status("Antenna refresh complete")
            try:
                if not self._is_running:
                    self.run_btn.configure(state="normal")
            except Exception:
                pass
            messagebox.showinfo("Antenna Refresh", f"Loaded {len(antennas)} antennas.")
        except AntennaSourceError as exc:
            ANTENNA_LOAD_FATAL_MESSAGE = str(exc)
            self._antenna_load_blocked = True
            print(f"FATAL ANTENNA SOURCE ERROR: {ANTENNA_LOAD_FATAL_MESSAGE}")
            self._set_urgent_status("Antenna refresh failed - run blocked", color=ALERT_TEXT_COLOR)
            self._update_status(f"ERROR: {exc}")
            try:
                self.run_btn.configure(state="disabled")
            except Exception:
                pass
            messagebox.showerror(
                "Antenna Source Error",
                (
                    "Failed to load antennas from SNAPobs after Notion failed.\n\n"
                    f"{exc}\n\n"
                    "Observations are blocked until this is fixed."
                ),
            )
        except Exception as exc:
            self._set_urgent_status("Antenna refresh failed", color=ALERT_TEXT_COLOR)
            messagebox.showerror("Antenna Refresh Error", f"Failed to refresh antennas: {exc}")

    # Allow the user to browse files for the CSVs rather than just relying on typing
    def _browse_project(self):
        """Open a directory picker and set the project folder name from selection."""
        path = filedialog.askdirectory(title="Select Project Folder")
        if path:
            selected_folder = os.path.abspath(path)
            if self._is_rfsoc_root_folder(selected_folder):
                messagebox.showerror(
                    "Invalid Project Folder",
                    "Please select a project subfolder, not rfsoc_obs_scripts itself."
                )
                return
            self.project.set(selected_folder)
            folder_name = os.path.basename(selected_folder.rstrip("/\\"))
            ods_tag = make_ods_project_tag(project_name=folder_name, project_folder=selected_folder)
            self._update_status(f"Selected project folder: {selected_folder}")
            self._update_status(f"Friendly ODS filename tag: {ods_tag}")

    def _browse_csv(self):
        """Open a file picker and set the target CSV path."""
        path = filedialog.askopenfilename(
            title="Select CSV Containing Target List",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.csv_name.set(path)

    # Same as above but for the observed list
    def _browse_observed(self):
        """Open a file picker and set the observed-list CSV path."""
        path = filedialog.askopenfilename(
            title="Select CSV Containing Observed List",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.observed.set(path)

    def _toggle_inline_advanced_options(self):
        """Toggle the Advanced Options panel."""
        panel = getattr(self, "_advanced_options_panel", None)
        if panel is not None and panel.winfo_exists():
            try:
                panel.destroy()
            except Exception:
                pass
            self._advanced_options_panel = None
            self._queue_wait_adv_chk = None
            self._target_obs_time_override_chk = None
            # Clear all widget references to avoid stale references to destroyed widgets
            self._start_after_entry = None
            self._schedule_start_after_btn = None
            self._clear_scheduled_start_btn = None
            self._stop_after_entry = None
            self._schedule_stop_after_btn = None
            self._stop_at_hour_menu = None
            self._stop_at_minute_menu = None
            self._stop_at_second_menu = None
            self._stop_at_timezone_entry = None
            self._schedule_stop_at_btn = None
            self._clear_scheduled_stop_btn = None
            self._advanced_schedule_status_label = None
            self._ods_push_btn = None
            self.advanced_options_btn.configure(text="Advanced Options")
            return

        try:
            panel_w, panel_h = (460, 470)
            panel = ctk.CTkFrame(
                self,
                corner_radius=10,
                border_width=2,
                border_color="#888888",
                fg_color=UI_PANEL_COLOR,
                width=panel_w,
                height=panel_h,
            )
            panel.place(relx=0.5, rely=0.5, anchor="center")
            try:
                panel.pack_propagate(False)
            except Exception:
                pass
            try:
                panel.grid_propagate(False)
            except Exception:
                pass
            try:
                panel.lift()
                panel.focus_set()
            except Exception:
                pass

            self._advanced_options_panel = panel

            content = ctk.CTkFrame(panel, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=8, pady=8)

            # Make advanced options scrollable so all controls are reachable in the fixed-size panel.
            scroll_content = ctk.CTkScrollableFrame(content, fg_color="transparent")
            scroll_content.pack(fill="both", expand=True)

            ctk.CTkLabel(
                scroll_content,
                text="Advanced Options",
                font=TITLE_FONT,
                text_color=TITLE_TEXT_COLOR,
            ).pack(anchor="w", padx=6, pady=(2, 8))

            self._queue_wait_adv_chk = ctk.CTkCheckBox(
                scroll_content,
                text="Wait for ODS to activate (Recommended ON)",
                variable=self.queue_wait,
                text_color=NORMAL_TEXT_COLOR,
                corner_radius=CHECKBOX_CORNER_RADIUS,
            )
            self._queue_wait_adv_chk.pack(anchor="w", padx=6, pady=(0, 4))
            if self._is_running:
                try:
                    self._queue_wait_adv_chk.configure(state="disabled")
                except Exception:
                    pass

            self._ods_push_btn = ctk.CTkCheckBox(
                scroll_content,
                text="Push ODS? (Recommended ON)",
                variable=self.ods_push,
                text_color=NORMAL_TEXT_COLOR,
                corner_radius=CHECKBOX_CORNER_RADIUS,
            )
            self._ods_push_btn.pack(anchor="w", padx=6, pady=(0, 10))
            if self._is_running:
                try:
                    self._ods_push_btn.configure(state="disabled")
                except Exception:
                    pass

            self._target_obs_time_override_chk = ctk.CTkCheckBox(
                scroll_content,
                text='Use per-target "Obs Time" from target CSV when available',
                variable=self.use_target_obs_time_override,
                text_color=NORMAL_TEXT_COLOR,
                corner_radius=CHECKBOX_CORNER_RADIUS,
            )
            self._target_obs_time_override_chk.pack(anchor="w", padx=6, pady=(0, 10))
            if self._is_running:
                try:
                    self._target_obs_time_override_chk.configure(state="disabled")
                except Exception:
                    pass

            ctk.CTkLabel(
                scroll_content,
                text="Start Scheduling",
                font=NORMAL_FONT,
                text_color=NORMAL_TEXT_COLOR,
            ).pack(anchor="w", padx=6, pady=(4, 2))

            start_after_row = ctk.CTkFrame(scroll_content, fg_color="transparent")
            start_after_row.pack(fill="x", padx=6, pady=(0, 4))

            ctk.CTkLabel(
                start_after_row,
                text="Start After:",
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
            ).pack(side="left", padx=(0, 6))

            self._start_after_entry = ctk.CTkEntry(
                start_after_row,
                textvariable=self.start_after_value,
                width=160,
                fg_color=UI_ENTRY_COLOR,
                border_color=UI_BORDER_COLOR,
                text_color=NORMAL_TEXT_COLOR,
            )
            self._start_after_entry.pack(side="left", padx=(0, 6))

            self._schedule_start_after_btn = ctk.CTkButton(
                start_after_row,
                text="Set",
                command=self._on_schedule_start_after,
                width=60,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            self._schedule_start_after_btn.pack(side="left", padx=(0, 6))

            self._clear_scheduled_start_btn = ctk.CTkButton(
                start_after_row,
                text="Clear",
                command=self._on_clear_scheduled_start,
                width=70,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            self._clear_scheduled_start_btn.pack(side="left")

            ctk.CTkLabel(
                scroll_content,
                text="Examples: 4 hours, 1h 30m, 45m, or 14400",
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
            ).pack(anchor="w", padx=6, pady=(0, 4))

            self._scheduled_start_label = ctk.CTkLabel(
                scroll_content,
                textvariable=self.scheduled_start_display,
                font=SMALL_FONT,
                text_color="#E69F00"
            )
            self._scheduled_start_label.pack(anchor="w", padx=6, pady=(0, 2))

            ctk.CTkLabel(
                scroll_content,
                textvariable=self.advanced_start_status,
                font=SMALL_FONT,
                text_color="#E69F00",
                wraplength=430,
                justify="left",
            ).pack(anchor="w", padx=6, pady=(0, 6))

            ctk.CTkLabel(
                scroll_content,
                text="Stop Scheduling",
                font=NORMAL_FONT,
                text_color=NORMAL_TEXT_COLOR,
            ).pack(anchor="w", padx=6, pady=(4, 2))

            stop_after_row = ctk.CTkFrame(scroll_content, fg_color="transparent")
            stop_after_row.pack(fill="x", padx=6, pady=(0, 4))

            ctk.CTkLabel(
                stop_after_row,
                text="Stop After:",
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
            ).pack(side="left", padx=(0, 6))

            self._stop_after_entry = ctk.CTkEntry(
                stop_after_row,
                textvariable=self.stop_after_value,
                width=160,
                fg_color=UI_ENTRY_COLOR,
                border_color=UI_BORDER_COLOR,
                text_color=NORMAL_TEXT_COLOR,
            )
            self._stop_after_entry.pack(side="left", padx=(0, 6))

            self._schedule_stop_after_btn = ctk.CTkButton(
                stop_after_row,
                text="Set",
                command=self._on_schedule_stop_after,
                width=60,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            self._schedule_stop_after_btn.pack(side="left")

            ctk.CTkLabel(
                scroll_content,
                text="Examples: 8 hours, 1.5 hours, 90m, or 28800 (script converts to seconds)",
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
            ).pack(anchor="w", padx=6, pady=(0, 6))

            stop_at_row = ctk.CTkFrame(scroll_content, fg_color="transparent")
            stop_at_row.pack(fill="x", padx=6, pady=(0, 4))

            ctk.CTkLabel(
                stop_at_row,
                text="Stop At:",
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
            ).pack(side="left", padx=(0, 6))

            self._stop_at_hour_menu = ctk.CTkOptionMenu(
                stop_at_row,
                variable=self.stop_at_hour_value,
                values=[f"{h:02d}" for h in range(24)],
                width=60,
                fg_color=UI_ENTRY_COLOR,
                button_color=UI_BORDER_COLOR,
                button_hover_color=UI_BORDER_COLOR,
            )
            self._stop_at_hour_menu.pack(side="left", padx=(0, 2))

            ctk.CTkLabel(
                stop_at_row,
                text=":",
                font=NORMAL_FONT,
                text_color=NORMAL_TEXT_COLOR,
            ).pack(side="left")

            self._stop_at_minute_menu = ctk.CTkOptionMenu(
                stop_at_row,
                variable=self.stop_at_minute_value,
                values=[f"{m:02d}" for m in range(60)],
                width=60,
                fg_color=UI_ENTRY_COLOR,
                button_color=UI_BORDER_COLOR,
                button_hover_color=UI_BORDER_COLOR,
            )
            self._stop_at_minute_menu.pack(side="left", padx=(2, 2))

            ctk.CTkLabel(
                stop_at_row,
                text=":",
                font=NORMAL_FONT,
                text_color=NORMAL_TEXT_COLOR,
            ).pack(side="left")

            self._stop_at_second_menu = ctk.CTkOptionMenu(
                stop_at_row,
                variable=self.stop_at_second_value,
                values=[f"{s:02d}" for s in range(60)],
                width=60,
                fg_color=UI_ENTRY_COLOR,
                button_color=UI_BORDER_COLOR,
                button_hover_color=UI_BORDER_COLOR,
            )
            self._stop_at_second_menu.pack(side="left", padx=(2, 6))

            self._stop_at_timezone_entry = ctk.CTkEntry(
                stop_at_row,
                textvariable=self.stop_at_timezone_value,
                width=80,
                fg_color=UI_ENTRY_COLOR,
                border_color=UI_BORDER_COLOR,
                text_color=NORMAL_TEXT_COLOR,
            )
            self._stop_at_timezone_entry.pack(side="left", padx=(0, 6))

            self._schedule_stop_at_btn = ctk.CTkButton(
                stop_at_row,
                text="Set",
                command=self._on_schedule_stop_at,
                width=60,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            self._schedule_stop_at_btn.pack(side="left")

            ctk.CTkLabel(
                scroll_content,
                text="24-hour format | Timezone: UTC, PST, EST, etc.",
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
            ).pack(anchor="w", padx=6, pady=(0, 8))

            controls_row = ctk.CTkFrame(scroll_content, fg_color="transparent")
            controls_row.pack(fill="x", padx=6, pady=(6, 2))

            self._clear_scheduled_stop_btn = ctk.CTkButton(
                controls_row,
                text="Clear Scheduled Stop",
                command=self._on_clear_scheduled_stop,
                width=170,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            )
            self._clear_scheduled_stop_btn.pack(side="left")

            ctk.CTkButton(
                controls_row,
                text="Close",
                command=self._toggle_inline_advanced_options,
                width=100,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            ).pack(side="right")

            self._advanced_schedule_status_label = ctk.CTkLabel(
                scroll_content,
                textvariable=self.advanced_schedule_status,
                font=SMALL_FONT,
                text_color="#E69F00",
                wraplength=430,
                justify="left",
            )
            self._advanced_schedule_status_label.pack(anchor="w", padx=6, pady=(4, 4))

            self.advanced_options_btn.configure(text="Hide Advanced Options")
            self._update_start_controls_state()
            self._update_schedule_controls_state()
        except Exception as exc:
            self._update_status(f"ERROR: Failed to open inline advanced options panel: {exc}")
            messagebox.showerror("Advanced Options Error", f"Failed to show inline advanced options panel: {exc}")

    def _update_schedule_controls_state(self):
        """Enable/disable scheduling controls based on active or pending stop type."""
        is_scheduled = self._scheduled_stop_after_id is not None
        is_pending_after = self._pending_stop_after_duration is not None
        is_pending_at = self._pending_stop_at_hour is not None
        has_any_schedule = is_scheduled or is_pending_after or is_pending_at

        # Clear button is enabled if anything is scheduled or pending
        if self._clear_scheduled_stop_btn is not None:
            try:
                clear_state = "normal" if has_any_schedule else "disabled"
                self._clear_scheduled_stop_btn.configure(state=clear_state)
            except Exception:
                pass

        # Lock BOTH Set buttons whenever any schedule exists (active or pending).
        set_button_state = "disabled" if has_any_schedule else "normal"
        for widget in [self._schedule_stop_after_btn, self._schedule_stop_at_btn]:
            if widget is not None:
                try:
                    widget.configure(state=set_button_state)
                except Exception:
                    pass

        # Keep inputs editable so users can prepare the next value while current schedule is active.
        for widget in [
            self._stop_after_entry,
            self._stop_at_hour_menu,
            self._stop_at_minute_menu,
            self._stop_at_second_menu,
            self._stop_at_timezone_entry,
        ]:
            if widget is not None:
                try:
                    widget.configure(state="normal")
                except Exception:
                    pass

        if is_scheduled:
            panel_message = f"Scheduled stop active: {self._scheduled_stop_brief or self._scheduled_stop_description or 'configured'}"
        elif is_pending_after:
            panel_message = f"Scheduled stop pending: Stop After {self._pending_stop_after_brief or str(self._pending_stop_after_duration) + 's'}"
        elif is_pending_at:
            panel_message = f"Scheduled stop pending: Stop At {self._pending_stop_at_brief or 'configured'}"
        else:
            panel_message = "No stop scheduled."

        self.advanced_schedule_status.set(panel_message)

    def _show_schedule_confirmation(self, title: str, user_input: str, brief: str, full_desc: str, confirm_callback):
        """Display an inline confirmation dialog before applying schedule actions."""
        if getattr(self, "_confirmation_panel", None) is not None and self._confirmation_panel.winfo_exists():
            try:
                self._confirmation_panel.destroy()
            except Exception:
                pass

        try:
            panel_w, panel_h = (520, 220)
            panel = ctk.CTkFrame(
                self,
                corner_radius=10,
                border_width=2,
                border_color="#888888",
                fg_color=UI_PANEL_COLOR,
                width=panel_w,
                height=panel_h,
            )
            panel.place(relx=0.5, rely=0.5, anchor="center")
            try:
                panel.pack_propagate(False)
            except Exception:
                pass
            try:
                panel.grid_propagate(False)
            except Exception:
                pass
            try:
                panel.lift()
                panel.focus_set()
            except Exception:
                pass

            self._confirmation_panel = panel

            content = ctk.CTkFrame(panel, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=16, pady=16)

            ctk.CTkLabel(
                content,
                text=f"Confirm {title}",
                font=TITLE_FONT,
                text_color=TITLE_TEXT_COLOR,
            ).pack(anchor="w", padx=0, pady=(0, 8))

            ctk.CTkLabel(
                content,
                text=f"Input: {user_input}",
                font=NORMAL_FONT,
                text_color=NORMAL_TEXT_COLOR,
            ).pack(anchor="w", padx=0, pady=(0, 4))

            ctk.CTkLabel(
                content,
                text=full_desc,
                font=SMALL_FONT,
                text_color=SMALL_TEXT_COLOR,
                wraplength=480,
                justify="left",
            ).pack(anchor="w", padx=0, pady=(0, 10))

            ctk.CTkLabel(
                content,
                text="Are you sure you want to schedule this stop?",
                font=NORMAL_FONT,
                text_color=NORMAL_TEXT_COLOR,
            ).pack(anchor="w", padx=0, pady=(4, 12))

            footer = ctk.CTkFrame(content, fg_color="transparent")
            footer.pack(side="bottom", fill="both", padx=0, pady=(8, 0))
            footer.grid_columnconfigure(0, weight=1)
            footer.grid_columnconfigure(1, weight=1)

            def on_confirm():
                try:
                    self._confirmation_panel.destroy()
                except Exception:
                    pass
                self._confirmation_panel = None
                confirm_callback()

            def on_cancel():
                try:
                    self._confirmation_panel.destroy()
                except Exception:
                    pass
                self._confirmation_panel = None
                self._set_urgent_status("Schedule cancelled")

            ctk.CTkButton(
                footer,
                text="Cancel",
                command=on_cancel,
                width=160,
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

            ctk.CTkButton(
                footer,
                text="Confirm",
                command=on_confirm,
                width=160,
                fg_color="#009E73",
                corner_radius=BUTTON_CORNER_RADIUS,
                font=BUTTON_FONT,
            ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        except Exception as exc:
            self._update_status(f"ERROR: Failed to show confirmation panel: {exc}")
            messagebox.showerror("Confirmation Error", f"Failed to show confirmation: {exc}")

    # When the user clicks Run, this prints out what the inputs were for logging.
    def _on_run(self):
        """Validate inputs, launch observation worker, and transition UI to running state."""
        if self._antenna_load_blocked:
            warning = (
                "Observation start blocked because SNAPobs fallback antenna loading failed.\n\n"
                f"{ANTENNA_LOAD_FATAL_MESSAGE or 'Unknown antenna source failure.'}\n\n"
                "Fix antenna source connectivity and refresh antennas before running."
            )
            self._set_urgent_status("Observation blocked: antenna source failure", color=ALERT_TEXT_COLOR)
            self._update_status(f"ERROR: {warning}")
            messagebox.showerror("Antenna Source Error", warning)
            return

        if self._is_running and self._worker_thread is not None and self._worker_thread.is_alive():
            messagebox.showwarning("Already Running", "Observation is already running. Please wait for it to stop before running again.")
            return

        validation = self._validate_run_configuration()
        if validation["errors"]:
            self._show_configuration_errors(validation["errors"])
            return

        remove_ant_list = [
            name for name, var in self.ant_vars.items()
            if (name in self.active_antennas and not var.get())
        ]
        checked_ant_list = [
            name for name, var in self.ant_vars.items()
            if (name in self.active_antennas and bool(var.get()))
        ]
        run_configuration = { # NOTE: Update this with all the values that the GUI takes
            "PROJECT_NAME": validation["project_name"],
            "PROJECT_FOLDER": validation["project_folder"],
            "ODS_PROJECT_TAG": validation["ods_project_tag"],
            "CSV_NAME": validation["csv_path"],
            "OBSERVED_LIST": validation["observed_path"],
            "OBS_TIME": validation["obs_time_seconds"],
            "REMOVE_ANT": remove_ant_list,
            "GUI_SELECTED_ANTENNAS": checked_ant_list,
            "ACTIVE_RECORDERS": self._selected_recorders_dict(),
            "ODS_PUSH": bool(self.ods_push.get()),
            "QUEUE_WAIT": bool(self.queue_wait.get()),
            "REARRANGE_BY_LST": bool(self.rearrange_by_lst.get()),
            "RECORDING": bool(self.recording.get()),
            "TESTING": bool(self.testing.get()),
            "SORT_BY_OBSERVED": bool(self.sort_by_observed.get()),
            "MARKING": bool(self.marking.get() and self.sort_by_observed.get()),
            "USE_TARGET_OBS_TIME_OVERRIDE": bool(self.use_target_obs_time_override.get()),
            "START_AFTER_SECONDS": self._pending_start_after_duration,
            "START_AFTER_BRIEF": self._pending_start_after_brief or "None",
            "GUI_CONTROLLED": True,
        }

        if bool(self.marking.get()) and (not bool(self.sort_by_observed.get())):
            self._update_status("Sort by observed list is OFF, so Mark Target as Observed was disabled for this run.")

        primary_lines, secondary_lines = self._build_run_confirmation_content(run_configuration)
        self._update_status("Run configuration summary:")
        for key, value in primary_lines:
            self._update_status(f"  {key}: {value}")
        for line in secondary_lines:
            self._update_status(f"  {line}")

        def _start_confirmed_run():
            if self._pending_start_after_duration is not None:
                delay_seconds = int(self._pending_start_after_duration)
                brief = self._pending_start_after_brief or self._format_duration_brief(delay_seconds)
                self._cancel_pending_start_after()
                try:
                    self._schedule_start_request(delay_seconds, run_configuration, remove_ant_list, brief)
                    messagebox.showinfo(
                        "Start Scheduled",
                        (
                            f"Observation start has been scheduled for {brief} from now.\n\n"
                            "The run configuration is now locked until start or clear."
                        ),
                    )
                except Exception as exc:
                    self._set_start_scheduled_state(False)
                    self._report_error("Failed to schedule delayed start", type(exc), exc, exc.__traceback__)
                return

            self._start_observation_run(run_configuration, remove_ant_list)

        self._show_run_confirmation_panel(run_configuration, _start_confirmed_run)

    # When stop button is pressed
    def _on_stop(self):
        """Request a stop after the current scan completes."""
        self._submit_stop_after_scan(trigger_source="manual", show_popup=True)

    def _on_resume(self):
        """Clear a pending stop request and resume normal target processing."""
        self._set_urgent_status("Resume Requested...")
        if self._observe_module is None:
            messagebox.showwarning("No Active Module", "No observe module is currently loaded.")
            return
        try:
            self._observe_module.request_resume()
            self._set_stop_resume_buttons(stop_requested=False)
            messagebox.showinfo("Resume", "Resume requested. Any pending Stop request has been cleared.")
        except Exception as e:
            messagebox.showerror("Error", f"Resume failed: {e}")

    # When abort button is pressed
    def _on_abort(self):
        """Request immediate Abort of the active observation run. Closes EVERYTHING."""
        self._cancel_scheduled_start(show_status=False)
        self._cancel_pending_start_after()
        self._cancel_scheduled_stop(show_status=False)
        self._set_urgent_status("Abort requested")
        if self._observe_module is None:
            messagebox.showwarning("No Active Module", "No observe module is currently loaded.")
            return
        try:
            self._observe_module.request_abort()
            messagebox.showinfo("Abort", "Abort requested. Observe script will exit immediately.")
        except Exception as e:
            messagebox.showerror("Error", f"Abort failed: {e}")

    # When close GUI button is pressed
    def _on_close_gui(self):
        """Confirm close and terminate GUI without forcing antenna release."""
        if messagebox.askyesno("Close GUI", "Are you sure you want to close the GUI?"):
            self._cancel_scheduled_start(show_status=False)
            self._cancel_pending_start_after()
            self._cancel_scheduled_stop(show_status=False)
            try:
                if self._observe_module is not None and hasattr(self._observe_module, "request_gui_close"):
                    self._observe_module.request_gui_close()
            except Exception:
                pass
            self.destroy() # Close the GUI window
            import sys
            sys.exit(0) # Exit the entire Python process

    def _open_readme_window(self):
        """Open the README window and render markdown-like README content."""
        # NOTE: Consider just changing the README to a .md file
        readme_win = ctk.CTkToplevel(self)
        readme_win.title("README")
        readme_w, readme_h = GUI_POPUP_SIZES["readme"]
        readme_win.geometry(f"{readme_w}x{readme_h}")
        readme_win.configure(fg_color=UI_BG_COLOR)
        readme_win.transient(self)
        readme_image_path = README_WINDOW_IMAGE_PATH or MAIN_WINDOW_IMAGE_PATH
        _apply_window_image(readme_win, readme_image_path)
        readme_win.after(200, lambda: _apply_window_image(readme_win, readme_image_path))

        container = ctk.CTkFrame(
            readme_win,
            corner_radius=10,
            border_width=1,
            border_color=UI_BORDER_COLOR,
            fg_color=UI_PANEL_COLOR
        )
        container.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            container,
            text="README",
            font=TITLE_FONT,
            text_color=TITLE_TEXT_COLOR
        ).pack(anchor="w", padx=10, pady=(8, 4))

        readme_text = ctk.CTkTextbox(
            container,
            wrap="word",
            fg_color=UI_ENTRY_COLOR,
            text_color=NORMAL_TEXT_COLOR
        )
        readme_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        _render_readme_markup(readme_text, README_TEXT)

if __name__ == "__main__":
    app = SurveyConfigGUI()
    app.mainloop()
