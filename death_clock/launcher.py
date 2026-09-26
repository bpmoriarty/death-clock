"""Dependency-free bootstrap: use the project interpreter, never borrow packages."""

from pathlib import Path
import subprocess

from .diagnostics import report_error


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def runtime_paths(project_root=PROJECT_ROOT):
    scripts = Path(project_root) / ".venv" / "Scripts"
    python, pythonw = scripts / "python.exe", scripts / "pythonw.exe"
    if not python.is_file() or not pythonw.is_file():
        raise FileNotFoundError("The project Python environment is incomplete")
    return python, pythonw


def check_runtime(project_root=PROJECT_ROOT):
    python, pythonw = runtime_paths(project_root)
    # No profile reads, registry writes, GUI creation, or dependency installation.
    result = subprocess.run(
        [str(python), "-I", "-c",
         "import tkinter, customtkinter, PIL.Image, pystray; "
         "import sys; assert sys.version_info >= (3, 12)"],
        cwd=project_root, capture_output=True, timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode:
        # Never retain stdout/stderr: paths and arbitrary exception data may be private.
        raise RuntimeError("The project interpreter or dependencies could not start")
    return pythonw


def launch(project_root=PROJECT_ROOT):
    try:
        pythonw = check_runtime(project_root)
        subprocess.Popen([str(pythonw), "-B", "-m", "death_clock.main"],
                         cwd=project_root, creationflags=subprocess.CREATE_NO_WINDOW)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        report_error("launcher", error,
                     "Death Clock could not start its project Python environment.\n\n"
                     "If the clock is already running, exit it normally before making repairs. "
                     "Then follow the Setup / launch troubleshooting steps in README.md. "
                     "Do not delete settings.json. No setup changes were made automatically.")
        return 1
