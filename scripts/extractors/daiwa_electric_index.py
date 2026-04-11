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

DEFAULT_SOURCE_SITE = "daiwa_official"
DEFAULT_MAKER = "daiwa"
DEFAULT_CATEGORY_RAW = ["リール", "電動リール"]
DEFAULT_CATEGORY_MECHANISM = "electric"
PRICE_PATTERN = re.compile(r"([\d,]+円)")
PAGE_PATTERN = re.compile(r"検索結果\s*0*\d+件\s*（\s*(\d+)～(\d+)件を表示\s*）")


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
    if not match:
        return 1
    start = int(match.group(1))
    return ((start - 1) // 50) + 1


def _find_product_link(anchor: Tag) -> bool:
    text = normalize_ws(anchor.get_text(" ", strip=True))
    return "電動リール" in text and "メーカー希望本体価格" in text


def extract_product_nodes(soup: BeautifulSoup) -> list[Tag]:
    nodes: list[Tag] = []
    seen: set[int] = set()
    for anchor in soup.find_all("a", href=True):
        if not _find_product_link(anchor):
            continue
        parent = anchor
        while parent.parent and isinstance(parent.parent, Tag) and parent.parent.name in {"div", "li", "article"}:
            parent = parent.parent
        node_id = id(parent)
        if node_id in seen:
            continue
        seen.add(node_id)
        nodes.append(parent)
    return nodes


def _extract_price(text: str) -> str | None:
    match = PRICE_PATTERN.search(text)
    return normalize_ws(match.group(1)) if match else None


def _extract_name(text: str, price_raw: str | None) -> str:
    cleaned = text
    cleaned = cleaned.replace("電動リール", " ")
    cleaned = cleaned.replace("メーカー希望本体価格", " ")
    if price_raw:
        cleaned = cleaned.replace(price_raw, " ")
    return normalize_ws(cleaned)


def extract_item(node: Tag, base_url: str) -> dict[str, Any]:
    anchor = None
    for candidate in node.find_all("a", href=True):
        if _find_product_link(candidate):
            anchor = candidate
            break
    if anchor is None:
        raise ValueError("電動リールの商品リンクが見つかりません")

    text = normalize_ws(anchor.get_text(" ", strip=True))
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
        "badge_raw": None,
        "status_raw": None,
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
    payload = build_index_raw(url, crawl_date, page_no, items)
    return save_index_raw(payload, out_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DAIWA 電動リール一覧 raw extractor")
    parser.add_argument("url")
    parser.add_argument("--crawl-date", required=True)
    parser.add_argument("--out-dir", default=".")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    print(run(args.url, args.crawl_date, args.out_dir))


if __name__ == "__main__":
    main()
