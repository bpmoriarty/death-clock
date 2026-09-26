# Death Clock improvement plan

Purpose: a personal reminder to use time well, not a medical prediction or a
product for wider distribution. Used on several computers, currently with one
monitor per setup. Multiple-monitor support is future-proofing.

## Working rules

- Preserve the existing saved target exactly. Never recalculate at startup,
  during migration, after recovery, or just because preferences changed.
- Work in the numbered order below. Update this checklist and PROJECT_STATUS.md
  after each verified increment; distinguish automated checks from manual checks.
- Use fictional profiles and temporary settings in tests. Do not modify the live
  profile, restart the running clock, or replace its environment during testing.
- Keep the application small and local. Account for OneDrive synchronization.
- When every item has been completed or explicitly retired with a reason, move
  the final outcome into PROJECT_STATUS.md and delete this plan.

## 1. Protect the saved countdown — implemented, automated checks passed

- [x] Validate settings types and nested fields; retain a usable target even if
  unrelated preferences or profile fields need repair.
- [x] Keep a last-known-good backup and preserve damaged originals without
  overwriting earlier recovery copies. Explain recovery to the user.
- [x] Save proposed settings successfully before changing the running state;
  show errors and allow retry. Never destroy readable data on a read failure.
- [x] Handle position-save failures and allow exit even when disk writes fail.
- [x] Confirm an explicitly changed target; keep preference-only saves exact.
- [x] Prevent repeat successful saves from creating duplicate first-run widgets.
- [x] Test malformed data, backup recovery, failed writes, unchanged targets,
  repeated saves, and shutdown errors. Verify live settings remain untouched.

Verification: 96 tests passed using Python 3.12.14 and the existing project
packages. UI handlers and form construction were tested with stand-in controls;
real dialogs, tray behavior, and reboot remain manual checks for the next normal
restart. The running app was left alone and settings.json is byte-for-byte unchanged.

## 2. Remember and recover window placement — implemented, automated checks passed

- [x] Use actual monitor work areas, including negative coordinates, rather than
  assuming a single screen with its origin at zero.
- [x] Preserve reachable positions; recover when a monitor disappears.
- [x] Add Reset position to the tray menu.
- [x] Check small screens, Windows scaling, font fitting, and resize limits.
- [x] Test geometry with synthetic monitor layouts; record manual verification.

Verification: 136 regression tests passed (40 new placement checks), plus 12
invisible real-Tk layout checks across four sizes and three Tk scaling values.
Native Windows work-area enumeration and negative geometry were checked on the
current single-monitor desktop. Physical monitor unplug/replug, mixed Windows DPI,
and clicking the real tray menu remain manual checks on a suitable setup.

## 3. Prevent duplicate clocks and improve launching — implemented, automated checks passed

- [x] Allow only one instance per Windows user; another launch reveals the
  existing clock, including when hidden.
- [x] Make the launcher use the intended Python interpreter rather than mixing
  an arbitrary interpreter with another environment's packages.
- [x] Show actionable launch errors and keep a small local diagnostic log without
  profile data. Investigate the review environment's missing interpreter without
  assuming the user's working setup is broken.
- [x] Verify double-click, login startup, paths containing spaces, and shutdown.
- [x] Provide a reliable shortcut/setup path without rebuilding a live environment.

Verification: 160 tests passed, including 24 new launch checks. Real Windows
processes verified repeat launches, simultaneous ownership races, and recovery
from a crashed owner using unique test-only names. Windows scripts compiled;
a real shortcut was created and inspected in a temporary fake desktop, and the
missing-runtime route was tested with dialogs redirected to captured output.
An independent process also revealed an invisible isolated test widget.

The actual project Python 3.12.10 and UI imports work outside the sandbox; the
earlier interpreter issue was access restriction, not a broken installation.
No dependencies were synchronized. The user confirmed that the VBS launcher
opens the clock successfully. Desktop-shortcut click and Windows login remain
manual acceptance checks. No real desktop
shortcut or login registration was changed. Exit the old running clock once
before switching to the new launcher; legacy processes do not hold the lock.

## 4. Separate shared information from device preferences — implemented, automated checks passed

- [x] Keep the target/profile portable; store placement, opacity, and login startup
  separately per computer, outside the shared project settings.
- [x] Migrate existing settings without recalculation and with recovery copies.
- [x] Read actual login registration and report registration failures honestly.
- [x] Add export/restore with validation, target preview, and backup before restore.
- [x] Document OneDrive synchronization, conflicts, and what is local vs shared.
- [x] Verify migration, portability, and preference-only saves across two simulated
  devices; do not promise automatic conflict-free synchronization.

