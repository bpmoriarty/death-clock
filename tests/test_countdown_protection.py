"""Recovery and UI transactions using fictional profiles and isolated files."""

import json
from copy import deepcopy
from datetime import datetime
from unittest.mock import Mock

import pytest

from death_clock import config, settings_window, startup, storage, targets
from death_clock.app import App


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "device"))
    return path


@pytest.fixture
def profile():
    result = config._fresh_defaults()
    result.update(date_of_birth="1990-02-03",
                  death_datetime_iso="2075-06-07T12:34:56.000000")
    return result


@pytest.mark.parametrize("fields", [
    {"factors": None}, {"window": []}, {"date_of_birth": None},
    {"factors": {"diabetes": "false"}}, {"window": {"width": "wide"}},
    {"window": {"height": -1, "x": True}}, {"start_on_boot": 0},
    {"sex": []},
])
def test_invalid_preferences_keep_exact_target(settings_path, profile, fields):
    profile.update(fields)
    original = json.dumps(profile)
    settings_path.write_text(original, encoding="utf-8")
    warnings = []
    loaded = config.load_config(warnings.append)
    assert loaded["death_datetime_iso"] == profile["death_datetime_iso"]
    assert settings_path.read_text(encoding="utf-8") == original
    assert warnings
    assert settings_path.with_suffix(".json.corrupt").exists()


@pytest.mark.parametrize("value", [None, 123, [], {}, "broken"])
def test_invalid_target_types_do_not_raise(value):
    assert config.get_death_datetime({"death_datetime_iso": value}) is None


def test_offset_target_can_be_used_by_local_countdown():
    result = config.get_death_datetime({"death_datetime_iso": "2075-01-01T00:00:00+00:00"})
    assert result.tzinfo is None
    assert (result - datetime.now()).total_seconds() > 0


@pytest.mark.parametrize("primary", [None, "broken", '{"death_datetime_iso": 123}'])
def test_backup_recovers_without_recalculating(settings_path, profile, primary):
    settings_path.with_suffix(".json.bak").write_text(json.dumps(profile), encoding="utf-8")
    if primary is not None:
        settings_path.write_text(primary, encoding="utf-8")
    warnings = []
    loaded = config.load_config(warnings.append)
    assert loaded == profile
    assert any("recovered" in message for message in warnings)
    if primary is not None:
        assert settings_path.read_text(encoding="utf-8") == primary
    else:
        assert not settings_path.exists()


def test_first_save_has_backup_and_later_save_preserves_previous(settings_path, profile):
    config.save_config(profile)
    backup = settings_path.with_suffix(".json.bak")
    assert json.loads(backup.read_text()) == profile
    changed = {**profile, "death_datetime_iso": "2076-01-01T00:00:00"}
    config.save_config(changed)
    assert json.loads(settings_path.read_text()) == changed
    assert json.loads(backup.read_text()) == profile
    assert not list(settings_path.parent.glob("*.tmp"))


def test_recovery_copies_never_overwrite_previous_damage(settings_path):
    settings_path.write_text("first damage")
    config.load_config()
    settings_path.write_text("second damage")
    config.load_config()
    copies = {p.read_text() for p in settings_path.parent.glob("*.corrupt*")}
    assert copies == {"first damage", "second damage"}


def test_failed_main_replace_keeps_disk_and_memory(settings_path, profile, monkeypatch):
    config.save_config(profile)
    original = deepcopy(profile)
    original_replace = config.os.replace

    def fail_main(source, destination):
        if destination == str(settings_path):
            raise OSError("simulated disk failure")
        original_replace(source, destination)

    monkeypatch.setattr(config.os, "replace", fail_main)
    with pytest.raises(OSError):
        config.commit_config(profile, {**profile, "death_datetime_iso": "2080-01-01"})
    assert profile == original
    assert json.loads(settings_path.read_text()) == original
    assert json.loads(settings_path.with_suffix(".json.bak").read_text()) == original
    assert not list(settings_path.parent.glob("*.tmp"))


def test_unreadable_original_is_not_overwritten(settings_path, profile, monkeypatch):
    settings_path.write_text(json.dumps(profile))
    original = settings_path.read_bytes()
    monkeypatch.setattr(config, "_read_object", Mock(side_effect=PermissionError("blocked")))
    with pytest.raises(PermissionError):
        config.save_config(profile)
    assert settings_path.read_bytes() == original


def test_cannot_clear_existing_target(settings_path, profile):
    config.save_config(profile)
    with pytest.raises(ValueError):
        config.save_config({**profile, "death_datetime_iso": ""})
    assert config.load_config() == profile


