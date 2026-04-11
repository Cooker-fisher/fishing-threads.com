from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.daiwa_electric_spec import (  # noqa: E402
    build_spec_payload,
    extract_code_fields,
    extract_spec_notes,
    extract_spec_rows,
    find_spec_section,
    parse_html,
    save_spec_payload,
)

SAMPLE_HTML = """
<html>
  <body>
    <section>
      <h2>製品スペック</h2>
      <div>アイテム</div>
      <div>標準自重（ｇ）</div>
      <div>ギア比</div>
      <div>メーカー希望本体価格（円）</div>
      <div>JAN</div>
      <div>レオブリッツ 400J</div>
      <div>560</div>
      <div>5.1</div>
      <div>84,400</div>
      <div>4550133434808</div>
      <div>レオブリッツ 300J</div>
      <div>540</div>
      <div>5.1</div>
      <div>83,100</div>
      <div>4550133434815</div>
      <p>※価格はメーカー希望本体価格です。</p>
    </section>
    <section>
      <h2>関連製品</h2>
      <p>stop</p>
    </section>
  </body>
</html>
"""

class DaiwaElectricSpecExtractorTests(unittest.TestCase):
    def test_find_spec_section(self):
        soup = parse_html(SAMPLE_HTML)
        section = find_spec_section(soup)
        self.assertIn("製品スペック", section.get_text(" ", strip=True))

    def test_extract_spec_rows(self):
        soup = parse_html(SAMPLE_HTML)
        section = find_spec_section(soup)
        rows = extract_spec_rows(section)
        self.assertTrue(any(r["section"] == "製品スペック:レオブリッツ 400J" for r in rows))
        self.assertTrue(any(r["label"] == "ギア比" and r["value"] == "5.1" for r in rows))

    def test_extract_code_fields(self):
        soup = parse_html(SAMPLE_HTML)
        section = find_spec_section(soup)
        rows = extract_spec_rows(section)
        fields = extract_code_fields(rows)
        self.assertEqual(fields["price_raw"], "84,400")
        self.assertEqual(fields["jan_upc_raw"], "4550133434808")

    def test_extract_notes(self):
        soup = parse_html(SAMPLE_HTML)
        section = find_spec_section(soup)
        notes = extract_spec_notes(section)
        self.assertTrue(any(note.startswith("※") for note in notes))

    def test_save_spec_payload(self):
        payload = build_spec_payload(
            price_raw="84,400",
            jan_upc_raw="4550133434808",
            spec_rows_raw=[{"section": "製品スペック:レオブリッツ 400J", "label": "ギア比", "value": "5.1", "unit": None, "note": None, "source_text": "レオブリッツ 400J ギア比 5.1"}],
            notes_raw=["※価格はメーカー希望本体価格です。"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = save_spec_payload(payload, tmpdir)
            self.assertTrue(out_path.exists())
            self.assertTrue(str(out_path).endswith("tmp/spec_payloads/daiwa-electric-spec.json"))

if __name__ == "__main__":
    unittest.main()
