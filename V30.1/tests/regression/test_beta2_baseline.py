"""Executable characterization tests for the archived V30.0-beta2 baseline.

These tests intentionally characterize known defects as reproduced observations.
They are not assertions that those behaviours are acceptable for V30.1 release.
"""
from decimal import Decimal
import unittest

from v30core.compat.beta2_engine_snapshot import (
    process_row, apply_patch, aggregate_rows, render_tsv5, release_gate,
)


def row(model, quantity="10", unit="m", **extra):
    return {"row_id": "R1", "model": model, "quantity": quantity, "unit": unit, **extra}


class Beta2BaselineRegressionTests(unittest.TestCase):
    def test_001_concatenated_prefix_is_not_recognized_but_held(self):
        result = process_row(row("WDZBNYJV-0.6/1kV 3×50"))
        self.assertIsNone(result["ast"]["prefix"])
        self.assertEqual(result["status"], "HOLD")

    def test_002_patch_leaves_stale_ast_and_status(self):
        original = process_row(row("YJV 0.6/1kV 3×50"))
        old_ast = original["ast"]
        patched = apply_patch([original], {
            "target_path": "model",
            "row_id": "R1",
            "before_value": original["model"],
            "after_value": "WDZ-YJV 0.6/1kV 3×50",
            "authorization_ref": "TEST-AUTH",
            "patch_id": "PATCH-STALE-001",
        })[0]
        self.assertEqual(patched["model"], "WDZ-YJV 0.6/1kV 3×50")
        self.assertIs(patched["ast"], old_ast)
        self.assertEqual(patched["status"], "PASS")
        self.assertEqual(patched["findings"], [])

    def test_003_user_supplied_wrong_pack_factor_is_accepted(self):
        result = process_row(row("YJV 0.6/1kV 3×50", "5", "扎", pack_length_m="10"))
        self.assertEqual(result["quantity"], "50")
        self.assertEqual(result["unit"], "m")
        groups = aggregate_rows([result])
        tsv = render_tsv5(groups)
        gate = release_gate([result], groups, tsv)
        self.assertEqual(gate["status"], "RELEASED")
        self.assertEqual(Decimal(gate["source_quantity_by_unit"]["m"]), Decimal("50"))

    def test_004_missing_power_voltage_uses_implicit_default(self):
        result = process_row(row("YJV 3×50"))
        self.assertEqual(result["ast"]["voltage"], "0.6/1kV")
        self.assertEqual(result["status"], "PASS")

    def test_005_wd_pvc_material_conflict_is_held(self):
        result = process_row(row("WDZ-YJV 0.6/1kV 3×50"))
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("HALOGEN_FREE_PVC_CONFLICT", {f["code"] for f in result["findings"]})

    def test_006_fractional_metre_has_no_dedicated_integer_metre_finding(self):
        result = process_row(row("YJV 0.6/1kV 3×50", "50.5", "m"))
        self.assertEqual(result["quantity"], "50.5")
        self.assertNotIn("FRACTIONAL_METRE", {f["code"] for f in result["findings"]})
        self.assertEqual(result["status"], "PASS")

    def test_007_chinese_metre_alias_is_not_normalized(self):
        result = process_row(row("YJV 0.6/1kV 3×50", "45.6", "米"))
        self.assertEqual(result["unit"], "米")
        self.assertEqual(result["status"], "PASS")

    def test_008_hundred_metre_unit_is_not_converted(self):
        result = process_row(row("BYJ-450/750V 1×2.5", "661", "百米"))
        self.assertEqual(result["unit"], "百米")
        self.assertEqual(result["quantity"], "661")

    def test_009_roll_without_pack_factor_remains_roll(self):
        result = process_row(row("BVR-450/750V 1×2.5", "22", "卷"))
        self.assertEqual(result["unit"], "卷")
        self.assertEqual(result["quantity"], "22")

    def test_010_mapping_requires_authorization_reference(self):
        mappings = [{
            "source_model": "YJV 0.6/1kV 3×50",
            "target_model": "WDZB-YJY 0.6/1kV 3×50",
            "scope": "current-batch",
        }]
        result = process_row(row("YJV 0.6/1kV 3×50"), mappings=mappings)
        self.assertIsNone(result["mapping_audit"])

    def test_011_authorized_mapping_is_audited(self):
        mappings = [{
            "source_model": "YJV 0.6/1kV 3×50",
            "target_model": "WDZB-YJY 0.6/1kV 3×50",
            "scope": "current-batch",
            "authorization_ref": "USER-AUTH-001",
        }]
        result = process_row(row("YJV 0.6/1kV 3×50"), mappings=mappings)
        self.assertEqual(result["working_model"], "WDZB-YJY 0.6/1kV 3×50")
        self.assertEqual(result["mapping_audit"]["authorization_ref"], "USER-AUTH-001")

    def test_012_project_scope_does_not_leak_between_batches(self):
        first = process_row(row("YJV 0.6/1kV 3×50"), scope="project-A")
        second = process_row(row("YJV 0.6/1kV 3×50"), scope="project-B")
        groups = aggregate_rows([first, second])
        self.assertEqual(len(groups), 2)
        self.assertEqual({g["scope"] for g in groups}, {"project-A", "project-B"})

    def test_013_tsv_has_exactly_five_columns(self):
        result = process_row(row("YJV 0.6/1kV 3×50"))
        tsv = render_tsv5(aggregate_rows([result]))
        self.assertEqual(len(tsv.splitlines()[0].split("\t")), 5)

    def test_014_decimal_aggregation_is_exact(self):
        a = process_row(row("YJV 0.6/1kV 3×50", "0.1"))
        b = process_row({**row("YJV 0.6/1kV 3×50", "0.2"), "row_id": "R2"})
        groups = aggregate_rows([a, b])
        self.assertEqual(groups[0]["quantity"], "0.3")

    def test_015_two_core_twisted_pair_is_kept_distinct(self):
        result = process_row(row("RVS-300/300V 2×1.5"))
        self.assertEqual(result["ast"]["product"], "RVS")
        self.assertEqual(result["ast"]["components"][0]["cores"], 2)
        self.assertEqual(result["ast"]["voltage"], "300/300V")


if __name__ == "__main__":
    unittest.main()
