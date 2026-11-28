"""Integrity checks for user-adjudicated Golden Dataset fixtures."""
from decimal import Decimal
import json
from pathlib import Path
import unittest

CASE = Path(__file__).parents[2] / "datasets" / "golden" / "cases" / "adjudicated" / "GOLD-IMG-20261128-001.json"


class AdjudicatedGoldenCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads(CASE.read_text(encoding="utf-8"))

    def test_case_is_adjudicated_by_user(self):
        self.assertEqual(self.case["adjudication"]["status"], "ADJUDICATED")
        self.assertEqual(self.case["adjudication"]["authority"], "USER_EXPLICIT")

    def test_expected_ten_canonical_rows(self):
        rows = self.case["labels"]["expected_standardized_rows"]
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({(r["model"], r["unit"]) for r in rows}), 10)

    def test_yjv_voltage_comes_from_explicit_case_adjudication(self):
        rows = self.case["labels"]["expected_standardized_rows"]
        yjv = [r for r in rows if r["model"].startswith("ZC-YJV-")]
        self.assertEqual(len(yjv), 8)
        self.assertTrue(all("-0.6/1kV " in r["model"] for r in yjv))

    def test_bvr_profile_and_roll_conversion(self):
        rows = self.case["labels"]["expected_standardized_rows"]
        bvr = {r["model"]: r["quantity"] for r in rows if r["model"].startswith("ZC-BVR-")}
        self.assertEqual(bvr, {
            "ZC-BVR-450/750V 1×2.5": "4900",
            "ZC-BVR-450/750V 1×4": "5600",
        })

    def test_decimal_quantity_conservation(self):
        rows = self.case["labels"]["expected_standardized_rows"]
        total = sum((Decimal(r["quantity"]) for r in rows), Decimal("0"))
        self.assertEqual(total, Decimal("11038"))
        self.assertEqual(self.case["labels"]["expected_quantity_by_unit"]["m"], "11038")

    def test_source_row_lineage_covers_all_seventeen_rows(self):
        rows = self.case["input"]["source_rows"]
        self.assertEqual(len(rows), 17)
        self.assertEqual([r["row"] for r in rows], list(range(1, 18)))

    def test_project_specific_adjudication_is_not_global_rule(self):
        notes = " ".join(self.case["quality"]["notes"])
        self.assertIn("must not be generalized", notes)


if __name__ == "__main__":
    unittest.main()
