"""
Life expectancy calculation engine.

This module takes your date of birth, sex, and health factors and returns
an estimated death datetime. This calculation should only run when you
SAVE your settings — the result is then stored in settings.json and reused
on every subsequent app launch.

How it works:
1. Look up remaining life expectancy from the SSA actuarial table (2021 data)
2. Combine any health/lifestyle hazard ratios you've selected
3. Compute: death_date = date_of_birth + (current_age + adjusted_remaining_years)

The result is anchored to your date of birth, so it's a fixed calendar date
that doesn't drift when you reopen the app.
"""

from datetime import datetime, timedelta
from .ssa_life_table import get_life_expectancy

# Hazard ratios tell us how each factor affects life expectancy.
# A value > 1.0 means the factor SHORTENS life (risk factor).
# A value < 1.0 means the factor EXTENDS life (protective factor).
# These are multiplied together to get a combined effect.
#
# Sources: Based on published epidemiological data (relative risk estimates).
HAZARD_RATIOS = {
    "current_smoker":    2.50,   # Cuts remaining life roughly in half
    "former_smoker":     1.40,   # Still meaningful long-term risk
    "obesity":           1.40,   # BMI 35+ carries significant risk
    "sedentary":         1.30,   # Inactivity is a major risk factor
    "heavy_drinking":    1.40,   # Chronic heavy drinking shortens life
    "diabetes":          1.75,   # Significant systemic disease burden
    "regular_exercise":  0.75,   # Regular exercise adds meaningful years
    "mediterranean_diet":0.85,   # Diet pattern linked to longevity
    "college_degree":    0.85,   # Education correlates with better health outcomes
    "married":           0.90,   # Social support has measurable protective effect
}

# Human-readable labels for each factor (used in the settings window)
FACTOR_LABELS = {
    "current_smoker":    "Current smoker",
    "former_smoker":     "Former smoker",
    "obesity":           "Obesity (BMI 35+)",
    "sedentary":         "Sedentary lifestyle",
    "heavy_drinking":    "Heavy drinking",
    "diabetes":          "Diabetes",
    "regular_exercise":  "Regular exercise",
    "mediterranean_diet":"Mediterranean diet",
    "college_degree":    "College degree",
    "married":           "Married / long-term partner",
}


def compute_death_datetime(
    date_of_birth: datetime,
    sex: str,
    factors: dict,
) -> datetime:
    """
    Compute and return the estimated death datetime.

    Call this ONLY when saving settings. Store the result in config and
    use the stored value for the countdown — don't call this on every launch.

    Args:
        date_of_birth: The user's date of birth as a datetime object.
        sex: 'male' or 'female'
        factors: Dict of factor keys mapped to True/False (True = applies to you)

    Returns:
        A datetime representing the estimated date of death.
    """
    now = datetime.now()

    # Calculate current age as a decimal (e.g. 38.7 years)
    age_float = (now - date_of_birth).days / 365.25

    # Look up remaining life expectancy, interpolated at the exact fractional age.
    #
    # We deliberately pass the DECIMAL age, not int(age_float). Using the whole
    # number made the result unstable: age_float crept up every day while the
    # table lookup only changed on your birthday, so the computed death date
    # drifted later day by day and then snapped ~11 months backwards each year.
    # Interpolating keeps the two in step, so the same inputs give the same
    # answer no matter which day (or machine) you calculate on.
    base_remaining_years = get_life_expectancy(age_float, sex)

    # Combine all active hazard ratios (multiply them together)
    combined_hazard = 1.0
    for factor_key, is_active in factors.items():
        if is_active and factor_key in HAZARD_RATIOS:
            combined_hazard *= HAZARD_RATIOS[factor_key]

    # Adjust remaining life by the combined hazard ratio
    # A hazard of 2.0 means remaining life is halved; 0.75 means it's extended
    adjusted_remaining_years = max(base_remaining_years / combined_hazard, 0.01)

    # Total lifespan from birth = current age + adjusted remaining years
    total_life_years = age_float + adjusted_remaining_years

    # Death date = date of birth + total lifespan
    # Anchoring to DOB (not "now") means this date stays stable across launches
    death_datetime = date_of_birth + timedelta(days=total_life_years * 365.25)

    return death_datetime
