"""Small, independent display controls; no profile fields or recalculation."""

import customtkinter as ctk
from tkinter import messagebox

from .storage import DISPLAY_DEFAULTS, commit_display

MODES = {"Years and days": "years", "Total days": "days", "Total weeks and days": "weeks"}


class DisplayWindow:
    def __init__(self, parent, config, on_save):
        self.config, self.on_save = config, on_save
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Death Clock — Display")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self.win.grab_set()
        ctk.CTkLabel(self.win, text="Display on this computer", font=("Consolas", 16, "bold")).pack(padx=24, pady=16)
        self.lock = ctk.BooleanVar(value=config.get("lock_position", False))
        self.seconds = ctk.BooleanVar(value=config.get("show_seconds", True))
        ctk.CTkCheckBox(self.win, text="Lock position and size", variable=self.lock).pack(padx=24, pady=8, anchor="w")
        ctk.CTkCheckBox(self.win, text="Show seconds", variable=self.seconds).pack(padx=24, pady=8, anchor="w")
        self.mode = ctk.StringVar(value=next(label for label, mode in MODES.items()
                                           if mode == config.get("display_mode", "years")))
        ctk.CTkOptionMenu(self.win, values=list(MODES), variable=self.mode, width=240).pack(padx=24, pady=12)
        self.opacity_label = ctk.CTkLabel(self.win, text="")
        self.opacity_label.pack()
        self.opacity = ctk.CTkSlider(self.win, from_=20, to=100, number_of_steps=80,
                                    command=self._opacity_label)
        self.opacity.set(config.get("opacity", DISPLAY_DEFAULTS["opacity"]) * 100)
        self._opacity_label(self.opacity.get())
        self.opacity.pack(padx=24, pady=8)
        ctk.CTkLabel(self.win, text="Changes apply when saved. Your target stays unchanged.",
                     wraplength=300).pack(padx=24, pady=8)
        buttons = ctk.CTkFrame(self.win, fg_color="transparent")
        buttons.pack(padx=24, pady=(8, 20))
        ctk.CTkButton(buttons, text="Cancel", width=110, command=self.win.destroy).pack(side="left", padx=4)
        ctk.CTkButton(buttons, text="Save display", width=110, command=self._save).pack(side="left", padx=4)

    def _opacity_label(self, value):
        self.opacity_label.configure(text=f"Opacity: {value:.0f}%")

    def _save(self):
        changes = {"lock_position": self.lock.get(), "show_seconds": self.seconds.get(),
                   "display_mode": MODES[self.mode.get()], "opacity": round(self.opacity.get()) / 100}
        try:
            commit_display(self.config, changes)
        except (OSError, ValueError) as error:
            messagebox.showerror("Display not saved", f"Your display and target are unchanged.\n\n{error}", parent=self.win)
            return
        self.on_save()
        self.win.destroy()
