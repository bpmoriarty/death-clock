"""Main application orchestrator - wires together widget, tray, config."""

import sys
import threading
import tkinter as tk

from PIL import Image, ImageDraw
import pystray

from .config import load_config, save_config, get_dob
from .life_expectancy import compute_death_datetime
from .startup import add_to_startup, remove_from_startup, is_in_startup
from .ui.countdown_widget import CountdownWidget
from .ui.settings_window import SettingsWindow


class DeathClockApp:
    def __init__(self):
        self.config = load_config()
        self.death_datetime = self._compute_death()

        # Create tkinter root
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the default root window

        # Create the countdown widget in a Toplevel
        self.widget_window = tk.Toplevel(self.root)
        self.widget_window.withdraw()  # Hide until setup is complete

        self.widget = CountdownWidget(self.widget_window, self.death_datetime, self.config)
        self.widget.set_on_window_change(self._on_window_change)

        self.widget_window.deiconify()  # Show after setup

        self.settings_window = SettingsWindow(self.config, self._on_settings_save)

        # Register with Windows startup (idempotent)
        try:
            add_to_startup()
        except Exception:
            pass

        # Start system tray in background thread
        self.tray_icon = None
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()

    def _compute_death(self):
        dob = get_dob(self.config)
        return compute_death_datetime(dob, self.config["sex"], self.config["factors"])

    def _create_tray_icon_image(self):
        """Generate a simple hourglass icon with Pillow."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Hourglass shape
        draw.polygon([(12, 8), (52, 8), (32, 32)], fill="#ff3333")
        draw.polygon([(12, 56), (52, 56), (32, 32)], fill="#ff3333", outline="#ff3333")

        # Top and bottom bars
        draw.rectangle([(8, 4), (56, 10)], fill="#cccccc")
        draw.rectangle([(8, 54), (56, 60)], fill="#cccccc")

        return img

    def _run_tray(self):
        icon_image = self._create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Settings", self._open_settings),
            pystray.MenuItem("Show / Hide", self._toggle_visibility),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start on Boot", self._toggle_startup, checked=lambda item: is_in_startup()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit_app),
        )
        self.tray_icon = pystray.Icon("death_clock", icon_image, "Death Clock", menu)
        self.tray_icon.run()

    def _open_settings(self, _icon=None, _item=None):
        self.root.after(0, self.settings_window.open)

    def _toggle_visibility(self, _icon=None, _item=None):
        def _toggle():
            if self.widget_window.state() == "withdrawn":
                self.widget_window.deiconify()
                self.widget_window.attributes("-topmost", True)
            else:
                self.widget_window.withdraw()
        self.root.after(0, _toggle)

    def _toggle_startup(self, _icon=None, _item=None):
        try:
            if is_in_startup():
                remove_from_startup()
            else:
                add_to_startup()
        except Exception:
            pass

    def _exit_app(self, _icon=None, _item=None):
        save_config(self.config)
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def _on_settings_save(self, updated_config):
        self.config = updated_config
        save_config(self.config)
        self.death_datetime = self._compute_death()
        self.widget.update_death_datetime(self.death_datetime)

    def _on_window_change(self):
        save_config(self.config)

    def run(self):
        self.root.mainloop()
