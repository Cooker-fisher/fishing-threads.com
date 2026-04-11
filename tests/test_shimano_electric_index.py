from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.shimano_electric_index import (  # noqa: E402
    build_index_raw,
    extract_item,
    extract_page_no,
    extract_product_nodes,
    parse_html,
    save_index_raw,
)


SAMPLE_HTML = """
<html>
  <body>
    <div>検索結果 19件</div>
    <div class="product-card">
      <img src="/images/fm200.jpg" />
      <div>ForceMaster 200 100,000円 (税別)</div>
      <a href="/products/force-master-200.html">VIEW PRODUCT</a>
    </div>
    <div class="product-card">
      <span>NEW</span>
      <img src="/images/bm3000.jpg" />
      <div>BeastMaster MD 3000 OPEN</div>
      <a href="/products/beast-master-md-3000.html">VIEW PRODUCT</a>
    </div>
    <div class="promo">NEW PRODUCTS <a href="/promo.html">VIEW PRODUCT</a></div>
    <div class="pagination">1 / 2 / NEXT</div>
  </body>
</html>
"""


class ShimanoElectricIndexExtractorTests(unittest.TestCase):
    def test_extract_page_no(self) -> None:
        self.assertEqual(extract_page_no(SAMPLE_HTML), 1)

    def test_extract_product_nodes(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        nodes = extract_product_nodes(soup)
        self.assertEqual(len(nodes), 2)

    def test_extract_item(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        node = extract_product_nodes(soup)[0]
        item = extract_item(node, "https://fish.shimano.com")
        self.assertEqual(item["series_name_or_model_name"], "ForceMaster 200")
        self.assertEqual(item["price_raw"], "100,000円 (税別)")
        self.assertEqual(item["source_url"], "https://fish.shimano.com/products/force-master-200.html")
        self.assertEqual(item["image_url"], "https://fish.shimano.com/images/fm200.jpg")

    def test_save_index_raw(self) -> None:
        payload = build_index_raw(
            source_url="https://fish.shimano.com/ja-JP/product/reel/electricaccessories.html",
            crawl_date="2026-04-11",
            page_no=1,
            items=[{"series_name_or_model_name": "ForceMaster 200", "price_raw": "100,000円 (税別)", "source_url": "https://fish.shimano.com/products/force-master-200.html", "image_url": "https://fish.shimano.com/images/fm200.jpg", "badge_raw": None, "status_raw": None}],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = save_index_raw(payload, tmpdir)
            self.assertTrue(out_path.exists())
            self.assertTrue(str(out_path).endswith("raw/index/shimano/electric/001.json"))


if __name__ == "__main__":
    unittest.main()
