"""V30.1 rule registry: deterministic validation, hashing and dependency checks.

This module validates the V30.1 canonical registry format. It deliberately does
not reinterpret legacy beta2 rulebook sections or assert technical correctness.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

ALLOWED_STATUS = {"draft", "active", "deprecated", "blocked"}
ALLOWED_PROVENANCE = {
    "USER_CONFIRMED", "STANDARD_VERIFIED", "PROJECT_MAPPING",
    "PROVISIONAL", "BLOCKED",
}
ALLOWED_SCOPE = {"global", "project-bound", "current-batch"}
ALLOWED_SEVERITY = {"INFO", "WARN", "HOLD", "BLOCK"}
REQUIRED = {
    "rule_id", "name", "domain", "status", "provenance", "scope",
    "severity", "condition", "constraint", "source", "tests", "version",
}


class RulebookError(ValueError):
    """Raised when the registry cannot safely be loaded."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_rule(rule: Any, index: int = 0) -> list[str]:
    errors: list[str] = []
    where = f"rules[{index}]"
    if not isinstance(rule, dict):
        return [f"{where} must be an object"]
    missing = sorted(REQUIRED - set(rule))
    if missing:
        errors.append(f"{where} missing fields: {', '.join(missing)}")
        return errors

    for field in ("rule_id", "name", "domain"):
        if not _nonempty_string(rule[field]):
            errors.append(f"{where}.{field} must be a non-empty string")
    if rule["status"] not in ALLOWED_STATUS:
        errors.append(f"{where}.status is invalid")
    if rule["provenance"] not in ALLOWED_PROVENANCE:
        errors.append(f"{where}.provenance is invalid")
    if rule["scope"] not in ALLOWED_SCOPE:
        errors.append(f"{where}.scope is invalid")
    if rule["severity"] not in ALLOWED_SEVERITY:
        errors.append(f"{where}.severity is invalid")
    if not isinstance(rule["condition"], dict):
        errors.append(f"{where}.condition must be an object")
    if not isinstance(rule["constraint"], dict):
        errors.append(f"{where}.constraint must be an object")
    if not isinstance(rule["source"], dict) or not rule["source"]:
        errors.append(f"{where}.source must be a non-empty object")
    if not isinstance(rule["tests"], list) or any(not _nonempty_string(x) for x in rule["tests"]):
        errors.append(f"{where}.tests must be an array of non-empty case IDs")
    if not isinstance(rule["version"], int) or isinstance(rule["version"], bool) or rule["version"] < 1:
        errors.append(f"{where}.version must be an integer >= 1")
    if rule["provenance"] == "PROJECT_MAPPING" and rule["scope"] == "global":
        errors.append(f"{where}: PROJECT_MAPPING cannot have global scope")
    if rule["provenance"] == "STANDARD_VERIFIED":
        source = rule["source"]
        if not isinstance(source, dict) or not _nonempty_string(source.get("reference")):
            errors.append(f"{where}: STANDARD_VERIFIED requires source.reference evidence")
    if rule["status"] == "active" and rule["provenance"] in {"PROVISIONAL", "BLOCKED"}:
        errors.append(f"{where}: provisional/blocked provenance cannot be active")
    return errors


