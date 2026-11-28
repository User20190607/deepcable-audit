# V30.1 Upgrade Workspace

V30.1 is an incremental upgrade built on the archived V30.0-beta2 implementation.

## Baseline

- Runtime source: `archive/V30/beta2/src/v30_cable_engine.py`
- Rulebook source: `archive/V30/beta2/rulebook/rulebook.json`
- Implementation report: `archive/V30/beta2/V30.0-beta2-implementation-report.md`
- Baseline status: runnable beta prototype; **not production-ready**.

The archived baseline remains immutable during V30.1 work. New implementation must be made under this directory and promoted only after tests pass.

## Upgrade sequence

1. P0 — Rule Registry: schema, stable IDs, provenance, scope, status, versioning, dependency and conflict checks.
2. P0 — Regression Evals: golden cases, regression runner, adversarial and invariant tests.
3. P1 — Experience Memory: correction capture, review states, promotion workflow.
4. P1 — Context Router: dependency-aware rule loading and run trace.
5. P2 — Quantity Vector and reversible aggregation.
6. P3 — Expert routing and release hardening.

## Non-negotiable invariants

- Decimal-only arithmetic for quantities and money.
- LLM output is not a source of deterministic calculations.
- User instructions, verified standards, project mappings and provisional experience remain distinct provenance classes.
- Project mappings require explicit project/batch scope and authorization.
- Batches remain isolated unless explicitly merged.
- Every transformation remains traceable to source rows.
- HOLD/BLOCK/INCOMPLETE findings prevent release.
- No production-ready claim without executable tests and evidence.

## Current status

This commit establishes the isolated workspace and migration contract only. It does not claim that the planned modules are implemented or that tests have passed.
