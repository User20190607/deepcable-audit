# Golden Dataset v0.1

## Purpose

Create an evidence-backed, user-adjudicated evaluation corpus for V30.1. The dataset is not a copy of historical assistant outputs. A historical assistant TSV is never a gold label unless the relevant rows are matched to a later user confirmation or other authoritative evidence.

## Trust hierarchy

1. Explicit user correction/confirmation tied to an identifiable source row.
2. User-approved final list for the same batch, with source lineage.
3. Contract / drawing / technical agreement, with exact document and page or row evidence.
4. Verified standard text, with edition and clause evidence.
5. Assistant output or inferred interpretation: candidate only, never gold by itself.

Conflicts are not silently reconciled. Mark `NEEDS_CONTEXT` or `UNRESOLVED` and keep the case out of scored accuracy metrics.

## Case statuses

- `UNREVIEWED`: extracted candidate, no human decision yet.
- `NEEDS_CONTEXT`: a correction exists but its target/source row or scope is ambiguous.
- `ADJUDICATED`: input, decision, scope and expected output are traceable.
- `REJECTED`: duplicate, irrelevant, or not a valid cable-list case.

Only `ADJUDICATED` cases can enter the golden evaluation score. Keep baseline-characterization tests separate from correctness goldens.

## Required invariants

- Preserve the exact raw input and source message IDs.
- Every changed field has a decision evidence reference.
- Do not infer a missing model, voltage, unit, quantity, colour, project, or scope.
- Preserve quantity and structure unless an explicit authorized transformation says otherwise.
- Unit conversions must state the conversion basis; never infer packaging length from an unverified assumption.
- Keep user corrections separate from assistant proposals and assistant outputs.
- Do not merge separate batches unless the source explicitly says merge/append/compare.
- Split by source conversation/batch, not randomly by individual rows, to avoid leakage.
- Never put raw customer/private chat exports into the repository. Store source hashes and message IDs; commit only cable-relevant excerpts needed for audit.

## Directory layout

- `schema/golden_case.schema.json`: canonical case contract.
- `cases/adjudicated/`: cases with explicit, traceable expected decisions.
- `cases/unreviewed/`: extraction candidates awaiting review.
- `sources/manifest.json`: source inventory, hashes, coverage and limitations.
- `tools/extract_candidates.py`: deterministic candidate extractor.
- `reports/QUALITY_REPORT.md`: dataset counts, exclusions and coverage gaps.

## Current v0.1 scope

The September conversation export `chat-export-1792110211452.json` was retrieved from the user's Library. It contains 787 message objects (379 user, 408 assistant) and is 5,350,332 bytes. SHA-256 is recorded in `sources/manifest.json`.

This differs from the prior audit report's stated 793 messages / 385 user messages. The discrepancy is recorded rather than silently reconciled. The current export has 158 cable-related user-message candidates using a conservative lexical filter; candidates are not gold labels.

The October audit report refers to a separate `raw_sources/2026-10_chat_export.txt` (92,365 chars) and replay artefacts, but that exact source file was not found in the Library search. A separate `2026-10_非群聊.txt` exists (1,031,412 bytes) but is a different export and must not be substituted without confirming scope. October is therefore not included in the v0.1 candidate queue.

## Evaluation policy

Metrics must be reported separately:
- exact-row accuracy on adjudicated cases;
- transformation accuracy by rule family;
- quantity/unit exactness;
- false PASS rate for cases that should HOLD/BLOCK;
- abstention quality (correct HOLD vs unsupported guessing);
- coverage by product family, unit type, input modality and risk class.

No headline accuracy is published until the adjudicated test split is large and representative enough. The test split is locked and must not be used for rule tuning.
