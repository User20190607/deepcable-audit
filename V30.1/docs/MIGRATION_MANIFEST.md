# V30.1 Migration Manifest

## Source baseline

| Asset | Source | Treatment |
|---|---|---|
| Deterministic runtime | `archive/V30/beta2/src/v30_cable_engine.py` | Preserve as immutable baseline; port/refactor only with tests |
| Rulebook | `archive/V30/beta2/rulebook/rulebook.json` | Preserve original declarations; validate and migrate explicitly |
| Implementation report | `archive/V30/beta2/V30.0-beta2-implementation-report.md` | Authoritative record of beta2 claims and known gaps |
| Replay audit | `archive/V30/audit/REAL_REPLAY_AUDIT_REPORT.md` | Use as audit input; do not assume every historical output is ground truth |

## Known baseline gaps from beta2 report

- Full V29.1 state machine incomplete.
- Quantity vector incomplete.
- P14 incomplete.
- Full model grammar incomplete.
- Real seven-expert model service incomplete.
- Complete regression corpus incomplete.
- `STRUCT-TWIST-PAIR` has a documented conflict between n×2×S and the earlier two-core notation constraint; scope must be resolved before auto-rewrite.
- `RYJYP` candidate lacks a voltage profile.
- Building-wire voltage profile has an uncovered section interval.
- Six standards are marked STANDARD_VERIFIED in the uploaded rulebook, but beta2 report says source texts/evidence were not supplied for independent verification.

## Gates

### P0-A Rule Registry
- [ ] JSON Schema or equivalent structural validator
- [ ] Stable unique rule IDs
- [ ] Provenance and scope validation
- [ ] Duplicate and contradictory rule detection
- [ ] Dependency closure and missing-dependency detection
- [ ] Rulebook version and content hash

### P0-B Regression Evals
- [ ] Golden cases are evidence-backed and reviewed
- [ ] Regression runner emits machine-readable report
- [ ] Adversarial cases cover near-match models and prefix boundaries
- [ ] Property tests cover Decimal arithmetic and quantity conservation
- [ ] No test is marked passed without execution evidence

### P1 Experience Memory
- [ ] Append-only correction event
- [ ] Candidate status and reviewer decision
- [ ] Rejected candidates retained with rationale
- [ ] Promotion requires linked tests

### P1 Context Router
- [ ] Task classification
- [ ] Dependency-aware rule loading
- [ ] Run trace records loaded rule IDs
- [ ] No missing required rule can silently pass

### P2 Quantity Vector and Aggregation
- [ ] Demand, reviewed, purchased, supplied and remaining quantities separated
- [ ] Unit conversions explicit and Decimal-based
- [ ] Reversible source-row lineage
- [ ] Color and packaging constraints checked independently

### P3 Release
- [ ] Release Gate covers all required invariants
- [ ] CI executes full regression suite
- [ ] Release report records commit, runtime, rulebook hash and test result

## Current execution status

Only the V30.1 branch and planning documents are established at this point. No P0 implementation or test execution is claimed by this manifest.
