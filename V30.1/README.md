# V30.1.0 — Cable Standardization Engine

**Status: candidate implementation / not production-certified.**

V30.1 is an additive hardening layer over the archived V30.0-beta2 baseline. It implements selected invariants and fail-closed behavior; it does not claim every historical mapping or every national-standard electrical calculation is complete.

## Implemented
- Compact/hyphenated prefix parsing.
- Missing power-cable voltage => HOLD; explicit medium voltage preserved.
- Armor 22/23 preserved; no implicit rewrite.
- Decimal quantities; fractional metres => HOLD, no silent rounding.
- PCS/roll/bale conversion requires explicit pack_length_m.
- Production loss is remark-only.
- Explicit source/model sorting; aggregation retains source row IDs.
- Patch reruns parsing and validation.
- Release Gate independently recomputes quantities from raw input.
- N/PE/PEN checks fail closed; compound-section power cable requires explicit conductor-role mapping and approved standards evidence.
- Correction registry maps recurring corrections to code/tests.

## Run
python -m unittest discover -s tests -v
python src/v30_1_engine.py --input tests/sample_input.json --output out.tsv --audit audit.json

Python 3.10+; standard library only.

## Safety boundary
The N/PE/PEN standards profile registry is intentionally empty until each rule has an authoritative current standard, exact clause, material and installation conditions reviewed and approved. No numeric compliance result may PASS without this evidence.

## Remaining acceptance work
- Full V28.5/V29.1 mapping migration and parity tests.
- Full September historical replay workbench.
- Additional adversarial/property tests.
- Review of complete product/package catalogue.
- Independent review and approval of all N/PE/PEN standard profiles.

Do not promote to production solely because unit tests pass. Historical replay and full acceptance are mandatory.
