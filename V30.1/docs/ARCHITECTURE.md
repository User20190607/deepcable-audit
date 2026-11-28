# V30.1 Target Architecture

## Layers

1. Behavior Policy — instruction precedence, batch isolation, patch authorization and output contract.
2. Rule Registry — versioned rules with stable IDs, provenance, scope, severity, conditions, constraints and test references.
3. Project Mapping — project-specific mappings with explicit activation and authorization.
4. Experience Memory — immutable correction events and reviewable rule candidates.
5. Execution and Release — deterministic parsing, Decimal arithmetic, validation, aggregation, sorting, TSV-5 and release gate.

## Rule record contract

A formal rule should contain:

- `rule_id`: stable unique identifier
- `name`, `domain`
- `status`: draft, active, deprecated or blocked
- `provenance`: USER_CONFIRMED, STANDARD_VERIFIED, PROJECT_MAPPING, PROVISIONAL or BLOCKED
- `scope`: global, project-bound or current-batch
- `severity`: INFO, WARN, HOLD or BLOCK
- `condition` and `constraint`
- `source` / evidence reference
- `tests`: regression case IDs
- `version`

A schema-valid rule is not thereby proven technically correct. STANDARD_VERIFIED requires independently traceable standard evidence; a user correction must not be relabeled as a national-standard requirement.

## Run trace

Each execution should record:

- runtime version
- rulebook version and deterministic hash
- loaded rule IDs and dependency closure
- source batch ID and row IDs
- mapping decisions and authorization references
- findings and release-gate result

## Experience lifecycle

CAPTURED → CLASSIFIED → REVIEWED → IMPLEMENTED → TESTED → RELEASED

Only reviewed and tested candidates may be promoted. Correction events are retained even when rejected or superseded. Global rules must not be silently inferred from a one-batch correction.

## Aggregation invariants

- Aggregate only compatible canonical model, unit, quantity basis, scope and status.
- Preserve source row identity and reversible source-row details.
- Keep quantity bases distinct; never mix metres, rolls and pieces without an explicit conversion.
- Preserve color allocation and remarks.
- Verify quantity conservation independently by unit.
- Enforce packaging and color constraints before release.

## Release policy

Release is blocked by HOLD, BLOCK, INCOMPLETE, unresolved required dependencies, failed regression tests, quantity non-conservation, invalid TSV-5 shape or missing required provenance.
