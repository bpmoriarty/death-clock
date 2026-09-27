"""Explicit target selection; keeping a saved target requires no profile data."""

from calendar import monthrange
from copy import deepcopy
from datetime import datetime

from .config import get_death_datetime
from .life_expectancy import compute_death_datetime, calculation_provenance

MODES = ("Keep saved target", "Choose a date", "Choose an age", "Legacy calculation")


def propose_target(current, mode, date_text="", age_text="", dob_text="", sex="male", factors=None, *, now=None):
    now = now or datetime.now()
    proposed = deepcopy(current)
    if mode == "Keep saved target":
        if get_death_datetime(current) is None:
            raise ValueError("Choose a target date or age, or restore a saved countdown.")
        return proposed
    if mode == "Choose a date":
        proposed.pop("target_provenance", None)
        try:
            target = datetime.strptime(date_text.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Enter the target date as YYYY-MM-DD.") from None
    elif mode in ("Choose an age", "Legacy calculation"):
        try:
            dob = datetime.strptime(dob_text.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Enter a birth date as YYYY-MM-DD for this option.") from None
        if dob >= now:
            raise ValueError("Birth date must be in the past.")
        if mode == "Choose an age":
            proposed.pop("target_provenance", None)
            try:
                age = int(age_text.strip())
                if not 1 <= age <= 150:
                    raise ValueError()
                year = dob.year + age
                target = dob.replace(year=year, day=min(dob.day, monthrange(year, dob.month)[1]))
            except ValueError:
                raise ValueError("Enter a whole target age from 1 to 150.") from None
        else:
            factors = factors or {}
            if factors.get("current_smoker") and factors.get("former_smoker"):
                raise ValueError("For a new calculation, select current smoker or former smoker, not both.")
            target = compute_death_datetime(dob, sex, factors, now=now)
            proposed["target_provenance"] = calculation_provenance(now, target)
            proposed.update(sex=sex, factors=deepcopy(factors))
        proposed["date_of_birth"] = dob_text.strip()
    else:
        raise ValueError("Choose a target option.")
    proposed["death_datetime_iso"] = target.isoformat()
    return proposed
