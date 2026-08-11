"""Windows startup registration for Death Clock via Registry Run key."""

import os
import winreg

APP_NAME = "DeathClock"
_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_run_command() -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_pythonw = os.path.join(project_root, ".venv", "Scripts", "pythonw.exe")
    pythonw = venv_pythonw if os.path.isfile(venv_pythonw) else "pythonw.exe"
    run_script = os.path.join(project_root, "run.pyw")
    return f'"{pythonw}" "{run_script}"'


def add_to_startup() -> None:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_run_command())
    winreg.CloseKey(key)


def remove_from_startup() -> None:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass


def is_in_startup() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
