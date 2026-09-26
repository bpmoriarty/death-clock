"""Shared countdown storage and independent, per-user device preferences.

Legacy settings are read without rewriting them. Local preferences are seeded
once; an explicit profile save removes the now-inert legacy device fields.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from . import config

DISPLAY_DEFAULTS = {"opacity": 0.93, "lock_position": False,
                    "show_seconds": True, "display_mode": "years"}
DEVICE_KEYS = ("window", "start_on_boot", *DISPLAY_DEFAULTS)
PROFILE_KEYS = ("date_of_birth", "sex", "factors", "death_datetime_iso")


def device_path() -> str:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise OSError("Windows local application data folder is unavailable.")
    return os.path.join(base, "DeathClock", "preferences.json")


def shared_fields(value: dict) -> dict:
    return deepcopy({k: v for k, v in value.items() if k not in DEVICE_KEYS})


def _token() -> bytes | None:
    try:
        return hashlib.sha256(Path(config.CONFIG_PATH).read_bytes()).digest()
    except FileNotFoundError:
        return None


class Settings(dict):
    """Runtime values plus the shared-file snapshot, never serialized as metadata."""

    def __init__(self, values, token):
        super().__init__(values)
        self.shared_baseline = shared_fields(values)
        self.disk_token = token


def _device_values(value: dict) -> dict:
    normalized, repaired = config._normalize({"window": value.get("window", {})})
    opacity = value.get("opacity", 0.93)
    if repaired or type(opacity) not in (int, float) or not 0.2 <= opacity <= 1:
        raise ValueError("Invalid device preferences.")
    display = {key: value.get(key, default) for key, default in DISPLAY_DEFAULTS.items()}
    if (type(display["lock_position"]) is not bool or type(display["show_seconds"]) is not bool
            or display["display_mode"] not in ("years", "days", "weeks")):
        raise ValueError("Invalid display preferences.")
    return {"window": {key: normalized["window"][key] for key in config.DEFAULT_CONFIG["window"]},
            **display}


def commit_display(current: dict, changes: dict) -> None:
    """Save only display options and keep the running settings intact on failure."""
    proposed = {**current, **{key: changes[key] for key in DISPLAY_DEFAULTS}}
    save_preferences(proposed)
    current.update({key: proposed[key] for key in DISPLAY_DEFAULTS})


def _preserve(path: str) -> None:
    destination = path + ".corrupt." + uuid4().hex
    with open(path, "rb") as source, open(destination, "xb") as target:
        target.write(source.read())
        target.flush()
        os.fsync(target.fileno())


def save_preferences(value: dict) -> None:
    """Never read or write shared settings, including on move, resize, or exit."""
    proposed = _device_values(value)
    path = device_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    previous = None
    try:
        previous = _device_values(config._read_object(path))
    except FileNotFoundError:
        pass
    except (ValueError, UnicodeDecodeError):
        _preserve(path)
    if previous is not None:
        config._atomic_write(path + ".bak", previous)
    elif not os.path.exists(path + ".bak"):
        config._atomic_write(path + ".bak", proposed)
    config._atomic_write(path, proposed)


def load_settings(on_warning=None) -> Settings:
    warn = on_warning or (lambda message: None)
    # Capture before loading: a sync during loading must not authorize a stale save.
    try:
        token = _token()
    except OSError:
        token = None
    values = config.load_config(warn)
    try:
        path = device_path()
        try:
            local = _device_values(config._read_object(path))
        except FileNotFoundError:
            try:
                local = _device_values(config._read_object(path + ".bak"))
                warn("Missing device preferences were recovered from the local backup.")
            except FileNotFoundError:
                local = _device_values(values)
            # Establish a one-time migration marker even for default placement.
            save_preferences(local)
        except (ValueError, UnicodeDecodeError, OSError):
            warn("Device preferences could not be read. Trying the local backup; "
                 "your shared countdown is unchanged.")
            try:
                local = _device_values(config._read_object(path + ".bak"))
            except (ValueError, UnicodeDecodeError, OSError):
                local = _device_values({})
        values.update(local)
    except (OSError, ValueError):
        values.update(_device_values({}))
        warn("Local preferences could not be initialized. Placement may not be "
             "remembered. Your shared countdown is unchanged.")
    # Login registration belongs to Windows, never to the portable profile.
    values.pop("start_on_boot", None)
    return Settings(values, token)


def commit_settings(current: dict, proposed: dict, *, force: bool = False) -> None:
    """Save local preferences first; commit the target only after they succeed.

    Two files cannot form one atomic transaction. If the shared save fails,
    local placement may have saved, but the running target remains unchanged.
    """
    snapshot = deepcopy(proposed)
    shared = shared_fields(snapshot)
    baseline = getattr(current, "shared_baseline", shared_fields(current))
    changed = force or shared != baseline or config.get_death_datetime(current) is None
    if changed and isinstance(current, Settings) and _token() != current.disk_token:
        raise ValueError("The shared settings changed since this clock opened. "
                         "Close and reopen the clock to review them before saving.")
    normalized, repaired = config._normalize(shared)
    if repaired:
        raise ValueError("Invalid profile; nothing was saved.")
    save_preferences(snapshot)
    if changed:
        if isinstance(current, Settings) and _token() != current.disk_token:
            raise ValueError("Shared settings changed during saving. Reopen the clock "
                             "to review them. Your running target is unchanged.")
        config.save_config(shared, shared_only=True)
    current.clear()
    current.update(snapshot)
    if isinstance(current, Settings) and changed:
        current.shared_baseline = shared_fields(normalized)
        # Derive from the bytes we wrote, not a potentially newer synced file.
        current.disk_token = hashlib.sha256(
            json.dumps(current.shared_baseline, indent=2).encode("utf-8")
        ).digest()


def read_export(path: str) -> dict:
    """Strictly validate a portable target; never calculate or silently repair it."""
    raw = config._read_object(path)
    profile = {key: raw[key] for key in PROFILE_KEYS if key in raw}
    if set(profile) != set(PROFILE_KEYS):
        raise ValueError("Choose a countdown export or settings file with a complete profile.")
    normalized, repaired = config._normalize(profile)
    if repaired or config.get_death_datetime(normalized) is None:
        raise ValueError("The file contains an invalid profile or saved target.")
    return {key: normalized[key] for key in PROFILE_KEYS}


def export_profile(current: dict, path: str) -> None:
    """Export only the saved profile; never include placement or login settings."""
    destination = Path(path).resolve()
    shared = Path(config.CONFIG_PATH).resolve()
    local = Path(device_path()).resolve()
    if (destination.parent == shared.parent and destination.name.casefold().startswith(shared.name.casefold())
            or destination.parent == local.parent):
        raise ValueError("Choose a separate export file, outside the app's managed settings.")
    profile = {key: current[key] for key in PROFILE_KEYS}
    normalized, repaired = config._normalize(profile)
    if repaired or config.get_death_datetime(normalized) is None:
        raise ValueError("There is no valid saved countdown to export.")
    config._atomic_write(str(destination), profile)


def restore_profile(current: dict, profile: dict) -> None:
    proposed = deepcopy(current)
    proposed.update({key: profile[key] for key in PROFILE_KEYS})
    commit_settings(current, proposed, force=True)
