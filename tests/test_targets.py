"""Explicit target choice, including first-run and damaged-profile recovery."""

from datetime import datetime
from unittest.mock import Mock
import pytest
from death_clock import targets, config, storage, settings_window

NOW = datetime(2026, 9, 26, 12)


def test_keep_preserves_exact_target_without_valid_profile(monkeypatch):
    current = {"death_datetime_iso": "2080-01-01T12:34:56.000000+00:00", "date_of_birth": ""}
    monkeypatch.setattr(targets, "compute_death_datetime", Mock(side_effect=AssertionError()))
    assert targets.propose_target(current, "Keep saved target", now=NOW) == current


def test_manual_date_needs_no_birth_or_factors(monkeypatch):
    monkeypatch.setattr(targets, "compute_death_datetime", Mock(side_effect=AssertionError()))
    current = config._fresh_defaults()
    result = targets.propose_target(current, "Choose a date", date_text="2080-06-15", now=NOW)
    assert result["death_datetime_iso"] == "2080-06-15T00:00:00"
    assert current["death_datetime_iso"] == ""


@pytest.mark.parametrize("age,expected", [("80", "2080-02-29T00:00:00"), ("81", "2081-02-28T00:00:00")])
def test_target_age_calendar_birthday(age, expected):
    result = targets.propose_target({}, "Choose an age", age_text=age, dob_text="2000-02-29", now=NOW)
    assert result["death_datetime_iso"] == expected


@pytest.mark.parametrize("mode,kwargs", [
    ("Keep saved target", {}), ("Choose a date", {"date_text": "2080-02-30"}),
    ("Choose an age", {"dob_text": "2000-01-01", "age_text": "1.5"}),
    ("Choose an age", {"dob_text": "2000-01-01", "age_text": "151"}),
    ("Choose an age", {"dob_text": "2090-01-01", "age_text": "80"}),
    ("Legacy calculation", {"dob_text": "2000-01-01", "factors": {"current_smoker": True, "former_smoker": True}}),
])
def test_invalid_selection_rejected(mode, kwargs):
    with pytest.raises(ValueError):
        targets.propose_target({}, mode, now=NOW, **kwargs)


def test_legacy_calculation_receives_explicit_time(monkeypatch):
    compute = Mock(return_value=datetime(2070, 1, 1))
    monkeypatch.setattr(targets, "compute_death_datetime", compute)
    targets.propose_target({}, "Legacy calculation", dob_text="2000-01-01", now=NOW)
    assert compute.call_args.kwargs["now"] == NOW


@pytest.mark.parametrize("approve", [True, False])
def test_first_manual_target_requires_preview(tmp_path, monkeypatch, approve):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    form = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    form.config = storage.load_settings()
    form._saved = False
    form._startup_available = False
    form.win, form.save_button, form.ref_label, form.on_save = Mock(), Mock(), Mock(), Mock()
    for name, value in {"target_mode": "Choose a date", "target_entry": "2080-06-15", "age_entry": "",
                        "dob_entry": "", "sex_var": "male", "startup_var": False}.items():
        setattr(form, name, Mock(get=Mock(return_value=value)))
    form.factor_vars = {}
    confirmation = Mock(return_value=approve)
    monkeypatch.setattr(settings_window.messagebox, "askyesno", confirmation)
    form._save()
    assert "2080-06-15T00:00:00" in confirmation.call_args.args[1]
    assert path.exists() == approve
    assert form.on_save.called == approve
    if approve:
        exported = tmp_path / "portable.json"
        storage.export_profile(form.config, str(exported))
        assert storage.read_export(str(exported))["date_of_birth"] == ""


def test_cancel_notifies_first_run_without_saving():
    form = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    form.win, form.on_close = Mock(), Mock()
    form._saved = False
    form._close()
    form.on_close.assert_called_once_with(False)
