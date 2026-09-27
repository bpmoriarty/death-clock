# Manual acceptance record

Checked September 26–27, 2026 on the current Windows desktop. These are real
UI checks, separate from the previously passing 252 automated tests.

## Isolated local checks — passed

Used `tools/manual_acceptance.py` with fictional profiles in temporary folders.
The harness disables login registration and the tray and does not acquire the
production instance lock. It cannot establish acceptance of those features.

- First-run date form and confirmation preview displayed correctly. The saved
  fictional target was `2080-06-15T00:00:00`, also shown by the test clock.
- Export through the native Save dialog produced a profile-only JSON file.
- A fresh isolated instance opened that export through the native Open dialog.
  The restore preview showed the exact target. Choosing No left no saved target;
  choosing Yes restored it and displayed the correct countdown date.
- Reopening Settings defaulted to Keep saved target with the exact ISO value.
- Choosing age 81 with fictional birth date `2000-02-29` previewed
  `2081-02-28T00:00:00`. Choosing No preserved the existing target.
- The legacy explanation and all factor controls were readable by scrolling;
  Save, Cancel, export, and restore stayed visible outside the scrolling area.
- Cancel discarded the edited birth date and target selection. Inspection of
  the saved JSON confirmed all profile fields matched the exported profile,
  including the empty birth date and exact original target.
- The isolated test process exited normally after the checks.

The user's live countdown, startup registration, and live preferences were not
changed. No application fixes were needed from this local pass. The README was
left unchanged during testing, then updated after the owner's approval.
Temporary fictional files are retained for inspection.

## Earlier user acceptance

The user confirmed VBS launch, reopening after storage changes, and working
display options. These confirmations are not evidence for Windows login startup
or physical monitor changes.

## Deferred by the owner — September 27, 2026

The user confirmed on September 26 that login startup, a second-computer restore,
and physical monitor/scaling checks had not been performed. On September 27 the
owner explicitly deferred the remaining checks and authorized the README update.
They are retired from the current plan's completion requirements so documentation
can be finished. They remain untested, not passed, and can be revisited later.

| Check | Expected result |
| --- | --- |
| Windows sign-in with startup enabled | One clock opens with the same exact saved target. |
| Export/restore on the second computer | Preview and restored target match; that computer keeps its own display/placement preferences. |
| Monitor unplug/replug and Windows scaling changes | Clock remains reachable and readable; Reset position recovers it. Requires suitable hardware. |
| Real tray Hide/Show/Reset and desktop-shortcut click | Menus operate correctly; shortcut reveals the existing instance without a duplicate. |

Existing automated/simulated checks cover these underlying behaviors, but do not
replace the real-environment checks. Restore over an existing target and its
backup, error dialogs, and legacy calculation validation remain covered by the
automated suite rather than a complete manual traversal in this pass.

The final README update is complete and the improvement plan is closed. Retain
this record for the deferred checks; closing the plan does not certify them.
