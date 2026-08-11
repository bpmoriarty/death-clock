"""
Tests for the SSA life table lookup.

The table itself is just data copied from ssa.gov. What's worth testing is the
lookup around it -- particularly the interpolation, which is what stopped the
death date jumping on birthdays.
"""

import pytest

from death_clock.ssa_life_table import (
    get_life_expectancy,
    MALE_LIFE_EXPECTANCY,
    FEMALE_LIFE_EXPECTANCY,
)


def test_exact_ages_return_the_table_value():
    """A whole-number age should give back exactly what the table says."""
    assert get_life_expectancy(39, "male") == 36.63
    assert get_life_expectancy(0, "male") == 73.50
    assert get_life_expectancy(65, "female") == 19.25


def test_halfway_between_two_ages_is_the_midpoint():
    """
    At 39.5 we're halfway between e(39)=36.63 and e(40)=35.72,
    so we expect the average of the two: 36.175.
    """
    assert get_life_expectancy(39.5, "male") == pytest.approx(36.175)


def test_interpolation_is_proportional():
    """A quarter of the way between rows should be a quarter of the way down."""
    lower, upper = MALE_LIFE_EXPECTANCY[50], MALE_LIFE_EXPECTANCY[51]
    expected = lower + (upper - lower) * 0.25
    assert get_life_expectancy(50.25, "male") == pytest.approx(expected)


def test_no_sudden_jump_across_a_birthday():
    """
    The bug this guards against: the day before and the day after a birthday
    should give near-identical answers. Before interpolation, the value sat
    still all year and then dropped by nearly a full year at once.
    """
    day_before = get_life_expectancy(40.999, "male")
    day_after = get_life_expectancy(41.001, "male")
    assert abs(day_before - day_after) < 0.01


def test_life_expectancy_falls_as_age_rises():
    """Remaining years should never increase as you get older."""
    values = [get_life_expectancy(age, "male") for age in range(0, 120)]
    assert values == sorted(values, reverse=True)


def test_women_outlive_men_at_every_age():
    for age in range(0, 120):
        assert get_life_expectancy(age, "female") >= get_life_expectancy(age, "male")


@pytest.mark.parametrize("age", [-1, -100, 0])
def test_ages_below_zero_clamp_to_birth(age):
    assert get_life_expectancy(age, "male") == MALE_LIFE_EXPECTANCY[0]


@pytest.mark.parametrize("age", [119, 120, 500])
def test_ages_past_the_end_of_the_table_clamp_to_the_last_row(age):
    assert get_life_expectancy(age, "male") == MALE_LIFE_EXPECTANCY[119]


def test_unknown_sex_falls_back_to_the_female_table():
    """Not a deliberate feature, but pinning the current behaviour."""
    assert get_life_expectancy(40, "unspecified") == FEMALE_LIFE_EXPECTANCY[40]


def test_sex_is_case_insensitive():
    assert get_life_expectancy(40, "MALE") == get_life_expectancy(40, "male")


def test_both_tables_cover_every_age_to_119():
    assert set(MALE_LIFE_EXPECTANCY) == set(range(120))
    assert set(FEMALE_LIFE_EXPECTANCY) == set(range(120))
