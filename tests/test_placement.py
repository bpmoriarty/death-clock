"""Placement regressions using synthetic desktops; never reads live settings."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from death_clock import placement, widget
from death_clock.app import App
from death_clock.placement import (WorkArea, Placement, recover_placement,
                                   reset_placement, resize_placement, fit_font_sizes)


PRIMARY = WorkArea(0, 0, 1920, 1040, True)
LEFT = WorkArea(-1600, 0, 0, 860)
ABOVE = WorkArea(0, -1080, 1920, 0)


@pytest.mark.parametrize("saved, areas", [
    (Placement(100, 100, 440, 120), (PRIMARY,)),
    (Placement(-27, 100, 440, 120), (PRIMARY,)),
    (Placement(-1300, 100, 440, 120), (PRIMARY, LEFT)),
    (Placement(100, -800, 440, 120), (PRIMARY, ABOVE)),
    (Placement(-200, 100, 440, 120), (PRIMARY, LEFT)),
    (Placement(1860, 100, 440, 120), (PRIMARY,)),
])
def test_reachable_position_does_not_drift(saved, areas):
    assert recover_placement(saved, areas) == saved


@pytest.mark.parametrize("saved, areas", [
    (Placement(-1300, 100, 440, 120), (PRIMARY,)),
    (Placement(100, -800, 440, 120), (PRIMARY,)),
    (Placement(2000, 100, 440, 120), (PRIMARY,)),
    (Placement(1870, 100, 440, 120), (PRIMARY,)),
    (Placement(100, 1041, 440, 120), (PRIMARY,)),
    (Placement(2100, 200, 440, 120), (PRIMARY, WorkArea(3000, 0, 4600, 900))),
    (Placement(0, 0, 9000, 9000), (PRIMARY,)),
    (Placement(100, 100, 440, 120), (WorkArea(0, 0, 240, 80, True),)),
    (Placement(0, -20, 440, 120), (WorkArea(80, 60, 1280, 720, True),)),
])
def test_unreachable_or_oversized_clock_fits_a_work_area(saved, areas):
    result = recover_placement(saved, areas)
    assert any(a.left <= result.x and a.top <= result.y
               and result.x + result.width <= a.right
               and result.y + result.height <= a.bottom for a in areas)
    assert recover_placement(result, areas) == result


def test_reset_uses_primary_not_enumeration_order():
    result = reset_placement(Placement(-1000, 100, 440, 120), (LEFT, PRIMARY))
    assert result == Placement(740, 460, 440, 120)


@pytest.mark.parametrize("area", [PRIMARY, LEFT, WorkArea(0, 0, 240, 80, True)])
def test_resize_grip_cannot_be_dragged_past_work_area(area):
    start = Placement(area.left + 10, area.top + 10, 280, 90)
    result = resize_placement(start, 10000, 10000, area)
    assert result.x + result.width == area.right
    assert result.y + result.height == area.bottom
    smaller = resize_placement(start, -100, -100, area)
    assert smaller.width == min(280, area.width - 10)
    assert smaller.height == min(90, area.height - 10)


def test_negative_geometry_is_absolute_left_top_offset():
    assert Placement(-1500, -900, 440, 120).geometry() == "440x120+-1500+-900"


@pytest.mark.parametrize("size", [(280, 90), (440, 120), (240, 80), (800, 200)])
@pytest.mark.parametrize("metric_scale", [1, 1.5, 2])
def test_font_fitting_uses_measured_dimensions(size, metric_scale):
    # Simulate different font metrics rather than assuming a fixed point/pixel ratio.
    measure = lambda text, pixels: len(text) * pixels * .65 * metric_scale
    linespace = lambda pixels: pixels * 1.3 * metric_scale
    countdown = "100y 365d 23:59:59"
    date = "Est. September 30, 2075"
    large, small = fit_font_sizes(*size, countdown, date, measure, linespace)
    assert large >= small >= 1
    assert measure(countdown, large) <= size[0] - 26
    assert measure(date, small) <= size[0] - 44
    assert linespace(large) + 2 * linespace(small) <= size[1] - 18


def test_monitor_query_failure_keeps_last_good_layout(monkeypatch):
    monkeypatch.setattr(placement, "_windows_work_areas", Mock(side_effect=OSError))
    window = Mock()
    assert placement.get_work_areas(window, (PRIMARY, LEFT)) == (PRIMARY, LEFT)
    window.winfo_screenwidth.return_value = 1280
    window.winfo_screenheight.return_value = 720
    assert placement.get_work_areas(window) == (WorkArea(0, 0, 1280, 720, True),)


@pytest.fixture
def clock(monkeypatch):
    clock = widget.CountdownWidget.__new__(widget.CountdownWidget)
    clock.config = {"death_datetime_iso": "2075-01-01T00:00:00", "window": {}}
    clock._work_areas = (PRIMARY, LEFT)
    clock._interacting = False
    clock._scale_fonts = Mock()
    clock.on_window_change = Mock()
    clock.win = Mock()
    clock.win.winfo_x.return_value = -1300
    clock.win.winfo_y.return_value = 100
    clock.win.winfo_width.return_value = 440
    clock.win.winfo_height.return_value = 120
    clock.win.state.return_value = "normal"

    def geometry(value):
        import re
        w, h, x, y = map(int, re.fullmatch(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", value).groups())
        clock.win.winfo_x.return_value = x
        clock.win.winfo_y.return_value = y
        clock.win.winfo_width.return_value = w
        clock.win.winfo_height.return_value = h

    clock.win.geometry.side_effect = geometry
    monkeypatch.setattr(widget, "get_work_areas", Mock(return_value=(PRIMARY,)))
    return clock


def test_unplug_recovery_preserves_target_and_stays_hidden(clock):
    clock.win.state.return_value = "withdrawn"
    target = clock.config["death_datetime_iso"]
    clock._reassert_topmost()
    assert clock._current_placement() == Placement(0, 100, 440, 120)
    assert clock.config["death_datetime_iso"] == target
    clock.on_window_change.assert_called_once()
    clock.win.deiconify.assert_not_called()
    clock.win.lift.assert_not_called()
    clock._reassert_topmost()
    clock.on_window_change.assert_called_once()  # no repeat disk writes


def test_layout_recovery_waits_until_drag_finishes(clock):
    clock._interacting = True
    clock._reassert_topmost()
    clock.win.geometry.assert_not_called()
    clock._drag_end(None)
    assert clock._current_placement().x == 0
    clock.on_window_change.assert_called_once()


def test_reset_reveals_clock_and_saves_only_placement(clock):
    original = deepcopy(clock.config)
    clock.reset_position()
    assert clock.config == {**original, "window": dict(x=740, y=460, width=440, height=120)}
    clock.win.deiconify.assert_called_once()
    clock.on_window_change.assert_called_once()


def test_show_recovers_before_revealing(clock):
    clock.show()
    assert clock._current_placement().x == 0
    clock.win.deiconify.assert_called_once()
    clock.on_window_change.assert_called_once()


def test_startup_preserves_valid_secondary_monitor_position(clock, monkeypatch):
    monkeypatch.setattr(widget, "get_work_areas", Mock(return_value=(PRIMARY, LEFT)))
    saved = dict(x=-1300, y=100, width=440, height=120)
    clock.config["window"] = saved.copy()
    clock._setup_window()
    assert clock.config["window"] == saved
    assert clock._current_placement() == Placement(**saved)
    clock.on_window_change.assert_not_called()


def test_tray_reset_schedules_work_on_ui_thread():
    app = App.__new__(App)
    app.root = Mock()
    app.widget = Mock()
    app._tray_reset_position()
    app.root.after.assert_called_once_with(0, app._reset_widget_position)
    app.widget.reset_position.assert_not_called()
    app.root.after.call_args.args[1]()
    app.widget.reset_position.assert_called_once()


def test_configure_updates_fonts_only_for_toplevel(clock):
    clock._on_configure(SimpleNamespace(widget=object(), width=10, height=10))
    clock._scale_fonts.assert_not_called()
    clock._on_configure(SimpleNamespace(widget=clock.win, width=280, height=90))
    clock._scale_fonts.assert_called_once_with(280, 90)
