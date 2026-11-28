# Regression Corpus

This directory will contain reviewed, executable golden cases.

## Admission requirements

Each case must include:

- stable case ID
- raw input and expected normalized output
- expected status/findings
- provenance and evidence reference
- scope (global, project-bound or batch)
- review status

Historical assistant output is not automatically ground truth. Prefer explicit user corrections, user-confirmed rules, source documents and independently verified standards. Ambiguous cases must remain pending and must not be used as automatic-correction tests.

## Initial candidate themes

- WD/PVC material conflict and exact authorized mapping
- WDZBN versus WDZCN prefix isolation
- RV voltage profiles and section boundaries
- RVS/RYJS pair notation boundaries
- BYJ 100 m packaging and color allocation
- single-core wire versus multi-core cable parsing
- batch isolation and explicit merge behavior
- Decimal conversion and aggregation conservation
- TSV-5 five-column output
- project mapping activation authorization

These are themes only; no expected result is asserted until each case is reviewed.