@pytest.fixture
def form(profile, settings_path, monkeypatch):
    # Exercise the real save handler without creating windows or registry entries.
    window = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    config.save_config(profile)
    window.config = storage.load_settings()
    window._saved = False
    window._startup_available = True
    window.target_mode = Mock(get=Mock(return_value="Keep saved target"))
    window.target_entry = Mock(get=Mock(return_value=""))
    window.age_entry = Mock(get=Mock(return_value=""))
    window.win = Mock()
    window.dob_entry = Mock()
    window.dob_entry.get.return_value = profile["date_of_birth"]
    window.sex_var = Mock()
    window.sex_var.get.return_value = profile["sex"]
    window.startup_var = Mock()
    window.startup_var.get.return_value = True
    window.factor_vars = {key: Mock() for key in profile["factors"]}
    for key, var in window.factor_vars.items():
        var.get.return_value = profile["factors"][key]
    window.on_save = Mock()
    window.save_button = Mock()
    window.ref_label = Mock()
    monkeypatch.setattr(settings_window.messagebox, "showerror", Mock())
    monkeypatch.setattr(settings_window.messagebox, "showwarning", Mock())
    monkeypatch.setattr(settings_window.messagebox, "askyesno", Mock(return_value=True))
    monkeypatch.setattr(startup, "add_to_startup", Mock())
    monkeypatch.setattr(startup, "remove_from_startup", Mock())
    return window


def test_preference_save_preserves_exact_string_and_notifies_once(settings_path, form, monkeypatch):
    calculate = Mock(side_effect=AssertionError("must not recalculate"))
    monkeypatch.setattr(targets, "compute_death_datetime", calculate)
    target = form.config["death_datetime_iso"]
    form._save()
    form._save()
    assert config.load_config()["death_datetime_iso"] == target
    form.on_save.assert_called_once()
    form.save_button.configure.assert_called_once_with(state="disabled")
    startup.add_to_startup.assert_called_once()


def test_save_error_allows_retry_without_changing_running_state(settings_path, form, monkeypatch):
    original = deepcopy(form.config)
    monkeypatch.setattr(storage, "save_preferences", Mock(side_effect=OSError("disk full")))
    form._save()
    assert form.config == original
    assert not form._saved
    form.on_save.assert_not_called()
    form.save_button.configure.assert_not_called()
    startup.add_to_startup.assert_not_called()
    settings_window.messagebox.showerror.assert_called_once()


def test_declining_target_change_does_not_write(settings_path, form, monkeypatch):
    original = deepcopy(form.config)
    original_file = settings_path.read_bytes()
    form.target_mode.get.return_value = "Legacy calculation"
    form.factor_vars["regular_exercise"].get.return_value = True
    settings_window.messagebox.askyesno.return_value = False
    form._save()
    assert form.config == original
    assert settings_path.read_bytes() == original_file
    form.on_save.assert_not_called()


def test_registration_failure_does_not_claim_total_save_failure(settings_path, form, monkeypatch):
    monkeypatch.setattr(startup, "add_to_startup", Mock(side_effect=OSError("registry blocked")))
    form._save()
    assert config.load_config()["death_datetime_iso"] == form.config["death_datetime_iso"]
    form.on_save.assert_called_once()
    settings_window.messagebox.showwarning.assert_called_once()


def test_exit_still_quits_after_save_failure(monkeypatch):
    app = App.__new__(App)
    app.widget = Mock()
    app.tray_icon = Mock()
    app.root = Mock()
    app.config = {}
    monkeypatch.setattr("death_clock.app.save_config", Mock(side_effect=OSError("disk full")))
    monkeypatch.setattr("death_clock.app.messagebox.showerror", Mock())
    app._exit()
    app.tray_icon.stop.assert_called_once()
    app.root.quit.assert_called_once()


def test_closing_first_run_does_not_write_defaults(monkeypatch):
    app = App.__new__(App)
    app.widget = None
    app.tray_icon = None
    app.root = Mock()
    save = Mock()
    monkeypatch.setattr("death_clock.app.save_config", save)
    app._exit()
    save.assert_not_called()
    app.root.quit.assert_called_once()


def test_settings_form_builds_before_first_save(profile, monkeypatch):
    """Build the form with stand-in controls; no real desktop window is opened."""
    for name in ("CTkLabel", "CTkEntry", "CTkFrame", "CTkRadioButton",
                 "CTkCheckBox", "CTkButton", "StringVar", "BooleanVar", "CTkScrollableFrame", "CTkOptionMenu"):
        monkeypatch.setattr(settings_window.ctk, name, Mock(side_effect=lambda *a, **kw: Mock()))
    monkeypatch.setattr(settings_window, "is_registered", Mock(return_value=False))
    form = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    form.config = profile
    form.win = Mock()
    form._build_ui()
    form.save_button.pack.assert_called_once()
    assert settings_window.ctk.CTkButton.call_args.kwargs["command"] == form._save


def test_usable_target_runs_even_if_profile_is_damaged(profile):
    app = App.__new__(App)
    app.config = {**profile, "date_of_birth": ""}
    app.root = Mock()
    app.load_warnings = []
    app._create_widget = Mock()
    app._start_tray = Mock()
    app._open_first_run_settings = Mock()
    app.run()
    app._create_widget.assert_called_once_with(config.get_death_datetime(profile))
    app._open_first_run_settings.assert_not_called()
