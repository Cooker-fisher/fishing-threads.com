"""Tests for scripts/run_target_band_ranges_generator.py"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_target_band_ranges_generator import build_output, build_target_ranges


class TestBuildTargetRanges(unittest.TestCase):
    def test_list_of_entries_shape(self):
        summary = [
            {"band": 100, "fish_targets": ["マダイ", "アジ"]},
            {"band": 200, "fish_targets": ["マダイ", "ブリ"]},
            {"band": 400, "fish_targets": ["ブリ", "キンメダイ"]},
        ]
        result = build_target_ranges(summary)
        self.assertEqual(
            result,
            [
                {"target": "アジ", "start_band": 100, "end_band": 100},
                {"target": "マダイ", "start_band": 100, "end_band": 200},
                {"target": "ブリ", "start_band": 200, "end_band": 400},
                {"target": "キンメダイ", "start_band": 400, "end_band": 400},
            ],
        )

    def test_wrapped_list_shape(self):
        summary = {
            "bands": [
                {"standard_band": 100, "fish_targets": ["アジ"]},
                {"standard_band": 300, "fish_targets": ["アジ", "タチウオ"]},
            ]
        }
        result = build_target_ranges(summary)
        self.assertEqual(
            result,
            [
                {"target": "アジ", "start_band": 100, "end_band": 300},
                {"target": "タチウオ", "start_band": 300, "end_band": 300},
            ],
        )

    def test_dict_keyed_by_band_shape(self):
        summary = {
            "100": {"fish_targets": ["アジ"]},
            "200": {"fish_targets": {"アジ": True, "ブリ": 1, "ムツ": 0}},
            "600": {"fish_targets": [{"target": "ブリ"}, {"name": "キンメダイ"}]},
        }
        result = build_target_ranges(summary)
        self.assertEqual(
            result,
            [
                {"target": "アジ", "start_band": 100, "end_band": 200},
                {"target": "ブリ", "start_band": 200, "end_band": 600},
                {"target": "キンメダイ", "start_band": 600, "end_band": 600},
            ],
        )


class TestBuildOutput(unittest.TestCase):
    def test_template_bands_and_brand_bands_are_preserved(self):
        summary = [
            {"band": 100, "fish_targets": ["アジ"]},
            {"band": 200, "fish_targets": ["アジ", "ブリ"]},
        ]
        template = {
            "bands": [100, 200, 300, 400, 500, 600],
            "brand_bands": {
                "daiwa": [100, 200, 300, 400, 500, 600],
                "shimano": [200, 300, 400, 600],
            },
        }
        out = build_output(summary, template, "runs/tmp/standard-band-summary.json")
        self.assertEqual(out["bands"], [100, 200, 300, 400, 500, 600])
        self.assertEqual(out["brand_bands"]["shimano"], [200, 300, 400, 600])
        self.assertEqual(
            out["target_ranges"],
            [
                {"target": "アジ", "start_band": 100, "end_band": 200},
                {"target": "ブリ", "start_band": 200, "end_band": 200},
            ],
        )

    def test_bands_fallback_to_summary_when_template_missing(self):
        summary = [
            {"band": 200, "fish_targets": ["ブリ"]},
            {"band": 600, "fish_targets": ["キンメダイ"]},
        ]
        out = build_output(summary, None, "runs/tmp/standard-band-summary.json")
        self.assertEqual(out["bands"], [200, 600])
        self.assertEqual(out["brand_bands"], {})


if __name__ == "__main__":
    unittest.main()
