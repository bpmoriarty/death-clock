"""
Tests for reading and writing settings.json.

Every test here redirects config.CONFIG_PATH at a temporary folder, so the real
settings.json -- which holds the live death date -- is never touched.
"""

import json
import os
from datetime import datetime

import pytest

from death_clock import config


@pytest.fixture
def config_path(tmp_path, monkeypatch):
    """Point the config module at a throwaway settings.json."""
    path = tmp_path / "settings.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(path))
    return path


# ── Loading ───────────────────────────────────────────────────────────────────

def test_missing_file_gives_defaults(config_path):
    loaded = config.load_config()
    assert loaded["date_of_birth"] == ""
    assert loaded["death_datetime_iso"] == ""
    assert loaded["start_on_boot"] is False


def test_defaults_are_not_shared_between_calls(config_path):
    """A caller mutating one result must not poison the next one."""
    first = config.load_config()
    first["factors"]["diabetes"] = True
    first["window"]["x"] = 9999

    second = config.load_config()
    assert second["factors"]["diabetes"] is False
    assert second["window"]["x"] == 100


def test_missing_keys_are_filled_in_from_defaults(config_path):
    """An old settings file shouldn't break after new keys are introduced."""
    config_path.write_text(json.dumps({"date_of_birth": "1986-05-30"}), encoding="utf-8")

    loaded = config.load_config()
    assert loaded["date_of_birth"] == "1986-05-30"   # kept
    assert loaded["sex"] == "male"                    # filled in
    assert "diabetes" in loaded["factors"]            # nested keys filled in
    assert loaded["window"]["width"] == 440


def test_saved_values_win_over_defaults(config_path):
    config_path.write_text(
        json.dumps({"sex": "female", "factors": {"diabetes": True}}), encoding="utf-8"
    )
    loaded = config.load_config()
    assert loaded["sex"] == "female"
    assert loaded["factors"]["diabetes"] is True
    assert loaded["factors"]["obesity"] is False  # untouched default


# ── Surviving a corrupt file ──────────────────────────────────────────────────

def test_corrupt_file_does_not_raise(config_path):
    """
    The app runs under pythonw.exe with no console, so an exception here would
    kill it at startup with nothing shown on screen.
    """
    config_path.write_text('{"date_of_birth": "1986-05-30",,, BROKEN', encoding="utf-8")

    loaded = config.load_config()
    assert loaded["date_of_birth"] == ""  # fell back to defaults


def test_corrupt_file_is_kept_for_recovery(config_path):
    """The death date may still be readable by hand inside the damaged file."""
    config_path.write_text("not json at all", encoding="utf-8")
    config.load_config()

    salvaged = config_path.parent / "settings.json.corrupt"
    assert salvaged.exists()
    assert salvaged.read_text(encoding="utf-8") == "not json at all"


def test_a_json_list_is_treated_as_corrupt(config_path):
    """Valid JSON, wrong shape -- must not crash the merge step."""
    config_path.write_text('["not", "an", "object"]', encoding="utf-8")
    assert config.load_config()["sex"] == "male"


# ── Saving ────────────────────────────────────────────────────────────────────

def test_save_then_load_round_trips(config_path):
    original = config.load_config()
    original["date_of_birth"] = "1986-05-30"
    original["death_datetime_iso"] = "2066-08-26T12:01:17.204457"
    original["factors"]["sedentary"] = True

    config.save_config(original)
    reloaded = config.load_config()

    assert reloaded["date_of_birth"] == "1986-05-30"
    assert reloaded["death_datetime_iso"] == "2066-08-26T12:01:17.204457"
    assert reloaded["factors"]["sedentary"] is True


def test_save_leaves_no_temporary_file_behind(config_path):
    config.save_config(config.load_config())
    leftovers = [p.name for p in config_path.parent.iterdir()]
    assert leftovers == ["settings.json"]


def test_save_never_leaves_a_half_written_file(config_path, monkeypatch):
    """
    Simulate a crash partway through writing. Because we write to a temp file
    and only then rename it into place, the previous settings.json must still
    be intact and readable.
    """
    good = config.load_config()
    good["date_of_birth"] = "1986-05-30"
    config.save_config(good)

    def explode(*args, **kwargs):
        raise OSError("simulated crash mid-write")

    monkeypatch.setattr(os, "replace", explode)
    with pytest.raises(OSError):
        config.save_config({**good, "date_of_birth": "1999-01-01"})

    # The original file survived the failed write untouched
    assert config.load_config()["date_of_birth"] == "1986-05-30"


def test_non_ascii_survives_a_round_trip(config_path):
    """Explicit UTF-8 encoding, rather than the Windows locale default."""
    cfg = config.load_config()
    cfg["date_of_birth"] = "1986-05-30"
    cfg["note"] = "café — naïve — 死"
    config.save_config(cfg)
    assert config.load_config()["note"] == "café — naïve — 死"


# ── Reading the death date ────────────────────────────────────────────────────

def test_death_datetime_is_parsed_back(config_path):
    cfg = {"death_datetime_iso": "2066-08-26T12:01:17.204457"}
    assert config.get_death_datetime(cfg) == datetime(2066, 8, 26, 12, 1, 17, 204457)


@pytest.mark.parametrize("stored", ["", "not a date", "2066-13-45T99:99:99"])
def test_unusable_death_dates_return_none(stored):
    """None sends the app to the Settings window rather than crashing it."""
    assert config.get_death_datetime({"death_datetime_iso": stored}) is None


def test_missing_death_date_key_returns_none():
    assert config.get_death_datetime({}) is None


@pytest.mark.parametrize(
    "dob, expected",
    [("1986-05-30", True), ("", False), ("   ", False)],
)
def test_has_profile_checks_for_a_real_date_of_birth(dob, expected):
    assert config.has_profile({"date_of_birth": dob}) is expected
