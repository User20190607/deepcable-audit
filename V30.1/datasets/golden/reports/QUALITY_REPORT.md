# Golden Dataset v0.1 Quality Report

## Current counts

| Item | Count | Meaning |
|---|---:|---|
| September export message objects | 787 | Parsed source message count |
| User messages | 379 | Parsed user-role messages |
| Assistant messages | 408 | Parsed assistant-role messages |
| Cable-related user candidates | 158 | Lexical candidate extraction only |
| High-priority correction candidates | 38 | Contains correction/authorization/confirmation language; still unreviewed |
| Adjudicated golden cases | 0 initially | Do not score until each case is reviewed |
| October candidates | 0 | Exact audit source not retrieved |

## Known source discrepancies

The prior V30 replay audit described the September export as 793 messages (385 user + 408 assistant). The Library copy actually inspected here contains 787 message objects (379 user + 408 assistant). This is a six-message / six-user-message discrepancy. No messages are fabricated to reconcile the counts.

The audit's October source `2026-10_chat_export.txt` (92,365 characters) was not found. The available `2026-10_非群聊.txt` is a 1,031,412-byte export with different scope and must not be treated as the same source.

## Label quality

The 158 September candidates preserve user message IDs, timestamps, exact user text and source hash. They are all `UNREVIEWED`. A candidate may contain:
- an original list;
- a correction;
- a preference or process instruction;
- a partial reference to an earlier row;
- a request that needs attachment context.

The lexical filter is intentionally high-recall and may include false positives. It may also miss image-only cable lists.

## Adjudicated examples

No source-derived cases have yet been promoted to `ADJUDICATED`. Explicit correction candidates are queued for human review in the local-only workbook. Each must be linked to its original source row and decision context before promotion.

## Privacy boundary

The GitHub repository is public. Raw chat exports, raw candidate excerpts, customer names, project details and the local review workbook are not committed to it. The repository contains schema, extractor code, source hashes and aggregate coverage metadata only.

## Next data work

1. Review candidates by conversation/batch and attach original source rows.
2. Link correction messages to the exact earlier row(s).
3. Confirm final normalized output and unit/quantity transformations.
4. Independently review all cases that affect model family, material, voltage, core structure, or quantity.
5. Lock a held-out test split only after sufficient coverage is reached.
