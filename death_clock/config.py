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


def load_config() -> dict:
    """Load settings from disk. Returns defaults if file doesn't exist."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            saved = json.load(f)
        # Merge with defaults so any new keys we add in the future are included
        merged = {**DEFAULT_CONFIG, **saved}
        merged["factors"] = {**DEFAULT_CONFIG["factors"], **saved.get("factors", {})}
        merged["window"] = {**DEFAULT_CONFIG["window"], **saved.get("window", {})}
        return merged
    # No file yet — return fresh defaults
    return {
        **DEFAULT_CONFIG,
        "factors": {**DEFAULT_CONFIG["factors"]},
        "window": {**DEFAULT_CONFIG["window"]},
    }


def save_config(config: dict) -> None:
    """Save settings to disk."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


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
