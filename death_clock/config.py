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
import tempfile
from copy import deepcopy
from collections.abc import Callable
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


def _read_object(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as stream:
        saved = json.load(stream)
    if not isinstance(saved, dict):
        raise ValueError("Settings must contain a JSON object")
    return saved


def _normalize(saved: dict) -> tuple[dict, bool]:
    """Repair individual fields without discarding a valid stored countdown."""
    result = {**_fresh_defaults(), **saved}
    invalid_type = False
    for key in ("date_of_birth", "death_datetime_iso"):
        if not isinstance(result[key], str):
            result[key] = ""
    if result["date_of_birth"]:
        try:
            datetime.strptime(result["date_of_birth"], "%Y-%m-%d")
        except ValueError:
            result["date_of_birth"] = ""
    if result["death_datetime_iso"] and get_death_datetime(result) is None:
        result["death_datetime_iso"] = ""
    if result["sex"] not in ("male", "female"):
        result["sex"] = "male"
    if type(result["start_on_boot"]) is not bool:
        invalid_type = True
        result["start_on_boot"] = False
    for section in ("factors", "window"):
        original = saved.get(section, {})
        original = original if isinstance(original, dict) else {}
        result[section] = {**DEFAULT_CONFIG[section], **original}
        for key, default in DEFAULT_CONFIG[section].items():
            value = result[section][key]
            valid = type(value) is type(default)
            if section == "window" and valid:
                valid = (-100000 <= value <= 100000 if key in ("x", "y")
                         else 1 <= value <= 10000)
            if not valid:
                invalid_type = True
                result[section][key] = default
    # Filling in missing keys is normal for older files, not damage.
    repaired = invalid_type or any(result.get(key) != value for key, value in saved.items()
                   if key not in ("factors", "window"))
    for section in ("factors", "window"):
        original = saved.get(section, {})
        repaired |= (not isinstance(original, dict) or
                     any(result[section].get(k) != v for k, v in original.items()))
    return result, repaired


def _preserve_damaged_file() -> None:
    """Copy, rather than move, the original; never overwrite recovery evidence."""
    from uuid import uuid4
    destination = CONFIG_PATH + ".corrupt"
    if os.path.exists(destination):
        destination += "." + uuid4().hex
    with open(CONFIG_PATH, "rb") as source, open(destination, "xb") as target:
        target.write(source.read())
        target.flush()
        os.fsync(target.fileno())


def load_config(on_warning: Callable[[str], None] | None = None) -> dict:
    """Read the countdown, repairing preferences or recovering a known-good copy.

    Loading never rewrites the main file or recalculates a date. Read failures
    remain protected: a later save must be able to read/preserve that original.
    """
    warn = on_warning or (lambda message: None)
    primary = None
    try:
        primary, repaired = _normalize(_read_object(CONFIG_PATH))
        if repaired:
            try:
                _preserve_damaged_file()
            except OSError:
                warn("Some settings need repair, but their original could not be backed up.")
            else:
                warn("Some settings were repaired. The original was kept in a .corrupt copy.")
        if get_death_datetime(primary) is not None:
            return primary
    except FileNotFoundError:
        pass
    except (ValueError, UnicodeDecodeError):
        try:
            _preserve_damaged_file()
        except OSError:
            warn("Settings are damaged and their original could not be backed up.")
        else:
            warn("Settings are damaged. The original was kept in a .corrupt copy.")
    except OSError:
        warn("Settings could not be read. Check the file permissions or OneDrive availability.")

    try:
        backup, _ = _normalize(_read_object(CONFIG_PATH + ".bak"))
        if get_death_datetime(backup) is not None:
            warn("Your saved countdown was recovered from settings.json.bak. "
                 "No date was recalculated.")
            return backup
    except (OSError, ValueError, UnicodeDecodeError):
        pass
    if primary is None and os.path.exists(CONFIG_PATH):
        warn("No usable countdown backup was found. Review Settings before saving a new target.")
    return primary if primary is not None else _fresh_defaults()


def _atomic_write(path: str, data: dict) -> None:
    """Use a unique neighboring temporary file, then atomically replace the file."""
    fd, temporary = tempfile.mkstemp(prefix=os.path.basename(path) + ".",
                                     suffix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_config(config: dict) -> None:
    """Preserve the previous usable countdown before committing a new one.

    Permission/read failures propagate, preventing an unreadable original from
    being replaced by defaults. A failed backup also stops the save.
    """
    proposed, repaired = _normalize(config)
    if repaired:
        raise ValueError("Settings contain invalid values; nothing was saved.")
    previous = None
    try:
        raw = _read_object(CONFIG_PATH)
        previous, damaged = _normalize(raw)
        if damaged:
            _preserve_damaged_file()
    except FileNotFoundError:
        pass
    except (ValueError, UnicodeDecodeError):
        _preserve_damaged_file()
    if previous is not None and get_death_datetime(previous) is not None:
        if get_death_datetime(proposed) is None:
            raise ValueError("Cannot replace a saved countdown with an empty target.")
        _atomic_write(CONFIG_PATH + ".bak", previous)
    elif not os.path.exists(CONFIG_PATH + ".bak") and get_death_datetime(proposed) is not None:
        # A first successful setup also has a recovery copy.
        _atomic_write(CONFIG_PATH + ".bak", proposed)
    _atomic_write(CONFIG_PATH, proposed)


def commit_config(current: dict, proposed: dict) -> None:
    """Keep widget/app references intact; update memory only after disk succeeds."""
    snapshot = deepcopy(proposed)
    save_config(snapshot)
    current.clear()
    current.update(snapshot)


def get_death_datetime(config: dict) -> datetime | None:
    """
    Return the stored death datetime, or None if not set yet.

    This is the key function — we always use the STORED date, never recalculate.
    """
    iso = config.get("death_datetime_iso", "")
    if not isinstance(iso, str) or not iso:
        return None
    try:
        parsed = datetime.fromisoformat(iso)
        return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed
    except (ValueError, OverflowError, OSError):
        return None


def has_profile(config: dict) -> bool:
    """Return True if the user has filled in their date of birth."""
    dob = config.get("date_of_birth", "")
    return isinstance(dob, str) and bool(dob.strip())


def stored_date_matches_inputs(
    config: dict, date_of_birth: str, sex: str, factors: dict
) -> bool:
    """
    Return True if the stored death date was calculated from these exact inputs.

    Why this exists: compute_death_datetime() reads the clock. Feeding it the
    same date of birth, sex and factors on a different day gives a different
    answer, because you are genuinely older -- the estimate slides gradually
    later as you survive. That is correct behaviour for a real change of
    profile, but it makes pressing Save destructive when nothing changed.

    The case that bit us: copy settings.json to a second computer, open
    Settings only to tick "launch at login", press Save -- and the carried-over
    death date is silently replaced with a freshly calculated one.

    So Save now asks this first. If the actuarial inputs are untouched, the
    stored date is kept as-is and only the preferences around it are written.

    Returns False if there is no stored date, or if it is unreadable -- both
    mean we have nothing worth preserving and should calculate afresh.
    """
    if get_death_datetime(config) is None:
        return False

    if date_of_birth != config.get("date_of_birth"):
        return False

    if sex != config.get("sex"):
        return False

    # Compare only the factors the settings window actually manages. An older
    # settings.json may carry keys we have since dropped; those are irrelevant
    # to the current calculation and must not force a needless recalculation.
    stored_factors = config.get("factors", {})
    if not isinstance(stored_factors, dict):
        return False
    return all(stored_factors.get(key, False) == value for key, value in factors.items())
