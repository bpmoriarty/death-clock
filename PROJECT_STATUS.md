# Project: Death Clock

## What This Is
A desktop app that counts down to an estimated death date using SSA actuarial life tables (2021) plus adjustments for health/lifestyle factors. The widget floats on top of other apps, is draggable and resizable, and persists the countdown across reboots.

---

## Current Status

**Phase:** Hardening (was: Polishing)

**Last Session:** 2026-08-11

**Overall Health:** 🟢 Working — in continuous daily use

### What's Working
- Always-on-top countdown widget (gray background, green numerals)
- Drag to move, resize grip in bottom-right corner
- Right-click menu: Settings | Hide | Exit
- System tray icon with Show | Settings | Exit
- Settings window (CustomTkinter): DOB, sex, all health factors, boot startup toggle
- Death date calculated once on Settings save and stored in `settings.json` as `death_datetime_iso`
- Countdown resumes correctly after app is closed and reopened (no reset)
- Boot startup registration via Windows Registry (opt-in toggle in Settings)
- **Now under version control** — private GitHub repo, personal data excluded
- **Dependencies locked** via `pyproject.toml` + `uv.lock`

### What's Broken or Incomplete
- 🔴 **First-run zombie process:** on a machine with no saved profile, closing the
  Settings window without saving leaves an invisible process with no UI and no tray
  icon — only Task Manager can kill it. Will be hit when setting up a second computer.
- 🟠 **Font scaling not restored on launch:** a resized window returns at the right
  size but with default-size text until the grip is nudged.
- 🟠 **`settings.json` writes are not atomic:** a crash or OneDrive sync landing
  mid-write corrupts the file, and the loader has no error handling, so the next
  launch dies silently. Would lose the stored death date.
- 🟡 Boot-startup checkbox swallows all failures silently — no feedback if it fails
- 🟡 Countdown displays 365-day years while the math uses 365.25
- 🟡 `widget.is_visible()` is dead code; Settings has no Cancel button
- No test suite
- No confirmation dialog when exiting (minor — low priority)
- Always-on-top does not work over exclusive-fullscreen games (Windows OS limitation, not fixable)

---

## What We're Doing Now

Version control and reproducibility are done. Next up is fixing the three bugs
found in review (zombie process, font scaling, atomic writes) and adding a test
suite over the pure calculation functions.

---

## Recent Decisions

