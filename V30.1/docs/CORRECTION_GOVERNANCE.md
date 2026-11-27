# Correction-to-Constraint Governance

Every user correction is captured before it is considered a global rule.

Lifecycle: CAPTURED -> CLASSIFIED -> REVIEWED -> IMPLEMENTED -> TESTED -> RELEASED.

A record must contain correction ID, raw example, incorrect behavior, expected behavior, category, scope, trigger, exclusions, priority, implementation target, regression test, evidence/authorization and lifecycle status.

Classify corrections as: (A) business invariants, (B) product/model knowledge, (C) execution constraints, (D) output preferences, or (E) one-batch instructions. A one-batch instruction must not become a global mapping without explicit approval.

Natural-language instructions are not enforcement. Deterministic rules belong in Python/Rulebook and require tests. Unknown or unsupported conditions fail closed as HOLD/BLOCKED. A rule is not RELEASED merely because it was written to a file.

Every code/rule change must preserve raw source data, add regression coverage for the triggering incident, run the full suite, and record commit SHA and test report. Historical incident tests are retained unless explicitly superseded by reviewed change.
