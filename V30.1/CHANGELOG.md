# V30.1.0 Candidate Changelog

## Added
- Correction registry and correction governance lifecycle.
- Independent source-to-processed-to-aggregate quantity reconciliation.
- Patch revalidation.
- Explicit package-length conversion requirement.
- Production-loss remark-only behavior.
- Fail-closed N/PE/PEN validator with reviewed evidence profiles.
- Compact prefix parsing and armor suffix preservation.
- Explicit sort mode and TSV-5 rendering.

## Fixed / guarded
- No silent fractional-metre rounding.
- No blind low-voltage default for power cables missing voltage.
- No implicit YJY22/YJY23 conversion.
- No guessed PCS/roll/bale length.

## Known limitations
- September historical replay is pending.
- Full V28.5/V29.1 mapping parity is pending.
- N/PE/PEN numeric profiles remain intentionally empty until standards review.
- This is a candidate branch, not a production release.
