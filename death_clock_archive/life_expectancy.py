"""Life expectancy calculation engine.

Combines SSA life table data with health/lifestyle hazard ratios
to compute an adjusted expected death datetime.
"""

from datetime import datetime, timedelta
from .ssa_life_table import get_life_expectancy

# Hazard ratios for risk/protective factors.
# Values > 1.0 reduce life expectancy (risk factors).
# Values < 1.0 increase life expectancy (protective factors).
HAZARD_RATIOS = {
    "current_smoker": 2.5,
    "former_smoker": 1.4,
    "obesity": 1.4,
    "sedentary": 1.3,
    "heavy_drinking": 1.4,
    "diabetes": 1.75,
    "regular_exercise": 0.75,
    "mediterranean_diet": 0.85,
    "college_degree": 0.85,
    "married": 0.9,
}

FACTOR_LABELS = {
    "current_smoker": "Current smoker",
    "former_smoker": "Former smoker",
    "obesity": "Obesity (BMI 35+)",
    "sedentary": "Sedentary lifestyle",
    "heavy_drinking": "Heavy drinking",
    "diabetes": "Diabetes",
    "regular_exercise": "Regular exercise",
    "mediterranean_diet": "Mediterranean diet",
    "college_degree": "College degree",
    "married": "Married",
}


def compute_death_datetime(
    date_of_birth: datetime,
    sex: str,
    factors: dict[str, bool],
) -> datetime:
    """Compute the expected death datetime.

    Args:
        date_of_birth: The user's date of birth.
        sex: 'male' or 'female'.
        factors: Dict mapping factor keys to True/False for whether they apply.

    Returns:
        Expected datetime of death.
    """
    now = datetime.now()
    age = (now - date_of_birth).days / 365.25  # float for accurate total lifespan
    age_int = int(age)                          # int for SSA table lookup

    base_remaining = get_life_expectancy(age_int, sex)

    # Combine all applicable hazard ratios
    combined_hazard = 1.0
    for factor_key, is_active in factors.items():
        if is_active and factor_key in HAZARD_RATIOS:
            combined_hazard *= HAZARD_RATIOS[factor_key]

    adjusted_remaining = max(base_remaining / combined_hazard, 0.01)

    # Anchor to DOB so the death date is a fixed calendar date, not relative to
    # when the app launches (which would reset the countdown on every restart).
    total_life_years = age + adjusted_remaining
    death_datetime = date_of_birth + timedelta(days=total_life_years * 365.25)
    return death_datetime
