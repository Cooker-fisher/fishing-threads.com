from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.daiwa_electric_pipeline import (  # noqa: E402
    collect_detail_urls_from_index,
    load_json,
    merge_spec_into_product_raw,
    save_json,
)


class DaiwaElectricPipelineTests(unittest.TestCase):
    def test_collect_detail_urls_from_index(self):
        index_raw = {
            "items": [
                {"source_url": "https://www.daiwa.com/jp/product/9806jt3"},
                {"source_url": "https://www.daiwa.com/jp/product/adbrdfh"},
                {"source_url": "https://www.daiwa.com/jp/product/9806jt3"},
            ]
        }
        self.assertEqual(
            collect_detail_urls_from_index(index_raw),
            [
                "https://www.daiwa.com/jp/product/9806jt3",
                "https://www.daiwa.com/jp/product/adbrdfh",
            ],
        )

    def test_merge_spec_into_product_raw(self):
        product_raw = {
            "price_raw": "84,400円",
            "sku_raw": None,
            "jan_upc_raw": None,
            "spec_rows_raw": [],
            "notes_raw": ["※本文注記"],
        }
        spec_payload = {
            "price_raw": "84,400",
            "sku_raw": None,
            "jan_upc_raw": "4550133434808",
            "spec_rows_raw": [{"label": "ギア比", "value": "5.1"}],
            "notes_raw": ["※spec注記"],
        }
        merged = merge_spec_into_product_raw(product_raw, spec_payload)
        self.assertEqual(merged["price_raw"], "84,400")
        self.assertEqual(merged["jan_upc_raw"], "4550133434808")
        self.assertEqual(len(merged["spec_rows_raw"]), 1)
        self.assertEqual(len(merged["notes_raw"]), 2)

    def test_save_and_load_json(self):
        payload = {"a": 1}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            save_json(path, payload)
            loaded = load_json(path)
            self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()
