"""
Settings window for Death Clock.

This is where you enter your date of birth, sex, and health/lifestyle factors.
When you click Save, it:
1. Validates your inputs
2. Recalculates your estimated death date using the actuarial engine
3. Saves everything to settings.json (including the new death date)
4. Tells the countdown widget to update immediately

Built with CustomTkinter for a cleaner look than plain tkinter.
"""

import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

from .life_expectancy import compute_death_datetime, FACTOR_LABELS
from .config import save_config


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

    def __init__(self, parent, config: dict, on_save: callable):
        """
        Args:
            parent:   The tkinter root (used as parent for the modal)
            config:   The current settings dict (will be mutated on save)
            on_save:  Callback called after successful save, receives updated config
        """
        self.config = config
        self.on_save = on_save

        # Create the settings window
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Death Clock — Settings")
        self.win.resizable(False, False)
        self.win.grab_set()  # Make it modal (blocks interaction with the widget)

        # Keep it on top while open
        self.win.attributes("-topmost", True)

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
                 "Saving will recalculate and lock in your death date.",
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
        ctk.CTkButton(
            self.win,
            text="Save & Recalculate Death Date",
            command=self._save,
            font=("Consolas", 13, "bold"),
            height=40,
            fg_color="#336644",
            hover_color="#44aa66",
        ).pack(**pad, pady=(16, 4))

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

    def _save(self):
        """Validate inputs, recalculate death date, and save to disk."""

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

        # ── Recalculate death date ─────────────────────────────────────────
        # This is the ONE place we recalculate. The result gets saved to
        # settings.json and reused on every future launch.
        death_dt = compute_death_datetime(dob, sex, factors)

        # ── Update config ──────────────────────────────────────────────────
        self.config["date_of_birth"]    = dob_str
        self.config["sex"]              = sex
        self.config["factors"]          = factors
        self.config["death_datetime_iso"] = death_dt.isoformat()
        self.config["start_on_boot"]    = start_on_boot

        # ── Handle startup registration ────────────────────────────────────
        try:
            from .startup import add_to_startup, remove_from_startup
            if start_on_boot:
                add_to_startup()
            else:
                remove_from_startup()
        except Exception:
            pass  # Startup registration is best-effort — don't crash if it fails

        # ── Save to disk ───────────────────────────────────────────────────
        save_config(self.config)

        # ── Notify the app ─────────────────────────────────────────────────
        self.on_save(self.config, death_dt)

        # Update the reference label to show the new death date
        self.ref_label.configure(
            text=f"Saved! Death date: {death_dt.strftime('%B %d, %Y')}"
        )

        self.win.after(1500, self.win.destroy)
