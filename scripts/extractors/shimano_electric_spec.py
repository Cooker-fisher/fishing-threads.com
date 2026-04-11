from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from scripts.extractors.shimano_electric_index import fetch_html, normalize_ws


SPEC_SECTION_PATTERN = re.compile(r"SPECIFICATION\s*スペック表|スペック表", re.IGNORECASE)
RELATED_PATTERN = re.compile(r"RELATED INFORMATION|関連情報", re.IGNORECASE)
NOTE_PATTERN = re.compile(r"^(注記|※|\*)")
PRICE_PATTERN = re.compile(r"([\d,]+\s*円\s*\(税別\)|[\d,]+\s*円|OPEN)")


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _find_heading_node(soup: BeautifulSoup) -> Tag:
    for tag in soup.find_all(["h1", "h2", "h3", "div", "span", "p"]):
        text = normalize_ws(tag.get_text(" ", strip=True))
        if text and SPEC_SECTION_PATTERN.search(text):
            return tag
    raise ValueError("SPECIFICATION スペック表 セクションが見つかりません")


def find_spec_section(soup: BeautifulSoup) -> Tag:
    heading = _find_heading_node(soup)
    current = heading.parent if heading.parent and isinstance(heading.parent, Tag) else heading
    return current


def _iter_until_related(start: Tag) -> list[Tag]:
    nodes: list[Tag] = [start]
    current = start.find_next_sibling()
    steps = 0
    while current is not None and steps < 30:
        steps += 1
        if isinstance(current, Tag):
            text = normalize_ws(current.get_text(" ", strip=True))
            if text and RELATED_PATTERN.search(text):
                break
            nodes.append(current)
        current = current.find_next_sibling()
    return nodes


def _collect_lines(nodes: list[Tag]) -> list[str]:
    lines: list[str] = []
    for node in nodes:
        for text in node.stripped_strings:
            value = normalize_ws(str(text))
            if value:
                lines.append(value)
    return lines


def _is_label(line: str) -> bool:
    if not line:
        return False
    if NOTE_PATTERN.search(line):
        return False
    if SPEC_SECTION_PATTERN.search(line) or RELATED_PATTERN.search(line):
        return False
    if PRICE_PATTERN.search(line):
        return False
    if re.fullmatch(r"[\d,\.\-/:a-zA-Z\s()]+", line):
        return False
    return True


def _is_value(line: str) -> bool:
    if not line:
        return False
    if NOTE_PATTERN.search(line):
        return False
    if SPEC_SECTION_PATTERN.search(line) or RELATED_PATTERN.search(line):
        return False
    return True


def _extract_content_lines(section: Tag) -> list[str]:
    nodes = _iter_until_related(section)
    lines = _collect_lines(nodes)
    return [line for line in lines if not SPEC_SECTION_PATTERN.search(line)]


def _split_label_value_blocks(lines: list[str]) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    values: list[str] = []
    started_values = False

    for line in lines:
        if NOTE_PATTERN.search(line):
            break
        if not started_values:
            if _is_label(line):
                labels.append(line)
                continue
            if labels and _is_value(line):
                started_values = True
                values.append(line)
                continue
            continue

        if _is_value(line):
            values.append(line)
            if labels and len(values) >= len(labels):
                break

    return labels, values


def extract_spec_labels(section: Tag) -> list[str]:
    lines = _extract_content_lines(section)
    labels, _ = _split_label_value_blocks(lines)
    return labels


def extract_spec_values(section: Tag, labels: list[str]) -> list[str]:
    lines = _extract_content_lines(section)
    parsed_labels, values = _split_label_value_blocks(lines)
    if labels and parsed_labels[: len(labels)] == labels:
        return values[: len(labels)]
    return values[: len(parsed_labels)]


def build_spec_rows(labels: list[str], values: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, value in zip(labels, values):
        rows.append(
            {
                "section": "スペック表",
                "label": label,
                "value": value,
                "unit": None,
                "note": None,
                "source_text": f"{label} {value}",
            }
        )
    return rows


def extract_code_fields(spec_rows: list[dict[str, Any]]) -> dict[str, str | None]:
    sku_raw = None
    jan_upc_raw = None
    for row in spec_rows:
        label = row.get("label") or ""
        value = row.get("value")
        if "商品コード" in label:
            sku_raw = value
        if "JANコード" in label:
            jan_upc_raw = value
    return {"sku_raw": sku_raw, "jan_upc_raw": jan_upc_raw}


def extract_spec_notes(section: Tag) -> list[str]:
    nodes = _iter_until_related(section)
    notes: list[str] = []
    seen: set[str] = set()
    for node in nodes:
        for text in node.stripped_strings:
            line = normalize_ws(str(text))
            if NOTE_PATTERN.search(line) and line not in seen:
                seen.add(line)
                notes.append(line)
    return notes


def extract_spec_price(soup: BeautifulSoup) -> str | None:
    text = normalize_ws(soup.get_text(" ", strip=True))
    match = PRICE_PATTERN.search(text)
    return normalize_ws(match.group(1)) if match else None


def build_spec_payload(
    price_raw: str | None,
    sku_raw: str | None,
    jan_upc_raw: str | None,
    spec_rows_raw: list[dict[str, Any]],
    notes_raw: list[str],
) -> dict[str, Any]:
    return {
        "price_raw": price_raw,
        "sku_raw": sku_raw,
        "jan_upc_raw": jan_upc_raw,
        "spec_rows_raw": spec_rows_raw,
        "notes_raw": notes_raw,
    }


def save_spec_payload(data: dict[str, Any], out_dir: str | Path, name: str = "shimano-electric-spec.json") -> Path:
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
    labels = extract_spec_labels(section)
    values = extract_spec_values(section, labels)
    spec_rows = build_spec_rows(labels, values)
    code_fields = extract_code_fields(spec_rows)
    notes = extract_spec_notes(section)
    price_raw = extract_spec_price(soup)
    payload = build_spec_payload(
        price_raw=price_raw,
        sku_raw=code_fields["sku_raw"],
        jan_upc_raw=code_fields["jan_upc_raw"],
        spec_rows_raw=spec_rows,
        notes_raw=notes,
    )
    return save_spec_payload(payload, out_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shimano 電動リール spec表 raw extractor")
    parser.add_argument("url", help="Shimano 電動リール spec表ページ URL")
    parser.add_argument("--out-dir", default=".", help="出力先ディレクトリ")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    output = run(url=args.url, out_dir=args.out_dir)
    print(output)


if __name__ == "__main__":
    main()
