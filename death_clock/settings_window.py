"""Explicit reminder target selection, profile restore, and local login controls."""

from collections.abc import Callable
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox, filedialog

from .factors import FACTOR_LABELS, RISK_FACTORS, PROTECTIVE_FACTORS
from .config import get_death_datetime
from .targets import MODES, propose_target
from .storage import commit_settings as commit_config, export_profile, read_export, restore_profile
from .startup import is_registered


# Match the rest of the app's dark theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class SettingsWindow:
    """Modal window for editing health profile and preferences."""

    def __init__(self, parent, config: dict, on_save: Callable, on_close: Callable | None = None):
        """
        Args:
            parent:   The tkinter root (used as parent for the modal)
            config:   The current settings dict (will be mutated on save)
            on_save:  Callback called after successful save, receives updated config
            on_close: Optional callback fired when the window is closed with the
                      X button. Receives True if a save happened first, False if
                      the user backed out. app.py uses this on first launch to
                      shut down cleanly rather than linger with no UI.
        """
        self.config = config
        self.on_save = on_save
        self.on_close = on_close

        # Tracks whether the user actually saved before closing
        self._saved = False

        # Create the settings window
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Death Clock — Settings")
        self.win.resizable(True, True)
        self.win.grab_set()  # Make it modal (blocks interaction with the widget)

        # Keep it on top while open
        self.win.attributes("-topmost", True)

        # Intercept the X button so the caller can react to being dismissed.
        # (This only fires for the window manager's close button -- calling
        # self.win.destroy() ourselves after a save does not trigger it.)
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()

        # Center on screen
        self.win.update_idletasks()
        w = min(520, self.win.winfo_screenwidth() - 40)
        h = min(680, self.win.winfo_screenheight() - 100)
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build_ui(self):
        """Keep actions visible while the input area scrolls."""
        self.body = ctk.CTkScrollableFrame(self.win, width=440, height=390)
        self.body.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(self.body, text="Choose your reminder target",
                     font=("Consolas", 16, "bold")).pack(pady=8)
        ctk.CTkLabel(self.body, text="Your saved countdown stays unchanged unless you confirm a new target.",
                     wraplength=400).pack(pady=6)
        self.target_mode = ctk.StringVar(value="Keep saved target" if get_death_datetime(self.config)
                                        else "Choose a date")
        ctk.CTkOptionMenu(self.body, values=list(MODES), variable=self.target_mode,
                           command=self._show_target_fields, width=280).pack(pady=8)
        self.date_frame = ctk.CTkFrame(self.body)
        ctk.CTkLabel(self.date_frame, text="Target date (YYYY-MM-DD), at midnight").pack(padx=12, pady=6)
        self.target_entry = ctk.CTkEntry(self.date_frame, placeholder_text="e.g. 2080-06-15", width=220)
        self.target_entry.pack(padx=12, pady=6)
        self.age_frame = ctk.CTkFrame(self.body)
        ctk.CTkLabel(self.age_frame, text="Target age (whole years, 1–150)").pack(padx=12, pady=6)
        self.age_entry = ctk.CTkEntry(self.age_frame, width=220)
        self.age_entry.pack(padx=12, pady=6)
        ctk.CTkLabel(self.age_frame, text="Uses midnight on that birthday; Feb 29 becomes Feb 28 in non-leap years.",
                     wraplength=380).pack(padx=12, pady=6)
        self.profile_frame = ctk.CTkFrame(self.body)
        ctk.CTkLabel(self.profile_frame, text="Birth date (YYYY-MM-DD)").pack(padx=12, pady=6)
        self.dob_entry = ctk.CTkEntry(self.profile_frame, width=220)
        self.dob_entry.pack(padx=12, pady=6)
        self.dob_entry.insert(0, self.config.get("date_of_birth", ""))
        self.legacy_frame = ctk.CTkFrame(self.body)
        ctk.CTkLabel(self.legacy_frame, text="Optional legacy calculation",
                     font=("Consolas", 14, "bold")).pack(pady=8)
        ctk.CTkLabel(self.legacy_frame, text="An approximate, unvalidated reminder formula—not a personal "
                     "longevity prediction. Its base table matches SSA 2021 (2024 report); "
                     "its factor adjustments are still unvalidated. "
                     "A new calculation depends on today's date. You will preview it before saving.",
                     wraplength=380, text_color="#cccccc").pack(padx=12, pady=6)
        self.sex_var = ctk.StringVar(value=self.config.get("sex", "male"))
        ctk.CTkOptionMenu(self.legacy_frame, variable=self.sex_var, values=["male", "female"]).pack(pady=8)
        self.factor_vars = {}
        for key in RISK_FACTORS + PROTECTIVE_FACTORS:
            var = ctk.BooleanVar(value=self.config.get("factors", {}).get(key, False))
            self.factor_vars[key] = var
            ctk.CTkCheckBox(self.legacy_frame, text=FACTOR_LABELS[key], variable=var).pack(
                anchor="w", padx=12, pady=4)
        self._show_target_fields()

        self._startup_available = True
        try:
            registered = is_registered()
        except OSError:
            registered = False
            self._startup_available = False
        self.startup_var = ctk.BooleanVar(value=registered)
        startup_checkbox = ctk.CTkCheckBox(self.win, text="Start automatically when I sign in",
                                          variable=self.startup_var)
        startup_checkbox.pack(padx=20, pady=6)
        if not self._startup_available:
            startup_checkbox.configure(state="disabled")
            ctk.CTkLabel(self.win, text="Windows login setting could not be read.").pack()
        transfer = ctk.CTkFrame(self.win, fg_color="transparent")
        transfer.pack(pady=6)
        ctk.CTkButton(transfer, text="Export countdown…", command=self._export).pack(side="left", padx=4)
        ctk.CTkButton(transfer, text="Restore countdown…", command=self._restore).pack(side="left", padx=4)
        self.ref_label = ctk.CTkLabel(self.win, text="Saved target: " +
                                     (self.config.get("death_datetime_iso") or "None"),
                                     wraplength=460, text_color="#b0b0b0")
        self.ref_label.pack(padx=12, pady=4)
        actions = ctk.CTkFrame(self.win, fg_color="transparent")
        actions.pack(pady=(4, 12))
        ctk.CTkButton(actions, text="Cancel", command=self._close, width=110).pack(side="left", padx=4)
        self.save_button = ctk.CTkButton(actions, text="Save settings", command=self._save)
        self.save_button.pack(side="left", padx=4)

    def _show_target_fields(self, _selection=None):
        mode = self.target_mode.get()
        for frame in (self.date_frame, self.age_frame, self.profile_frame, self.legacy_frame):
            frame.pack_forget()
        if mode == "Choose a date":
            self.date_frame.pack(fill="x", pady=8)
        if mode == "Choose an age":
            self.age_frame.pack(fill="x", pady=8)
        if mode in ("Choose an age", "Legacy calculation"):
            self.profile_frame.pack(fill="x", pady=8)
        if mode == "Legacy calculation":
            self.legacy_frame.pack(fill="x", pady=8)

    def _close(self):
        """Handle the window's X button, telling the caller whether we saved."""
        self.win.destroy()
        if self.on_close:
            self.on_close(self._saved)

    def _export(self):
        path = filedialog.asksaveasfilename(parent=self.win, title="Export saved countdown",
                                          defaultextension=".json",
                                          initialfile="countdown.deathclock-export.json",
                                          filetypes=[("Countdown file", "*.json")])
        if not path:
            return
        try:
            export_profile(self.config, path)
        except (OSError, ValueError, KeyError) as error:
            messagebox.showerror("Export failed", str(error), parent=self.win)
            return
        messagebox.showinfo("Countdown exported", "The saved target and profile were exported. "
                            "This file includes your birth date and health selections; "
                            "keep it private. Unsaved form edits were not exported.", parent=self.win)

    def _restore(self):
        if self._saved:
            return
        path = filedialog.askopenfilename(parent=self.win, title="Restore a saved countdown",
                                         filetypes=[("Countdown file", "*.json")])
        if not path:
            return
        try:
            profile = read_export(path)
            current = self.config.get("death_datetime_iso") or "None"
            if not messagebox.askyesno("Restore countdown?",
                    f"Current target: {current}\nRestored target: {profile['death_datetime_iso']}\n\n"
                    "Replace the saved target and profile? A backup will be kept. "
                    "Unsaved form edits will be discarded. This computer's placement "
                    "and login setting stay as they are.", parent=self.win):
                return
            restore_profile(self.config, profile)
        except (OSError, ValueError, KeyError) as error:
            messagebox.showerror("Countdown not restored", str(error), parent=self.win)
            return
        self._saved = True
        self.save_button.configure(state="disabled")
        self.on_save(self.config, get_death_datetime(self.config))
        self.win.destroy()

    def _save(self):
        if self._saved:
            return
        mode = self.target_mode.get()
        try:
            proposed = propose_target(
                self.config, mode, self.target_entry.get(), self.age_entry.get(),
                self.dob_entry.get(), self.sex_var.get(),
                {key: var.get() for key, var in self.factor_vars.items()})
        except (ValueError, OverflowError) as error:
            messagebox.showerror("Target not saved", str(error), parent=self.win)
            return
        if mode != "Keep saved target":
            old = self.config.get("death_datetime_iso") or "None"
            target = proposed["death_datetime_iso"]
            explanation = "A backup will be kept. No change happens until you confirm."
            if get_death_datetime(proposed) <= datetime.now():
                explanation += "\nThis date has passed; the clock will show Make today count."
            if not messagebox.askyesno("Confirm reminder target",
                    f"Current target: {old}\nProposed target: {target}\n\n{explanation}",
                    parent=self.win):
                return
        proposed["start_on_boot"] = self.startup_var.get()
        try:
            commit_config(self.config, proposed)
        except (OSError, ValueError) as error:
            messagebox.showerror("Settings not saved",
                    f"Your running target is unchanged.\n\n{error}", parent=self.win)
            return
        self._saved = True
        self.save_button.configure(state="disabled")
        try:
            if self._startup_available:
                from .startup import add_to_startup, remove_from_startup
                if self.startup_var.get():
                    add_to_startup()
                else:
                    remove_from_startup()
        except OSError as error:
            messagebox.showwarning("Countdown saved; Windows startup not updated",
                                   str(error), parent=self.win)
        death_dt = get_death_datetime(self.config)
        self.on_save(self.config, death_dt)
        self.ref_label.configure(text=f"Saved target: {self.config['death_datetime_iso']}")
        self.win.after(1500, self.win.destroy)
