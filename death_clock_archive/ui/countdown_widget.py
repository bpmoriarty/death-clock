"""Main countdown display widget - always-on-top, frameless, draggable, resizable."""

import tkinter as tk
from datetime import datetime


class CountdownWidget:
    """Frameless always-on-top countdown clock."""

    MIN_WIDTH = 300
    MIN_HEIGHT = 100

    def __init__(self, root: tk.Tk, death_datetime: datetime, config: dict):
        self.root = root
        self.death_datetime = death_datetime
        self.config = config

        # Drag state
        self._drag_x = 0
        self._drag_y = 0

        # Resize state
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._resize_start_w = 0
        self._resize_start_h = 0

        self._setup_window()
        self._create_widgets()
        self._bind_events()
        self._update_countdown()
        self._reassert_topmost()

    def _setup_window(self):
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.configure(bg="#0a0a0a")

        win = self.config.get("window", {})
        x = win.get("x", 100)
        y = win.get("y", 100)
        w = win.get("width", 420)
        h = win.get("height", 160)

        # Clamp to screen bounds so the window is always visible after monitor changes
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, min(x, screen_w - w))
        y = max(0, min(y, screen_h - h))

        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Prevent closing
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

    def _create_widgets(self):
        self.main_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        self.title_label = tk.Label(
            self.main_frame,
            text="TIME REMAINING",
            font=("Consolas", 10, "bold"),
            fg="#666666",
            bg="#0a0a0a",
            anchor="w",
        )
        self.title_label.pack(fill=tk.X, padx=12, pady=(8, 0))

        # Countdown display
        self.countdown_label = tk.Label(
            self.main_frame,
            text="",
            font=("Consolas", 26, "bold"),
            fg="#ff3333",
            bg="#0a0a0a",
            anchor="w",
        )
        self.countdown_label.pack(fill=tk.BOTH, expand=True, padx=12)

        # Subtitle with death date
        self.subtitle_label = tk.Label(
            self.main_frame,
            text="",
            font=("Consolas", 9),
            fg="#444444",
            bg="#0a0a0a",
            anchor="w",
        )
        self.subtitle_label.pack(fill=tk.X, padx=12, pady=(0, 4))

        # Resize grip (bottom-right corner)
        self.grip = tk.Label(
            self.main_frame,
            text="\u25e2",
            font=("Consolas", 10),
            fg="#333333",
            bg="#0a0a0a",
            cursor="size_nw_se",
        )
        self.grip.place(relx=1.0, rely=1.0, anchor="se")

        # Thin border effect
        self.border_frame = tk.Frame(self.root, bg="#331111", height=1)
        self.border_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def _bind_events(self):
        # Drag to move
        for widget in (self.main_frame, self.title_label, self.countdown_label, self.subtitle_label):
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._end_drag)

        # Resize via grip
        self.grip.bind("<Button-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._on_resize)
        self.grip.bind("<ButtonRelease-1>", self._end_resize)

        # Block Alt+F4
        self.root.bind("<Alt-F4>", lambda e: "break")

    def _start_drag(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _end_drag(self, _event):
        self._save_window_state()

    def _start_resize(self, event):
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.root.winfo_width()
        self._resize_start_h = self.root.winfo_height()

    def _on_resize(self, event):
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        new_w = max(self.MIN_WIDTH, self._resize_start_w + dx)
        new_h = max(self.MIN_HEIGHT, self._resize_start_h + dy)
        self.root.geometry(f"{new_w}x{new_h}")
        self._scale_fonts(new_w, new_h)

    def _end_resize(self, _event):
        self._save_window_state()

    def _scale_fonts(self, width, height):
        # Scale countdown font based on widget size
        base_size = max(12, min(int(width / 16), int(height / 4)))
        title_size = max(8, base_size // 3)
        subtitle_size = max(7, base_size // 3)
        self.countdown_label.configure(font=("Consolas", base_size, "bold"))
        self.title_label.configure(font=("Consolas", title_size, "bold"))
        self.subtitle_label.configure(font=("Consolas", subtitle_size))

    def _save_window_state(self):
        self.config["window"] = {
            "x": self.root.winfo_x(),
            "y": self.root.winfo_y(),
            "width": self.root.winfo_width(),
            "height": self.root.winfo_height(),
        }
        # Save will be handled by app.py via callback
        if hasattr(self, "on_window_change") and self.on_window_change:
            self.on_window_change()

    def _reassert_topmost(self):
        """Periodically re-assert topmost to stay visible."""
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            return
        self.root.after(5000, self._reassert_topmost)

    def _update_countdown(self):
        """Update the countdown display every 100ms."""
        now = datetime.now()
        remaining = self.death_datetime - now

        if remaining.total_seconds() <= 0:
            self.countdown_label.configure(text="TIME'S UP", fg="#ff0000")
            self.subtitle_label.configure(text="")
            return

        total_seconds = int(remaining.total_seconds())
        years = total_seconds // (365 * 24 * 3600)
        remainder = total_seconds % (365 * 24 * 3600)
        days = remainder // (24 * 3600)
        remainder = remainder % (24 * 3600)
        hours = remainder // 3600
        remainder = remainder % 3600
        minutes = remainder // 60
        seconds = remainder % 60

        text = f"{years}y {days:03d}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        self.countdown_label.configure(text=text)

        death_str = self.death_datetime.strftime("%B %d, %Y")
        self.subtitle_label.configure(text=f"Est. {death_str}")

        self.root.after(100, self._update_countdown)

    def update_death_datetime(self, new_datetime: datetime):
        """Update the target death datetime (called when settings change)."""
        self.death_datetime = new_datetime

    def set_on_window_change(self, callback):
        """Set callback for when window position/size changes."""
        self.on_window_change = callback
