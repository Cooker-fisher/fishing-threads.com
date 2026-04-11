from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from scripts.extractors.daiwa_electric_index import fetch_html, normalize_ws

DEFAULT_SOURCE_SITE = "daiwa_official"
DEFAULT_MAKER = "daiwa"
DEFAULT_BRAND = "daiwa"
DEFAULT_CATEGORY_MECHANISM = "electric"
DEFAULT_SCHEMA_VERSION = "raw-reel-v1"
DEFAULT_EXTRACTOR_VERSION = "v1"
PRICE_PATTERN = re.compile(r"([\d,]+円)")
NOTE_PATTERN = re.compile(r"^(※|\*|注記)")
STOP_PATTERN = re.compile(r"(ダイワテクノロジー|製品詳細|製品スペック|スペック|RELATED|VIDEO)")
ASCII_PRODUCT_PATTERN = re.compile(r"^[A-Z0-9\-\s]+$")
VARIANT_PATTERN = re.compile(r"([A-Z]*\d+[A-Z\-]*)$")


class MiniSoup(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.raw_html = html
        self.tokens: list[tuple[str, dict[str, str], str]] = []
        self._tag_stack: list[tuple[str, dict[str, str]]] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append((tag, {k: v or "" for k, v in attrs}))

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        text = normalize_ws(data)
        if not text:
            return
        if self._tag_stack:
            tag, attrs = self._tag_stack[-1]
        else:
            tag, attrs = "text", {}
        self.tokens.append((tag, attrs, text))


def parse_html(html: str) -> MiniSoup:
    return MiniSoup(html)


def extract_breadcrumb_categories(soup: MiniSoup) -> list[str]:
    text = normalize_ws(" ".join(t[2] for t in soup.tokens))
    categories: list[str] = []
    for candidate in ["リール", "電動リール"]:
        if candidate in text and candidate not in categories:
            categories.append(candidate)
    return categories


def _normalize_title(text: str) -> str:
    text = normalize_ws(text)
    if not text:
        return text
    parts = text.split(" ")
    jp_parts: list[str] = []
    for part in parts:
        if ASCII_PRODUCT_PATTERN.fullmatch(part) and not re.search(r"\d", part):
            break
        jp_parts.append(part)
    normalized = normalize_ws(" ".join(jp_parts)) if jp_parts else text
    return normalized


def _find_product_title(soup: MiniSoup) -> str:
    for tag, _, text in soup.tokens:
        if tag not in {"h1", "h2"}:
            continue
        if text and not STOP_PATTERN.search(text):
            return _normalize_title(text)
    raise ValueError("商品名が見つかりません")


def extract_title_and_price(soup: MiniSoup) -> dict[str, str | None]:
    title = _find_product_title(soup)
    page_text = normalize_ws(" ".join(t[2] for t in soup.tokens))
    match = PRICE_PATTERN.search(page_text)
    return {"title": title, "price_raw": normalize_ws(match.group(1)) if match else None}


def split_model_fields(title: str) -> dict[str, str | None]:
    title = normalize_ws(title)
    match = VARIANT_PATTERN.search(title)
    if match:
        variant = normalize_ws(match.group(1))
        base = normalize_ws(title[: match.start(1)]).rstrip("-").strip()
        return {"series_name": base or title, "model_name": title, "variant_name": variant}
    return {"series_name": title, "model_name": title, "variant_name": None}


def extract_main_description(soup: MiniSoup) -> list[str]:
    texts: list[str] = []
    seen: set[str] = set()
    for tag, _, text in soup.tokens:
        if tag not in {"p", "div"}:
            continue
        if NOTE_PATTERN.search(text) or PRICE_PATTERN.search(text):
            continue
        if STOP_PATTERN.search(text):
            break
        if len(text) < 12:
            continue
        if text not in seen:
            seen.add(text)
            texts.append(text)
        if len(texts) >= 3:
            break
    return texts


def extract_notes(soup: MiniSoup) -> list[str]:
    notes: list[str] = []
    seen: set[str] = set()
    for _, _, text in soup.tokens:
        if NOTE_PATTERN.search(text) or "注意" in text:
            if text not in seen:
                seen.add(text)
                notes.append(text)
    return notes


def extract_main_images(soup: MiniSoup, base_url: str) -> list[str]:
    srcs = re.findall(r'<img[^>]*src=["\']([^"\']+)', soup.raw_html, flags=re.IGNORECASE)
    images: list[str] = []
    seen: set[str] = set()
    for src in srcs:
        full = urljoin(base_url, src)
        if full not in seen:
            seen.add(full)
            images.append(full)
        if len(images) >= 3:
            break
    return images


def build_product_slug(fields: dict[str, str | None]) -> str:
    parts = [fields.get("series_name") or "daiwa", fields.get("variant_name") or ""]
    slug = "-".join(p for p in parts if p)
    slug = slug.lower().replace("/", "-")
    slug = re.sub(r"[^a-z0-9ぁ-んァ-ヶ一-龠ー\-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "daiwa-product"


def build_product_raw(source_url: str, crawl_date: str, title_fields: dict[str, str | None], price_raw: str | None, category_raw: list[str], description_raw: list[str], notes_raw: list[str], image_urls: list[str]) -> dict[str, Any]:
    slug = build_product_slug(title_fields)
    return {
        "id": f"{DEFAULT_MAKER}-{slug}", "maker": DEFAULT_MAKER, "brand": DEFAULT_BRAND,
        "source_site": DEFAULT_SOURCE_SITE, "source_url": source_url, "source_hash": None,
        "crawl_date": crawl_date, "extractor_version": DEFAULT_EXTRACTOR_VERSION, "schema_version": DEFAULT_SCHEMA_VERSION,
        "category_raw": category_raw or ["リール", "電動リール"], "category_mechanism": DEFAULT_CATEGORY_MECHANISM,
        "category_usage": [], "water_type": "unknown", "series_name": title_fields.get("series_name"),
        "model_name": title_fields.get("model_name"), "variant_name": title_fields.get("variant_name"),
        "price_raw": price_raw, "sku_raw": None, "jan_upc_raw": None, "status_raw": None,
        "description_raw": description_raw, "notes_raw": notes_raw, "image_urls": image_urls, "spec_rows_raw": [],
        "subtype": {"reel_type": "electric", "electric_raw": {}, "spinning_raw": None, "bait_raw": None, "conventional_raw": None, "lever_brake_raw": None, "fly_raw": None},
        "extra": {"technology_labels": [], "movie_links": [], "manual_links": [], "compatibility_links": [], "awards": [], "campaign_tags": [], "feature_section_titles": [], "hero_copy": []},
    }


def save_product_raw(data: dict[str, Any], out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    target_dir = out_dir / "raw" / "products" / DEFAULT_MAKER
    target_dir.mkdir(parents=True, exist_ok=True)
    product_slug = data["id"].replace(f"{DEFAULT_MAKER}-", "", 1)
    out_path = target_dir / f"{product_slug}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def run(url: str, crawl_date: str, out_dir: str | Path) -> Path:
    fetched = fetch_html(url)
    soup = parse_html(fetched.html)
    categories = extract_breadcrumb_categories(soup)
    title_price = extract_title_and_price(soup)
    title_fields = split_model_fields(title_price["title"] or "")
    description_raw = extract_main_description(soup)
    notes_raw = extract_notes(soup)
    image_urls = extract_main_images(soup, url)
    payload = build_product_raw(url, crawl_date, title_fields, title_price["price_raw"], categories, description_raw, notes_raw, image_urls)
    return save_product_raw(payload, out_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DAIWA 電動リール詳細 raw extractor")
    parser.add_argument("url")
    parser.add_argument("--crawl-date", required=True)
    parser.add_argument("--out-dir", default=".")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    print(run(args.url, args.crawl_date, args.out_dir))


if __name__ == "__main__":
    main()
