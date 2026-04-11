from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.shimano_electric_pipeline import (  # noqa: E402
    collect_detail_urls_from_index,
    merge_spec_into_product_raw,
    save_json,
    load_json,
)


class ShimanoElectricPipelineTests(unittest.TestCase):
    def test_collect_detail_urls_from_index(self) -> None:
        index_raw = {
            "items": [
                {"source_url": "https://example.com/a"},
                {"source_url": "https://example.com/b"},
                {"source_url": "https://example.com/a"},
            ]
        }
        self.assertEqual(
            collect_detail_urls_from_index(index_raw),
            ["https://example.com/a", "https://example.com/b"],
        )

    def test_merge_spec_into_product_raw(self) -> None:
        product_raw = {
            "price_raw": "170,200 円 (税別)",
            "sku_raw": None,
            "jan_upc_raw": None,
            "spec_rows_raw": [],
            "notes_raw": ["※画像はイメージです。"],
        }
        spec_payload = {
            "price_raw": "170,200 円 (税別)",
            "sku_raw": "123456",
            "jan_upc_raw": "4969363123456",
            "spec_rows_raw": [{"label": "ギア比", "value": "4.6"}],
            "notes_raw": ["※仕様は参考値です。"],
        }
        merged = merge_spec_into_product_raw(product_raw, spec_payload)
        self.assertEqual(merged["sku_raw"], "123456")
        self.assertEqual(merged["jan_upc_raw"], "4969363123456")
        self.assertEqual(len(merged["spec_rows_raw"]), 1)
        self.assertEqual(len(merged["notes_raw"]), 2)

    def test_save_and_load_json(self) -> None:
        payload = {"a": 1}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            save_json(path, payload)
            loaded = load_json(path)
            self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()
