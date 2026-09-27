"""Optional legacy reminder formula.

The table matches the SSA 2021/2024 report; the multipliers remain unverified. This is not a validated
longevity model. A fresh calculation changes with the calculation date; only
persisting the selected target makes the countdown stable across launches.
"""

from datetime import datetime, timedelta
from .ssa_life_table import get_life_expectancy, TABLE_ID, SOURCE_URL, DATA_SHA256
from .factors import HAZARD_RATIOS, FACTOR_LABELS

MODEL_VERSION = "legacy-ratio-v2-ssa2021tr2024"


def calculation_provenance(now: datetime, target: datetime) -> dict:
    return {"schema_version": 1, "method": "legacy_calculation",
            "model_version": MODEL_VERSION, "table_id": TABLE_ID,
            "source_url": SOURCE_URL, "table_sha256": DATA_SHA256,
            "calculated_at_local": now.isoformat(), "target_iso": target.isoformat()}


def compute_death_datetime(date_of_birth: datetime, sex: str, factors: dict,
                           *, now: datetime | None = None) -> datetime:
    """Calculate only for an explicit preview, then save after confirmation."""
    now = now or datetime.now()
    age_float = (now - date_of_birth).days / 365.25
    base_remaining_years = get_life_expectancy(age_float, sex)
    combined_hazard = 1.0
    for key, active in factors.items():
        if active and key in HAZARD_RATIOS:
            combined_hazard *= HAZARD_RATIOS[key]
    adjusted = max(base_remaining_years / combined_hazard, 0.01)
    return date_of_birth + timedelta(days=(age_float + adjusted) * 365.25)
