from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from scripts.extractors.daiwa_electric_index import normalize_ws

PRICE_KEY = "メーカー希望本体価格（円）"
JAN_KEY = "JAN"


class MiniSoup(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.tokens: list[tuple[str, str]] = []
        self.feed(html)

    def handle_data(self, data: str) -> None:
        text = normalize_ws(data)
        if text:
            self.tokens.append(("text", text))

    def get_text(self, sep: str = " ", strip: bool = True) -> str:
        text = sep.join(t for _, t in self.tokens)
        return normalize_ws(text) if strip else text


def parse_html(html: str) -> MiniSoup:
    return MiniSoup(html)


def find_spec_section(soup: MiniSoup) -> MiniSoup:
    # Minimal implementation for tests: whole page is enough.
    return soup


def extract_spec_rows(section: MiniSoup) -> list[dict[str, Any]]:
    texts = [t for _, t in section.tokens]
    try:
        header_index = texts.index("製品スペック")
    except ValueError:
        return []
    block = texts[header_index + 1 :]
    stop_words = {"関連製品", "ダイワテクノロジー"}
    cut = len(block)
    for i, t in enumerate(block):
        if t in stop_words:
            cut = i
            break
    block = block[:cut]
    labels = []
    i = 0
    while i < len(block) and not re.search(r"\d", block[i]):
        labels.append(block[i])
        i += 1
    rows: list[dict[str, Any]] = []
    while i < len(block):
        item = block[i]
        if item.startswith("※"):
            break
        if i + len(labels) >= len(block):
            break
        values = block[i + 1 : i + 1 + len(labels) - 1]
        if len(values) != len(labels) - 1:
            break
        for label, value in zip(labels[1:], values):
            rows.append({
                "section": f"製品スペック:{item}",
                "label": label,
                "value": value,
                "unit": None,
                "note": None,
                "source_text": f"{item} {label} {value}",
            })
        i += len(labels)
    return rows


def extract_code_fields(rows: list[dict[str, Any]]) -> dict[str, str | None]:
    price_raw = next((r["value"] for r in rows if r["label"] == PRICE_KEY), None)
    jan_raw = next((r["value"] for r in rows if r["label"] == JAN_KEY), None)
    return {"price_raw": price_raw, "jan_upc_raw": jan_raw}


def extract_spec_notes(section: MiniSoup) -> list[str]:
    return [text for _, text in section.tokens if text.startswith("※")]


def build_spec_payload(price_raw: str | None, jan_upc_raw: str | None, spec_rows_raw: list[dict[str, Any]], notes_raw: list[str]) -> dict[str, Any]:
    return {
        "price_raw": price_raw,
        "jan_upc_raw": jan_upc_raw,
        "spec_rows_raw": spec_rows_raw,
        "notes_raw": notes_raw,
    }


def save_spec_payload(payload: dict[str, Any], out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    target = out_dir / "tmp" / "spec_payloads"
    target.mkdir(parents=True, exist_ok=True)
    out_path = target / "daiwa-electric-spec.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
