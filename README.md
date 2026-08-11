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
uv sync          # creates .venv and installs the exact locked versions
```

Then launch it:

```bash
uv run python -m death_clock.main
```

On first launch the Settings window opens, since there's no profile yet. Fill in
your date of birth, sex, and health factors, then press **Save & Recalculate
Death Date**.

## Daily use

Double-click **`run.pyw`**. The `.pyw` extension makes Windows open it with
`pythonw.exe`, so no black console window appears — just the widget.

| Action | How |
|---|---|
| Move it | Click and drag anywhere on the widget |
| Resize it | Drag the ◢ grip in the bottom-right corner |
| Settings / Hide / Exit | Right-click the widget |
| Bring it back after hiding | Click the tray icon |
| Launch at Windows login | Tick the box in Settings |

## Your data stays local

`settings.json` holds your date of birth, health factors, and death date. It is
listed in `.gitignore` and **is never committed**. `settings.example.json` shows
the file's shape without any personal data.

To move your exact countdown to another computer, copy `settings.json` across by
hand. Cloning the repo alone won't do it — see below.

---

## How the countdown works

The important design rule: **the death date is calculated once and stored.**

1. You press Save in Settings.
2. `life_expectancy.compute_death_datetime()` runs — the only place it ever runs.
3. The result is written to `settings.json` as `death_datetime_iso`.
4. Every launch after that just reads that stored value and subtracts `now`.

This is why closing and reopening the app doesn't reset your countdown. Nothing
recalculates on startup.

### Reproducibility

The calculation interpolates the SSA table at your exact fractional age, so the
same inputs give the same answer regardless of which day you press Save. An
earlier version looked the table up at your whole-number age while measuring age
continuously, which made the result drift ~1 day later per day and then jump
~11 months backwards on each birthday.

A small drift remains by design: having survived another year genuinely raises
your expected total lifespan. Recalculating five years from now moves the date
about 10 days. That's real actuarial signal, not a bug.

---

## Project layout

| File | What it does |
|---|---|
| `run.pyw` | Double-click launcher (no console window) |
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
