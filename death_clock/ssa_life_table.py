"""
Legacy embedded table, originally labeled SSA 2021; source fidelity unverified.
Original reference: https://www.ssa.gov/oact/STATS/table4c6.html

Each dictionary maps age (int) to remaining life expectancy e(x) in years.
"""

# Male life expectancy e(x) by exact age
MALE_LIFE_EXPECTANCY = {
    0: 73.50, 1: 72.98, 2: 71.99, 3: 71.00, 4: 70.01,
    5: 69.02, 6: 68.02, 7: 67.03, 8: 66.03, 9: 65.04,
    10: 64.04, 11: 63.05, 12: 62.05, 13: 61.06, 14: 60.07,
    15: 59.08, 16: 58.10, 17: 57.13, 18: 56.16, 19: 55.20,
    20: 54.25, 21: 53.31, 22: 52.37, 23: 51.44, 24: 50.50,
    25: 49.57, 26: 48.64, 27: 47.71, 28: 46.78, 29: 45.85,
    30: 44.92, 31: 43.99, 32: 43.06, 33: 42.14, 34: 41.21,
    35: 40.29, 36: 39.37, 37: 38.45, 38: 37.54, 39: 36.63,
    40: 35.72, 41: 34.82, 42: 33.92, 43: 33.03, 44: 32.14,
    45: 31.26, 46: 30.39, 47: 29.53, 48: 28.67, 49: 27.82,
    50: 26.98, 51: 26.15, 52: 25.33, 53: 24.52, 54: 23.72,
    55: 22.93, 56: 22.15, 57: 21.38, 58: 20.62, 59: 19.87,
    60: 19.13, 61: 18.40, 62: 17.69, 63: 16.98, 64: 16.29,
    65: 15.61, 66: 14.94, 67: 14.28, 68: 13.63, 69: 13.00,
    70: 12.37, 71: 11.76, 72: 11.17, 73: 10.58, 74: 10.01,
    75: 9.46, 76: 8.92, 77: 8.40, 78: 7.89, 79: 7.40,
    80: 6.93, 81: 6.48, 82: 6.05, 83: 5.64, 84: 5.25,
    85: 4.89, 86: 4.55, 87: 4.23, 88: 3.93, 89: 3.66,
    90: 3.41, 91: 3.18, 92: 2.97, 93: 2.78, 94: 2.61,
    95: 2.45, 96: 2.31, 97: 2.18, 98: 2.06, 99: 1.95,
    100: 1.85, 101: 1.76, 102: 1.67, 103: 1.59, 104: 1.51,
    105: 1.44, 106: 1.37, 107: 1.31, 108: 1.25, 109: 1.19,
    110: 1.14, 111: 1.09, 112: 1.04, 113: 0.99, 114: 0.95,
    115: 0.91, 116: 0.87, 117: 0.84, 118: 0.80, 119: 0.77,
}

# Female life expectancy e(x) by exact age
FEMALE_LIFE_EXPECTANCY = {
    0: 79.05, 1: 78.47, 2: 77.49, 3: 76.50, 4: 75.51,
    5: 74.51, 6: 73.52, 7: 72.52, 8: 71.53, 9: 70.53,
    10: 69.54, 11: 68.54, 12: 67.55, 13: 66.55, 14: 65.56,
    15: 64.57, 16: 63.58, 17: 62.60, 18: 61.62, 19: 60.64,
    20: 59.67, 21: 58.69, 22: 57.72, 23: 56.76, 24: 55.79,
    25: 54.83, 26: 53.86, 27: 52.90, 28: 51.94, 29: 50.98,
    30: 50.02, 31: 49.06, 32: 48.11, 33: 47.15, 34: 46.20,
    35: 45.25, 36: 44.30, 37: 43.35, 38: 42.41, 39: 41.47,
    40: 40.54, 41: 39.60, 42: 38.68, 43: 37.75, 44: 36.83,
    45: 35.92, 46: 35.01, 47: 34.11, 48: 33.22, 49: 32.33,
    50: 31.45, 51: 30.58, 52: 29.71, 53: 28.86, 54: 28.01,
    55: 27.17, 56: 26.34, 57: 25.51, 58: 24.70, 59: 23.89,
    60: 23.10, 61: 22.31, 62: 21.53, 63: 20.76, 64: 20.00,
    65: 19.25, 66: 18.51, 67: 17.78, 68: 17.06, 69: 16.35,
    70: 15.64, 71: 14.95, 72: 14.27, 73: 13.60, 74: 12.95,
    75: 12.30, 76: 11.67, 77: 11.06, 78: 10.45, 79: 9.87,
    80: 9.30, 81: 8.75, 82: 8.22, 83: 7.70, 84: 7.21,
    85: 6.74, 86: 6.29, 87: 5.86, 88: 5.45, 89: 5.07,
    90: 4.71, 91: 4.38, 92: 4.07, 93: 3.79, 94: 3.53,
    95: 3.29, 96: 3.07, 97: 2.87, 98: 2.69, 99: 2.52,
    100: 2.37, 101: 2.23, 102: 2.10, 103: 1.98, 104: 1.87,
    105: 1.77, 106: 1.67, 107: 1.58, 108: 1.50, 109: 1.42,
    110: 1.35, 111: 1.28, 112: 1.22, 113: 1.16, 114: 1.10,
    115: 1.05, 116: 1.00, 117: 0.96, 118: 0.91, 119: 0.87,
}


def get_life_expectancy(age: float, sex: str) -> float:
    """Get remaining life expectancy in years for a given age and sex.

    The SSA table only lists whole ages (39, 40, 41...). If we looked up just
    the whole-number age, the estimate would sit perfectly still for a year and
    then lurch on your birthday. That's what caused the death date to jump
    backwards by ~11 months whenever it was recalculated after a birthday.

    So we interpolate: for an age in between two rows, we blend the two
    surrounding values proportionally. At age 39.5 — exactly halfway between
    e(39)=36.63 and e(40)=35.72 — this returns 36.175.

    Args:
        age: Current age in years, may be fractional (e.g. 39.7).
             Clamped to the 0-119 range the table covers.
        sex: 'male' or 'female'

    Returns:
        Remaining life expectancy in years.
    """
    table = MALE_LIFE_EXPECTANCY if sex.lower() == "male" else FEMALE_LIFE_EXPECTANCY

    age = max(0.0, min(float(age), 119.0))

    lower_age = int(age)             # e.g. 39 for age 39.7
    upper_age = min(lower_age + 1, 119)
    fraction = age - lower_age       # e.g. 0.7 — how far between the two rows

    lower_value = table.get(lower_age, 0.5)
    upper_value = table.get(upper_age, 0.5)

    # Linear blend between the two table rows
    return lower_value + (upper_value - lower_value) * fraction
