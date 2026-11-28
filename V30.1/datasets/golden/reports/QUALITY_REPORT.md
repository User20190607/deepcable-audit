# Golden Dataset v0.2 Quality Report

## Current counts

| Item | Count | Meaning |
|---|---:|---|
| September export message objects | 787 | Parsed source message count |
| User messages | 379 | Parsed user-role messages |
| Assistant messages | 408 | Parsed assistant-role messages |
| Cable-related user candidates | 158 | Lexical candidate extraction only |
| High-priority correction candidates | 38 | Still unreviewed unless individually adjudicated |
| Adjudicated image cases | 1 | User explicitly confirmed voltage and wire model profile |
| Adjudicated source rows | 17 | One image-backed engineering schedule |
| Canonical aggregated output rows | 10 | Exact model+unit aggregation with source lineage |
| October candidates | 0 | Exact audit source not retrieved |

## First adjudicated case

`GOLD-IMG-20261128-001` is an image-backed engineering cable schedule. The user explicitly confirmed:
- All ZC-YJV rows in this image use 0.6/1kV.
- ZR-BVR rows use `ZR-BVR-450/750V 1×cross-section`.
- The established business conversion for this case is 1 roll = 100m.

The case has 17 source rows and 10 canonical aggregated rows. The Decimal quantity total is 11,038m. The adjudication is scoped to this image case and is not a global voltage rule.

Equipment labels in the public JSON fixture are anonymized as DEV-01..DEV-10. Original customer/project details remain in the user's local workbook and are not committed to this public repository.

## Source discrepancies

The prior V30 replay audit described the September export as 793 messages (385 user + 408 assistant). The Library copy actually inspected contains 787 message objects (379 user + 408 assistant). This six-message discrepancy remains unresolved.

The audit's October source `2026-10_chat_export.txt` (92,365 characters) was not found. A separate `2026-10_非群聊.txt` exists but has different scope and is not substituted.

## Label quality and limitations

The 158 September candidates remain unreviewed. Assistant outputs are not gold labels without explicit confirmation. Image-only lists may be missed by lexical extraction. The first adjudicated image case tests a single user-confirmed batch; it is not a statistically representative accuracy benchmark.

## Privacy boundary

The GitHub repository is public. Raw chat exports, raw customer/project text and the detailed local review workbook are not committed. The repository contains schema, extractor code, source hashes, aggregate coverage and an anonymized adjudicated fixture.

## Next data work

1. Review remaining correction candidates and link each correction to exact source rows.
2. Add more image/PDF and text-based cases across product families.
3. Add reviewed adversarial cases for prefixes, voltage, structure, packaging and color.
4. Lock a held-out test split only after adequate case diversity and coverage.