def validate_rulebook(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["rulebook must be a JSON object"]
    if not _nonempty_string(document.get("rulebook_id")):
        return ["rulebook_id must be a non-empty string"]
    if not isinstance(document.get("version"), str) or not document["version"].strip():
        return ["version must be a non-empty string"]
    rules = document.get("rules")
    if not isinstance(rules, list):
        return ["rules must be an array"]

    errors: list[str] = []
    seen: set[str] = set()
    for i, rule in enumerate(rules):
        errors.extend(validate_rule(rule, i))
        if isinstance(rule, dict) and _nonempty_string(rule.get("rule_id")):
            rid = rule["rule_id"]
            if rid in seen:
                errors.append(f"duplicate rule_id: {rid}")
            seen.add(rid)

    known = {r.get("rule_id") for r in rules if isinstance(r, dict)}
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        dependencies = rule.get("depends_on", [])
        if not isinstance(dependencies, list) or any(not _nonempty_string(x) for x in dependencies):
            errors.append(f"rules[{i}].depends_on must be an array of rule IDs")
            continue
        for dep in dependencies:
            if dep not in known:
                errors.append(f"rules[{i}] references missing dependency: {dep}")
    return errors


def _signature(rule: dict[str, Any]) -> str:
    """A conservative signature for detecting exact-condition contradictions."""
    return canonical_json({
        "domain": rule.get("domain"),
        "scope": rule.get("scope"),
        "condition": rule.get("condition"),
    })


def detect_conflicts(rules: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Detect exact-scope/exact-condition rules with different constraints.

    This is a conservative structural warning, not a semantic theorem prover.
    """
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in rules:
        if isinstance(rule, dict):
            buckets[_signature(rule)].append(rule)
    conflicts = []
    for group in buckets.values():
        active = [r for r in group if r.get("status") == "active"]
        constraints = {canonical_json(r.get("constraint")) for r in active}
        if len(active) > 1 and len(constraints) > 1:
            conflicts.append({
                "rule_ids": ",".join(sorted(str(r.get("rule_id")) for r in active)),
                "reason": "same domain/scope/condition has different active constraints",
            })
    return conflicts


def dependency_order(rules: list[dict[str, Any]]) -> list[str]:
    """Return dependencies before dependants; reject cycles."""
    by_id = {r["rule_id"]: r for r in rules}
    indegree = {rid: 0 for rid in by_id}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for rid, rule in by_id.items():
        for dep in rule.get("depends_on", []):
            if dep not in by_id:
                raise RulebookError(f"{rid} has missing dependency {dep}")
            indegree[rid] += 1
            outgoing[dep].append(rid)
    queue = deque(sorted(rid for rid, degree in indegree.items() if degree == 0))
    ordered = []
    while queue:
        rid = queue.popleft()
        ordered.append(rid)
        for child in sorted(outgoing[rid]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(ordered) != len(by_id):
        raise RulebookError("dependency cycle detected")
    return ordered


class RuleRegistry:
    def __init__(self, document: dict[str, Any]):
        errors = validate_rulebook(document)
        if errors:
            raise RulebookError("; ".join(errors))
        self.document = document
        self.rules = {r["rule_id"]: r for r in document["rules"]}
        self.version = document["version"]
        self.sha256 = content_hash(document)

    @classmethod
    def from_file(cls, path: str | Path) -> "RuleRegistry":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls(json.load(handle))

    def get(self, rule_id: str) -> dict[str, Any]:
        try:
            return self.rules[rule_id]
        except KeyError as exc:
            raise RulebookError(f"unknown rule_id: {rule_id}") from exc

    def load(self, requested_ids: list[str], include_dependencies: bool = True) -> list[dict[str, Any]]:
        selected: set[str] = set()

        def visit(rule_id: str) -> None:
            if rule_id not in self.rules:
                raise RulebookError(f"unknown rule_id: {rule_id}")
            if rule_id in selected:
                return
            rule = self.rules[rule_id]
            if rule.get("status") != "active":
                raise RulebookError(f"rule is not active: {rule_id}")
            selected.add(rule_id)
            if include_dependencies:
                for dep in rule.get("depends_on", []):
                    visit(dep)

        for rid in requested_ids:
            visit(rid)
        order = dependency_order(list(self.rules.values()))
        return [self.rules[rid] for rid in order if rid in selected]

    def audit(self) -> dict[str, Any]:
        return {
            "rulebook_id": self.document["rulebook_id"],
            "version": self.version,
            "sha256": self.sha256,
            "rule_count": len(self.rules),
            "conflicts": detect_conflicts(list(self.rules.values())),
            "dependency_order": dependency_order(list(self.rules.values())),
        }
