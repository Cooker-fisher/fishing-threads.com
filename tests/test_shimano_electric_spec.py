from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.shimano_electric_spec import (  # noqa: E402
    build_spec_payload,
    build_spec_rows,
    extract_code_fields,
    extract_spec_labels,
    extract_spec_notes,
    extract_spec_price,
    extract_spec_values,
    find_spec_section,
    parse_html,
    save_spec_payload,
)


SAMPLE_HTML = """
<html>
  <body>
    <section>
      <h2>SPECIFICATION スペック表</h2>
      <div>品番</div>
      <div>ギア比</div>
      <div>最大ドラグ力</div>
      <div>商品コード</div>
      <div>JANコード</div>
      <div>MD3000</div>
      <div>4.6</div>
      <div>25kg</div>
      <div>123456</div>
      <div>4969363123456</div>
      <p>注記</p>
      <p>※画像はイメージです。</p>
      <p>※仕様は参考値です。</p>
    </section>
    <section>
      <h2>RELATED INFORMATION 関連情報</h2>
      <a href="/related">related</a>
    </section>
    <div>170,200 円 (税別)</div>
  </body>
</html>
"""


SAMPLE_HTML_WITH_EXTRA_TEXT = """
<html>
  <body>
    <section>
      <h2>SPECIFICATION スペック表</h2>
      <div>品番</div>
      <div>ギア比</div>
      <div>最大ドラグ力</div>
      <div>商品コード</div>
      <div>JANコード</div>
      <div>MD3000</div>
      <div>4.6</div>
      <div>25kg</div>
      <div>123456</div>
      <div>4969363123456</div>
      <div>シマノ巻上力 38kg</div>
      <p>注記</p>
      <p>※商品コードは改定される場合があります。</p>
    </section>
  </body>
</html>
"""


class ShimanoElectricSpecExtractorTests(unittest.TestCase):
    def test_find_spec_section(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        section = find_spec_section(soup)
        self.assertIn("SPECIFICATION", section.get_text(" ", strip=True))

    def test_extract_labels_and_values(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        section = find_spec_section(soup)
        labels = extract_spec_labels(section)
        values = extract_spec_values(section, labels)
        self.assertEqual(labels[:5], ["品番", "ギア比", "最大ドラグ力", "商品コード", "JANコード"])
        self.assertEqual(values[:5], ["MD3000", "4.6", "25kg", "123456", "4969363123456"])
        self.assertNotIn("related", " ".join(values).lower())

    def test_extract_values_stops_before_notes(self) -> None:
        soup = parse_html(SAMPLE_HTML_WITH_EXTRA_TEXT)
        section = find_spec_section(soup)
        labels = extract_spec_labels(section)
        values = extract_spec_values(section, labels)
        self.assertEqual(len(labels), 5)
        self.assertEqual(len(values), 5)
        self.assertNotIn("シマノ巻上力 38kg", values)

    def test_build_rows_and_code_fields(self) -> None:
        rows = build_spec_rows(
            ["品番", "商品コード", "JANコード"],
            ["MD3000", "123456", "4969363123456"],
        )
        codes = extract_code_fields(rows)
        self.assertEqual(codes["sku_raw"], "123456")
        self.assertEqual(codes["jan_upc_raw"], "4969363123456")

    def test_extract_notes(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        section = find_spec_section(soup)
        notes = extract_spec_notes(section)
        self.assertTrue(any(note.startswith("注記") for note in notes))
        self.assertTrue(any(note.startswith("※") for note in notes))

    def test_extract_price(self) -> None:
        soup = parse_html(SAMPLE_HTML)
        self.assertEqual(extract_spec_price(soup), "170,200 円 (税別)")

    def test_save_spec_payload(self) -> None:
        payload = build_spec_payload(
            price_raw="170,200 円 (税別)",
            sku_raw="123456",
            jan_upc_raw="4969363123456",
            spec_rows_raw=[{"section": "スペック表", "label": "ギア比", "value": "4.6", "unit": None, "note": None, "source_text": "ギア比 4.6"}],
            notes_raw=["※画像はイメージです。"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = save_spec_payload(payload, tmpdir)
            self.assertTrue(out_path.exists())
            self.assertTrue(str(out_path).endswith("tmp/spec_payloads/shimano-electric-spec.json"))


if __name__ == "__main__":
    unittest.main()
