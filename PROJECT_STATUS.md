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

## Latest increment — target selection and cleanup

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

**238 tests passed** with the project's Python 3.12.10. This includes target date
and age boundaries, preview acceptance/decline, damaged-profile preservation,
first-run setup/export, and deterministic legacy calculation checks. The count
decreased from an intermediate 240 when redundant legacy tests were replaced.
All settings tests use temporary paths and fictional profiles.

Invisible Settings forms built every selection mode at normal and 150% widget
scaling. Earlier verification included 48 native display-font layouts, monitor
geometry checks, native single-instance processes, and isolated VBS/shortcut checks.
The user confirmed successful reopening after storage changes and working display
options. Manual acceptance remains for new target-selection interactions, actual
cross-computer restore, login startup, and physical monitor/DPI changes.

Implementation/tests did not change the live profile, local preferences, running
clock, registry, or dependencies. Activate UI changes on a normal exit/relaunch.

## Remaining work

Work is paused at the user's request. Resume with the open plan items when asked.
After the plan is finished, give README.md a final update for GitHub covering the
finished behavior, setup, and usage. Existing incremental README edits are not
that final pass. Record completion here before deleting IMPROVEMENT_PLAN.md.

Keep IMPROVEMENT_PLAN.md until the open work is completed or explicitly retired.
The embedded legacy table still needs verification against a fixed official
source; model/source provenance is unverified and labeled accordingly. No table
values or multipliers were changed. This work does not claim medical accuracy.

OneDrive is not conflict-free storage. Change the shared profile on one computer
at a time; shared-change checks cannot prevent every simultaneous remote write.
The running clock retains its loaded target until reopened or explicitly restored.
Old legacy device fields stay inert until an explicit profile save/restore removes
them after backup. Local preferences may save before a later shared save fails,
but the running target stays unchanged on that failure.

Runtime settings and default export names are ignored by Git; renamed exports may
not be. OneDrive may still sync those private files. Historical Git content was
not rewritten.
