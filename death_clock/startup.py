"""
Windows startup registration for Death Clock.

This module adds or removes a Windows Registry entry that makes Death Clock
launch automatically when you log in to Windows.

How Windows startup registration works:
- There's a special Registry folder: HKEY_CURRENT_USER\\...\\Run
- Any program listed there is launched when you log in
- We add an entry: "DeathClock" -> "path_to_pythonw.exe" "path_to_run.pyw"
- We use pythonw.exe (not python.exe) so no console window appears
"""

import os
import sys
import winreg

APP_NAME = "DeathClock"
_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _find_pythonw() -> str:
    """
    Find the best pythonw.exe to use for startup registration.

    Preference order:
    1. pythonw.exe in the project's .venv (most reliable — uses the right packages)
    2. pythonw.exe next to the currently running python.exe (current venv)
    3. Fall back to bare "pythonw.exe" (relies on PATH — less reliable)
    """
    project_root = _get_project_root()

    # Option 1: Project's own .venv
    venv_pythonw = os.path.join(project_root, ".venv", "Scripts", "pythonw.exe")
    if os.path.isfile(venv_pythonw):
        return venv_pythonw

    # Option 2: pythonw.exe beside the currently running Python interpreter
    current_python = sys.executable  # e.g. C:\..\.venv\Scripts\python.exe
    current_pythonw = current_python.replace("python.exe", "pythonw.exe")
    if os.path.isfile(current_pythonw):
        return current_pythonw

    # Option 3: System pythonw (last resort)
    return "pythonw.exe"


def _get_project_root() -> str:
    """Return the absolute path to the project root folder."""
    # This file is at death_clock/startup.py, so go up one level
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _build_startup_command() -> str:
    """Build the full command string for the registry entry."""
    pythonw = _find_pythonw()
    run_script = os.path.join(_get_project_root(), "run.pyw")
    # Quote both paths in case they contain spaces (common on Windows)
    return f'"{pythonw}" "{run_script}"'


def add_to_startup() -> None:
    """Register Death Clock to launch at Windows login."""
    command = _build_startup_command()
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
    winreg.CloseKey(key)


def remove_from_startup() -> None:
    """Remove Death Clock from Windows login startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass  # Already not registered — that's fine


def is_registered() -> bool:
    """Return True if Death Clock is currently registered for startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
