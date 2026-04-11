from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from scripts.extractors.shimano_electric_index import fetch_html, normalize_ws


DEFAULT_SOURCE_SITE = "shimano_official"
DEFAULT_MAKER = "shimano"
DEFAULT_BRAND = "shimano"
DEFAULT_CATEGORY_MECHANISM = "electric"
DEFAULT_SCHEMA_VERSION = "raw-reel-v1"
DEFAULT_EXTRACTOR_VERSION = "v1"
PRICE_PATTERN = re.compile(r"([\d,]+\s*円\s*\(税別\)|[\d,]+\s*円|OPEN)")
NOTE_PATTERN = re.compile(r"^(※|\*|注記)")
HEADING_SKIP_PATTERN = re.compile(
    r"(CONCEPT MOVIE|KEY FEATURE|FEATURE|MOVIE|LINE UP|LINEUP|SPECIFICATION|RELATED INFORMATION)",
    re.IGNORECASE,
)


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def extract_breadcrumb_categories(soup: BeautifulSoup) -> list[str]:
    text = normalize_ws(soup.get_text(" ", strip=True))
    categories: list[str] = []
    for candidate in ["リール", "電動"]:
        if candidate in text and candidate not in categories:
            categories.append(candidate)
    return categories


def _find_product_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find(["h1", "h2"], string=True)
    if title_tag:
        title = normalize_ws(title_tag.get_text(" ", strip=True))
        if title and not HEADING_SKIP_PATTERN.search(title):
            return title

    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = normalize_ws(tag.get_text(" ", strip=True))
        if text and not HEADING_SKIP_PATTERN.search(text) and not PRICE_PATTERN.search(text):
            return text
    raise ValueError("商品名の見出しが見つかりません")


def extract_title_and_price(soup: BeautifulSoup) -> dict[str, str | None]:
    title = _find_product_title(soup)
    price_raw: str | None = None

    title_tag = soup.find(string=re.compile(re.escape(title)))
    if title_tag and isinstance(title_tag.parent, Tag):
        nearby = title_tag.parent.parent if title_tag.parent.parent else title_tag.parent
        nearby_text = normalize_ws(nearby.get_text(" ", strip=True))
        match = PRICE_PATTERN.search(nearby_text)
        if match:
            price_raw = normalize_ws(match.group(1))

    if price_raw is None:
        page_text = normalize_ws(soup.get_text(" ", strip=True))
        match = PRICE_PATTERN.search(page_text)
        if match:
            price_raw = normalize_ws(match.group(1))

    return {"title": title, "price_raw": price_raw}


def split_model_fields(title: str) -> dict[str, str | None]:
    match = re.match(r"^(.*?)(?:\s+|\-)?(\d{2,5}[A-Za-z]*)$", title)
    if match:
        base = normalize_ws(match.group(1))
        variant = normalize_ws(match.group(2))
        return {
            "series_name": base,
            "model_name": base,
            "variant_name": variant,
        }
    return {
        "series_name": title,
        "model_name": title,
        "variant_name": None,
    }


def extract_main_description(soup: BeautifulSoup) -> list[str]:
    title = _find_product_title(soup)
    texts: list[str] = []
    seen: set[str] = set()

    title_node = soup.find(string=re.compile(re.escape(title)))
    if title_node and isinstance(title_node.parent, Tag):
        current: Tag | None = title_node.parent.parent if title_node.parent.parent else title_node.parent
        steps = 0
        while current is not None and steps < 8:
            steps += 1
            for tag in current.find_all(["p", "div", "li"], recursive=False):
                text = normalize_ws(tag.get_text(" ", strip=True))
                if not text:
                    continue
                if text == title:
                    continue
                if PRICE_PATTERN.search(text):
                    continue
                if NOTE_PATTERN.search(text):
                    continue
                if HEADING_SKIP_PATTERN.search(text):
                    continue
                if len(text) < 8:
                    continue
                if text not in seen:
                    seen.add(text)
                    texts.append(text)
            current = current.find_next_sibling() if isinstance(current, Tag) else None
            if current and isinstance(current, Tag):
                marker = normalize_ws(current.get_text(" ", strip=True))
                if HEADING_SKIP_PATTERN.search(marker):
                    break

    if not texts:
        for tag in soup.find_all(["p"]):
            text = normalize_ws(tag.get_text(" ", strip=True))
            if not text or NOTE_PATTERN.search(text) or PRICE_PATTERN.search(text):
                continue
            if HEADING_SKIP_PATTERN.search(text):
                continue
            if len(text) >= 8 and text not in seen:
                texts.append(text)
                seen.add(text)
            if len(texts) >= 3:
                break
    return texts


