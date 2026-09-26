# Death Clock working rules

- Treat the exact stored target as authoritative. Never recalculate on launch,
  migration, recovery, or preference-only saves.
- Use fictional profiles and temporary paths for tests. Do not edit live shared
  settings, local preferences, startup registration, or the running app for tests.
- Never synchronize dependencies while the clock is running.
- Display preferences belong in local application data; export only the profile.
- Keep PROJECT_STATUS.md and IMPROVEMENT_PLAN.md current. Retain the plan until
  all accepted work is completed or explicitly retired.
- Preserve existing user changes. Do not rewrite Git history for privacy cleanup.
