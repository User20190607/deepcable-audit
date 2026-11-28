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
- [x] Canonical structural validator in `v30core/rules/registry.py`
- [x] Stable unique rule IDs
- [x] Provenance and scope validation
- [x] Duplicate-ID detection and conservative exact-condition conflict detection
- [x] Dependency closure, missing-dependency detection and cycle detection
- [x] Rulebook version and deterministic SHA-256 content hash
- [x] Dependency-aware loading of active rules
- [x] GitHub Actions compile + unit-test workflow
- [ ] Legacy beta2 rulebook migration and reviewed rule-by-rule import
- [ ] Semantic conflict review beyond exact structural matches

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

- V30.1 branch created from `main`; main remains unchanged.
- P0-A registry implementation committed under `V30.1/v30core/rules/`.
- Nine registry unit tests are defined.
- GitHub Actions run #1 completed successfully for Python compilation and registry unit tests.
- The beta2 rulebook has **not** yet been migrated into the canonical registry. Its legacy sections remain archived and authoritative until individually reviewed.
- P0-B regression corpus is not complete. The current unit tests validate registry mechanics, not cable-domain correctness.
- No production-ready claim is made.
