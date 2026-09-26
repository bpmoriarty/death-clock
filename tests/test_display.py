"""Display controls and calendar boundaries, with fictional targets only."""

from datetime import datetime, timedelta
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from death_clock import config, storage, widget, display_window
from death_clock.countdown import format_countdown


@pytest.mark.parametrize("now,target,expected", [
    ("2024-01-01", "2025-01-01", "1y 000d 00:00:00"),
    ("2023-03-01", "2024-03-01", "1y 000d 00:00:00"),
    ("2024-02-29", "2025-02-28", "1y 000d 00:00:00"),
    ("2024-02-29", "2028-02-29", "4y 000d 00:00:00"),
    ("2025-02-28", "2028-02-29", "3y 001d 00:00:00"),
    ("2024-12-31T23:59:59", "2025-01-01", "0y 000d 00:00:01"),
    ("2024-01-01T00:00:00.500000", "2024-01-01T00:00:01", "0y 000d 00:00:01"),
])
def test_calendar_boundaries(now, target, expected):
    assert format_countdown(datetime.fromisoformat(target), datetime.fromisoformat(now)).countdown == expected


@pytest.mark.parametrize("mode,expected", [("years", "0y 009d 02:03"),
                                           ("days", "9d 02:03"), ("weeks", "1w 2d 02:03")])
@pytest.mark.parametrize("seconds", [True, False])
def test_formats_with_optional_seconds(mode, expected, seconds):
    now = datetime(2026, 1, 1)
    target = now + timedelta(days=9, hours=2, minutes=3, seconds=4)
    result = format_countdown(target, now, mode, seconds)
    assert result.countdown == expected + (":04" if seconds else "")
    assert "January 10, 2026" in result.target


@pytest.mark.parametrize("days", [0, -1, -365])
def test_target_reached_keeps_date_and_encouraging_message(days):
    now = datetime(2026, 1, 1)
    target = now + timedelta(days=days)
    result = format_countdown(target, now)
    assert result.countdown == "Make today count"
    assert result.target == f"Target: {target:%B %d, %Y}"


def test_total_days_count_leap_day():
    assert format_countdown(datetime(2025, 1, 1), datetime(2024, 1, 1), "days").countdown == "366d 00:00:00"


@pytest.fixture
def local(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "device"))
    shared = tmp_path / "settings.json"
    monkeypatch.setattr(config, "CONFIG_PATH", str(shared))
    shared.write_text(json.dumps({"death_datetime_iso": "2090-01-01T00:00:00.000000"}))
    return shared


def test_display_save_roundtrips_locally_without_shared_write(local):
    current = storage.load_settings()
    before = local.read_bytes()
    changes = {"opacity": .67, "lock_position": True, "show_seconds": False, "display_mode": "weeks"}
    storage.commit_display(current, changes)
    loaded = storage.load_settings()
    assert all(loaded[k] == v for k, v in changes.items())
    assert local.read_bytes() == before
    assert storage.shared_fields(current) == current.shared_baseline


def test_failed_display_save_keeps_live_options(local, monkeypatch):
    current = storage.load_settings()
    before = deepcopy(current)
    monkeypatch.setattr(storage, "save_preferences", Mock(side_effect=OSError()))
    with pytest.raises(OSError):
        storage.commit_display(current, {**storage.DISPLAY_DEFAULTS, "opacity": .6})
    assert current == before


@pytest.mark.parametrize("change", [{"opacity": float("nan")}, {"opacity": 0.1},
                                    {"show_seconds": 1}, {"lock_position": "yes"}, {"display_mode": []}])
def test_invalid_display_values_rejected(local, change):
    current = storage.load_settings()
    with pytest.raises(ValueError):
        storage.commit_display(current, {**storage.DISPLAY_DEFAULTS, **change})


@pytest.mark.parametrize("method", ["_drag_start", "_drag_move", "_drag_end", "_resize_start", "_resize_move", "_resize_end"])
def test_locked_clock_cannot_move_or_resize(method):
    clock = widget.CountdownWidget.__new__(widget.CountdownWidget)
    clock.config = {"lock_position": True}
    clock.win = Mock()
    clock._recover_window = Mock()
    clock._save_window_state = Mock()
    getattr(clock, method)(SimpleNamespace(x_root=500, y_root=500))
    clock.win.geometry.assert_not_called()
    clock._recover_window.assert_not_called()
    clock._save_window_state.assert_not_called()


@pytest.mark.parametrize("visible,modal,should_lift", [(True, False, True), (True, True, False), (False, False, False)])
def test_topmost_refresh_respects_hide_and_modal_dialog(monkeypatch, visible, modal, should_lift):
    clock = widget.CountdownWidget.__new__(widget.CountdownWidget)
    clock.win = Mock()
    clock._work_areas = ()
    clock._interacting = False
    clock.is_visible = Mock(return_value=visible)
    clock.win.grab_current.return_value = object() if modal else None
    monkeypatch.setattr(widget, "get_work_areas", Mock(return_value=()))
    clock._reassert_topmost()
    assert clock.win.lift.called == should_lift
    clock.win.deiconify.assert_not_called()
    clock.win.after.assert_called_once()


def test_apply_display_does_not_reveal_hidden_clock():
    clock = widget.CountdownWidget.__new__(widget.CountdownWidget)
    clock.config = {"lock_position": True, "opacity": .6}
    clock.win, clock.grip = Mock(), Mock()
    clock._update_display = Mock()
    clock.apply_display_preferences()
    clock.win.attributes.assert_called_once_with("-alpha", .6)
    clock.grip.place_forget.assert_called_once()
    clock.win.deiconify.assert_not_called()
    clock.win.lift.assert_not_called()


def test_display_form_failure_allows_retry(local, monkeypatch):
    form = display_window.DisplayWindow.__new__(display_window.DisplayWindow)
    form.config = storage.load_settings()
    form.lock = Mock(get=Mock(return_value=True))
    form.seconds = Mock(get=Mock(return_value=False))
    form.mode = Mock(get=Mock(return_value="Total days"))
    form.opacity = Mock(get=Mock(return_value=60))
    form.win, form.on_save = Mock(), Mock()
    monkeypatch.setattr(storage, "save_preferences", Mock(side_effect=OSError()))
    error = Mock()
    monkeypatch.setattr(display_window.messagebox, "showerror", error)
    form._save()
    error.assert_called_once()
    form.on_save.assert_not_called()
    form.win.destroy.assert_not_called()
