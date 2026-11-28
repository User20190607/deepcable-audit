# Golden Dataset v0.2

## Purpose

Evidence-backed, user-adjudicated evaluation corpus for V30.1. Historical assistant outputs are never gold labels without matching user confirmation or authoritative source evidence.

## Trust hierarchy

1. Explicit user correction/confirmation tied to an identifiable source row.
2. User-approved final list for the same batch, with source lineage.
3. Contract / drawing / technical agreement, with exact document and page or row evidence.
4. Verified standard text, with edition and clause evidence.
5. Assistant output or inferred interpretation: candidate only, never gold by itself.

## Case statuses

- `UNREVIEWED`: extracted candidate, no human decision.
- `NEEDS_CONTEXT`: correction exists but target row or scope is ambiguous.
- `ADJUDICATED`: input, decision, scope and expected output are traceable.
- `REJECTED`: duplicate, irrelevant or invalid cable-list case.

Only `ADJUDICATED` cases enter scored golden evaluation. Baseline characterization tests remain separate.

## Current adjudicated case

- `GOLD-IMG-20261128-001`: 17 source rows, 10 canonical output rows, user-confirmed voltage/profile and 100m roll conversion. Public fixture uses anonymized equipment labels. The decision applies only to this image case, not as a global rule.

## Required invariants

- Preserve exact raw input and source message IDs or upload reference.
- Every changed field has a decision evidence reference.
- Do not infer missing model, voltage, unit, quantity, colour, project or scope.
- Unit conversions state their basis and use Decimal.
- Keep user corrections separate from assistant proposals and outputs.
- Do not merge batches unless explicitly requested.
- Split by conversation/batch, not randomly by individual rows.
- Never commit raw private chat exports or customer-identifying source text to this public repository.

## Directories

- `schema/`: canonical case contract.
- `cases/adjudicated/`: reviewed expected outcomes.
- `cases/unreviewed/`: candidates awaiting review.
- `sources/manifest.json`: source hashes and coverage.
- `tools/`: deterministic extraction utilities.
- `reports/`: quality and coverage reports.