def extract_notes(soup: BeautifulSoup) -> list[str]:
    notes: list[str] = []
    seen: set[str] = set()
    for text_node in soup.find_all(string=True):
        text = normalize_ws(str(text_node))
        if not text:
            continue
        if NOTE_PATTERN.search(text) or "電源" in text or "注意" in text:
            if text not in seen and len(text) >= 3:
                seen.add(text)
                notes.append(text)
    return notes


def extract_main_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    images: list[str] = []
    seen: set[str] = set()
    for image in soup.find_all("img", src=True):
        src = image.get("src") or ""
        alt = normalize_ws(image.get("alt", ""))
        full = urljoin(base_url, src)
        text = f"{alt} {src}".lower()
        if any(bad in text for bad in ["movie", "icon", "logo", "banner", "youtube"]):
            continue
        if full not in seen:
            seen.add(full)
            images.append(full)
        if len(images) >= 3:
            break
    return images


def build_product_slug(fields: dict[str, str | None]) -> str:
    parts = [fields.get("series_name") or "shimano", fields.get("variant_name") or ""]
    slug = "-".join(p for p in parts if p)
    slug = slug.lower()
    slug = slug.replace("/", "-")
    slug = re.sub(r"[^a-z0-9ぁ-んァ-ヶ一-龠ー\-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "shimano-product"


def build_product_raw(
    source_url: str,
    crawl_date: str,
    title_fields: dict[str, str | None],
    price_raw: str | None,
    category_raw: list[str],
    description_raw: list[str],
    notes_raw: list[str],
    image_urls: list[str],
) -> dict[str, Any]:
    slug = build_product_slug(title_fields)
    return {
        "id": f"{DEFAULT_MAKER}-{slug}",
        "maker": DEFAULT_MAKER,
        "brand": DEFAULT_BRAND,
        "source_site": DEFAULT_SOURCE_SITE,
        "source_url": source_url,
        "source_hash": None,
        "crawl_date": crawl_date,
        "extractor_version": DEFAULT_EXTRACTOR_VERSION,
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "category_raw": category_raw or ["リール", "電動"],
        "category_mechanism": DEFAULT_CATEGORY_MECHANISM,
        "category_usage": [],
        "water_type": "unknown",
        "series_name": title_fields.get("series_name"),
        "model_name": title_fields.get("model_name"),
        "variant_name": title_fields.get("variant_name"),
        "price_raw": price_raw,
        "sku_raw": None,
        "jan_upc_raw": None,
        "status_raw": None,
        "description_raw": description_raw,
        "notes_raw": notes_raw,
        "image_urls": image_urls,
        "spec_rows_raw": [],
        "subtype": {
            "reel_type": "electric",
            "electric_raw": {
                "motor_note_raw": None,
                "max_drag_raw": None,
                "weight_raw": None,
                "pe_capacity_raw": None,
                "flouro_capacity_raw": None,
                "max_winding_speed_raw": None,
                "practical_winding_power_raw": None,
            },
            "spinning_raw": None,
            "bait_raw": None,
            "conventional_raw": None,
            "lever_brake_raw": None,
            "fly_raw": None,
        },
        "extra": {
            "technology_labels": [],
            "movie_links": [],
            "manual_links": [],
            "compatibility_links": [],
            "awards": [],
            "campaign_tags": [],
            "feature_section_titles": [],
            "hero_copy": [],
        },
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
    payload = build_product_raw(
        source_url=url,
        crawl_date=crawl_date,
        title_fields=title_fields,
        price_raw=title_price["price_raw"],
        category_raw=categories,
        description_raw=description_raw,
        notes_raw=notes_raw,
        image_urls=image_urls,
    )
    return save_product_raw(payload, out_dir)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shimano 電動リール詳細 raw extractor")
    parser.add_argument("url", help="Shimano 電動リール詳細ページ URL")
    parser.add_argument("--crawl-date", required=True, help="取得日。形式: YYYY-MM-DD")
    parser.add_argument("--out-dir", default=".", help="出力先ディレクトリ")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    output = run(url=args.url, crawl_date=args.crawl_date, out_dir=args.out_dir)
    print(output)


if __name__ == "__main__":
    main()
