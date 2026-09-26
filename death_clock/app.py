"""
Death Clock application orchestrator.

This module ties everything together:
- Loads config (including the stored death date)
- Creates the countdown widget
- Creates the system tray icon
- Handles show/hide, settings, and exit

Think of this as the "manager" — it doesn't do the visual work itself,
it just coordinates the other pieces.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageDraw

from .config import get_death_datetime
from .storage import load_settings as load_config, save_preferences as save_config
from .widget import CountdownWidget
from .settings_window import SettingsWindow
from .display_window import DisplayWindow
from .diagnostics import report_error

# pystray creates the system tray icon
import pystray
from pystray import MenuItem as Item, Menu


def _make_tray_icon_image() -> Image.Image:
    """
    Generate a simple clock icon for the system tray.

    We draw it programmatically with Pillow so we don't need an image file.
    Result: a small gray circle with green clock hands.
    """
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gray circle background
    margin = 4
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill="#3a3a3a", outline="#666666", width=2)

    # Green clock hands (12 o'clock and 3 o'clock position)
    cx, cy = size // 2, size // 2
    # Hour hand pointing up
    draw.line([cx, cy, cx, cy - 16], fill="#44cc77", width=3)
    # Minute hand pointing right
    draw.line([cx, cy, cx + 18, cy], fill="#44cc77", width=2)
    # Center dot
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill="#44cc77")

    return img


class App:
    """
    Main application class. Create one instance and call run().

    Lifetime of the app:
    1. Load config from disk
    2. Create the hidden tkinter root (needed as anchor for all windows)
    3. Check if death date is saved — if not, open Settings first
    4. Create the countdown widget
    5. Create the system tray icon in a background thread
    6. Enter the tkinter event loop (blocks until exit is called)
    """

    def __init__(self, instance=None):
        self.instance = instance
        self._settings_window = None
        self.load_warnings = []
        self.config = load_config(self.load_warnings.append)
        self.tray_icon: pystray.Icon | None = None
        self.widget: CountdownWidget | None = None

        # The "root" is a hidden window that acts as the parent for everything.
        # It never appears on screen — the widget is a separate Toplevel window.
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window immediately
        self.root.report_callback_exception = self._callback_error

        # Prevent the root window from closing the app on Alt+F4
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

    def run(self):
        """Start the application."""
        death_dt = get_death_datetime(self.config)

        if death_dt is None:
            # First launch or no data — open settings immediately
            # We need to show settings before the widget exists
            self._open_first_run_settings()
        else:
            # Normal launch — create widget with stored death date
            self._create_widget(death_dt)
            self._start_tray()

        if self.load_warnings:
            self.root.after(0, self._show_load_warnings)
        if getattr(self, "instance", None) is not None:
            self.root.after(0, self._poll_show_requests)

        # Enter the tkinter event loop — this runs until self.root.quit() is called
        self.root.mainloop()

    def _create_widget(self, death_dt):
        """Create the countdown overlay widget."""
        self.widget = CountdownWidget(
            root=self.root,
            death_datetime=death_dt,
            config=self.config,
            on_settings=self._open_settings,
            on_exit=self._exit,
            on_display_settings=self._open_display_settings,
        )
        # When the widget moves/resizes, save the new position to disk
        self.widget.on_window_change = self._save_preferences

    def _start_tray(self):
        """Start the system tray icon in a background thread."""
        icon_image = _make_tray_icon_image()

        # Build the tray right-click menu
        menu = Menu(
            Item("Show",     self._tray_show, default=True),  # Default = double-click action
            Item("Reset position", self._tray_reset_position),
            Item("Settings", self._tray_settings),
            Item("Display…", self._tray_display_settings),
            Menu.SEPARATOR,
            Item("Exit",     self._tray_exit),
        )

        self.tray_icon = pystray.Icon(
            name="DeathClock",
            icon=icon_image,
            title="Death Clock",
            menu=menu,
        )

        # Run tray in a daemon thread (dies when main thread exits)
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()

    def _run_tray(self):
        try:
            self.tray_icon.run()
        except Exception as error:
            report_error("system tray", error,
                         "The Death Clock tray icon could not start. Use the clock's "
                         "right-click menu to exit, then launch it again. Your target "
                         "has not been recalculated.")

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_first_run_settings(self):
        """
        Open settings on first launch (no death date stored yet).
        After the user saves, create the widget and start the tray.
        """
        def on_first_save(updated_config, death_dt):
            self.config = updated_config
            self._create_widget(death_dt)
            self._start_tray()

        def on_first_close(was_saved: bool):
            # At this point nothing else exists yet -- no widget, no tray icon.
            # If the user closed the form without saving, there is no remaining
            # way to interact with the app, and because we launch via pythonw.exe
            # there is no console either. Without this the process would sit in
            # mainloop() completely invisible, killable only via Task Manager.
            if not was_saved:
                self._exit()

        self._settings_window = SettingsWindow(self.root, self.config,
                                               on_save=on_first_save,
                                               on_close=on_first_close)

    def _open_settings(self):
        """Open the settings window from the widget's right-click menu."""
        if self._raise_settings():
            return
        def on_settings_save(updated_config, death_dt):
            self.config = updated_config
            if self.widget:
                self.widget.update_death_datetime(death_dt)

        self._settings_window = SettingsWindow(self.root, self.config, on_save=on_settings_save)

    def _raise_settings(self):
        settings = getattr(self, "_settings_window", None)
        if settings is not None and settings.win.winfo_exists():
            settings.win.deiconify()
            settings.win.lift()
            settings.win.focus_force()
            return True
        return False

    def _open_display_settings(self):
        if self._raise_settings():
            return
        self._settings_window = DisplayWindow(self.root, self.config,
                                              self.widget.apply_display_preferences)

    def _tray_display_settings(self, icon=None, item=None):
        self.root.after(0, self._open_display_settings)

    def _poll_show_requests(self):
        if self.instance.take_show_request():
            self._show_widget()
        self.root.after(250, self._poll_show_requests)

    def _callback_error(self, _kind, error, _traceback):
        report_error("interface callback", error)

    def close(self):
        """Release windows/tray before the process releases single-instance ownership."""
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        finally:
            self.root.destroy()

    # ── Tray callbacks ────────────────────────────────────────────────────────

    def _tray_show(self, icon=None, item=None):
        """Show the widget when clicked from the tray."""
        # Tray callbacks run in the tray thread — schedule UI work on the main thread
        self.root.after(0, self._show_widget)

    def _show_widget(self):
        if self.widget:
            self.widget.show()
        self._raise_settings()

    def _tray_settings(self, icon=None, item=None):
        """Open settings from the tray menu."""
        self.root.after(0, self._open_settings)

    def _tray_reset_position(self, icon=None, item=None):
        self.root.after(0, self._reset_widget_position)

    def _reset_widget_position(self):
        if self.widget:
            self.widget.reset_position()

    def _tray_exit(self, icon=None, item=None):
        """Exit the whole app from the tray menu."""
        self.root.after(0, self._exit)

    def _show_load_warnings(self):
        messagebox.showwarning("Settings recovery", "\n\n".join(self.load_warnings),
                               parent=self.root)

    def _save_preferences(self):
        try:
            save_config(self.config)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "Window position not saved",
                f"The countdown is still running. Your window position may not be "
                f"remembered next time.\n\n{error}", parent=self.root,
            )

    # ── Exit ──────────────────────────────────────────────────────────────────

    def _exit(self):
        """Exit even if storage is unavailable; never save empty first-run defaults."""
        try:
            if self.widget:
                self._save_preferences()
        finally:
            try:
                if self.tray_icon:
                    self.tray_icon.stop()
            finally:
                self.root.quit()
