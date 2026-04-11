from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.daiwa_electric_detail import (  # noqa: E402
    build_product_raw,
    extract_breadcrumb_categories,
    extract_main_description,
    extract_main_images,
    extract_notes,
    extract_title_and_price,
    parse_html,
    save_product_raw,
    split_model_fields,
)

SAMPLE_HTML = """
<html>
  <body>
    <nav>Top > 製品情報 > リール > 電動リール > レオブリッツ 400J</nav>
    <section>
      <h1>レオブリッツ 400J LEOBRITZ 400J</h1>
      <div>メーカー希望本体価格 84,400円</div>
      <p>軽さは感度「LIGHT MONSTER 2」</p>
      <p>JAFS基準巻上力11kg、JAFS基準巻上速度190m/分を実現。</p>
      <p>※価格はメーカー希望本体価格です。</p>
      <img src="/images/leobritz400j-main.jpg" alt="レオブリッツ 400J" />
    </section>
    <section>
      <h2>ダイワテクノロジー</h2>
      <p>tech text</p>
    </section>
    <section>
      <h2>製品スペック</h2>
      <p>spec text</p>
    </section>
  </body>
</html>
"""

class DaiwaElectricDetailExtractorTests(unittest.TestCase):
    def test_extract_breadcrumb_categories(self):
        soup = parse_html(SAMPLE_HTML)
        categories = extract_breadcrumb_categories(soup)
        self.assertEqual(categories, ["リール", "電動リール"])

    def test_extract_title_and_price(self):
        soup = parse_html(SAMPLE_HTML)
        result = extract_title_and_price(soup)
        self.assertEqual(result["title"], "レオブリッツ 400J")
        self.assertEqual(result["price_raw"], "84,400円")

    def test_split_model_fields(self):
        fields = split_model_fields("レオブリッツ 400J")
        self.assertEqual(fields["series_name"], "レオブリッツ")
        self.assertEqual(fields["model_name"], "レオブリッツ 400J")
        self.assertEqual(fields["variant_name"], "400J")

    def test_extract_main_description(self):
        soup = parse_html(SAMPLE_HTML)
        description = extract_main_description(soup)
        self.assertTrue(any("JAFS基準巻上力11kg" in line for line in description))
        self.assertFalse(any("tech text" in line for line in description))
        self.assertFalse(any("spec text" in line for line in description))

    def test_extract_notes(self):
        soup = parse_html(SAMPLE_HTML)
        notes = extract_notes(soup)
        self.assertTrue(any(note.startswith("※") for note in notes))

    def test_extract_main_images(self):
        soup = parse_html(SAMPLE_HTML)
        images = extract_main_images(soup, "https://www.daiwa.com")
        self.assertIn("https://www.daiwa.com/images/leobritz400j-main.jpg", images)

    def test_save_product_raw(self):
        payload = build_product_raw(
            source_url="https://www.daiwa.com/jp/product/9806jt3",
            crawl_date="2026-04-11",
            title_fields={"series_name": "レオブリッツ", "model_name": "レオブリッツ 400J", "variant_name": "400J"},
            price_raw="84,400円",
            category_raw=["リール", "電動リール"],
            description_raw=["軽さは感度"],
            notes_raw=["※価格はメーカー希望本体価格です。"],
            image_urls=["https://www.daiwa.com/images/leobritz400j-main.jpg"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = save_product_raw(payload, tmpdir)
            self.assertTrue(out_path.exists())
            self.assertTrue(str(out_path).endswith("raw/products/daiwa/レオブリッツ-400j.json"))

if __name__ == "__main__":
    unittest.main()
