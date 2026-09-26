"""Pure presentation of a saved target, using local calendar time."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime
from math import ceil


@dataclass(frozen=True)
class CountdownText:
    heading: str
    countdown: str
    target: str


def format_countdown(target: datetime, now: datetime, mode="years", show_seconds=True) -> CountdownText:
    """Whole calendar years from now, then remaining days and clock time.

    A February 29 anniversary falls on February 28 in non-leap years. Total
    days/weeks use 24-hour local wall-clock days. Round partial seconds upward
    so a future target never appears expired early.
    """
    if mode not in ("years", "days", "weeks"):
        raise ValueError("Unknown countdown format")
    date_label = f"Target: {target:%B %d, %Y}"
    if target <= now:
        return CountdownText("YOUR TIME MATTERS", "Make today count", date_label)
    years = 0
    anchor = now
    if mode == "years":
        years = target.year - now.year
        def anniversary(n):
            year = now.year + n
            return now.replace(year=year, day=min(now.day, monthrange(year, now.month)[1]))
        anchor = anniversary(years)
        if anchor > target:
            years -= 1
            anchor = anniversary(years)
    seconds = ceil((target - anchor).total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    clock = f"{hours:02d}:{minutes:02d}"
    if show_seconds:
        clock += f":{seconds:02d}"
    if mode == "years":
        prefix = f"{years}y {days:03d}d"
    elif mode == "days":
        prefix = f"{days:,}d"
    else:
        weeks, days = divmod(days, 7)
        prefix = f"{weeks:,}w {days}d"
    return CountdownText("TIME REMAINING", f"{prefix} {clock}", date_label)
