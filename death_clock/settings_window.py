"""
Settings window for Death Clock.

This is where you enter your date of birth, sex, and health/lifestyle factors.
When you click Save, it:
1. Validates your inputs
2. Recalculates your estimated death date using the actuarial engine --
   but only if the date of birth, sex or factors actually changed. Saving
   with those untouched keeps the stored date exactly as it was.
3. Saves everything to settings.json
4. Tells the countdown widget to update immediately

Built with CustomTkinter for a cleaner look than plain tkinter.
"""

from copy import deepcopy
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

from .life_expectancy import compute_death_datetime, FACTOR_LABELS
from .config import commit_config, get_death_datetime, stored_date_matches_inputs


# Match the rest of the app's dark theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


# Which factors to show in the settings window, grouped by type
RISK_FACTORS = [
    "current_smoker",
    "former_smoker",
    "obesity",
    "sedentary",
    "heavy_drinking",
    "diabetes",
]

PROTECTIVE_FACTORS = [
    "regular_exercise",
    "mediterranean_diet",
    "college_degree",
    "married",
]


class SettingsWindow:
    """Modal window for editing health profile and preferences."""

    # Note: on_close has no type annotation on purpose. The rest of this file
    # uses `callable` as a shorthand hint, but `callable` is a builtin function
    # rather than a real type, so writing `callable | None` raises a TypeError
    # when Python evaluates the signature -- which would stop the app booting.
    def __init__(self, parent, config: dict, on_save: callable, on_close=None):
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
        self.win.resizable(False, False)
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
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build_ui(self):
        """Build all the form elements."""
        pad = {"padx": 20}  # pady set per-element to avoid "multiple values" error

        # ── Header ────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self.win,
            text="Your Health Profile",
            font=("Consolas", 16, "bold"),
        ).pack(**pad, pady=(16, 4))

        ctk.CTkLabel(
            self.win,
            text="This information is used to estimate your death date.\n"
                 "Your saved target changes only when you confirm a new one.",
            font=("Consolas", 11),
            text_color="#aaaaaa",
            justify="center",
        ).pack(**pad, pady=6)

        # ── Date of Birth ─────────────────────────────────────────────────────
        ctk.CTkLabel(self.win, text="Date of Birth (YYYY-MM-DD)",
                     font=("Consolas", 12)).pack(**pad, pady=(14, 2))

        self.dob_entry = ctk.CTkEntry(
            self.win, width=200,
            placeholder_text="e.g. 1986-05-30",
            font=("Consolas", 13),
        )
        self.dob_entry.pack(**pad, pady=(0, 6))
        if self.config.get("date_of_birth"):
            self.dob_entry.insert(0, self.config["date_of_birth"])

        # ── Sex ───────────────────────────────────────────────────────────────
        ctk.CTkLabel(self.win, text="Biological Sex (affects SSA life table lookup)",
                     font=("Consolas", 12)).pack(**pad, pady=(4, 2))

        self.sex_var = ctk.StringVar(value=self.config.get("sex", "male"))
        sex_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        sex_frame.pack(**pad, pady=(0, 8))
        ctk.CTkRadioButton(sex_frame, text="Male",   variable=self.sex_var,
                           value="male",   font=("Consolas", 12)).pack(side="left", padx=12)
        ctk.CTkRadioButton(sex_frame, text="Female", variable=self.sex_var,
                           value="female", font=("Consolas", 12)).pack(side="left", padx=12)

        # ── Risk Factors ──────────────────────────────────────────────────────
        ctk.CTkLabel(self.win, text="Risk Factors  (shorten life expectancy)",
                     font=("Consolas", 12, "bold"),
                     text_color="#cc6666").pack(**pad, pady=(10, 2))

        self.factor_vars = {}
        factors = self.config.get("factors", {})

        for key in RISK_FACTORS:
            var = ctk.BooleanVar(value=factors.get(key, False))
            self.factor_vars[key] = var
            ctk.CTkCheckBox(
                self.win,
                text=FACTOR_LABELS.get(key, key),
                variable=var,
                font=("Consolas", 12),
            ).pack(anchor="w", padx=30, pady=2)

        # ── Protective Factors ────────────────────────────────────────────────
        ctk.CTkLabel(self.win, text="Protective Factors  (extend life expectancy)",
                     font=("Consolas", 12, "bold"),
                     text_color="#44cc77").pack(**pad, pady=(12, 2))

        for key in PROTECTIVE_FACTORS:
            var = ctk.BooleanVar(value=factors.get(key, False))
            self.factor_vars[key] = var
            ctk.CTkCheckBox(
                self.win,
                text=FACTOR_LABELS.get(key, key),
                variable=var,
                font=("Consolas", 12),
            ).pack(anchor="w", padx=30, pady=2)

        # ── Start on Boot ─────────────────────────────────────────────────────
        ctk.CTkLabel(self.win, text="Startup",
                     font=("Consolas", 12, "bold")).pack(**pad, pady=(12, 2))

        self.startup_var = ctk.BooleanVar(value=self.config.get("start_on_boot", False))
        ctk.CTkCheckBox(
            self.win,
            text="Start Death Clock automatically when Windows boots",
            variable=self.startup_var,
            font=("Consolas", 12),
        ).pack(anchor="w", padx=30, pady=2)

        # ── Save Button ───────────────────────────────────────────────────────
        self.save_button = ctk.CTkButton(
            self.win,
            text="Save settings",
            command=self._save,
            font=("Consolas", 13, "bold"),
            height=40,
            fg_color="#336644",
            hover_color="#44aa66",
        )
        self.save_button.pack(**pad, pady=(16, 4))

        # Shows the current stored death date for reference
        stored_iso = self.config.get("death_datetime_iso", "")
        if stored_iso:
            try:
                stored_dt = datetime.fromisoformat(stored_iso)
                ref_text = f"Current death date: {stored_dt.strftime('%B %d, %Y')}"
            except ValueError:
                ref_text = ""
        else:
            ref_text = "No death date set yet — fill in the form and save."

        self.ref_label = ctk.CTkLabel(
            self.win,
            text=ref_text,
            font=("Consolas", 10),
            text_color="#666666",
        )
        self.ref_label.pack(**pad, pady=(0, 16))

    def _close(self):
        """Handle the window's X button, telling the caller whether we saved."""
        self.win.destroy()
        if self.on_close:
            self.on_close(self._saved)

    def _save(self):
        """Validate inputs, recalculate death date, and save to disk."""

        if self._saved:
            return

        # ── Validate date of birth ─────────────────────────────────────────
        dob_str = self.dob_entry.get().strip()
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Please enter your date of birth as YYYY-MM-DD\n(e.g. 1986-05-30)",
                parent=self.win,
            )
            return

        # Must be in the past
        if dob >= datetime.now():
            messagebox.showerror(
                "Invalid Date",
                "Date of birth must be in the past.",
                parent=self.win,
            )
            return

        sex = self.sex_var.get()
        factors = {key: var.get() for key, var in self.factor_vars.items()}
        start_on_boot = self.startup_var.get()

        # ── Recalculate death date, but only if it needs it ────────────────
        # This is the ONE place we recalculate. The result gets saved to
        # settings.json and reused on every future launch.
        #
        # We check the existing config BEFORE overwriting it below. If the date
        # of birth, sex and factors are all unchanged, the stored date already
        # answers this exact question and we keep it untouched -- otherwise
        # saving a preference like "launch at login" would quietly move your
        # death date, since the calculation reads today's clock.
        keeping_stored_date = stored_date_matches_inputs(
            self.config, dob_str, sex, factors
        )
        if keeping_stored_date:
            death_dt = get_death_datetime(self.config)
        else:
            death_dt = compute_death_datetime(dob, sex, factors)

        if not keeping_stored_date and get_death_datetime(self.config) is not None:
            old_dt = get_death_datetime(self.config)
            if not messagebox.askyesno(
                "Change saved target?",
                f"Current target: {old_dt:%B %d, %Y}\n"
                f"Proposed target: {death_dt:%B %d, %Y}\n\n"
                "Replace your saved countdown? A backup will be kept.",
                parent=self.win,
            ):
                return

        proposed = deepcopy(self.config)
        proposed.update(date_of_birth=dob_str, sex=sex, factors=factors,
                        start_on_boot=start_on_boot)
        # Preserve the original string exactly on preference-only saves.
        if not keeping_stored_date:
            proposed["death_datetime_iso"] = death_dt.isoformat()
        try:
            commit_config(self.config, proposed)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "Settings not saved",
                "Your running countdown has not changed. Check disk space, file "
                f"permissions, or OneDrive, then try again.\n\n{error}",
                parent=self.win,
            )
            return
        self._saved = True
        self.save_button.configure(state="disabled")

        # Registration is a separate Windows operation; a failure must be visible.
        try:
            from .startup import add_to_startup, remove_from_startup
            if start_on_boot:
                add_to_startup()
            else:
                remove_from_startup()
        except Exception as error:
            messagebox.showwarning(
                "Countdown saved; Windows startup not updated",
                f"Your target was saved, but the login setting could not be applied.\n\n{error}",
                parent=self.win,
            )

        # ── Notify the app ─────────────────────────────────────────────────
        self.on_save(self.config, death_dt)

        # Update the reference label to show the death date, and say plainly
        # whether it was recalculated -- otherwise "Saved!" next to an
        # unchanged date looks like the save silently failed.
        if keeping_stored_date:
            message = f"Saved. Death date unchanged: {death_dt.strftime('%B %d, %Y')}"
        else:
            message = f"Saved! Death date: {death_dt.strftime('%B %d, %Y')}"
        self.ref_label.configure(text=message)

        self.win.after(1500, self.win.destroy)
