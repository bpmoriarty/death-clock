# Death Clock

An always-on-top personal reminder to use time well. Keep your existing countdown
or choose a target date or age. An optional, unvalidated legacy calculation is
available with a preview before saving.

Windows only — it uses the Windows registry for launch-at-login and a system
tray icon.

![gray widget showing TIME REMAINING above a large green countdown](reboot%20test%20reference.png)

---

## Setup on a new machine

You need [uv](https://docs.astral.sh/uv/) installed. Then:

```powershell
git clone https://github.com/bpmoriarty/death-clock.git
cd death-clock
uv sync --python 3.12  # creates .venv and installs the locked dependencies
```

Then double-click **Start Death Clock.vbs** in the project folder. To launch
from PowerShell instead, use `uv run --no-sync python -m death_clock.main`.

On first launch Settings opens. Choose a reminder date or age and confirm the preview. You can also restore an existing countdown. The optional legacy calculation accepts
a birth date, sex, and health factors.

## Daily use

Double-click **`Start Death Clock.vbs`**, or double-click
**`Create Desktop Shortcut.vbs`** once to create a desktop shortcut. Both use the
project's Python environment without a console window and do not depend on the
system's `.pyw` file association. `run.pyw` remains available when that association
works; it now checks and launches the project interpreter instead of borrowing
its packages.

Opening the clock again brings the existing instance forward, including when
hidden. If first-run Settings is open, that same form is brought forward. Only
one updated clock per Windows user can own the settings, including across copies
of this project. The first copy opened wins.

**When upgrading from older code:** exit the existing clock once before using the
new launcher. Already-running older versions do not have the new instance lock.
If launch-at-login is enabled, open Settings in the updated clock and Save once
to refresh the login entry to the checked launcher; the target stays unchanged.

| Action | How |
|---|---|
| Move it | Click and drag anywhere on the widget |
| Resize it | Drag the ◢ grip in the bottom-right corner |
| Settings / Hide / Exit | Right-click the widget |
| Bring it back after hiding | Tray menu → Show, or open the launcher again |
| Recover a misplaced clock | Tray menu → Reset position |
| Lock position, change opacity or countdown format | Clock or tray menu → Display… |
| Launch at Windows login | Tick the box in Settings |

The clock remembers positions on any connected monitor, including monitors to
the left or above the primary display. If its monitor disappears, it moves back
into a usable work area. A layout check runs every five seconds and waits until
you finish dragging/resizing. **Reset position** centers it on the primary screen
and shows it, without changing the saved countdown. Automatic recovery keeps a
hidden clock hidden.

Resizing is limited to the current monitor's usable area. Text is measured to fit
the chosen size, including the date label and resize grip.

## Launch troubleshooting

The launcher only checks the environment; it never installs or upgrades anything.
If startup fails, it shows an actionable error. Small diagnostic logs are stored
under `%LOCALAPPDATA%\DeathClock\logs`, outside the OneDrive project. They contain
error categories/types and code locations, not profile values, exception messages,
or captured process output. The Python log rotates at 32 KB with one previous
copy; the Windows bootstrap log is also capped around 32 KB.

For a genuinely missing/broken environment, exit the clock normally, keep
`settings.json` and its backup safe, then run `uv sync --python 3.12` from this
folder. Never synchronize dependencies while the clock is running. Reopen
`Start Death Clock.vbs` afterward. Recreate the shortcut and re-save the login
setting if you move the project folder.

The `.vbs` entry points require Windows Script Host. If your Windows configuration
disables it, use `uv run --no-sync python -m death_clock.main` from this folder;
that entry point has the same single-instance protection. Do not change Windows
security policy just to enable a shortcut.

## Your saved data

`settings.json` holds your saved reminder target and any profile inputs (birth
date, sex, and health selections). A date-only target needs no birth date. New
legacy calculations also retain source/model details and calculation time. It is
excluded from Git by `.gitignore`. Files in a OneDrive folder may still sync
between computers; Git exclusion does not prevent that. `settings.example.json` shows
the file's shape without any personal data.

Window placement and opacity live in
`%LOCALAPPDATA%\DeathClock\preferences.json`, with a rolling `.bak` beside it.
These preferences belong to this Windows user on this computer and are shared
by project copies on that computer. They do not travel with the project folder.
Display options live in the same local file; the default opacity remains 0.93.
Moving, resizing, and exiting write only this local file. Login startup is read
from Windows when Settings opens; an unreadable entry disables that checkbox
and shows an explanation. Imported files never enable login startup.

On the first updated launch, existing placement is copied into local preferences
with a backup. The original shared file stays intact as a recovery source.
Legacy window/startup fields in it become inactive and are removed on the next
explicit profile change or restore, after backing up the previous file. Later
launches use local preferences even if another computer changes those old fields.
Local preference damage uses the local backup; unreadable originals are protected
from overwriting. No migration recalculates a target or changes login registration.

## Display options

Choose **Display…** from the clock's right-click menu or its tray menu. Lock the
position and size, adjust opacity from 20% to 100%, hide seconds, or choose years
and days, total days, or total weeks with remaining days. **Save display** applies
the changes only after saving them on this computer. **Cancel** leaves the clock
unchanged. A hidden clock stays hidden. Unlock through Display to move/resize
again; Reset position and automatic monitor recovery still work while locked.

Years are whole calendar years from the current time to the target, followed by
remaining days and clock time. February 29 anniversaries use February 28 in
non-leap years. This corrects the previous fixed 365-day year display, so the
digits may differ without changing the saved target. Total days use 24-hour local
wall-clock days; weeks are groups of seven days. Partial seconds round upward.
Hiding seconds removes that field while the clock continues refreshing normally.

At or after the target, the message becomes **Make today count**, and the target
date stays visible. The app never starts a new target automatically. Brighter
gray labels retain the existing gray-and-green appearance, and periodic topmost
refresh leaves Settings and Display dialogs in front.

## Moving a countdown between computers

In Settings, choose **Export countdown…**, copy the resulting file to the other
computer, and choose **Restore countdown…** there. Restore works in first-run
Settings too. It previews the target and asks before replacing the profile,
backs up the previous countdown, and retains that computer's preferences.
It never recalculates. Cancel leaves everything unchanged. Export uses the saved
profile; Restore discards unsaved form edits after confirmation.

Exports contain the target, birth date, sex, health selections, and calculation
details when present. They exclude device preferences. Keep them
private. The default `*.deathclock-export.json` names are ignored by Git; a
renamed export is not necessarily ignored. Exports in OneDrive may still sync.
You can also copy `settings.json` before the first launch or select an existing
settings file in Restore. Cloning the repository alone does not copy your target.

OneDrive is not a conflict-free database. Let it finish syncing and change the
shared profile on only one computer at a time. If the shared file changes while
the clock is running, local preference saves leave it alone; profile changes and
restores refuse to overwrite a detected change and ask you to reopen the clock.
The running clock keeps its loaded target until reopened or explicitly restored.
This check cannot eliminate simultaneous cross-computer writes or OneDrive
conflict copies. Review competing files through Restore rather than guessing
which target to overwrite. Use the updated version on each computer; old versions
still write device preferences into shared settings.

---

## Countdown protection

After a target is saved with the updated app, `settings.json.bak` holds a recovery
copy. Later profile changes/restores keep the previous usable countdown in that
rolling backup. Preference-only saves do not touch the shared file or its backup.
If the main settings are damaged or missing, the app can load the backup and
explain what happened without recalculating your target. Damaged originals are
kept as `settings.json.corrupt` (with unique suffixes for additional copies).
These files also contain personal information and are excluded from Git.

A failed settings save leaves the running target unchanged and displays an error
so you can retry. Saving preferences preserves the target exactly. Changing the
profile asks you to confirm before replacing an existing target. A Windows-login
registration failure is reported separately if the countdown itself was saved.
Local preferences are saved before a changed shared target. If that second save
fails, local placement may have saved, but the running target stays unchanged.

## Choosing a reminder target

Settings opens with **Keep saved target** when a countdown exists. This keeps
the exact stored value, even if the birth date is missing or damaged. Use this
option for login-setting changes. Profile fields are hidden until needed.

- **Choose a date:** enter YYYY-MM-DD. No birth date or health profile is needed.
  The target is midnight at the start of that date, in local time.
- **Choose an age:** enter a whole age from 1 to 150 and your birth date. The
  target is midnight on that birthday; February 29 uses February 28 in non-leap years.
- **Legacy calculation:** explicitly request a fresh result from the legacy formula.
  Its base table matches the fixed SSA 2021 table in the 2024 Trustees Report.
  The lifestyle adjustments and resulting personal estimate remain unvalidated.
  Current/former smoker cannot both be selected for a new calculation.

Every new selection, including first setup, previews the exact target before
saving. Declining or Cancel changes nothing. Past dates are allowed after a
clear preview and show “Make today count.” The input area scrolls and the window
can be resized; Save, Cancel, and the existing target stay outside that area.

Only the saved date drives the clock. Startup, recovery, migration, display
changes, and keeping the saved target never calculate a replacement. The legacy
formula depends on the calculation date: interpolation smooths changes, but
does not make repeated calculations on different dates identical.

## Project layout

| File | What it does |
|---|---|
| `Start Death Clock.vbs` | Checked Windows launcher (no console window) |
| `Create Desktop Shortcut.vbs` | Creates the desktop shortcut |
| `run.pyw` | Python bootstrap for the Windows launcher or `.pyw` association |
| `death_clock/launcher.py` | Verifies and starts the project's own interpreter |
| `death_clock/instance.py` | Single-instance lock and reveal requests |
| `death_clock/diagnostics.py` | Bounded local error reporting without profile data |
| `death_clock/storage.py` | Local preferences, shared-file conflict checks, export/restore |
| `death_clock/countdown.py` | Calendar-aware countdown formatting |
| `death_clock/display_window.py` | Local display controls |
| `death_clock/main.py` | Entry point |
| `death_clock/app.py` | Orchestrator — wires the widget, tray, and settings together |
| `death_clock/widget.py` | The floating countdown overlay |
| `death_clock/settings_window.py` | CustomTkinter settings form |
| `death_clock/config.py` | Reads/writes `settings.json` |
| `death_clock/targets.py` | Explicit target date/age selection and validation |
| `death_clock/factors.py` | Shared definitions for legacy formula inputs |
| `death_clock/life_expectancy.py` | Optional legacy reminder formula |
| `death_clock/ssa_life_table.py` | Loads and interpolates the pinned SSA table |
| `death_clock/data/ssa_2021_tr2024.csv` | Verified 2021 table from the 2024 Trustees Report |
| `death_clock/provenance.py` | Validates saved calculation attribution |
| `tools/verify_ssa_source.py` | Offline comparison against the retained source |
| `death_clock/startup.py` | Windows registry launch-at-login |

---

## A caveat on the numbers

All 240 base-table values were checked against the fixed official source. The
audit corrected 238 values in the earlier embedded table. Existing saved targets
were preserved exactly; only a newly confirmed calculation uses the corrected
table. See the [source verification and audit](docs/sources/SSA_VERIFICATION.md).

The legacy multipliers have no verified source mapping in this project and are
combined as if independent. Verifying the base table does not validate those
adjustments or make the result an individual prediction. A chosen date or age
better matches the app's purpose as a personal reminder.

New legacy calculations save the source, table hash, model version, calculation
time, and exact target. Export/restore preserves valid attribution; old targets
receive no invented calculation history. Choosing a manual date or age clears
that attribution. Imported metadata is not proof of authenticity.

## Development and verification

After setup, run these commands from the project root in PowerShell. They use
the existing environment without installing or updating dependencies:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B tools/verify_ssa_source.py
```

The latest regression run passed **252 tests**. Tests use fictional profiles and
temporary paths. The source check compares all 120 ages for both sexes against
the retained HTML and checks pinned hashes; it does not fetch a changing online
table. Preserve exact existing targets when maintaining code or data.

For an isolated UI session, run
`.\.venv\Scripts\python.exe -B tools/manual_acceptance.py`. This creates temporary
fictional settings and disables login registration, the tray, and the production
instance lock. It is a test helper, not the normal launcher.

Local manual checks covered target previews, export/restore dialogs, cancellation,
and scrolling. Windows sign-in, actual second-computer restore, physical
monitor/scaling changes, and real tray/desktop-shortcut checks were explicitly
deferred by the owner on September 27, 2026; they are not claimed as passed.
See the [acceptance record](docs/MANUAL_ACCEPTANCE.md) and
[project status](PROJECT_STATUS.md) for details and future checks.

## License

This project is licensed under the [MIT License](LICENSE).
