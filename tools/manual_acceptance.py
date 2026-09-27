"""Launch isolated real windows for acceptance checks without touching live data.

Run: python -B tools/manual_acceptance.py
Only the UI/storage are real: login registration is disabled, no production lock
or tray is used, and all profile files live in a newly created temporary folder.
The folder is retained for inspecting the fictional test results after exit.
"""

import json
import os
from pathlib import Path
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from death_clock import config, settings_window, startup
from death_clock.app import App


def main():
    folder = Path(tempfile.mkdtemp(prefix="death-clock-acceptance-"))
    config.CONFIG_PATH = str(folder / "settings.json")
    os.environ["LOCALAPPDATA"] = str(folder / "device")
    settings_window.is_registered = lambda: False
    startup.add_to_startup = lambda: None
    startup.remove_from_startup = lambda: None
    app = App()
    app._start_tray = lambda: None
    controller = tk.Toplevel(app.root)
    controller.title("Death Clock — Isolated acceptance")
    tk.Label(controller, text="FICTIONAL TEST ONLY — login and tray disabled").pack(padx=16, pady=12)
    for label, action in (("Settings", app._open_settings),
                          ("Display", app._open_display_settings),
                          ("Show test clock", app._show_widget),
                          ("Reset test position", app._reset_widget_position),
                          ("Exit test", app._exit)):
        tk.Button(controller, text=label, command=action).pack(fill="x", padx=16, pady=3)
    controller.protocol("WM_DELETE_WINDOW", app._exit)
    print(json.dumps({"pid": os.getpid(), "test_folder": str(folder)}), flush=True)
    try:
        app.run()
    finally:
        app.close()
        print("Isolated acceptance closed.", flush=True)


if __name__ == "__main__":
    main()