Verification: 191 tests passed, including 31 new storage/restore checks. Legacy
settings stay intact during loading; local preferences are seeded once and backed
up. Old shared device fields are inert until an explicit profile save/restore
removes them. Windows holds the actual login setting. Local-only writes never
rewrite the shared target. Shared-change detection is best-effort protection,
not a distributed lock or a promise of conflict-free OneDrive synchronization.
An invisible real Settings form fit the current display. Manual checks remain
for file dialogs and actual use on a second computer.

User acceptance: exited and reopened after priority 4; reports that it looks good.

## 5. Add modest display controls — implemented, automated checks passed

- [x] Add lock position, adjustable opacity, optional seconds, and total days/weeks.
- [x] Improve small-label contrast while retaining the gray-and-green design.
- [x] Extract and test countdown formatting, including zero/past targets.
- [x] Use a clear calendar-aware years/days convention when displaying years.
- [x] Define a suitable message after the target passes; keep the target intact.
- [x] Ensure Hide remains hidden and topmost refresh does not disrupt Settings.

Verification: 226 tests passed, including 35 new display checks. An invisible
Display window measured 304 × 354 and 48 native-font layouts passed across four
sizes, all formats, optional seconds, and future/past targets. Display changes
save only local preferences and apply after successful saving. Defaults remain
unlocked, 93% opacity, years/days, and seconds shown. Whole calendar years replace
365-day blocks; February 29 anniversaries use February 28 in non-leap years.
At/past the target, show “Make today count” and retain the target date. Locking
blocks manual movement/resizing; monitor recovery and Reset position still work.
Actual use of the new controls remains a manual acceptance check. The remaining
review suggestions below keep this plan open after the five priorities.

## Remaining review suggestions

### Settings and target selection

- [x] Rename Save to match its actual behavior; reuse one Settings window.
- [x] Add Cancel and a scrollable layout suitable for larger text/small screens.
- [x] Offer a deliberately chosen target age/date as the natural reminder mode.
- [x] Keep the legacy calculated target usable. Make any new calculation optional,
  previewed, and explicit; describe the existing lifestyle formula as approximate.
- [ ] If retaining the SSA option, verify every row against a fixed official source,
  record source/model/calculation date, and test source fidelity.
- [x] Resolve current/former smoking overlap in the legacy form. Do not add more
  health factors or claim medical accuracy. A validated longevity model is outside
  this personal-reminder project's scope.

### Code, tests, and documentation

- [x] Replace callable annotations with Callable; remove unused imports/helpers.
- [x] Consolidate factor labels, defaults, grouping, and adjustments.
- [x] Inject the calculation date for deterministic tests; correct weak assertions
  (including the test that checks a future result only against birth).
- [x] Remove inaccurate reproducibility claims and repetitive historical comments.
- [x] Replace personal dates and health references in tracked tests/docs with
  fictional examples. Do not rewrite Git history without a separate decision.
- [x] Clarify privacy wording: Git exclusion does not prevent OneDrive syncing.
- [x] Keep PROJECT_STATUS.md concise and current; retain useful history in Git.
- [x] Remove empty/redundant agent-note files only if no longer useful; place lasting
  project invariants in AGENTS.md rather than duplicating them across agent files.

Latest verification: 238 tests passed after replacing time-dependent legacy tests
with deterministic checks and adding 14 target-selection checks. Every target
choice is previewed, including first setup; Keep saved target requires no valid
birth date. Manual targets export/restore with an empty birth date. Invisible
Settings forms built all modes at normal and 150% widget scaling. The user
confirmed the display options work. New Settings interactions remain a manual
acceptance check. Source verification of the legacy table remains open; no table
values or multipliers were changed, and the UI/docs explicitly call them unverified.

## Deliberately not planned

- An exit-confirmation dialog: reliable persistence and easy reopening are better
  for this small personal utility.
- A framework rewrite, accounts, cloud service, or wider-distribution packaging.
- Automatically changing the saved target when data or calculation code changes.

## Completion

Work is paused at the user's request. Keep this plan for the remaining work.

- [ ] All accepted items verified; unresolved manual checks stated clearly.
- [ ] Update README.md for GitHub after the plan's implementation work is finished.
- [ ] PROJECT_STATUS.md records the final behavior and maintenance instructions.
- [ ] Delete this document only after the above work is complete.
