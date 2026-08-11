# Project: Death Clock

## What This Is
A desktop app that counts down to an estimated death date using SSA actuarial life tables (2021) plus adjustments for health/lifestyle factors. The widget floats on top of other apps, is draggable and resizable, and persists the countdown across reboots.

---

## Current Status

**Phase:** Polishing

**Last Session:** 2026-04-05

**Overall Health:** 🟢 Working

### What's Working
- Always-on-top countdown widget (gray background, green numerals)
- Drag to move, resize grip in bottom-right corner
- Right-click menu: Settings | Hide | Exit
- System tray icon with Show | Settings | Exit
- Settings window (CustomTkinter): DOB, sex, all health factors, boot startup toggle
- Death date calculated once on Settings save and stored in `settings.json` as `death_datetime_iso`
- Countdown resumes correctly after app is closed and reopened (no reset)
- Boot startup registration via Windows Registry (opt-in toggle in Settings)

### What's Broken or Incomplete
- No confirmation dialog when exiting (minor — low priority)
- Always-on-top does not work over exclusive-fullscreen games (Windows OS limitation, not fixable)

---

## What We're Doing Now

All testing complete. App is fully functional and in daily use. No active tasks — next work would be optional polish (desktop shortcut, styling tweaks).

---

## Recent Decisions

| Date | Decision | Why |
|------|----------|-----|
| 2026-04-05 | Started completely from scratch | Previous version had persistent reset and boot startup bugs; fresh design was cleaner |
| 2026-04-05 | Store `death_datetime_iso` in settings.json | The core fix — death date calculated once on Save, never recalculated on launch |
| 2026-04-05 | Gray background (#2d2d2d), green text (#44cc77) | Previous black/red was too aggressive |
| 2026-04-05 | Hide via right-click menu (no close button on widget) | Cleaner look; tray icon handles restore |
| 2026-04-05 | Archived old code to `death_clock_archive/` | Preserved for reference, not deleted |
| 2026-04-05 | Boot startup opt-in via Settings checkbox | More reliable than auto-registering; user controls it |

---

## Next Steps

1. [x] **Reset test** — confirmed: countdown does not reset on close/reopen
2. [x] **Hide/show test** — confirmed working
3. [x] **Double-click launcher** — confirmed: double-clicking `run.pyw` opens app cleanly and stays open independently
4. [x] **Reboot test** — confirmed: app launches automatically at Windows login
5. [ ] **Desktop shortcut** — create shortcut to `run.pyw` for easy daily launching (holding off until after reboot test)
6. [ ] **Tweak styling** — adjust anything that feels off after more use

---

## Important Files

| File | What It Does |
|------|--------------|
| `run.pyw` | Double-click launcher (uses .pyw to suppress console window) |
| `settings.json` | Persisted config — includes `death_datetime_iso`, health factors, window position |
| `death_clock/app.py` | Main orchestrator — coordinates widget, tray, settings |
| `death_clock/widget.py` | The floating countdown overlay |
| `death_clock/settings_window.py` | CustomTkinter settings form |
| `death_clock/config.py` | Load/save settings.json; `get_death_datetime()` is the key function |
| `death_clock/life_expectancy.py` | Actuarial calculation — called only when user saves settings |
| `death_clock/ssa_life_table.py` | SSA 2021 life table data (male/female by age) |
| `death_clock/startup.py` | Windows Registry boot startup registration |
| `death_clock_archive/` | Old code — kept for reference, not used |

---

## Things Claude Should Remember

- The death date must NEVER be recalculated on app launch — only when the user explicitly saves settings
- `death_datetime_iso` in settings.json is the source of truth for the countdown
- Use `uv run python -m death_clock.main` to run during development
- Double-click `run.pyw` for a clean no-console launch
- The `.venv` is already set up with customtkinter, pystray, Pillow installed
- Always-on-top does NOT work over exclusive-fullscreen games (Windows OS limitation — nothing can)
- Brian is learning to code — explain changes in plain language and comment the code

---

## Session Log

### 2026-04-05 (session 2)
- Completed all user acceptance tests:
  - Reset test passed: countdown does not reset on close/reopen
  - Hide/show test passed: right-click Hide and tray restore both work
  - Double-click `run.pyw` confirmed: app launches independently, stays open
  - Reboot test passed: app auto-launches at Windows login via Registry
- App is fully functional and in daily use
- Next: optional — create desktop shortcut, tweak styling after more use

### 2026-04-05 (session 1)
- Reviewed previous broken version (reset bug root cause: death date was never saved to disk)
- Designed fresh architecture from scratch; archived old `death_clock/` folder
- Built all modules: config, life_expectancy, widget, settings_window, app, startup, main, run.pyw
- Fixed `pady` double-keyword bug in settings_window.py
- Fixed invalid escape sequence in startup.py docstring
- App confirmed launching and displaying countdown

