# V30.1 Level-2 Agent Loop Design

## Decision

Implement Level 2 before researching Level 3. Level 2 is an external orchestration loop over deterministic tools and validators; it is not a Looped Transformer and does not alter model hidden states or share Transformer weights.

## Control cycle

1. Observe: read current batch state, provenance, findings and prior trace.
2. Plan: propose one bounded action using an injected planner.
3. Authorize: reject tools outside the explicit allow-list; reject malformed arguments.
4. Act: invoke one deterministic tool; tools return a state patch, not arbitrary side effects.
5. Validate: rerun the relevant validator after every tool action.
6. Continue or stop: complete only when validation is clean; HOLD on planner stop, repeated action guard, or max-step exhaustion.

## Safety invariants

- The loop never treats an assistant proposal as a user authorization.
- No shell, network, filesystem, email, GitHub write or external side-effect tool is included by default.
- Project mappings and source-row patches still require the existing authorization reference and scope checks.
- Every tool action is allow-listed and must return a state patch.
- Validation runs after every action.
- Max steps and repeated-action guards prevent infinite loops.
- Unresolved findings produce HOLD, not speculative repair.
- Decimal arithmetic and release gate remain in the deterministic core.
- Each run records tool name, step, validation result and finding codes.
- The planner is an adapter contract; this repository kernel does not embed a model provider or credentials.

## Current implementation boundary

`v30core/agent_loop.py` is a provider-neutral bounded orchestration kernel. A host application must supply:
- a planner implementing `propose(state, findings, available_tools)`;
- deterministic, allow-listed tools;
- a domain validator.

The current tests use a scripted planner to test orchestration mechanics. They do not claim autonomous LLM planning, end-to-end cable processing, or production readiness.

## Next increments

- L2.1: tool contracts and typed input/output schemas for parse, normalize, aggregate, audit, render and release gate.
- L2.2: dependency-aware context router that loads only required rule IDs and records the rulebook hash.
- L2.3: correction event memory with UNREVIEWED / NEEDS_CONTEXT / ADJUDICATED / REJECTED lifecycle; promotion must link to a regression test.
- L2.4: batch replay and end-to-end evals using adjudicated Golden Dataset cases.
- L2.5: optional model planner adapter, isolated behind schema validation and no direct write permissions.
- L2.6: release gate and run trace integration.

Level 3 research (shared-weight recurrent Transformer / adaptive compute) remains explicitly out of scope until Level 2 is measured and stable.
