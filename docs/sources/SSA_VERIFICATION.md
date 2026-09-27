# SSA table verification

Verified on 2026-09-26 against the fixed [SSA Period Life Table, 2021, as used
in the 2024 Trustees Report](https://www.ssa.gov/oact/STATS/table4c6_2021_TR2024.html).
This is the Social Security area population period table, not a cohort forecast
or an individual prediction. Use the year/report-specific URL; the original
generic table4c6.html link changes to newer editions over time.

## Evidence retained

- `ssa_2021_tr2024.html`: main-content HTML returned by the Firecrawl connector,
  retained without editing. This is extracted HTML, not a byte-for-byte raw HTTP
  response. The service returned status 200 and a cache timestamp of
  `2026-09-26T03:46:59.082Z`; its source URL was the fixed link above.
- `../../death_clock/data/ssa_2021_tr2024.csv`: exact age, male remaining years,
  and female remaining years, preserving the source's two-decimal precision.
  Extracted from the returned Markdown table; independently checked against the
  retained HTML cells at columns 0, 3, and 6.
- `legacy_table_audit.csv`: every mismatch with the prior embedded dictionaries
  in commit `da33526`. Difference is official minus previous remaining years.

All 120 ages (0–119) and both sexes were compared: **238 of 240 values differed**,
119 for each sex. The unchanged values were male age 111 and female age 84.
The largest absolute difference was male age 66: 14.94 became 16.29 years,
a difference of 1.35 years. For another example, male age 65 was 15.61 and is
16.95; female age 65 was 19.25 and is 19.75. No cause for the old discrepancies
has been established; the old values must not be described as accurate SSA 2021.

SHA-256 pins (LF line endings, enforced by .gitattributes):

- HTML: `54a7ba64bba1d36c0c8269784c4f4392dbc2de010da2c8ff944e8e08acfe5f73`
- CSV: `9de6f7c4c116c956f5d12b1712405b148350d612ee8f7a320589814e79da81bd`

## Runtime behavior and attribution

Only an explicitly selected, previewed, and confirmed **Legacy calculation**
uses the corrected values to create a new target. Launching, keeping a target,
loading backups, changing preferences, and moving the clock do not calculate.
Existing targets keep their exact saved value and receive no invented source
history. No live settings were read or written for this audit.

New calculations record `target_provenance`, with schema version 1, method,
model version `legacy-ratio-v2-ssa2021tr2024`, table ID `ssa-period-2021-tr2024`,
fixed source URL, CSV hash, calculation time from the application's local clock,
and exact target ISO string. Details are persisted only when saving succeeds.
They travel with exports/restores and are checked for shape and target binding;
imported metadata is an attribution claim, not cryptographic proof of origin.
Manual date/age choices clear old calculation attribution. Restoring an older
file without attribution also clears the destination's previous attribution.

Model v2 keeps the existing application formula and factor values: age is elapsed
whole days / 365.25; remaining years are linearly interpolated between exact-age
rows with age clamped to 0–119; selected factor multipliers are multiplied; adjusted
remaining years have a 0.01-year floor. The target is birth date plus
(fractional age + adjusted remaining years) × 365.25 days. The v2 change is the
corrected base table and explicit provenance, not validation of that formula.

The factor multipliers and their combination remain unvalidated and are not SSA
adjustments. Source fidelity does not establish personal predictive accuracy.

## Rechecking and maintenance

From the project root, run `python -B tools/verify_ssa_source.py` for the offline
comparison. The regression suite also compares all runtime values to the parsed
HTML and verifies both hashes. Neither check contacts the internet or accesses
profiles. There is no network fetch at application launch.

For a deliberate future table update, retrieve an explicit year/report source,
retain the evidence, compare all rows, update hashes and model/table IDs, and run
the tests. Never rewrite or recalculate existing targets as part of such an update.
