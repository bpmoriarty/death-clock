"""
The Death Clock overlay widget.

This is the always-on-top countdown window that floats over everything else
on your screen. It has no title bar or border — just the countdown itself.

Features:
- Stays on top of other windows (including most apps, but NOT exclusive-fullscreen games)
- Drag it anywhere by clicking and dragging
- Resize it by dragging the ◢ grip in the bottom-right corner
- Right-click for a menu: Settings | Hide | Exit
- Remembers its position and size between sessions
- Gray background with green numerals
"""

import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from collections.abc import Callable
from .countdown import format_countdown

from .placement import (Placement, get_work_areas,
                        monitor_for, recover_placement, reset_placement,
                        resize_placement, fit_font_sizes)


# ── Colors ────────────────────────────────────────────────────────────────────
BG_COLOR       = "#2d2d2d"   # Dark neutral gray background
BORDER_COLOR   = "#444444"   # Slightly lighter gray for the thin border
TEXT_COLOR     = "#44cc77"   # Soft green for the countdown numbers
LABEL_COLOR    = "#b0b0b0"   # Readable gray for the small labels
GRIP_COLOR     = "#999999"   # Gray for the resize handle triangle
FONT_FAMILY    = "Consolas"  # Monospace so digits don't jump around


class CountdownWidget:
    """The floating always-on-top countdown clock."""

    def __init__(self, root: tk.Tk, death_datetime: datetime, config: dict,
                 on_settings: Callable[[], None], on_exit: Callable[[], None],
                 on_display_settings: Callable[[], None] | None = None):
        """
        Args:
            root:           The tkinter root window (hidden — we use this as the anchor)
            death_datetime: The target datetime we're counting down to
            config:         The full settings dict (for window position/size)
            on_settings:    Callback to open the settings window
            on_exit:        Callback to quit the entire application
        """
        self.death_datetime = death_datetime
        self.config = config
        self.on_settings = on_settings
        self.on_exit = on_exit
        self.on_display_settings = on_display_settings

        # Drag tracking
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Resize tracking
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._resize_start_w = 0
        self._resize_start_h = 0

        # Callback for when the window moves/resizes (so app.py can save to disk)
        self.on_window_change: Callable[[], None] | None = None
        self._interacting = False
        self._font_fit_key = None

        # Create the actual visible window as a Toplevel (child of the hidden root)
        self.win = tk.Toplevel(root)
        self._setup_window()
        self._build_ui()
        self._bind_events()
        self.apply_display_preferences()

        # Start the countdown loop and the topmost re-assertion loop
        self._tick()
        self._reassert_topmost()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        """Configure the window: frameless, always-on-top, correct size/position."""
        # overrideredirect removes the title bar and OS window decorations
        self.win.overrideredirect(True)

        # Always on top of other windows
        self.win.attributes("-topmost", True)

        # Slight transparency — 0.0 = invisible, 1.0 = fully opaque
        self.win.attributes("-alpha", self.config.get("opacity", 0.93))

        self.win.configure(bg=BORDER_COLOR)

        # Restore against individual work areas, not the desktop bounding box:
        # space between monitors is not a reachable part of the desktop.
        win_cfg = self.config.get("window", {})
        self._work_areas = get_work_areas(self.win)
        placement = recover_placement(Placement(
            win_cfg.get("x", 100), win_cfg.get("y", 100),
            win_cfg.get("width", 440), win_cfg.get("height", 120)), self._work_areas)
        self.win.geometry(placement.geometry())
        # Remember a recovery in memory; normal save/exit persists it later.
        self.config["window"] = placement.as_dict()

        # Remember the restored size so _build_ui() can scale the fonts to match.
        # We can't ask the window for its own width here -- it hasn't been drawn
        # yet, so winfo_width() would report 1.
        self._restored_width = placement.width
        self._restored_height = placement.height

        # Block Alt+F4 (it would kill the whole process since we have no title bar)
        self.win.bind("<Alt-F4>", lambda e: "break")

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        """Create all the visual elements inside the window."""
        self._measure_font = tkfont.Font(root=self.win, family=FONT_FAMILY, weight="bold")
        # Inner frame with the main background color (sits inside the thin border)
        self.frame = tk.Frame(self.win, bg=BG_COLOR, padx=10, pady=6)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # "TIME REMAINING" label at the top
        self.label_top = tk.Label(
            self.frame,
            text="TIME REMAINING",
            font=(FONT_FAMILY, 9, "bold"),
            fg=LABEL_COLOR,
            bg=BG_COLOR,
            anchor="w",
        )
        self.label_top.pack(fill=tk.X)

        # The big countdown text: "38y 147d 14:22:09"
        self.label_countdown = tk.Label(
            self.frame,
            text="--y ---d --:--:--",
            font=(FONT_FAMILY, 26, "bold"),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            anchor="w",
        )
        self.label_countdown.pack(fill=tk.BOTH, expand=True)

        # Estimated death date shown in small text below
        self.label_date = tk.Label(
            self.frame,
            text="",
            font=(FONT_FAMILY, 9),
            fg=LABEL_COLOR,
            bg=BG_COLOR,
            anchor="w",
        )
        self.label_date.pack(fill=tk.X)

        for label in (self.label_top, self.label_countdown, self.label_date):
            label.configure(padx=0, pady=0, borderwidth=0, highlightthickness=0)

        # Resize grip — the ◢ symbol in the bottom-right corner
        # Users drag this to resize the window
        self.grip = tk.Label(
            self.frame,
            text="◢",
            font=(FONT_FAMILY, 10),
            fg=GRIP_COLOR,
            bg=BG_COLOR,
            cursor="size_nw_se",  # Shows a diagonal resize cursor on hover
        )
        self.grip.place(relx=1.0, rely=1.0, anchor="se")

        # Scale the text to the size the window was actually restored at.
        # The font sizes above are just starting values; without this the
        # widget came back at its saved dimensions but with default-size text,
        # so a window you had resized looked wrong until you nudged the grip.
        self._scale_fonts(self._restored_width, self._restored_height)

    # ── Event binding ─────────────────────────────────────────────────────────

    def _bind_events(self):
        """Set up mouse events for dragging, resizing, and the right-click menu."""
        # All these widgets participate in dragging the window
        draggable = [self.frame, self.label_top, self.label_countdown, self.label_date]
        for widget in draggable:
            widget.bind("<Button-1>",        self._drag_start)
            widget.bind("<B1-Motion>",       self._drag_move)
            widget.bind("<ButtonRelease-1>", self._drag_end)
            widget.bind("<Button-3>",        self._show_context_menu)  # Right-click

        # Right-click also works on the main window
        self.win.bind("<Button-3>", self._show_context_menu)
        self.win.bind("<Configure>", self._on_configure)

        # Resize grip events
        self.grip.bind("<Button-1>",        self._resize_start)
        self.grip.bind("<B1-Motion>",       self._resize_move)
        self.grip.bind("<ButtonRelease-1>", self._resize_end)

    def _show_context_menu(self, event):
        """Show the right-click popup menu."""
        menu = tk.Menu(self.win, tearoff=0,
                       bg="#3a3a3a", fg="#dddddd",
                       activebackground="#505050", activeforeground="#ffffff",
                       relief="flat", borderwidth=0)
        menu.add_command(label="Settings",  command=self.on_settings)
        if self.on_display_settings:
            menu.add_command(label="Display…", command=self.on_display_settings)
        menu.add_separator()
        menu.add_command(label="Hide",      command=self.hide)
        menu.add_command(label="Exit",      command=self.on_exit)
        # Show the menu at the cursor position
        menu.tk_popup(event.x_root, event.y_root)

    # ── Drag to move ──────────────────────────────────────────────────────────

    def _drag_start(self, event):
        """Record where the drag started."""
        if self.config.get("lock_position", False):
            return
        self._interacting = True
        self._drag_start_x = event.x_root - self.win.winfo_x()
        self._drag_start_y = event.y_root - self.win.winfo_y()

    def _drag_move(self, event):
        """Move the window as the mouse drags."""
        if self.config.get("lock_position", False):
            return
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.win.geometry(f"+{x}+{y}")

    def _drag_end(self, _event):
        """Save the new position when the drag is released."""
        if self.config.get("lock_position", False):
            return
        self._interacting = False
        self._recover_window()
        self._save_window_state()

    # ── Resize ────────────────────────────────────────────────────────────────

    def _resize_start(self, event):
        """Record the starting point and window size for a resize operation."""
        if self.config.get("lock_position", False):
            return
        self._recover_window()
        self._interacting = True
        self._resize_origin = self._current_placement()
        self._resize_area = monitor_for(self._resize_origin, self._work_areas)
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.win.winfo_width()
        self._resize_start_h = self.win.winfo_height()

    def _resize_move(self, event):
        """Resize the window as the grip is dragged."""
        if self.config.get("lock_position", False):
            return
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        placement = resize_placement(self._resize_origin,
                                     self._resize_start_w + dx,
                                     self._resize_start_h + dy, self._resize_area)
        self.win.geometry(placement.geometry())
        self._scale_fonts(placement.width, placement.height)

    def _resize_end(self, _event):
        """Save the new size when resize is done."""
        if self.config.get("lock_position", False):
            return
        self._interacting = False
        self._recover_window()
        self._save_window_state()

    def _scale_fonts(self, width: int, height: int):
        """Measure real text; negative Tk sizes are pixels, not scaled points."""
        countdown = self.label_countdown.cget("text")
        date_text = self.label_date.cget("text")
        heading = self.label_top.cget("text")
        key = (width, height, countdown, date_text, heading)
        if key == self._font_fit_key:
            return

        def measure(text, size):
            self._measure_font.configure(size=-size)
            return self._measure_font.measure(text)

        def linespace(size):
            self._measure_font.configure(size=-size)
            return self._measure_font.metrics("linespace")

        size, small = fit_font_sizes(width, height, countdown, date_text, measure, linespace, heading)
        self.label_countdown.configure(font=(FONT_FAMILY, -size, "bold"))
        self.label_top.configure(font=(FONT_FAMILY, -small, "bold"))
        self.label_date.configure(font=(FONT_FAMILY, -small))
        self._font_fit_key = key

    def _on_configure(self, event):
        if event.widget == self.win:
            self._scale_fonts(event.width, event.height)

    def _scale_current_fonts(self):
        # Tk reports 1x1 before first mapping; the saved size is known already.
        width, height = self.win.winfo_width(), self.win.winfo_height()
        self._scale_fonts(width if width > 1 else self._restored_width,
                          height if height > 1 else self._restored_height)

    def _current_placement(self):
        return Placement(self.win.winfo_x(), self.win.winfo_y(),
                         self.win.winfo_width(), self.win.winfo_height())

    def _apply_placement(self, placement):
        self.win.geometry(placement.geometry())
        self.win.update_idletasks()
        self._scale_fonts(placement.width, placement.height)

    def _recover_window(self):
        self._work_areas = get_work_areas(self.win, self._work_areas)
        self.win.update_idletasks()
        current = self._current_placement()
        recovered = recover_placement(current, self._work_areas)
        if recovered != current:
            self._apply_placement(recovered)
            return True
        return False

    def reset_position(self):
        """Bring a hidden or misplaced clock to the primary screen and save it."""
        self._work_areas = get_work_areas(self.win, self._work_areas)
        placement = reset_placement(self._current_placement(), self._work_areas)
        self._apply_placement(placement)
        self.show()
        self._save_window_state()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_window_state(self):
        """Save current position and size to config, then write to disk."""
        self.config["window"] = {
            "x":      self.win.winfo_x(),
            "y":      self.win.winfo_y(),
            "width":  self.win.winfo_width(),
            "height": self.win.winfo_height(),
        }
        if self.on_window_change:
            self.on_window_change()

    # ── Topmost re-assertion ──────────────────────────────────────────────────

    def _reassert_topmost(self):
        """
        Re-assert always-on-top every 5 seconds.

        Some apps temporarily steal focus and push our window down. This keeps
        nudging it back to the top. (Note: exclusive-fullscreen games override
        this — nothing can sit on top of them at the OS level.)
        """
        try:
            areas = get_work_areas(self.win, self._work_areas)
            if not self._interacting and areas != self._work_areas:
                if self._recover_window():
                    self._save_window_state()
            if self.is_visible() and self.win.grab_current() is None:
                self.win.attributes("-topmost", True)
                self.win.lift()
        except tk.TclError:
            return  # Window was destroyed
        self.win.after(5000, self._reassert_topmost)

    # ── Countdown loop ────────────────────────────────────────────────────────

    def _tick(self):
        """
        Update the countdown display every second.

        This simply calculates (stored_death_date - now) and formats it.
        It never recalculates the death date — that only happens in settings.
        """
        try:
            self._update_display()
        except tk.TclError:
            return  # Window was destroyed — stop the loop
        # Schedule next update in 1000ms (1 second)
        self.win.after(1000, self._tick)

    def _update_display(self):
        """Format remaining time and update labels."""
        display = format_countdown(self.death_datetime, datetime.now(),
                                   self.config.get("display_mode", "years"),
                                   self.config.get("show_seconds", True))
        self.label_top.configure(text=display.heading)
        self.label_countdown.configure(text=display.countdown)
        self.label_date.configure(text=display.target)
        self._scale_current_fonts()

    def apply_display_preferences(self):
        """Apply saved appearance without showing, lifting, or changing the target."""
        self._interacting = False
        self.win.attributes("-alpha", self.config.get("opacity", 0.93))
        if self.config.get("lock_position", False):
            self.grip.place_forget()
        else:
            self.grip.place(relx=1.0, rely=1.0, anchor="se")
        self._update_display()

    # ── Show / Hide ───────────────────────────────────────────────────────────

    def show(self):
        """Make the widget visible."""
        if self._recover_window():
            self._save_window_state()
        self.win.deiconify()
        self.win.attributes("-topmost", True)
        self.win.lift()

    def hide(self):
        """Hide the widget (it keeps running in the tray)."""
        self.win.withdraw()

    def is_visible(self) -> bool:
        """Return True if the widget is currently visible."""
        return self.win.state() != "withdrawn"

    # ── Death date update ─────────────────────────────────────────────────────

    def update_death_datetime(self, new_dt: datetime):
        """
        Called when the user saves new health info in Settings.
        Updates the target and immediately refreshes the display.
        """
        self.death_datetime = new_dt
        self._update_display()
