"""
Windows startup registration for Death Clock.

This module adds or removes a Windows Registry entry that makes Death Clock
launch automatically when you log in to Windows.

How Windows startup registration works:
- There's a special Registry folder: HKEY_CURRENT_USER\\...\\Run
- Any program listed there is launched when you log in
- The entry launches Start Death Clock.vbs through Windows Script Host
- That checked bootstrap starts the project Python without a console window
"""

import os
import subprocess
import winreg

APP_NAME = "DeathClock"
_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_project_root() -> str:
    """Return the absolute path to the project root folder."""
    # This file is at death_clock/startup.py, so go up one level
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _build_startup_command() -> str:
    """Build the full command string for the registry entry."""
    host = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "wscript.exe")
    script = os.path.join(_get_project_root(), "Start Death Clock.vbs")
    if not os.path.isfile(host) or not os.path.isfile(script):
        raise FileNotFoundError("The Windows launcher is unavailable")
    return subprocess.list2cmdline([host, "//nologo", script])


def add_to_startup() -> None:
    """Register the same checked launcher used by the desktop shortcut."""
    command = _build_startup_command()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)


def remove_from_startup() -> None:
    """Remove Death Clock from Windows login startup."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass


def is_registered() -> bool:
    """Return True if Death Clock is currently registered for startup."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ) as key:
            command, kind = winreg.QueryValueEx(key, APP_NAME)
        return kind in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) and bool(command.strip())
    except FileNotFoundError:
        return False
