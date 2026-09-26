"""Small local diagnostics: no profile values, exception messages, or locals."""

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import os
from pathlib import Path
import traceback


def log_directory():
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "DeathClock" / "logs"


def record_error(stage, error):
    """Two bounded files; error messages can contain private data, so omit them."""
    try:
        directory = log_directory()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "death-clock.log"
        if path.exists() and path.stat().st_size >= 32768:
            path.replace(directory / "death-clock.previous.log")
        frames = traceback.extract_tb(error.__traceback__)[-8:]
        locations = ", ".join(f"{Path(f.filename).name}:{f.lineno}" for f in frames)
        entry = f"{datetime.now(timezone.utc).isoformat()} {stage}: {type(error).__name__} {locations}\n"
        with path.open("a", encoding="utf-8") as stream:
            stream.write(entry)
        return path
    except OSError:
        return None


def show_error(message):
    # Works even when Tk or application dependencies cannot be imported.
    api = ctypes.WinDLL("user32", use_last_error=True)
    api.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
    api.MessageBoxW.restype = ctypes.c_int
    api.MessageBoxW(None, message, "Death Clock", 0x10 | 0x10000)


def report_error(stage, error, guidance=None):
    path = record_error(stage, error)
    message = guidance or ("Death Clock encountered a problem. Your saved target was not "
                           "recalculated. Close the clock normally before repairing its setup.")
    message += f"\n\nError type: {type(error).__name__}"
    message += f"\nDiagnostic log: {path}" if path else "\nThe diagnostic log could not be written."
    show_error(message)
