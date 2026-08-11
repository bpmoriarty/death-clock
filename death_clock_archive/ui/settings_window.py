"""Settings window for updating health inputs."""

import customtkinter as ctk
from datetime import datetime
from ..life_expectancy import FACTOR_LABELS


class SettingsWindow:
    """Modal-style settings window for health input configuration."""

    def __init__(self, config: dict, on_save):
        self.config = config
        self.on_save = on_save
        self.window = None
        self.factor_vars = {}

    def open(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.focus_force()
            return

        self.window = ctk.CTkToplevel()
        self.window.title("Death Clock - Settings")
        self.window.geometry("400x620")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        main_frame = ctk.CTkScrollableFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # --- Personal Info ---
        ctk.CTkLabel(main_frame, text="Personal Information", font=("", 16, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Date of birth
        dob_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        dob_frame.pack(fill="x", pady=4)
        ctk.CTkLabel(dob_frame, text="Date of Birth:").pack(side="left")
        self.dob_entry = ctk.CTkEntry(dob_frame, width=140, placeholder_text="YYYY-MM-DD")
        self.dob_entry.pack(side="right")
        self.dob_entry.insert(0, self.config.get("date_of_birth", "1990-01-01"))

        # Sex
        sex_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        sex_frame.pack(fill="x", pady=4)
        ctk.CTkLabel(sex_frame, text="Sex:").pack(side="left")
        self.sex_var = ctk.StringVar(value=self.config.get("sex", "male"))
        self.sex_menu = ctk.CTkOptionMenu(
            sex_frame, variable=self.sex_var, values=["male", "female"], width=140
        )
        self.sex_menu.pack(side="right")

        # --- Risk Factors ---
        ctk.CTkLabel(main_frame, text="Risk Factors", font=("", 16, "bold"), text_color="#ff6666").pack(
            anchor="w", pady=(20, 10)
        )

        risk_factors = ["current_smoker", "former_smoker", "obesity", "sedentary", "heavy_drinking", "diabetes"]
        for key in risk_factors:
            var = ctk.BooleanVar(value=self.config.get("factors", {}).get(key, False))
            self.factor_vars[key] = var
            ctk.CTkCheckBox(main_frame, text=FACTOR_LABELS[key], variable=var).pack(
                anchor="w", pady=3
            )

        # --- Protective Factors ---
        ctk.CTkLabel(main_frame, text="Protective Factors", font=("", 16, "bold"), text_color="#66ff66").pack(
            anchor="w", pady=(20, 10)
        )

        protective_factors = ["regular_exercise", "mediterranean_diet", "college_degree", "married"]
        for key in protective_factors:
            var = ctk.BooleanVar(value=self.config.get("factors", {}).get(key, False))
            self.factor_vars[key] = var
            ctk.CTkCheckBox(main_frame, text=FACTOR_LABELS[key], variable=var).pack(
                anchor="w", pady=3
            )

        # --- Save Button ---
        self.status_label = ctk.CTkLabel(main_frame, text="", font=("", 11))
        self.status_label.pack(pady=(15, 5))

        ctk.CTkButton(
            main_frame, text="Save & Update", command=self._save, height=40, font=("", 14, "bold")
        ).pack(fill="x", pady=(5, 10))

    def _save(self):
        # Validate date of birth
        dob_str = self.dob_entry.get().strip()
        try:
            datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            self.status_label.configure(text="Invalid date format. Use YYYY-MM-DD.", text_color="#ff4444")
            return

        self.config["date_of_birth"] = dob_str
        self.config["sex"] = self.sex_var.get()
        for key, var in self.factor_vars.items():
            self.config["factors"][key] = var.get()

        self.on_save(self.config)
        self.status_label.configure(text="Settings saved!", text_color="#44ff44")
        self.window.after(1500, lambda: self.window.destroy() if self.window.winfo_exists() else None)
