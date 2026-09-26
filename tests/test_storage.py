"""Portable profiles and isolated device storage; never access the live profile."""

from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

from death_clock import config, storage, settings_window, startup


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    shared = tmp_path / "shared" / "settings.json"
    shared.parent.mkdir()
    monkeypatch.setattr(config, "CONFIG_PATH", str(shared))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "device-a"))
    legacy = config._fresh_defaults()
    legacy.update(date_of_birth="1991-02-03", death_datetime_iso="2078-09-10T11:12:13.000000+00:00",
                  start_on_boot=True, opacity=0.81)
    legacy["window"]["x"] = 432
    shared.write_text(json.dumps(legacy), encoding="utf-8")
    return shared, legacy


def test_migration_keeps_original_and_seeds_device_once(isolated):
    shared, legacy = isolated
    before = shared.read_bytes()
    current = storage.load_settings()
    local = Path(storage.device_path())
    assert shared.read_bytes() == before
    assert local.with_suffix(".json.bak").exists()
    assert json.loads(local.read_text()) == {"window": legacy["window"],
                                           **storage.DISPLAY_DEFAULTS, "opacity": 0.81}
    assert "start_on_boot" not in current
    legacy["window"]["x"] = -987
    shared.write_text(json.dumps(legacy))
    assert storage.load_settings()["window"]["x"] == 432


def test_two_devices_keep_independent_preferences(isolated, tmp_path, monkeypatch):
    shared, _ = isolated
    before = shared.read_bytes()
    a = storage.load_settings()
    a["window"]["x"] = 123
    storage.save_preferences(a)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "device-b"))
    b = storage.load_settings()
    b["window"]["x"] = 765
    b["opacity"] = 0.65
    storage.save_preferences(b)
    assert storage.load_settings()["window"]["x"] == 765
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "device-a"))
    assert storage.load_settings()["window"]["x"] == 123
    assert storage.load_settings()["opacity"] == 0.81
    assert shared.read_bytes() == before
    assert a["death_datetime_iso"] == b["death_datetime_iso"]


def test_preferences_do_not_access_shared_storage(isolated, monkeypatch):
    current = storage.load_settings()
    read = config._read_object
    monkeypatch.setattr(config, "_read_object", lambda p: (_ for _ in ()).throw(AssertionError())
                        if p == config.CONFIG_PATH else read(p))
    monkeypatch.setattr(config, "save_config", Mock(side_effect=AssertionError()))
    proposed = deepcopy(current)
    proposed["window"]["y"] = 654
    storage.commit_settings(current, proposed)
    assert current["window"]["y"] == 654


def test_profile_save_removes_legacy_fields_and_keeps_recovery_copy(isolated):
    shared, legacy = isolated
    current = storage.load_settings()
    proposed = deepcopy(current)
    proposed["death_datetime_iso"] = "2079-01-01T00:00:00.000000"
    storage.commit_settings(current, proposed)
    assert json.loads(shared.with_suffix(".json.bak").read_text()) == legacy
    assert not set(storage.DEVICE_KEYS) & json.loads(shared.read_text()).keys()
    # A second save also succeeds: the expected digest matches our written bytes.
    proposed["death_datetime_iso"] = "2080-01-01T00:00:00"
    storage.commit_settings(current, proposed)
    assert storage.load_settings()["death_datetime_iso"] == proposed["death_datetime_iso"]


def test_stale_device_does_not_overwrite_new_shared_target(isolated):
    shared, _ = isolated
    a, b = storage.load_settings(), storage.load_settings()
    update = deepcopy(b)
    update["death_datetime_iso"] = "2090-01-01"
    storage.commit_settings(b, update)
    before = shared.read_bytes()
    # Local-only saves remain possible, without writing the stale target back.
    storage.commit_settings(a, {**a, "opacity": 0.7})
    with pytest.raises(ValueError, match="changed"):
        storage.commit_settings(a, {**a, "death_datetime_iso": "2091-01-01"})
    assert shared.read_bytes() == before
    assert a["death_datetime_iso"] != b["death_datetime_iso"]


