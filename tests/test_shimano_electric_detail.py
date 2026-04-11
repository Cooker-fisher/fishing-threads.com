from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.shimano_electric_detail import (  # noqa: E402
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
    <nav>製品情報 > リール > 電動 > ビーストマスター MD 3000</nav>
    <section>
      <h1>ビーストマスター MD 3000</h1>
      <div>170,200 円 (税別)</div>
      <p>ギガマックスモーター搭載。</p>
      <p>大物狙いの船釣りに対応する高出力モデル。</p>
      <p>※画像はイメージです。</p>
      <p>電源は専用バッテリーを使用してください。</p>
      <img src="/images/beastmaster-main.jpg" alt="ビーストマスター MD 3000" />
    </section>
    <section>
      <h2>CONCEPT MOVIE</h2>
      <p>movie text</p>
      <img src="/images/movie-thumb.jpg" alt="movie" />
    </section>
  </body>
</html>
"""

class ShimanoElectricDetailExtractorTests(unittest.TestCase):
    def test_extract_breadcrumb_categories(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        categories = extract_breadcrumb_categories(soup)
        self.assertEqual(categories, ["リール", "電動"])

    def test_extract_title_and_price(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        result = extract_title_and_price(soup)
        self.assertEqual(result["title"], "ビーストマスター MD 3000")
        self.assertEqual(result["price_raw"], "170,200 円 (税別)")

    def test_split_model_fields(self) -> None:
        fields = split_model_fields("ビーストマスター MD 3000")
        self.assertEqual(fields["series_name"], "ビーストマスター MD")
        self.assertEqual(fields["variant_name"], "3000")

    def test_extract_main_description(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        description = extract_main_description(soup)
        self.assertTrue(any("ギガマックスモーター" in line for line in description))
        self.assertFalse(any("movie text" in line for line in description))

    def test_extract_notes(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        notes = extract_notes(soup)
        self.assertTrue(any(note.startswith("※") for note in notes))
        self.assertTrue(any("電源" in note for note in notes))

    def test_extract_main_images(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        images = extract_main_images(soup, "https://fish.shimano.com")
        self.assertIn("https://fish.shimano.com/images/beastmaster-main.jpg", images)
        self.assertNotIn("https://fish.shimano.com/images/movie-thumb.jpg", images)

    def test_save_product_raw(self) -> None:
        payload = build_product_raw(
            source_url="https://fish.shimano.com/ja-JP/product/reel/electricaccessories/a075f00003u1bmwqau.html",
            crawl_date="2026-04-11",
            title_fields={"series_name": "ビーストマスター MD", "model_name": "ビーストマスター MD", "variant_name": "3000"},
            price_raw="170,200 円 (税別)",
            category_raw=["リール", "電動"],
            description_raw=["ギガマックスモーター搭載。"],
            notes_raw=["※画像はイメージです。"],
            image_urls=["https://fish.shimano.com/images/beastmaster-main.jpg"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = save_product_raw(payload, tmpdir)
            self.assertTrue(out_path.exists())
            self.assertTrue(str(out_path).endswith("raw/products/shimano/ビーストマスター-md-3000.json"))

if __name__ == "__main__":
    unittest.main()
