# Death Clock — project status

## Purpose

A personal reminder to use time well, not a longevity prediction or a product
for wider distribution. Used on multiple computers, currently one monitor each.

## Current behavior

All five original priorities are implemented and tested:

1. **Countdown protection:** validation, atomic writes, rolling backups, recovery
   copies, and saving before changing the live target.
2. **Placement:** monitor work areas, off-screen recovery, Reset position, resize
   limits, and measured font fitting.
3. **Launching:** checked VBS launcher, optional desktop shortcut, per-user single
   instance, reveal requests, and bounded local diagnostic logs.
4. **Portable target:** shared profile in settings.json; device preferences in
   LOCALAPPDATA/DeathClock/preferences.json. Local-only saves never rewrite the
   target. Export/restore previews and backs up the target. Windows supplies the
   login setting. Detected stale shared-file writes are rejected.
5. **Display:** lock position/size, opacity, optional seconds, calendar years/days,
   total days or weeks/days. Defaults stay familiar. After the target passes,
   show “Make today count” and retain the date. Modal dialogs stay in front.

## Latest increment — verified SSA base table

- Pin the SSA 2021 period table as used in the 2024 Trustees Report, using its
  fixed year/report URL. Retain extracted HTML, the runtime CSV, hashes, and a
  complete audit in docs/sources/SSA_VERIFICATION.md.
- Correct 238 of 240 embedded values (119 per sex); all ages 0–119 now match
  the retained official source. No lifestyle multipliers or formula rules changed.
- Newly confirmed legacy calculations record source URL, table ID/hash, model
  version, local calculation time, and exact target. Export/restore carries these
  details, validates their shape and target binding, and clears stale attribution
  when restoring an older file or choosing a manual target.
- Existing targets stay exact and receive no invented calculation history.
  Source verification does not validate the lifestyle-adjusted formula.

## Completed — target selection and cleanup

- Existing countdowns open with Keep saved target, preserving the exact ISO value
  even with a missing/damaged birth date.
- First setup defaults to choosing a date. Date targets need no health profile.
  Age targets use midnight on the chosen birthday, with February 29 clamped to
  February 28 in non-leap years. Every new choice is previewed before saving;
  past targets are identified explicitly.
- Legacy calculation is optional and explicitly described as unvalidated. A
  fresh calculation requires confirmation; current/former smoker cannot both be
  selected. Existing targets remain usable without correcting their old inputs.
- Settings has a resizable, scrollable input area and persistent Save/Cancel
  controls. Cancel writes nothing. Restore remains available on first setup.
- Centralize factor labels/defaults/groups/multipliers; inject calculation time.
  Replace time-dependent tests and personal examples with fictional fixed cases.
  Remove inaccurate reproducibility claims and the empty claude.md placeholder;
  put lasting working rules in AGENTS.md.

## Verification and acceptance

**252 tests passed** with the project's Python 3.12.10. The 14 new source/provenance
checks compare all 240 runtime values to independently parsed SSA HTML, pin both
source/data hashes, and cover metadata saving, export/restore, invalid imports,
failed writes, and unchanged existing targets. Earlier checks include target date
and age boundaries, preview acceptance/decline, damaged-profile preservation,
first-run setup/export, and deterministic legacy calculation checks.
All settings tests use temporary paths and fictional profiles.

Invisible Settings forms built every selection mode at normal and 150% widget
scaling. Earlier verification included 48 native display-font layouts, monitor
geometry checks, native single-instance processes, and isolated VBS/shortcut checks.
The user confirmed successful reopening after storage changes and working display
options. The September 26–27 isolated manual pass verified date setup, native
export/restore dialogs, restore acceptance/decline, Keep saved target, a leap-day
age preview, target-change decline, Cancel persistence, and legacy-form scrolling.
The test copy exited normally. See docs/MANUAL_ACCEPTANCE.md for evidence and
limits. Actual cross-computer restore, login startup, physical monitor/DPI
changes, and real tray/desktop-shortcut interactions remain untested manually.
On September 27, 2026 the owner explicitly deferred these environment-specific
checks and authorized the README update. They are retired from this improvement
plan's completion requirements, not recorded as passed; the acceptance record
retains the steps for a future suitable session.

Implementation/tests did not change the live profile, local preferences, running
clock, registry, or dependencies. Activate UI changes on a normal exit/relaunch.

## Improvement plan completed — September 27, 2026

All five priorities, target selection, code/test cleanup, and SSA source
verification are implemented. Local manual acceptance is recorded; outstanding
environment checks were explicitly deferred by the owner. The final GitHub README
now covers setup, daily use, target protection, device preferences, portability,
verified source data and its limits, and maintenance commands. The completed
IMPROVEMENT_PLAN.md was deleted as requested. Its history remains in Git.

No further implementation work is scheduled. The deferred checks remain useful
future follow-ups in docs/MANUAL_ACCEPTANCE.md. The lifecycle of this plan is
complete without claiming those checks passed or the legacy formula is validated.

## Maintenance

On October 14, 2026, added the MIT License in LICENSE and linked it from the
README. Copyright is attributed to Brian, matching the repository's Git author
configuration. No application behavior changed.

Use the existing environment to run the regression suite and offline source
verification (commands in README.md). Follow AGENTS.md: use fictional temporary
profiles, preserve exact saved targets, and never synchronize dependencies while
the clock runs. For table changes, retain a fixed source and update all rows,
hashes, and model/table IDs together; see docs/sources/SSA_VERIFICATION.md.

OneDrive is not conflict-free storage. Change the shared profile on one computer
at a time; shared-change checks cannot prevent every simultaneous remote write.
The running clock retains its loaded target until reopened or explicitly restored.
Old legacy device fields stay inert until an explicit profile save/restore removes
them after backup. Local preferences may save before a later shared save fails,
but the running target stays unchanged on that failure.

Runtime settings and default export names are ignored by Git; renamed exports may
not be. OneDrive may still sync those private files. Historical Git content was
not rewritten.
