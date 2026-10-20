import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aggregator import aggregate
from deepcable_normalize import normalize, normalize_detailed


class PipelineResultTests(unittest.TestCase):
    def test_standard_model_is_accepted(self):
        result = normalize_detailed('YJV-0.6/1kV-5×16')
        self.assertEqual(result.status, 'accepted')
        self.assertEqual(result.model, 'YJV-0.6/1kV-5×16')
        self.assertFalse(result.issues)

    def test_rule_correction_is_reported(self):
        result = normalize_detailed('NHYJV-0.6/1KV-5X16')
        self.assertEqual(result.status, 'corrected')
        self.assertEqual(result.model, 'N-YJV-0.6/1kV-5×16')
        self.assertTrue(result.changes)

    def test_missing_fields_are_marked_as_inferred(self):
        result = normalize_detailed('BV2.5')
        self.assertEqual(result.status, 'inferred')
        self.assertEqual(result.model, 'BV-450/750V-1×2.5')
        self.assertEqual(set(result.spec.inferred_fields), {'core_count', 'voltage'})

    def test_unknown_model_does_not_match_embedded_known_model(self):
        result = normalize_detailed('KYJVP7×1.5')
        self.assertEqual(result.status, 'needs_review')
        self.assertEqual(result.model, 'KYJVP-7×1.5')
        self.assertIn('unknown_base', {issue.code for issue in result.issues})

    def test_combustion_grade_is_preserved(self):
        result = normalize_detailed('WDZC-B1-BYJ-6')
        self.assertEqual(result.status, 'inferred')
        self.assertEqual(result.model, 'WDZC-BYJ-B1-450/750V-1×6')
        self.assertTrue(result.spec.b1)

    def test_english_model_mapping_is_preserved(self):
        result = normalize_detailed('CU/XLPE/PVC 4x25+1x16')
        self.assertEqual(result.status, 'corrected')
        self.assertEqual(result.model, 'YJV-0.6/1kV-4×25+1×16')

    def test_system_voltage_is_canonicalized(self):
        result = normalize_detailed('YJV22-10kV-3×300')
        self.assertEqual(result.model, 'YJV22-8.7/15kV-3×300')

    def test_needs_review_item_is_not_aggregated(self):
        aggregated, failed, index = aggregate([
            {'raw': 'YJV-0.6/1kV-5×16', 'qty': 10},
            {'raw': 'KYJVP7×1.5', 'qty': 20},
        ])
        self.assertEqual(aggregated, {'YJV-0.6/1kV-5×16': 10.0})
        self.assertEqual(failed[0]['status'], 'needs_review')
        self.assertEqual(index[1]['model'], 'KYJVP-7×1.5')

    def test_legacy_api_remains_available(self):
        self.assertEqual(normalize('BV2.5'), 'BV-450/750V-1×2.5')


if __name__ == '__main__':
    unittest.main()
