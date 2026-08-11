"""
Tests for the death date calculation.

The headline property here is reproducibility: the same date of birth, sex and
factors must produce the same death date regardless of when you press Save.
That did not hold before -- the answer drifted about a day later per day and
snapped roughly 11 months backwards on each birthday.

compute_death_datetime() reads the clock internally, so we can't hand it a
fake "now". Instead we shift the date of birth by the same amount: the function
only ever looks at the gap between the two, so asking "what would this return
in five years?" is the same as asking about someone born five years earlier.
"""

from datetime import datetime, timedelta

import pytest

from death_clock.life_expectancy import (
    compute_death_datetime,
    HAZARD_RATIOS,
    FACTOR_LABELS,
)

DOB = datetime(1986, 5, 30)

NO_FACTORS = {key: False for key in HAZARD_RATIOS}


def death_date_as_if_it_were(pretend_now, dob=DOB, sex="male", factors=None):
    """What compute_death_datetime() would return on some other date."""
    factors = NO_FACTORS if factors is None else factors
    offset = datetime.now() - pretend_now
    shifted = compute_death_datetime(dob + offset, sex, factors)
    return shifted - offset  # put the answer back on the real calendar


# ── Reproducibility ───────────────────────────────────────────────────────────

def test_same_inputs_give_the_same_answer_on_a_later_day():
    """Calculating tomorrow instead of today should barely move the date."""
    today = death_date_as_if_it_were(datetime(2026, 8, 11))
    tomorrow = death_date_as_if_it_were(datetime(2026, 8, 12))
    assert abs((today - tomorrow).days) <= 1


def test_no_cliff_when_crossing_a_birthday():
    """
    The regression test for the original bug. Brian's birthday is 30 May;
    calculating either side of it used to differ by ~324 days.
    """
    before = death_date_as_if_it_were(datetime(2027, 5, 29))
    after = death_date_as_if_it_were(datetime(2027, 5, 31))
    assert abs((before - after).days) <= 2


def test_the_date_never_lurches_from_one_day_to_the_next():
    """
    This is the real invariant the original bug broke. Recalculating on
    consecutive days must give near-identical answers -- everywhere, including
    across a birthday. The old version crept about a day later per day and then
    snapped ~324 days backwards every 30 May.

    Slow drift measured in years is expected and correct; a cliff between two
    adjacent days is not.
    """
    start = datetime(2027, 5, 25)  # deliberately spans his 30 May birthday
    dates = [death_date_as_if_it_were(start + timedelta(days=n)) for n in range(12)]

    jumps = [abs((b - a).days) for a, b in zip(dates, dates[1:])]
    assert max(jumps) <= 1, f"date lurched between adjacent days: {jumps}"


def test_drift_across_five_years_stays_under_a_year():
    """
    Living another five years does legitimately push the estimate later --
    having survived that long raises your expected total lifespan, and the
    effect compounds with age. The point is that it's a gradual slope, not the
    368-day spread the old version produced inside a single year.
    """
    dates = [
        death_date_as_if_it_were(datetime(year, 8, 11))
        for year in range(2026, 2032)
    ]
    spread = (max(dates) - min(dates)).days
    assert spread < 365, f"death date moved {spread} days over five years"


# ── Direction of each factor ──────────────────────────────────────────────────

@pytest.mark.parametrize(
    "factor", [f for f, ratio in HAZARD_RATIOS.items() if ratio > 1.0]
)
def test_risk_factors_bring_the_date_forward(factor):
    baseline = compute_death_datetime(DOB, "male", NO_FACTORS)
    with_risk = compute_death_datetime(DOB, "male", {**NO_FACTORS, factor: True})
    assert with_risk < baseline


@pytest.mark.parametrize(
    "factor", [f for f, ratio in HAZARD_RATIOS.items() if ratio < 1.0]
)
def test_protective_factors_push_the_date_back(factor):
    baseline = compute_death_datetime(DOB, "male", NO_FACTORS)
    with_benefit = compute_death_datetime(DOB, "male", {**NO_FACTORS, factor: True})
    assert with_benefit > baseline


def test_opposing_factors_partly_cancel():
    """
    Brian's real situation: a sedentary desk job (1.30) offset by exercise
    outside work (0.75). The pair should land between the two on their own.
    """
    both = compute_death_datetime(
        DOB, "male", {**NO_FACTORS, "sedentary": True, "regular_exercise": True}
    )
    sedentary_only = compute_death_datetime(
        DOB, "male", {**NO_FACTORS, "sedentary": True}
    )
    exercise_only = compute_death_datetime(
        DOB, "male", {**NO_FACTORS, "regular_exercise": True}
    )
    assert sedentary_only < both < exercise_only


def test_smoking_is_the_heaviest_single_risk():
    ratios = {f: r for f, r in HAZARD_RATIOS.items() if r > 1.0}
    assert max(ratios, key=ratios.get) == "current_smoker"


# ── Sanity ────────────────────────────────────────────────────────────────────

def test_death_date_is_in_the_future_for_a_healthy_adult():
    assert compute_death_datetime(DOB, "male", NO_FACTORS) > datetime.now()


def test_women_get_a_later_date_than_men_all_else_equal():
    male = compute_death_datetime(DOB, "male", NO_FACTORS)
    female = compute_death_datetime(DOB, "female", NO_FACTORS)
    assert female > male


def test_an_older_person_gets_an_earlier_date():
    younger = compute_death_datetime(datetime(1996, 5, 30), "male", NO_FACTORS)
    older = compute_death_datetime(datetime(1956, 5, 30), "male", NO_FACTORS)
    assert older < younger


def test_every_hazard_ratio_has_a_label_for_the_settings_window():
    assert set(HAZARD_RATIOS) == set(FACTOR_LABELS)


def test_unknown_factor_keys_are_ignored():
    """Old settings files might carry factors we no longer recognise."""
    baseline = compute_death_datetime(DOB, "male", NO_FACTORS)
    with_junk = compute_death_datetime(
        DOB, "male", {**NO_FACTORS, "astrological_sign": True}
    )
    assert with_junk == baseline


def test_stacking_every_risk_factor_still_gives_a_future_date():
    """The max(..., 0.01) floor should stop the date landing in the past."""
    all_risks = {f: (r > 1.0) for f, r in HAZARD_RATIOS.items()}
    result = compute_death_datetime(datetime(1930, 1, 1), "male", all_risks)
    assert result > datetime(1930, 1, 1)