def test_change_during_local_save_is_detected(isolated, monkeypatch):
    shared, legacy = isolated
    current = storage.load_settings()
    original = deepcopy(current)
    def sync(_):
        shared.write_text(json.dumps({**legacy, "death_datetime_iso": "2095-01-01"}))
    monkeypatch.setattr(storage, "save_preferences", sync)
    with pytest.raises(ValueError, match="changed"):
        storage.commit_settings(current, {**current, "death_datetime_iso": "2096-01-01"})
    assert current == original
    assert json.loads(shared.read_text())["death_datetime_iso"] == "2095-01-01"


@pytest.mark.parametrize("which", ["device", "shared", "backup"])
def test_failed_writes_leave_running_target_unchanged(isolated, monkeypatch, which):
    shared, _ = isolated
    current = storage.load_settings()
    before = shared.read_bytes()
    snapshot = deepcopy(current)
    real = config._atomic_write
    blocked = {"device": storage.device_path(), "shared": str(shared), "backup": str(shared) + ".bak"}[which]
    def fail(path, value):
        if path == blocked:
            raise OSError("simulated write failure")
        real(path, value)
    monkeypatch.setattr(config, "_atomic_write", fail)
    with pytest.raises(OSError):
        storage.commit_settings(current, {**current, "death_datetime_iso": "2099-01-01"})
    assert current == snapshot
    assert shared.read_bytes() == before


@pytest.mark.parametrize("damage", [None, "broken", '{"window": []}', '{"opacity": 4}'])
def test_local_backup_recovers_without_touching_shared(isolated, damage):
    shared, _ = isolated
    storage.load_settings()
    local = Path(storage.device_path())
    if damage is None:
        local.unlink()
    else:
        local.write_text(damage)
    before = shared.read_bytes()
    warnings = []
    current = storage.load_settings(warnings.append)
    assert current["window"]["x"] == 432
    assert warnings
    storage.save_preferences(current)
    if damage is not None:
        assert any(p.read_text() == damage for p in local.parent.glob("*.corrupt.*"))
    assert shared.read_bytes() == before


def test_unreadable_local_file_is_not_overwritten(isolated, monkeypatch):
    current = storage.load_settings()
    local = Path(storage.device_path())
    before = local.read_bytes()
    real = config._read_object
    def denied(path):
        if path == str(local):
            raise PermissionError()
        return real(path)
    monkeypatch.setattr(config, "_read_object", denied)
    with pytest.raises(PermissionError):
        storage.save_preferences(current)
    assert local.read_bytes() == before


def test_export_restore_preserves_target_and_keeps_destination_preferences(isolated, tmp_path):
    shared, legacy = isolated
    current = storage.load_settings()
    output = tmp_path / "portable.json"
    storage.export_profile(current, str(output))
    exported = storage.read_export(str(output))
    assert set(exported) == set(storage.PROFILE_KEYS)
    assert exported["death_datetime_iso"] == legacy["death_datetime_iso"]
    storage.commit_settings(current, {**current, "death_datetime_iso": "2090-01-01"})
    current["window"]["x"] = 888
    storage.restore_profile(current, exported)
    assert current["window"]["x"] == 888
    assert current["death_datetime_iso"] == legacy["death_datetime_iso"]
    assert json.loads(shared.with_suffix(".json.bak").read_text())["death_datetime_iso"] == "2090-01-01"


@pytest.mark.parametrize("fields", [{"death_datetime_iso": "invalid"}, {"factors": []},
                                       {"sex": []}, {"date_of_birth": None}, {"factors": {"diabetes": 1}}])
def test_restore_rejects_invalid_profile(isolated, tmp_path, fields):
    _, legacy = isolated
    output = tmp_path / "invalid.json"
    output.write_text(json.dumps({**legacy, **fields}))
    with pytest.raises(ValueError):
        storage.read_export(str(output))


def test_export_cannot_replace_managed_settings(isolated):
    shared, _ = isolated
    current = storage.load_settings()
    before = shared.read_bytes()
    for path in (str(shared), str(shared).upper(), str(shared) + ".bak", storage.device_path()):
        with pytest.raises(ValueError):
            storage.export_profile(current, path)
    assert shared.read_bytes() == before


