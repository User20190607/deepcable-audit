import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from v30_1_engine import parse_model, process_row, run_pipeline, apply_patch, validate_conductors

class V301Tests(unittest.TestCase):
    def test_compact_prefix(self):
        p=parse_model("WDZBNYJY23-0.6/1kV 4×150+1×95")
        self.assertEqual((p.prefix,p.product,p.armor),("WDZBN","YJY","23"))
    def test_armor_preserved(self):
        self.assertEqual(parse_model("WDZBN-YJY22-0.6/1kV 4×150+1×95").armor,"22")
    def test_voltage_handling(self):
        self.assertIn("VOLTAGE_UNRESOLVED",[x["code"] for x in parse_model("YJV 3×50").findings])
        self.assertEqual(parse_model("ZB-YJV22-8.7/15kV 3×300").voltage,"8.7/15kV")
    def test_loss_is_remark_only(self):
        r=process_row({"row_id":"r","model":"BVV-300/500V 1×35","unit":"m","quantity":"38","production_loss_m":"4"})
        self.assertEqual(r["quantity"],"38"); self.assertIn("生产损耗4m",r["remark"])
    def test_package_requires_length(self):
        self.assertEqual(process_row({"row_id":"r","model":"BVR-450/750V 1×6","unit":"PCS","quantity":"3"})["status"],"HOLD")
    def test_package_explicit_length(self):
        r=process_row({"row_id":"r","model":"BVR-450/750V 1×6","unit":"PCS","quantity":"3","pack_length_m":"100"})
        self.assertEqual((r["quantity"],r["unit"]),("300","m"))
    def test_fractional_metre_holds(self):
        self.assertEqual(process_row({"row_id":"r","model":"YJV-0.6/1kV 3×50","unit":"m","quantity":"10.5"})["status"],"HOLD")
    def test_patch_revalidates(self):
        r=process_row({"row_id":"r","model":"YJV-0.6/1kV 3×50","unit":"m","quantity":"10"})
        x=apply_patch(r,{"field":"model","before_value":r["model"],"after_value":"YJV 3×50","authorization_ref":"USER"})
        self.assertEqual(x["status"],"HOLD"); self.assertTrue(x["patch_audit"]["revalidated"])
    def test_conductor_fail_closed(self):
        self.assertEqual(validate_conductors({"conductor_roles":[{"role":"PEN","section_mm2":"70","profile_id":"x"}]},{"x":{"review_status":"DRAFT","standard_id":"STD","clause":"1","required_section_mm2":"70"}})["status"],"BLOCKED")
    def test_compound_cable_role_missing_holds(self):
        x=run_pipeline({"rows":[{"row_id":"r","model":"YJV-0.6/1kV 4×150+1×70","unit":"m","quantity":"10"}]})
        self.assertEqual(x["release_gate"]["status"],"HELD")
    def test_raw_quantity_recomputed(self):
        from v30_1_engine import release_gate, aggregate_rows, render_tsv5
        raw=[{"row_id":"r","model":"YJV-0.6/1kV 3×50","unit":"m","quantity":"100"}]
        x=run_pipeline({"rows":raw}); x["source_rows"][0]["quantity"]="99"
        groups=aggregate_rows(x["source_rows"])
        self.assertEqual(release_gate(raw,x["source_rows"],groups,render_tsv5(groups))["status"],"HELD")
    def test_aggregate_total(self):
        x=run_pipeline({"rows":[{"row_id":"a","model":"BVV-300/500V 1×35","unit":"m","quantity":"38"},{"row_id":"b","model":"BVV-300/500V 1×35","unit":"m","quantity":"62"}]})
        self.assertEqual(x["aggregated_rows"][0]["quantity"],"100")
        self.assertEqual(x["release_gate"]["status"],"RELEASED")
    def test_tsv5(self):
        x=run_pipeline({"rows":[{"row_id":"a","model":"BVV-300/500V 1×35","unit":"m","quantity":"38"}]})
        self.assertEqual(len(x["tsv5"].split("\t")),5)

if __name__=="__main__": unittest.main(verbosity=2)
