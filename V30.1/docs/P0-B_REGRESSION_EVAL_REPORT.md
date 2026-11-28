# P0-B Regression Evals — Initial Execution Report

**Branch:** `v30.1`  
**Baseline:** frozen copy of `archive/V30/beta2/src/v30_cable_engine.py`  
**Source SHA:** `fb2ee5d157a21ffab57537ddb9bf9d66deeac8ad`  
**Evaluation commit:** `a714295148ff951041027cccea5d2201daf31ca8`  
**CI run:** [46123397880](https://github.com/User20190607/deepcable-audit/actions/runs/46123397880)

## What was implemented

1. Vendored the beta2 engine as an immutable compatibility snapshot under `v30core/compat/`; no production runtime code was changed.
2. Added a JSONL manifest of ten named audit cases with input, expected baseline observation and evidence basis.
3. Added fifteen executable characterization/regression tests covering parser prefix recognition, patch revalidation, unit conversion, voltage defaults, material conflicts, authorization, scope isolation, Decimal aggregation and TSV-5.
4. Extended GitHub Actions to run both the rule registry tests and beta2 baseline regression evaluations.

## Execution result

- Python compilation: passed.
- Rule registry unit tests: passed.
- Beta2 baseline regression tests: passed.
- GitHub Actions workflow: **success**.

The regression tests are deliberately written as characterization tests: for known defects, a passing test means the frozen baseline reproduces the documented unsafe behaviour. It does **not** mean the behaviour is accepted for V30.1. The case IDs and defect observations remain visible in the test names and JSONL manifest.

## Defects reproduced / characterized

| Case | Area | Baseline behaviour |
|---|---|---|
| B2-ADV-001 | Prefix parser | Concatenated prefix not recognized; row held |
| B2-ADV-002 | Patch | Model can change while AST/findings/status remain stale |
| B2-ADV-003 | Quantity ledger | Caller-supplied incorrect pack factor is accepted; gate validates only post-conversion conservation |
| B2-ADV-004 | Voltage | Missing power-cable voltage can be silently defaulted to 0.6/1kV |
| B2-ADV-005 | Material conflict | WD/PVC conflict correctly produces HOLD |
| B2-ADV-006 | Integer metres | Fractional metres have no dedicated integer-metre validation |
| B2-ADV-007 | Unit aliases | `米` is not normalized to `m` |
| B2-ADV-008 | Hundred-metre unit | `百米` is not converted to metres |
| B2-ADV-009 | Roll packaging | `卷` without explicit pack length remains a roll |
| B2-ADV-010 | Mapping authorization | Mapping without authorization reference is ignored |

Additional executable controls cover authorized mapping audit, batch-scope isolation, five-column TSV-5, exact Decimal aggregation and RVS 2-core/300/300V parsing.

## Important test classification

- **Characterization tests:** prove what the archived beta2 snapshot currently does.
- **Safety controls:** assert existing safeguards such as WD/PVC HOLD and authorization requirement.
- **Golden correctness tests:** not yet complete. They require user-adjudicated input/output pairs and evidence, not merely historical assistant outputs.

## Remaining P0-B work

1. Obtain and adjudicate the underlying source rows for the September and October historical replay batches; the audit report provides batch-level summaries, not the complete source data files in this repository.
2. Pair historical assistant outputs with later user confirmations/corrections before admitting any expected output as a golden oracle.
3. Add property-based tests for quantity conservation, packaging, colour allocation, model-prefix boundaries and reversible aggregation.
4. Add adversarial near-miss model grammar cases and explicit expected HOLD/BLOCK decisions.
5. Add a V30.1 candidate implementation suite where each known defect is expected to be fixed; keep the frozen beta2 tests as baseline characterization.

## Release assessment

**P0-B is partially implemented, not complete.** The baseline is now reproducibly characterized in CI, but no claim is made that the V30.1 candidate fixes these defects or that the complete historical corpus has been replayed. V30.1 remains non-production.