| Date | Decision | Why |
|------|----------|-----|
| 2026-08-11 | Set up git + private GitHub repo | No version control existed at all; the only safety net was a manual `death_clock_archive/` copy |
| 2026-08-11 | `settings.json` excluded from git | Holds date of birth and health conditions; `settings.example.json` documents its shape instead |
| 2026-08-11 | Repo is private | Personal nature of the app; can be flipped public later |
| 2026-08-11 | Interpolate the SSA table at fractional age | Death date was not reproducible from its inputs — it drifted ~1 day later per day and snapped ~11 months backwards each birthday |
| 2026-08-11 | Pinned dependency upper bounds | Unbounded constraints resolved customtkinter to 6.0.0, a major version jump from the working 5.2.2 |
| 2026-08-11 | Widget position no longer clamped to x≥0 | Saved position of -27 was rewritten to 0 on every launch, drifting the widget right |
| 2026-04-05 | Started completely from scratch | Previous version had persistent reset and boot startup bugs; fresh design was cleaner |
| 2026-04-05 | Store `death_datetime_iso` in settings.json | The core fix — death date calculated once on Save, never recalculated on launch |
| 2026-04-05 | Gray background (#2d2d2d), green text (#44cc77) | Previous black/red was too aggressive |
| 2026-04-05 | Hide via right-click menu (no close button on widget) | Cleaner look; tray icon handles restore |
| 2026-04-05 | Archived old code to `death_clock_archive/` | Preserved for reference — now redundant, git holds the history |
| 2026-04-05 | Boot startup opt-in via Settings checkbox | More reliable than auto-registering; user controls it |

---

## Next Steps

1. [x] Reset / hide-show / double-click / reboot tests — all confirmed
2. [x] Set up git and a private GitHub repo
3. [x] Migrate from bare `requirements.txt` to `pyproject.toml` + `uv.lock`
4. [x] Fix the window drift and the death-date reproducibility bug
5. [ ] Fix the first-run zombie process
6. [ ] Restore font scaling on launch
7. [ ] Make `settings.json` writes atomic and handle a corrupt file
8. [ ] Add a pytest suite over `life_expectancy` / `ssa_life_table`
9. [ ] Delete the now-redundant `requirements.txt` and `death_clock_archive/`
10. [ ] Desktop shortcut to `run.pyw` for easy daily launching
11. [ ] Tweak styling — revisit after the font-scaling fix

---

## Important Files

| File | What It Does |
|------|--------------|
| `run.pyw` | Double-click launcher (uses .pyw to suppress console window) |
| `pyproject.toml` | Dependencies and their version bounds |
| `uv.lock` | Exact resolved versions — `uv sync` reproduces this environment |
| `settings.json` | Persisted config — **git-ignored**, holds personal data |
| `settings.example.json` | Template showing the config shape, no personal data |
| `death_clock/app.py` | Main orchestrator — coordinates widget, tray, settings |
| `death_clock/widget.py` | The floating countdown overlay |
| `death_clock/settings_window.py` | CustomTkinter settings form |
| `death_clock/config.py` | Load/save settings.json; `get_death_datetime()` is the key function |
| `death_clock/life_expectancy.py` | Actuarial calculation — called only when user saves settings |
| `death_clock/ssa_life_table.py` | SSA 2021 life table data (male/female by age) |
| `death_clock/startup.py` | Windows Registry boot startup registration |
| `death_clock_archive/` | Old code — **redundant now that git holds history; slated for deletion** |

---

## Things Claude Should Remember

- The death date must NEVER be recalculated on app launch — only when the user explicitly saves settings
- `death_datetime_iso` in settings.json is the source of truth for the countdown
- **Pressing Save will move the stored date ~10.5 months earlier** (2067-07-12 → ~2066-08-26). The old value was inflated by the drift bug, not by the fix.
- **Never run `uv sync` while the widget is running** — Windows can't replace files a live process holds open. Exit via the tray first.
- Use `uv run python -m death_clock.main` to run during development
- Double-click `run.pyw` for a clean no-console launch
- Always-on-top does NOT work over exclusive-fullscreen games (Windows OS limitation — nothing can)
- Brian is learning to code — explain changes in plain language and comment the code
- Commit after each working feature; the repo is `bpmoriarty/death-clock` (private)

---

## Session Log

### 2026-08-11
- Reviewed full project state; confirmed the app has been running continuously since 2026-07-31
- **Set up git** and pushed to a new private GitHub repo (`bpmoriarty/death-clock`),
  capturing the original working code as a baseline commit before any changes
- `settings.json` excluded from version control; verified absent from GitHub
- **Fixed widget drift:** saved x of -27 was being clamped to 0 on every launch
- **Fixed death-date reproducibility:** the calculation mixed a continuous age with a
  whole-number table lookup, so the same inputs gave answers spread over 368 days
  depending on when you pressed Save. Now interpolates; spread is down to 9 days,
  and the birthday discontinuity is gone.
- **Migrated to uv:** `pyproject.toml` + `uv.lock` replace unpinned `requirements.txt`.
  Caught that unbounded constraints would have upgraded customtkinter 5.2.2 → 6.0.0.
- Added `README.md` and `settings.example.json`
- Code review surfaced three more bugs (zombie process, font scaling, atomic writes)
  and identified `requirements.txt` / `death_clock_archive/` as redundant

### 2026-04-05 (session 2)
- Completed all user acceptance tests:
  - Reset test passed: countdown does not reset on close/reopen
  - Hide/show test passed: right-click Hide and tray restore both work
  - Double-click `run.pyw` confirmed: app launches independently, stays open
  - Reboot test passed: app auto-launches at Windows login via Registry
- App is fully functional and in daily use

### 2026-04-05 (session 1)
- Reviewed previous broken version (reset bug root cause: death date was never saved to disk)
- Designed fresh architecture from scratch; archived old `death_clock/` folder
- Built all modules: config, life_expectancy, widget, settings_window, app, startup, main, run.pyw
- Fixed `pady` double-keyword bug in settings_window.py
- Fixed invalid escape sequence in startup.py docstring
- App confirmed launching and displaying countdown
