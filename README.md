# Death Clock

An always-on-top desktop widget that counts down to an estimated death date,
calculated from [SSA actuarial life tables (2021)](https://www.ssa.gov/oact/STATS/table4c6.html)
adjusted for health and lifestyle factors.

Windows only — it uses the Windows registry for launch-at-login and a system
tray icon.

![gray widget showing TIME REMAINING above a large green countdown](reboot%20test%20reference.png)

---

## Setup on a new machine

You need [uv](https://docs.astral.sh/uv/) installed. Then:

```bash
git clone https://github.com/bpmoriarty/death-clock.git
cd death-clock
uv sync --python 3.12  # creates .venv and installs the locked dependencies
```

Then launch it:

```bash
uv run python -m death_clock.main
```

On first launch the Settings window opens, since there's no profile yet. Fill in
your date of birth, sex, and health factors, then press **Save settings**.

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
| Bring it back after hiding | Click the tray icon |
| Recover a misplaced clock | Tray menu → Reset position |
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

`settings.json` holds your date of birth, health factors, and death date. It is
excluded from Git by `.gitignore`. Files in a OneDrive folder may still sync
between computers; Git exclusion does not prevent that. `settings.example.json` shows
the file's shape without any personal data.

To move your exact countdown to another computer, copy `settings.json` across by
hand. Cloning the repo alone won't do it — see below.

Copy the file in **before** the first launch. If it isn't there, the app assumes
you're a new user and opens first-run Settings. Once it is in place you can open
Settings freely — changing only a preference like "launch at login" leaves the
stored death date exactly as it was.

---

## Countdown protection

After a target is saved with the updated app, `settings.json.bak` holds a recovery
copy. Later saves keep the previous usable countdown in that rolling backup.
If the main settings are damaged or missing, the app can load the backup and
explain what happened without recalculating your target. Damaged originals are
kept as `settings.json.corrupt` (with unique suffixes for additional copies).
These files also contain personal information and are excluded from Git.

A failed settings save leaves the running target unchanged and displays an error
so you can retry. Saving preferences preserves the target exactly. Changing the
profile asks you to confirm before replacing an existing target. A Windows-login
registration failure is reported separately if the countdown itself was saved.

## How the countdown works

The important design rule: **the death date is calculated once and stored.**

1. You press Save in Settings.
2. `life_expectancy.compute_death_datetime()` runs — the only place it ever runs
   — and only if your date of birth, sex or factors actually changed.
3. The result is written to `settings.json` as `death_datetime_iso`.
4. Every launch after that just reads that stored value and subtracts `now`.

This is why closing and reopening the app doesn't reset your countdown. Nothing
recalculates on startup.

Step 2's condition matters on a second computer. The calculation reads today's
clock, so running it again months later gives a slightly different answer — you
are genuinely older. Without the check, opening Settings just to tick a checkbox
would quietly replace a death date you had deliberately carried across. Save now
keeps the stored date whenever the actuarial inputs are untouched, and says
"Death date unchanged" so you can see which happened.

### Reproducibility

The calculation interpolates the SSA table at your exact fractional age, so the
same inputs give the same answer regardless of which day you press Save. An
earlier version looked the table up at your whole-number age while measuring age
continuously, which made the result drift ~1 day later per day and then jump
~11 months backwards on each birthday.

A slow drift remains by design: having survived another year genuinely raises
your expected total lifespan, and the effect compounds with age. Recalculating
five years later moves the date by anywhere from a few days to a few months,
depending on your factor mix. That's real actuarial signal, not a bug — what's
gone is the discontinuity.

---

## Project layout

| File | What it does |
|---|---|
| `Start Death Clock.vbs` | Checked Windows launcher (no console window) |
| `Create Desktop Shortcut.vbs` | Creates the desktop shortcut |
| `run.pyw` | Python bootstrap for the Windows launcher or `.pyw` association |
| `death_clock/launcher.py` | Verifies and starts the project's own interpreter |
| `death_clock/instance.py` | Single-instance lock and reveal requests |
| `death_clock/diagnostics.py` | Bounded local error reporting without profile data |
| `death_clock/main.py` | Entry point |
| `death_clock/app.py` | Orchestrator — wires the widget, tray, and settings together |
| `death_clock/widget.py` | The floating countdown overlay |
| `death_clock/settings_window.py` | CustomTkinter settings form |
| `death_clock/config.py` | Reads/writes `settings.json` |
| `death_clock/life_expectancy.py` | Actuarial calculation and hazard ratios |
| `death_clock/ssa_life_table.py` | SSA 2021 life table data |
| `death_clock/startup.py` | Windows registry launch-at-login |

---

## A caveat on the numbers

The hazard ratios in `life_expectancy.py` are rough figures from published
epidemiology, multiplied together as if each factor were independent. They
aren't — smoking and heart disease overlap, exercise and sedentary work pull in
opposite directions. Treat the output as a memento mori, not a medical estimate.
