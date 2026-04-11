from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from scripts.extractors.daiwa_electric_index import fetch_html, normalize_ws

SPEC_PATTERN = re.compile(r"製品スペック|SPEC", re.IGNORECASE)
STOP_PATTERN = re.compile(r"(関連製品|おすすめコンテンツ|動画|VIDEO|ダイワテクノロジー)")
PRICE_LABEL_PATTERN = re.compile(r"メーカー希望本体価格")
JAN_LABEL_PATTERN = re.compile(r"JAN")
NOTE_PATTERN = re.compile(r"^(※|注記)")
PRICE_VALUE_PATTERN = re.compile(r"[\d,]+円")


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def find_spec_section(soup: BeautifulSoup) -> Tag:
    for tag in soup.find_all(["h1", "h2", "h3", "div", "span", "p"]):
        text = normalize_ws(tag.get_text(" ", strip=True))
        if text and SPEC_PATTERN.search(text):
            return tag.parent if tag.parent and isinstance(tag.parent, Tag) else tag
    raise ValueError("製品スペック セクションが見つかりません")


def _iter_section_nodes(start: Tag) -> list[Tag]:
    nodes = [start]
    current = start.find_next_sibling()
    steps = 0
    while current is not None and steps < 40:
        steps += 1
        if isinstance(current, Tag):
            text = normalize_ws(current.get_text(" ", strip=True))
            if text and STOP_PATTERN.search(text):
                break
            nodes.append(current)
        current = current.find_next_sibling()
    return nodes


def _collect_lines(nodes: list[Tag]) -> list[str]:
    lines: list[str] = []
    for node in nodes:
        for text in node.stripped_strings:
            line = normalize_ws(str(text))
            if line:
                lines.append(line)
    return lines


def _is_label(line: str) -> bool:
    if not line or NOTE_PATTERN.search(line):
        return False
    if SPEC_PATTERN.search(line) or STOP_PATTERN.search(line):
        return False
    if PRICE_VALUE_PATTERN.fullmatch(line):
        return False
    if re.fullmatch(r"\d{8,20}", line):
        return False
    if re.fullmatch(r"[\d\.]+", line):
        return False
    if re.fullmatch(r"[\dA-Za-z\-\/]+", line):
        return False
    return True


def extract_spec_labels(section: Tag) -> list[str]:
    lines = _collect_lines(_iter_section_nodes(section))
    labels: list[str] = []
    started_values = False
    for line in lines:
        if NOTE_PATTERN.search(line):
            break
        if _is_label(line) and not started_values:
            labels.append(line)
            continue
        if labels:
            started_values = True
        if started_values:
            break
    return labels


def extract_spec_rows(section: Tag) -> list[dict[str, Any]]:
    lines = _collect_lines(_iter_section_nodes(section))
    labels = extract_spec_labels(section)
    if not labels:
        return []

    rows: list[dict[str, Any]] = []
    values_started = False
    values: list[str] = []
    for line in lines:
        if line in labels and not values_started:
            continue
        if NOTE_PATTERN.search(line):
            break
        if labels:
            values_started = True
        if values_started:
            values.append(line)

    col_count = len(labels)
    for i in range(0, len(values), col_count):
        row_values = values[i:i + col_count]
        if len(row_values) < col_count:
            break
        item_name = row_values[0]
        for label, value in zip(labels[1:], row_values[1:]):
            rows.append({
                "section": f"製品スペック:{item_name}",
                "label": label,
                "value": value,
                "unit": None,
                "note": None,
                "source_text": f"{item_name} {label} {value}",
            })
    return rows


def extract_code_fields(spec_rows: list[dict[str, Any]]) -> dict[str, str | None]:
    price_raw = None
    jan_upc_raw = None
    for row in spec_rows:
        label = row.get("label") or ""
        value = row.get("value")
        if PRICE_LABEL_PATTERN.search(label) and price_raw is None:
            price_raw = value
        if JAN_LABEL_PATTERN.search(label) and jan_upc_raw is None:
            jan_upc_raw = value
    return {"price_raw": price_raw, "jan_upc_raw": jan_upc_raw}


def extract_spec_notes(section: Tag) -> list[str]:
    notes: list[str] = []
    seen: set[str] = set()
    for line in _collect_lines(_iter_section_nodes(section)):
        if NOTE_PATTERN.search(line) and line not in seen:
            seen.add(line)
            notes.append(line)
    return notes


def build_spec_payload(price_raw: str | None, jan_upc_raw: str | None, spec_rows_raw: list[dict[str, Any]], notes_raw: list[str]) -> dict[str, Any]:
    return {
        "price_raw": price_raw,
        "sku_raw": None,
        "jan_upc_raw": jan_upc_raw,
        "spec_rows_raw": spec_rows_raw,
        "notes_raw": notes_raw,
    }


def save_spec_payload(data: dict[str, Any], out_dir: str | Path, name: str = "daiwa-electric-spec.json") -> Path:
    out_dir = Path(out_dir)
    target_dir = out_dir / "tmp" / "spec_payloads"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / name
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def run(url: str, out_dir: str | Path) -> Path:
    fetched = fetch_html(url)
    soup = parse_html(fetched.html)
    section = find_spec_section(soup)
    spec_rows = extract_spec_rows(section)
    code_fields = extract_code_fields(spec_rows)
    notes = extract_spec_notes(section)
    payload = build_spec_payload(code_fields["price_raw"], code_fields["jan_upc_raw"], spec_rows, notes)
    return save_spec_payload(payload, out_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DAIWA 電動リール spec raw extractor")
    parser.add_argument("url")
    parser.add_argument("--out-dir", default=".")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    print(run(args.url, args.out_dir))


if __name__ == "__main__":
    main()
