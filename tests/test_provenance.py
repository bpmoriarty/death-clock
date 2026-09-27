"""Source details survive saving/transfer without reattributing existing targets."""

from copy import deepcopy
from datetime import datetime
import json
from unittest.mock import Mock

import pytest

from death_clock import config, storage, targets
from death_clock.life_expectancy import MODEL_VERSION
from death_clock.ssa_life_table import TABLE_ID, SOURCE_URL, DATA_SHA256

NOW = datetime(2026, 9, 26, 12, 34, 56)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "device"))
    return path


def calculated():
    return targets.propose_target(config._fresh_defaults(), "Legacy calculation",
                                  dob_text="1991-02-03", now=NOW)


def test_new_calculation_records_exact_source_version_date_and_target():
    proposed = calculated()
    assert proposed["target_provenance"] == {
        "schema_version": 1, "method": "legacy_calculation", "model_version": MODEL_VERSION,
        "table_id": TABLE_ID, "source_url": SOURCE_URL, "table_sha256": DATA_SHA256,
        "calculated_at_local": NOW.isoformat(), "target_iso": proposed["death_datetime_iso"]}


def test_source_details_roundtrip_save_export_restore(isolated, tmp_path):
    current = storage.load_settings()
    proposed = calculated()
    storage.commit_settings(current, proposed)
    export = tmp_path / "portable.json"
    storage.export_profile(current, str(export))
    imported = storage.read_export(str(export))
    assert imported["target_provenance"] == proposed["target_provenance"]
    storage.restore_profile(current, imported)
    assert storage.load_settings()["target_provenance"] == proposed["target_provenance"]


@pytest.mark.parametrize("mode,kwargs", [("Choose a date", {"date_text": "2080-01-01"}),
                                        ("Choose an age", {"dob_text": "1991-02-03", "age_text": "85"})])
def test_manual_choice_removes_old_calculation_attribution(mode, kwargs):
    proposed = targets.propose_target(calculated(), mode, now=NOW, **kwargs)
    assert "target_provenance" not in proposed


def test_restore_old_export_clears_destination_attribution(isolated):
    current = storage.load_settings()
    storage.commit_settings(current, calculated())
    old = {key: current[key] for key in storage.PROFILE_KEYS}
    old["death_datetime_iso"] = "2085-01-01T00:00:00"
    storage.restore_profile(current, old)
    assert "target_provenance" not in current
    assert "target_provenance" not in storage.load_settings()


def test_existing_target_stays_exact_and_unattributed(isolated, monkeypatch):
    original = {**config._fresh_defaults(), "death_datetime_iso": "2075-06-07T12:34:56.000000+00:00"}
    isolated.write_text(json.dumps(original))
    before = isolated.read_bytes()
    monkeypatch.setattr(targets, "compute_death_datetime", Mock(side_effect=AssertionError()))
    current = storage.load_settings()
    kept = targets.propose_target(current, "Keep saved target", now=NOW)
    storage.commit_settings(current, kept)
    assert isolated.read_bytes() == before
    assert current["death_datetime_iso"] == original["death_datetime_iso"]
    assert "target_provenance" not in current


@pytest.mark.parametrize("field,value", [("target_iso", "2099-01-01"), ("schema_version", True),
                                       ("calculated_at_local", "yesterday"), ("table_sha256", "bad"),
                                       ("source_url", "https://example.com/table"), ("model_version", None)])
def test_invalid_imported_details_are_rejected(isolated, tmp_path, field, value):
    profile = calculated()
    profile["target_provenance"][field] = value
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(profile))
    with pytest.raises(ValueError):
        storage.read_export(str(path))
    assert not isolated.exists()


def test_failed_save_does_not_attach_new_provenance(isolated, monkeypatch):
    current = storage.load_settings()
    before = deepcopy(current)
    monkeypatch.setattr(config, "save_config", Mock(side_effect=OSError("write failed")))
    with pytest.raises(OSError):
        storage.commit_settings(current, calculated())
    assert current == before
