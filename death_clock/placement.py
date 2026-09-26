"""Monitor discovery and placement rules, separate from the live widget.

Coordinates stay in the calling UI thread's Windows coordinate system. Do not
change process DPI awareness after Tk has created its windows.
Windows API reference: https://learn.microsoft.com/windows/win32/api/winuser/ns-winuser-monitorinfo
"""

from dataclasses import dataclass
import ctypes
from ctypes import wintypes


MIN_WIDTH = 280
MIN_HEIGHT = 90
VISIBLE_MARGIN = 60


@dataclass(frozen=True)
class WorkArea:
    left: int
    top: int
    right: int
    bottom: int
    primary: bool = False

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top


@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    width: int
    height: int

    def geometry(self):
        # The leading + means an offset from the LEFT/TOP, even when the
        # offset itself is negative. A bare - means right/bottom anchoring in Tk.
        return f"{self.width}x{self.height}+{self.x}+{self.y}"

    def as_dict(self):
        return dict(x=self.x, y=self.y, width=self.width, height=self.height)


def _windows_work_areas() -> tuple[WorkArea, ...]:
    class MonitorInfo(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE,
                                      wintypes.HDC, ctypes.POINTER(wintypes.RECT),
                                      wintypes.LPARAM)
    get_info = user32.GetMonitorInfoW
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
    get_info.restype = wintypes.BOOL
    enumerate_monitors = user32.EnumDisplayMonitors
    enumerate_monitors.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT),
                                  callback_type, wintypes.LPARAM]
    enumerate_monitors.restype = wintypes.BOOL
    areas = []
    failed = False

    @callback_type
    def collect(monitor, _dc, _rect, _data):
        nonlocal failed
        info = MonitorInfo()
        info.cbSize = ctypes.sizeof(info)
        if not get_info(monitor, ctypes.byref(info)):
            failed = True
            return False
        rect = info.rcWork
        if rect.right > rect.left and rect.bottom > rect.top:
            areas.append(WorkArea(rect.left, rect.top, rect.right, rect.bottom,
                                  bool(info.dwFlags & 1)))
        return True

    if not enumerate_monitors(None, None, collect, 0) or failed or not areas:
        raise OSError("Windows monitor work areas are unavailable")
    return tuple(sorted(set(areas), key=lambda a: (not a.primary, a.left, a.top)))


def get_work_areas(window, previous=()) -> tuple[WorkArea, ...]:
    """Keep the last good layout if a display query temporarily fails."""
    try:
        return _windows_work_areas()
    except (OSError, AttributeError):
        return previous or (WorkArea(0, 0, window.winfo_screenwidth(),
                                     window.winfo_screenheight(), True),)


def _overlap(window: Placement, area: WorkArea):
    return (max(0, min(window.x + window.width, area.right) - max(window.x, area.left)),
            max(0, min(window.y + window.height, area.bottom) - max(window.y, area.top)))


def monitor_for(window: Placement, areas: tuple[WorkArea, ...]) -> WorkArea:
    """Prefer greatest intersection, then nearest work area, then primary."""
    def score(area):
        width, height = _overlap(window, area)
        dx = max(area.left - (window.x + window.width), window.x - area.right, 0)
        dy = max(area.top - (window.y + window.height), window.y - area.bottom, 0)
        return (width * height, -(dx * dx + dy * dy), area.primary)
    return max(areas, key=score)


def recover_placement(window: Placement, areas: tuple[WorkArea, ...]) -> Placement:
    """Keep reachable placements exactly; otherwise bring the whole clock back."""
    area = monitor_for(window, areas)
    width = min(max(MIN_WIDTH, window.width), area.width)
    height = min(max(MIN_HEIGHT, window.height), area.height)
    visible_w, visible_h = _overlap(window, area)
    if (width == window.width and height == window.height
            and visible_w >= min(VISIBLE_MARGIN, width)
            and visible_h >= min(VISIBLE_MARGIN, height)):
        return window
    return Placement(min(max(window.x, area.left), area.right - width),
                     min(max(window.y, area.top), area.bottom - height), width, height)


def reset_placement(window: Placement, areas: tuple[WorkArea, ...]) -> Placement:
    """Center the current size on the primary work area, shrinking if necessary."""
    primary = next((a for a in areas if a.primary), areas[0])
    fitted = recover_placement(window, (primary,))
    return Placement(primary.left + (primary.width - fitted.width) // 2,
                     primary.top + (primary.height - fitted.height) // 2,
                     fitted.width, fitted.height)


def resize_placement(window: Placement, width: int, height: int,
                     area: WorkArea) -> Placement:
    """Keep the resize grip inside the selected monitor's usable bottom/right."""
    max_width = max(1, area.right - max(window.x, area.left))
    max_height = max(1, area.bottom - max(window.y, area.top))
    return Placement(window.x, window.y,
                     min(max(MIN_WIDTH, width), max_width),
                     min(max(MIN_HEIGHT, height), max_height))


def fit_font_sizes(width, height, countdown, date_text, measure, linespace):
    """Find the largest pixel font fitting all three rows, including grip space."""
    available_width = max(1, width - 26)
    available_height = max(1, height - 18)
    low, high = 1, max(1, min(120, height))
    best = (1, 1)
    while low <= high:
        size = (low + high) // 2
        small = min(size, max(11, size // 3))
        fits = (measure(countdown, size) <= available_width
                and measure("TIME REMAINING", small) <= available_width
                and measure(date_text, small) <= max(1, available_width - 18)
                and linespace(size) + 2 * linespace(small) <= available_height)
        if fits:
            best = size, small
            low = size + 1
        else:
            high = size - 1
    return best
