"""Legacy formula inputs, centralized for compatibility, not medical guidance."""

FACTORS = (
    ("current_smoker", "Current smoker", 2.50),
    ("former_smoker", "Former smoker", 1.40),
    ("obesity", "Obesity (BMI 35+)", 1.40),
    ("sedentary", "Sedentary lifestyle", 1.30),
    ("heavy_drinking", "Heavy drinking", 1.40),
    ("diabetes", "Diabetes", 1.75),
    ("regular_exercise", "Regular exercise", 0.75),
    ("mediterranean_diet", "Mediterranean diet", 0.85),
    ("college_degree", "College degree", 0.85),
    ("married", "Married / long-term partner", 0.90),
)
HAZARD_RATIOS = {key: ratio for key, _, ratio in FACTORS}
FACTOR_LABELS = {key: label for key, label, _ in FACTORS}
FACTOR_DEFAULTS = {key: False for key, _, _ in FACTORS}
RISK_FACTORS = [key for key, _, ratio in FACTORS if ratio > 1]
PROTECTIVE_FACTORS = [key for key, _, ratio in FACTORS if ratio < 1]
