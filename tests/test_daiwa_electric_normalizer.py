"""Tests for scripts/normalizers/electric_reel_minimal.py"""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.normalizers.electric_reel_minimal import (
    is_accessory,
    normalize_items,
    normalize_row,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_item(product_name: str, headers: list[str], rows: list[dict]) -> dict:
    return {
        "product_name": product_name,
        "detail_url": f"https://www.daiwa.com/jp/product/dummy",
        "spec": {"headers": headers, "rows": rows},
    }


_REEL_HEADERS_FULL = [
    "アイテム",
    "標準自重（ｇ）",
    "巻き取り長さ（cm/ハンドル1回転）",
    "ギア比",
    "標準巻糸量ナイロン（号ｰm）",
    "標準巻糸量PE（号ｰm）",
    "ベアリング（ボール/ローラー）",
    "最大ドラグ力（kg）",
    "最大巻上力（kg）",
    "JAFS基準巻上力（kg）",
    "JAFS基準巻上速度（m/分）",
    "メーカー希望本体価格（円）",
    "JAN",
]

# レオブリッツ S400 style: no ナイロン column
_REEL_HEADERS_NO_NYLON = [h for h in _REEL_HEADERS_FULL if h != "標準巻糸量ナイロン（号ｰm）"]

_REMOTE_JOG_HEADERS = [
    "アイテム",
    "標準自重（ｇ）",
    "メーカー希望本体価格（円）",
    "JAN",
]


class TestIsAccessory(unittest.TestCase):
    def test_reel_not_accessory(self):
        item = _make_item("シーボーグ G1800M-RJ", _REEL_HEADERS_FULL, [])
        self.assertFalse(is_accessory(item))

    def test_reel_no_nylon_not_accessory(self):
        """PE-only reel with 12 headers must NOT be classified as accessory."""
        item = _make_item("レオブリッツ S400", _REEL_HEADERS_NO_NYLON, [])
        self.assertFalse(is_accessory(item))

    def test_remote_jog_is_accessory(self):
        """リモート JOG has only 4 headers → accessory."""
        item = _make_item("リモート JOG", _REMOTE_JOG_HEADERS, [])
        self.assertTrue(is_accessory(item))

    def test_empty_spec_is_accessory(self):
        item = {"product_name": "Unknown", "spec": {"headers": [], "rows": []}}
        self.assertTrue(is_accessory(item))


class TestNormalizeRow(unittest.TestCase):
    def test_optional_nylon_absent_becomes_none(self):
        """When ナイロン column is absent from headers, result has None for it."""
        row = {h: "val" for h in _REEL_HEADERS_NO_NYLON}
        result = normalize_row(_REEL_HEADERS_NO_NYLON, row)
        self.assertIn("標準巻糸量ナイロン（号ｰm）", result)
        self.assertIsNone(result["標準巻糸量ナイロン（号ｰm）"])

    def test_nylon_present_preserved(self):
        row = {h: "test" for h in _REEL_HEADERS_FULL}
        row["標準巻糸量ナイロン（号ｰm）"] = "14-1000"
        result = normalize_row(_REEL_HEADERS_FULL, row)
        self.assertEqual(result["標準巻糸量ナイロン（号ｰm）"], "14-1000")


class TestNormalizeItems(unittest.TestCase):
    def test_accessory_excluded(self):
        """リモート JOG must not appear in normalize_items output."""
        reel_row = {h: "x" for h in _REEL_HEADERS_FULL}
        jog_row = {h: "y" for h in _REMOTE_JOG_HEADERS}
        raw_data = {
            "items": [
                _make_item("シーボーグ G1800M-RJ", _REEL_HEADERS_FULL, [reel_row]),
                _make_item("リモート JOG", _REMOTE_JOG_HEADERS, [jog_row]),
            ]
        }
        result = normalize_items(raw_data)
        names = [r["_product_name"] for r in result]
        self.assertIn("シーボーグ G1800M-RJ", names)
        self.assertNotIn("リモート JOG", names)

    def test_no_nylon_reel_included(self):
        """PE-only reel (no ナイロン column) must be included, not skipped."""
        row = {h: "v" for h in _REEL_HEADERS_NO_NYLON}
        raw_data = {"items": [_make_item("レオブリッツ S400", _REEL_HEADERS_NO_NYLON, [row])]}
        result = normalize_items(raw_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["_product_name"], "レオブリッツ S400")
        self.assertIsNone(result[0]["標準巻糸量ナイロン（号ｰm）"])

    def test_variant_rows_all_included(self):
        """Multi-variant products (multiple rows) each become a result entry."""
        rows = [{h: str(i) for h in _REEL_HEADERS_FULL} for i in range(3)]
        raw_data = {"items": [_make_item("シーボーグ 400J/JL", _REEL_HEADERS_FULL, rows)]}
        result = normalize_items(raw_data)
        self.assertEqual(len(result), 3)


if __name__ == "__main__":
    unittest.main()
