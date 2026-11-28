import unittest

from v30core.rules.registry import (
    RulebookError, RuleRegistry, detect_conflicts, validate_rulebook,
)


def rule(rule_id, **overrides):
    value = {
        "rule_id": rule_id,
        "name": rule_id,
        "domain": "packaging",
        "status": "active",
        "provenance": "USER_CONFIRMED",
        "scope": "global",
        "severity": "BLOCK",
        "condition": {"family": "BYJ"},
        "constraint": {"length_m": "100"},
        "source": {"type": "user_confirmation", "reference": "confirmed"},
        "tests": ["PKG-001"],
        "version": 1,
        "depends_on": [],
    }
    value.update(overrides)
    return value


def book(rules):
    return {"rulebook_id": "V30.1-TEST", "version": "1.0.0", "rules": rules}


class RuleRegistryTests(unittest.TestCase):
    def test_valid_registry_loads_and_hashes(self):
        registry = RuleRegistry(book([rule("PKG-001")]))
        self.assertEqual(registry.audit()["rule_count"], 1)
        self.assertEqual(len(registry.sha256), 64)

    def test_duplicate_ids_rejected(self):
        self.assertTrue(any("duplicate rule_id" in e for e in validate_rulebook(book([
            rule("DUP"), rule("DUP")
        ]))))

    def test_missing_dependency_rejected(self):
        errors = validate_rulebook(book([rule("A", depends_on=["MISSING"])]))
        self.assertTrue(any("missing dependency" in e for e in errors))

    def test_dependency_load_order(self):
        registry = RuleRegistry(book([
            rule("B", depends_on=["A"]),
            rule("A", condition={"family": "BYJ-A"}),
        ]))
        self.assertEqual([r["rule_id"] for r in registry.load(["B"])], ["A", "B"])

    def test_inactive_rule_cannot_load(self):
        registry = RuleRegistry(book([rule("A", status="draft")]))
        with self.assertRaises(RulebookError):
            registry.load(["A"])

    def test_project_mapping_cannot_be_global(self):
        errors = validate_rulebook(book([
            rule("PM-1", provenance="PROJECT_MAPPING", scope="global")
        ]))
        self.assertTrue(any("cannot have global scope" in e for e in errors))

    def test_standard_verified_requires_evidence_reference(self):
        errors = validate_rulebook(book([
            rule("STD-1", provenance="STANDARD_VERIFIED", source={"type": "standard"})
        ]))
        self.assertTrue(any("requires source.reference" in e for e in errors))

    def test_conflicting_active_constraints_reported(self):
        conflicts = detect_conflicts([
            rule("A", constraint={"pack": "100"}),
            rule("B", constraint={"pack": "200"}),
        ])
        self.assertEqual(len(conflicts), 1)

    def test_dependency_cycle_rejected(self):
        registry = RuleRegistry(book([
            rule("A", depends_on=["B"]),
            rule("B", depends_on=["A"], condition={"family": "BYJ-B"}),
        ]))
        with self.assertRaises(RulebookError):
            registry.audit()


if __name__ == "__main__":
    unittest.main()
