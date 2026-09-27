"""Pinned SSA 2021 period life expectancy, 2024 Trustees Report.

Values are remaining years at exact ages, published to two decimal places.
The CSV is checked against the retained SSA HTML snapshot in offline tests.
Interpolation and boundary clamping are application rules, not SSA predictions.
"""

import csv
from pathlib import Path

TABLE_ID = "ssa-period-2021-tr2024"
SOURCE_URL = "https://www.ssa.gov/oact/STATS/table4c6_2021_TR2024.html"
DATA_SHA256 = "9de6f7c4c116c956f5d12b1712405b148350d612ee8f7a320589814e79da81bd"
DATA_PATH = Path(__file__).with_name("data") / "ssa_2021_tr2024.csv"

with DATA_PATH.open(encoding="utf-8", newline="") as stream:
    _rows = list(csv.DictReader(stream))
if [int(row["age"]) for row in _rows] != list(range(120)):
    raise ValueError("The pinned SSA table must contain each age from 0 through 119 once.")
MALE_LIFE_EXPECTANCY = {int(row["age"]): float(row["male"]) for row in _rows}
FEMALE_LIFE_EXPECTANCY = {int(row["age"]): float(row["female"]) for row in _rows}
del _rows


def get_life_expectancy(age: float, sex: str) -> float:
    """Linearly interpolate exact-age rows, clamping ages to 0–119.

    Preserve legacy handling of sex: 'male' is case-insensitive; other values
    select the female table. Validated Settings offers only male/female.
    """
    table = MALE_LIFE_EXPECTANCY if sex.lower() == "male" else FEMALE_LIFE_EXPECTANCY
    age = max(0.0, min(float(age), 119.0))
    lower = int(age)
    upper = min(lower + 1, 119)
    return table[lower] + (table[upper] - table[lower]) * (age - lower)