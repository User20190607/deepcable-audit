"""Bounded Level-2 agent loop kernel for V30.1.

The kernel orchestrates allow-listed deterministic tools. It does not call an LLM,
perform network I/O, or mutate external systems. A planner is injected by the
host application; every proposed action is checked before execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
import json


class LoopError(RuntimeError):
    pass


class Planner(Protocol):
    def propose(self, state: dict[str, Any], findings: list[dict[str, Any]],
                available_tools: list[str]) -> dict[str, Any]: ...


Tool = Callable[[dict[str, Any]], dict[str, Any]]
Validator = Callable[[dict[str, Any]], list[dict[str, Any]]]


@dataclass
class LoopConfig:
    max_steps: int = 6
    max_repeated_action: int = 2
    require_validation_after_tool: bool = True


@dataclass
class LoopResult:
    status: str
    state: dict[str, Any]
    trace: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)


class AgentLoop:
    """A bounded observe -> plan -> act -> validate loop."""

    def __init__(self, tools: dict[str, Tool], validator: Validator,
                 planner: Planner, config: LoopConfig | None = None):
        self.tools = dict(tools)
        self.validator = validator
        self.planner = planner
        self.config = config or LoopConfig()

    def run(self, initial_state: dict[str, Any]) -> LoopResult:
        state = json.loads(json.dumps(initial_state, ensure_ascii=False))
        trace: list[dict[str, Any]] = []
        repeated: dict[str, int] = {}
        findings = self.validator(state)

        for step in range(1, self.config.max_steps + 1):
            if not findings:
                return LoopResult("COMPLETED", state, trace, [])

            proposal = self.planner.propose(
                state, findings, sorted(self.tools.keys())
            )
            if not isinstance(proposal, dict):
                raise LoopError("Planner proposal must be an object")

            action = proposal.get("action")
            if action == "stop":
                trace.append(self._event(step, "stop", proposal.get("reason", "")))
                return LoopResult("HOLD", state, trace, findings)

            if action != "tool":
                raise LoopError(f"Unsupported planner action: {action!r}")

            tool_name = proposal.get("tool")
            if tool_name not in self.tools:
                raise LoopError(f"Tool is not allow-listed: {tool_name!r}")

            args = proposal.get("args", {})
            if not isinstance(args, dict):
                raise LoopError("Tool args must be an object")

            fingerprint = json.dumps(
                {"tool": tool_name, "args": args},
                sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            repeated[fingerprint] = repeated.get(fingerprint, 0) + 1
            if repeated[fingerprint] > self.config.max_repeated_action:
                trace.append(self._event(step, "loop_guard", fingerprint))
                return LoopResult("HOLD", state, trace, findings)

            before = len(findings)
            patch = self.tools[tool_name](args)
            if not isinstance(patch, dict):
                raise LoopError(f"Tool {tool_name} must return a state patch")
            state.update(patch)
            trace.append(self._event(step, "tool", tool_name, {
                "args": args, "findings_before": before
            }))

            findings = self.validator(state)
            trace.append(self._event(step, "validate", "validator", {
                "findings_after": len(findings),
                "finding_codes": [x.get("code") for x in findings]
            }))
            if not findings:
                return LoopResult("COMPLETED", state, trace, [])

        trace.append(self._event(self.config.max_steps, "max_steps", "limit reached"))
        return LoopResult("HOLD", state, trace, findings)

    @staticmethod
    def _event(step: int, kind: str, name: str,
               details: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "step": step, "kind": kind, "name": name,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