def test_restore_declined_preview_changes_nothing(isolated, monkeypatch):
    shared, _ = isolated
    form = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    form.config = storage.load_settings()
    form._saved = False
    form.win = Mock()
    before = shared.read_bytes()
    monkeypatch.setattr(settings_window.filedialog, "askopenfilename", Mock(return_value=str(shared)))
    confirm = Mock(return_value=False)
    monkeypatch.setattr(settings_window.messagebox, "askyesno", confirm)
    form._restore()
    assert form.config["death_datetime_iso"] in confirm.call_args.args[1]
    assert shared.read_bytes() == before
    form.win.destroy.assert_not_called()


@pytest.mark.parametrize("registered", [True, False, None])
def test_startup_checkbox_uses_windows_not_shared_file(isolated, monkeypatch, registered):
    for name in ("CTkLabel", "CTkEntry", "CTkFrame", "CTkRadioButton", "CTkCheckBox", "CTkButton", "StringVar", "CTkScrollableFrame", "CTkOptionMenu"):
        monkeypatch.setattr(settings_window.ctk, name, Mock(side_effect=lambda *a, **kw: Mock()))
    boolean = Mock(side_effect=lambda *a, **kw: Mock())
    monkeypatch.setattr(settings_window.ctk, "BooleanVar", boolean)
    query = Mock(return_value=registered) if registered is not None else Mock(side_effect=PermissionError())
    monkeypatch.setattr(settings_window, "is_registered", query)
    form = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    form.config = {**storage.load_settings(), "start_on_boot": not registered}
    form.win = Mock()
    form._build_ui()
    assert boolean.call_args.kwargs["value"] == bool(registered)
    assert form._startup_available == (registered is not None)


@pytest.mark.parametrize("command,expected", [("", False), ("  ", False), ("launcher", True)])
def test_registration_reads_actual_entry(monkeypatch, command, expected):
    monkeypatch.setattr(startup.winreg, "OpenKey", Mock(return_value=MagicMock()))
    monkeypatch.setattr(startup.winreg, "QueryValueEx", Mock(return_value=(command, startup.winreg.REG_SZ)))
    assert startup.is_registered() is expected


def test_first_run_restore_notifies_once_and_never_changes_login(isolated, monkeypatch):
    shared, _ = isolated
    imported = storage.read_export(str(shared))
    shared.unlink()
    form = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    form.config = storage.load_settings()
    form._saved = False
    form.win = Mock()
    form.save_button = Mock()
    form.on_save = Mock()
    monkeypatch.setattr(settings_window.filedialog, "askopenfilename", Mock(return_value="chosen.json"))
    monkeypatch.setattr(settings_window, "read_export", Mock(return_value=imported))
    monkeypatch.setattr(settings_window.messagebox, "askyesno", Mock(return_value=True))
    registration = Mock(side_effect=AssertionError("restore must not change startup"))
    monkeypatch.setattr(startup, "add_to_startup", registration)
    monkeypatch.setattr(startup, "remove_from_startup", registration)
    form._restore()
    form._restore()
    form.on_save.assert_called_once()
    form.win.destroy.assert_called_once()
    assert form.config["death_datetime_iso"] == imported["death_datetime_iso"]
    assert shared.with_suffix(".json.bak").exists()


def test_failed_restore_keeps_window_open_for_retry(isolated, monkeypatch):
    shared, _ = isolated
    form = settings_window.SettingsWindow.__new__(settings_window.SettingsWindow)
    form.config = storage.load_settings()
    form._saved = False
    form.win = Mock()
    form.on_save = Mock()
    monkeypatch.setattr(settings_window.filedialog, "askopenfilename", Mock(return_value=str(shared)))
    monkeypatch.setattr(settings_window.messagebox, "askyesno", Mock(return_value=True))
    show = Mock()
    monkeypatch.setattr(settings_window.messagebox, "showerror", show)
    monkeypatch.setattr(storage, "save_preferences", Mock(side_effect=OSError("device unavailable")))
    form._restore()
    show.assert_called_once()
    form.win.destroy.assert_not_called()
    form.on_save.assert_not_called()
    assert not form._saved


def test_missing_localappdata_never_falls_back_to_shared_directory(isolated, monkeypatch):
    shared, _ = isolated
    before = shared.read_bytes()
    monkeypatch.delenv("LOCALAPPDATA")
    warnings = []
    current = storage.load_settings(warnings.append)
    assert warnings
    with pytest.raises(OSError):
        storage.save_preferences(current)
    assert shared.read_bytes() == before
    assert not (shared.parent / "preferences.json").exists()
