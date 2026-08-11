"""
Configuration persistence for Death Clock.

This module handles loading and saving settings.json.

IMPORTANT DESIGN NOTE:
- death_datetime_iso is the stored death date as an ISO string (e.g. "2058-03-15T14:22:00")
- This is calculated ONCE when the user saves their health info, then stored here
- On every app launch we just READ this value — we never recalculate it automatically
- This is what prevents the countdown from appearing to "reset"
"""

import json
import os
from datetime import datetime

# settings.json lives in the same folder as this project (one level up from this file)
CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")

# These are the values used if settings.json doesn't exist yet
DEFAULT_CONFIG = {
    "date_of_birth": "",           # User must fill this in
    "sex": "male",
    "death_datetime_iso": "",       # Empty until user saves settings for first time
    "factors": {
        "current_smoker": False,
        "former_smoker": False,
        "obesity": False,
        "sedentary": False,
        "heavy_drinking": False,
        "diabetes": False,
        "regular_exercise": False,
        "mediterranean_diet": False,
        "college_degree": False,
        "married": False,
    },
    "window": {
        "x": 100,
        "y": 100,
        "width": 440,
        "height": 120,
    },
    "start_on_boot": False,
}


def _fresh_defaults() -> dict:
    """Return a brand-new copy of the defaults, safe to modify."""
    return {
        **DEFAULT_CONFIG,
        "factors": {**DEFAULT_CONFIG["factors"]},
        "window": {**DEFAULT_CONFIG["window"]},
    }


def load_config() -> dict:
    """
    Load settings from disk. Returns defaults if the file doesn't exist.

    If the file exists but can't be read (corrupt JSON, bad permissions), we
    fall back to defaults rather than raising. That matters because the app
    runs under pythonw.exe with no console: an uncaught exception here would
    kill it at startup with nothing shown on screen at all. Falling back means
    the Settings window opens instead, which is recoverable.

    The damaged file is kept as settings.json.corrupt so nothing is lost --
    the death date may well still be readable inside it by hand.
    """
    if not os.path.exists(CONFIG_PATH):
        return _fresh_defaults()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if not isinstance(saved, dict):
            raise ValueError("settings.json does not contain a JSON object")
    except (json.JSONDecodeError, ValueError, OSError, UnicodeDecodeError):
        try:
            os.replace(CONFIG_PATH, CONFIG_PATH + ".corrupt")
        except OSError:
            pass  # Couldn't preserve it — still better to start than to crash
        return _fresh_defaults()

    # Merge with defaults so any new keys we add in the future are included
    merged = {**DEFAULT_CONFIG, **saved}
    merged["factors"] = {**DEFAULT_CONFIG["factors"], **saved.get("factors", {})}
    merged["window"] = {**DEFAULT_CONFIG["window"], **saved.get("window", {})}
    return merged


def save_config(config: dict) -> None:
    """
    Save settings to disk, atomically.

    Writing straight to settings.json meant truncating it first and then
    filling it back in. Anything interrupting that gap -- a crash, a power
    cut, OneDrive syncing the folder mid-write -- left a half-written file,
    and settings.json is the only copy of your death date.

    So we write the new contents to a temporary file alongside it, flush all
    the way down to the physical disk, and then rename it into place.
    os.replace() is atomic on Windows and POSIX alike: any reader sees either
    the complete old file or the complete new one, never a partial write.
    """
    temp_path = CONFIG_PATH + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.flush()          # Push Python's buffer into the OS
        os.fsync(f.fileno())  # Push the OS buffer onto the actual disk

    os.replace(temp_path, CONFIG_PATH)  # Atomic swap


def get_death_datetime(config: dict) -> datetime | None:
    """
    Return the stored death datetime, or None if not set yet.

    This is the key function — we always use the STORED date, never recalculate.
    """
    iso = config.get("death_datetime_iso", "")
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        return None


def has_profile(config: dict) -> bool:
    """Return True if the user has filled in their date of birth."""
    return bool(config.get("date_of_birth", "").strip())
