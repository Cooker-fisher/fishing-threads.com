from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag

DEFAULT_SOURCE_SITE = "shimano_official"
DEFAULT_MAKER = "shimano"
DEFAULT_CATEGORY_RAW = ["リール", "電動"]
DEFAULT_CATEGORY_MECHANISM = "electric"
PRICE_PATTERN = re.compile(r"(OPEN|[\d,]+\s*円\s*\(税別\)|[\d,]+\s*円)")
STATUS_PATTERN = re.compile(r"(生産終了|在庫なし|SOLD OUT|入荷待ち)")
BADGE_PATTERN = re.compile(r"\b(NEW|NEW!|NEW PRODUCT)\b")
PAGE_PATTERN = re.compile(r"\b(\d+)\s*/\s*\d+\s*/\s*NEXT\b", re.IGNORECASE)

@dataclass
class FetchResult:
    url: str
    html: str

def fetch_html(url: str, timeout: int = 20) -> FetchResult:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TsuriThreadsBot/0.1)"})
    with urlopen(request, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="replace")
    return FetchResult(url=url, html=html)

def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")

def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def extract_page_no(html: str) -> int:
    text = normalize_ws(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    match = PAGE_PATTERN.search(text)
    return int(match.group(1)) if match else 1

def _candidate_block(anchor: Tag) -> Tag:
    current = anchor
    while current.parent and isinstance(current.parent, Tag):
        parent = current.parent
        if parent.name in {"article", "li", "section"}:
            return parent
        if parent.name == "div":
            parent_text = normalize_ws(parent.get_text(" ", strip=True))
            if len(parent_text) > len(normalize_ws(anchor.get_text(" ", strip=True))) + 20:
                return parent
        current = parent
    return anchor

def extract_product_nodes(soup: BeautifulSoup) -> list[Tag]:
    nodes: list[Tag] = []
    seen: set[int] = set()
    for anchor in soup.find_all("a", href=True):
        anchor_text = normalize_ws(anchor.get_text(" ", strip=True))
        if "VIEW PRODUCT" not in anchor_text.upper():
            continue
        href = (anchor.get("href") or "").strip()
        if not href or href in {"#", "/"}:
            continue
        block = _candidate_block(anchor)
        block_text = normalize_ws(block.get_text(" ", strip=True))
        if "NEW PRODUCTS" in block_text.upper() or "SPECIAL SITE" in block_text.upper():
            continue
        if "VIEW PRODUCT" not in block_text.upper():
            continue
        block_id = id(block)
        if block_id in seen:
            continue
        seen.add(block_id)
        nodes.append(block)
    return nodes

def _extract_price(text: str) -> str | None:
    match = PRICE_PATTERN.search(text)
    return normalize_ws(match.group(1)) if match else None

def _extract_badge(text: str) -> str | None:
    match = BADGE_PATTERN.search(text)
    return match.group(1) if match else None

def _extract_status(text: str) -> str | None:
    match = STATUS_PATTERN.search(text)
    return match.group(1) if match else None

def _extract_name(text: str, price_raw: str | None) -> str:
    cleaned = text.replace("VIEW PRODUCT", " ")
    if price_raw:
        cleaned = cleaned.split(price_raw, 1)[0]
    cleaned = BADGE_PATTERN.sub(" ", cleaned)
    cleaned = STATUS_PATTERN.sub(" ", cleaned)
    return normalize_ws(cleaned)

def extract_item(node: Tag, base_url: str) -> dict[str, Any]:
    text = normalize_ws(node.get_text(" ", strip=True))
    anchor = None
    for candidate in node.find_all("a", href=True):
        if "VIEW PRODUCT" in normalize_ws(candidate.get_text(" ", strip=True)).upper():
            anchor = candidate
            break
    if anchor is None:
        raise ValueError("VIEW PRODUCT を含む商品リンクが見つかりません")
    href = anchor.get("href") or ""
    source_url = urljoin(base_url, href)
    price_raw = _extract_price(text)
    image = node.find("img")
    image_url = urljoin(base_url, image.get("src")) if image and image.get("src") else None
    return {
        "series_name_or_model_name": _extract_name(text, price_raw),
        "price_raw": price_raw,
        "source_url": source_url,
        "image_url": image_url,
        "badge_raw": _extract_badge(text),
        "status_raw": _extract_status(text),
    }

def build_index_raw(source_url: str, crawl_date: str, page_no: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_site": DEFAULT_SOURCE_SITE,
        "source_url": source_url,
        "crawl_date": crawl_date,
        "maker": DEFAULT_MAKER,
        "category_raw": DEFAULT_CATEGORY_RAW,
        "category_mechanism": DEFAULT_CATEGORY_MECHANISM,
        "page_no": page_no,
        "items": items,
    }

def save_index_raw(data: dict[str, Any], out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    target_dir = out_dir / "raw" / "index" / DEFAULT_MAKER / DEFAULT_CATEGORY_MECHANISM
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{int(data['page_no']):03}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path

def run(url: str, crawl_date: str, out_dir: str | Path) -> Path:
    fetched = fetch_html(url)
    soup = parse_html(fetched.html)
    page_no = extract_page_no(fetched.html)
    items = [extract_item(node, url) for node in extract_product_nodes(soup)]
    return save_index_raw(build_index_raw(url, crawl_date, page_no, items), out_dir)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shimano 電動リール一覧 raw extractor")
    parser.add_argument("url")
    parser.add_argument("--crawl-date", required=True)
    parser.add_argument("--out-dir", default=".")
    return parser

def main() -> None:
    args = build_arg_parser().parse_args()
    print(run(args.url, args.crawl_date, args.out_dir))

if __name__ == "__main__":
    main()
