"""Deterministic checks of legacy software behavior, not model accuracy."""

from datetime import datetime, timedelta
import pytest
from death_clock.life_expectancy import compute_death_datetime, HAZARD_RATIOS, FACTOR_LABELS

DOB = datetime(1991, 2, 3)
NOW = datetime(2026, 9, 26, 12)
NO_FACTORS = {key: False for key in HAZARD_RATIOS}


def calculate(factors=None, now=NOW, dob=DOB, sex="male"):
    return compute_death_datetime(dob, sex, NO_FACTORS if factors is None else factors, now=now)


def test_same_inputs_and_calculation_time_are_reproducible():
    assert calculate() == calculate()


def test_explicit_recalculation_on_later_date_can_change_target():
    assert calculate(now=NOW + timedelta(days=365)) != calculate()


def test_no_large_jump_across_fictional_birthday():
    start = datetime(2027, 1, 30)
    dates = [calculate(now=start + timedelta(days=n)) for n in range(12)]
    assert max(abs((b - a).total_seconds()) for a, b in zip(dates, dates[1:])) < 2 * 86400


@pytest.mark.parametrize("factor", [f for f, ratio in HAZARD_RATIOS.items() if ratio > 1])
def test_risk_factors_bring_date_forward(factor):
    assert calculate({**NO_FACTORS, factor: True}) < calculate()


@pytest.mark.parametrize("factor", [f for f, ratio in HAZARD_RATIOS.items() if ratio < 1])
def test_protective_factors_push_date_back(factor):
    assert calculate({**NO_FACTORS, factor: True}) > calculate()


def test_opposing_factors_partly_cancel():
    both = calculate({**NO_FACTORS, "sedentary": True, "regular_exercise": True})
    assert calculate({**NO_FACTORS, "sedentary": True}) < both < calculate({**NO_FACTORS, "regular_exercise": True})


def test_result_is_after_calculation_time():
    assert calculate() > NOW


def test_table_sex_selection_changes_result():
    assert calculate(sex="female") > calculate(sex="male")


def test_older_profile_gets_earlier_target():
    assert calculate(dob=datetime(1950, 2, 3)) < calculate(dob=datetime(2000, 2, 3))


def test_factor_labels_cover_formula_keys():
    assert set(HAZARD_RATIOS) == set(FACTOR_LABELS)


def test_unknown_factors_are_ignored():
    assert calculate({**NO_FACTORS, "obsolete_factor": True}) == calculate()


def test_every_risk_still_returns_a_future_date():
    factors = {key: ratio > 1 for key, ratio in HAZARD_RATIOS.items()}
    assert calculate(factors, dob=datetime(1930, 1, 1)) > NOW