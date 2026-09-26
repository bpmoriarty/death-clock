# Death Clock — project status

## Purpose and current use

A personal reminder to use time well, not a longevity prediction or a product for
wider distribution. Used successfully on several computers, currently with one
monitor per setup. Multiple-monitor support is future-proofing.

## Active work

The complete checklist is in [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md). Keep it
updated as work progresses. Delete it only after all accepted work is complete
and its final outcome is recorded here.

1. **Protect the saved countdown:** implemented; automated checks passed.
2. **Window placement and monitor recovery:** implemented; automated checks passed.
3. **Single instance and reliable launching:** implemented; automated checks passed.
4. **Shared target vs device preferences:** next.
5. **Modest display controls:** planned.

Work is paused at the user's request. Resume with priority 4 when requested.

Additional settings, target-selection, source-data, privacy, and code-cleanup
items are tracked in the plan. No automatic recalculation or medical-model
expansion is planned.

## Latest increment — single instance and reliable launching

- Acquire a Windows user-scoped mutex before importing the UI or reading settings.
  Repeat launches signal the owner and exit; requests queue during startup. A
  crashed owner does not leave a stale lock. Separate project copies share the lock.
- Reveal hidden clocks and reuse/raise the existing Settings window, including
  first-run Settings. Poll reveal requests on the Tk thread.
- Replace package-path injection with an explicit project-interpreter probe and
  pythonw launch. No automatic dependency installation or environment rebuilding.
- Provide Start Death Clock.vbs and Create Desktop Shortcut.vbs; route future login
  registration through the same checked Windows bootstrap. Paths with spaces work.
- Report launch, UI callback, and tray-thread failures. Keep bounded logs under
  LOCALAPPDATA/DeathClock/logs without profile values or exception messages.
- Close the tray and root window before releasing the instance lock.

Adoption: exit the currently running pre-lock version once, then use the new
launcher. If login startup is enabled, Save in the updated Settings once to
refresh its registry entry (preference-only saves retain the target). No actual
shortcut or registry entry was changed during implementation.

## Completed — window placement and monitor recovery

- Query each Windows monitor's usable work area, including negative coordinates
  and taskbar reservations. Preserve reachable positions, including slightly
  off-screen placements, rather than forcing everything onto the primary screen.
- Recover missing-monitor/off-screen positions and constrain oversized windows to
  the available work area. Desktop gaps do not count as reachable space.
- Check for layout changes every five seconds; defer recovery during drag/resize.
  Recovery does not reveal a hidden clock. A temporary monitor-query failure
  retains the last known layout instead of moving the clock unnecessarily.
- Add **Reset position** to the tray menu: center on the primary monitor, reveal
  the widget, and save its placement without changing the target.
- Constrain resize grip movement to the current work area; normal minimum size is
  280 by 90, reduced only when the available work area itself is smaller.
- Fit all three text rows using real font measurements and pixel-sized fonts,
  refreshing after resizing and display updates. Account for the resize grip.
- Move monitor discovery and geometry rules into death_clock/placement.py.

## Previous increment — countdown protection

- Validate nested settings and repair invalid preferences without discarding a
  usable target. A target can run even if the birth-date field is damaged.
- Create settings.json.bak on the first target save; later saves back up the
  previous usable countdown. This is a rolling backup, not permanent history.
- Recover from the backup if the primary target is missing or unusable. Warn the
  user; never recalculate during recovery or rewrite the primary during loading.
- Preserve damaged originals in unique .corrupt copies. Stop saves if an
  unreadable original or failed backup cannot safely be preserved.
- Use unique temporary files for atomic writes and remove them after failures.
- Save proposed settings before changing the live state. Show write errors and
  allow retry; failed saves do not change the running target.
- Preserve the exact stored target string on preference-only saves. Ask before
  replacing an existing target and disable Save after success.
- Show startup-registration failures separately from successful countdown saves.
- Report window-save failures and still allow exit. Closing first-run Settings
  without saving does not write empty defaults.
- Ignore backup, recovery, and temporary files in Git.

## Verification

**160 tests passed** using the project's own Python 3.12.10. This includes the
previous 136 checks plus 24 launch checks covering native duplicate processes,
simultaneous startup, abandoned locks, exact interpreter selection, error logs,
startup quoting, cleanup, Windows-script compilation, and real shortcut creation
in a temporary fake desktop. All settings tests use isolated fictional profiles.

An independent process successfully revealed an invisible real-Tk test clock
using a unique test-only lock name and an in-memory profile. Earlier placement
work also passed 12 invisible real-Tk checks across four sizes and three Tk
scaling values, plus actual Windows work-area enumeration.

The project interpreter and UI imports work outside the sandbox. The earlier
failure came from review-session access restrictions, not a broken environment.
No repair or dependency synchronization was needed or performed.

The user confirmed that the VBS launcher opens the clock successfully.
Remaining manual acceptance: clicking the real desktop shortcut/tray, Windows
login, physical monitor unplug/replug, and mixed Windows
DPI. The real clock was not restarted or signaled by the tests. No tool wrote the
live settings. Its file hash changed while the live application was in use; the
current file and rolling backup differ only in window placement and have the
same saved target. We did not restore or overwrite that live change.

## Lasting rules

- The stored target is authoritative. Never recalculate on launch, recovery,
  migration, or preference-only save.
- Do not edit the live profile or restart the running app just to run tests.
- Test with fictional profiles and temporary files; never use actual health data.
- Never synchronize dependencies while the widget is running.
- Runtime data is excluded from Git, but files inside OneDrive may still sync.
- Keep this status concise. Previous implementation history remains in Git.
