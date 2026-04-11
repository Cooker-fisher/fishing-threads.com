from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.daiwa_electric_index import build_index_raw, extract_item, extract_page_no, extract_product_nodes, parse_html, save_index_raw

SAMPLE_HTML = """
<html><body>
<div>検索結果 0161件（1～50件を表示）</div>
<div class='product-card'><img src='/images/leobritz400j.jpg' /><a href='/jp/product/9806jt3'>電動リール レオブリッツ 400J メーカー希望本体価格 84,400円</a></div>
<div class='product-card'><img src='/images/seaborg.jpg' /><a href='/jp/product/adbrdfh'>電動リール シーボーグ G1800M-RJ メーカー希望本体価格 374,500円</a></div>
<div class='product-card'><a href='/jp/product/spin123'>スピニングリール ルビアス メーカー希望本体価格 42,000円</a></div>
</body></html>
"""

class DaiwaElectricIndexExtractorTests(unittest.TestCase):
    def test_extract_page_no(self):
        self.assertEqual(extract_page_no(SAMPLE_HTML), 1)

    def test_extract_product_nodes(self):
        soup = parse_html(SAMPLE_HTML)
        self.assertEqual(len(extract_product_nodes(soup)), 2)

    def test_extract_item(self):
        soup = parse_html(SAMPLE_HTML)
        node = extract_product_nodes(soup)[0]
        item = extract_item(node, 'https://www.daiwa.com')
        self.assertEqual(item['series_name_or_model_name'], 'レオブリッツ 400J')
        self.assertEqual(item['price_raw'], '84,400円')
        self.assertEqual(item['source_url'], 'https://www.daiwa.com/jp/product/9806jt3')
        self.assertEqual(item['image_url'], 'https://www.daiwa.com/images/leobritz400j.jpg')

    def test_save_index_raw(self):
        payload = build_index_raw('https://www.daiwa.com/jp/product/productlist?category1=リール', '2026-04-11', 1, [{'series_name_or_model_name': 'レオブリッツ 400J', 'price_raw': '84,400円', 'source_url': 'https://www.daiwa.com/jp/product/9806jt3', 'image_url': 'https://www.daiwa.com/images/leobritz400j.jpg', 'badge_raw': None, 'status_raw': None}])
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = save_index_raw(payload, tmpdir)
            self.assertTrue(out_path.exists())
            self.assertTrue(str(out_path).endswith('raw/index/daiwa/electric/001.json'))

if __name__ == '__main__':
    unittest.main()
