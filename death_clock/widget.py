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
from datetime import datetime


# ── Colors ────────────────────────────────────────────────────────────────────
BG_COLOR       = "#2d2d2d"   # Dark neutral gray background
BORDER_COLOR   = "#444444"   # Slightly lighter gray for the thin border
TEXT_COLOR     = "#44cc77"   # Soft green for the countdown numbers
LABEL_COLOR    = "#888888"   # Dim gray for the small "TIME REMAINING" label
GRIP_COLOR     = "#555555"   # Gray for the resize handle triangle
FONT_FAMILY    = "Consolas"  # Monospace so digits don't jump around


class CountdownWidget:
    """The floating always-on-top countdown clock."""

    # Minimum window dimensions when resizing
    MIN_WIDTH  = 280
    MIN_HEIGHT = 90

    def __init__(self, root: tk.Tk, death_datetime: datetime, config: dict,
                 on_settings: callable, on_exit: callable):
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

        # Drag tracking
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Resize tracking
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._resize_start_w = 0
        self._resize_start_h = 0

        # Callback for when the window moves/resizes (so app.py can save to disk)
        self.on_window_change: callable | None = None

        # Create the actual visible window as a Toplevel (child of the hidden root)
        self.win = tk.Toplevel(root)
        self._setup_window()
        self._build_ui()
        self._bind_events()

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
        self.win.attributes("-alpha", 0.93)

        self.win.configure(bg=BORDER_COLOR)

        # Restore last-saved position and size, clamped to screen bounds
        win_cfg = self.config.get("window", {})
        w = max(self.MIN_WIDTH,  win_cfg.get("width",  440))
        h = max(self.MIN_HEIGHT, win_cfg.get("height", 120))
        x = win_cfg.get("x", 100)
        y = win_cfg.get("y", 100)

        # Keep the widget reachable, but don't force it fully on-screen.
        #
        # Negative coordinates are legitimate: they happen when you park the
        # widget slightly past the left or top edge, or on a second monitor
        # positioned to the left of the primary one. The old code clamped to
        # a minimum of 0, which quietly nudged the widget right every launch.
        #
        # Instead we only reposition when almost none of it would be visible
        # (e.g. after unplugging the monitor it was living on). VISIBLE_MARGIN
        # is how many pixels must stay on-screen so you can still grab it.
        VISIBLE_MARGIN = 60
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        x = max(VISIBLE_MARGIN - w, min(x, screen_w - VISIBLE_MARGIN))
        y = max(VISIBLE_MARGIN - h, min(y, screen_h - VISIBLE_MARGIN))

        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # Remember the restored size so _build_ui() can scale the fonts to match.
        # We can't ask the window for its own width here -- it hasn't been drawn
        # yet, so winfo_width() would report 1.
        self._restored_width = w
        self._restored_height = h

        # Block Alt+F4 (it would kill the whole process since we have no title bar)
        self.win.bind("<Alt-F4>", lambda e: "break")

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        """Create all the visual elements inside the window."""
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
        menu.add_separator()
        menu.add_command(label="Hide",      command=self.hide)
        menu.add_command(label="Exit",      command=self.on_exit)
        # Show the menu at the cursor position
        menu.tk_popup(event.x_root, event.y_root)

    # ── Drag to move ──────────────────────────────────────────────────────────

    def _drag_start(self, event):
        """Record where the drag started."""
        self._drag_start_x = event.x_root - self.win.winfo_x()
        self._drag_start_y = event.y_root - self.win.winfo_y()

    def _drag_move(self, event):
        """Move the window as the mouse drags."""
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.win.geometry(f"+{x}+{y}")

    def _drag_end(self, _event):
        """Save the new position when the drag is released."""
        self._save_window_state()

    # ── Resize ────────────────────────────────────────────────────────────────

    def _resize_start(self, event):
        """Record the starting point and window size for a resize operation."""
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.win.winfo_width()
        self._resize_start_h = self.win.winfo_height()

    def _resize_move(self, event):
        """Resize the window as the grip is dragged."""
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        new_w = max(self.MIN_WIDTH,  self._resize_start_w + dx)
        new_h = max(self.MIN_HEIGHT, self._resize_start_h + dy)
        self.win.geometry(f"{new_w}x{new_h}")
        self._scale_fonts(new_w, new_h)

    def _resize_end(self, _event):
        """Save the new size when resize is done."""
        self._save_window_state()

    def _scale_fonts(self, width: int, height: int):
        """Scale the countdown font to fit the window size."""
        # Derive font size from window dimensions — bigger window = bigger text
        size = max(12, min(int(width / 16), int(height / 3.5)))
        small = max(8, size // 3)
        self.label_countdown.configure(font=(FONT_FAMILY, size, "bold"))
        self.label_top.configure(font=(FONT_FAMILY, small, "bold"))
        self.label_date.configure(font=(FONT_FAMILY, small))

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
        now = datetime.now()
        remaining = self.death_datetime - now

        if remaining.total_seconds() <= 0:
            self.label_countdown.configure(text="TIME'S UP")
            self.label_date.configure(text="")
            return

        # Break total seconds down into years / days / hours / minutes / seconds
        total_secs = int(remaining.total_seconds())
        years, rem = divmod(total_secs, 365 * 24 * 3600)
        days,  rem = divmod(rem,        24 * 3600)
        hours, rem = divmod(rem,        3600)
        mins,  secs = divmod(rem,       60)

        # Format: "38y 147d 14:22:09"
        countdown_text = f"{years}y {days:03d}d {hours:02d}:{mins:02d}:{secs:02d}"
        self.label_countdown.configure(text=countdown_text)

        death_str = self.death_datetime.strftime("%B %d, %Y")
        self.label_date.configure(text=f"Est. {death_str}")

    # ── Show / Hide ───────────────────────────────────────────────────────────

    def show(self):
        """Make the widget visible."""
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
