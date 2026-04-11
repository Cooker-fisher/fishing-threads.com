from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.extractors.shimano_electric_detail import build_product_slug, run as run_detail_extractor, split_model_fields


DEFAULT_MAKER = "shimano"
DEFAULT_INDEX_DIR = Path("raw/index/shimano/electric")
DEFAULT_PRODUCTS_DIR = Path("raw/products/shimano")


def load_index_raw(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def extract_detail_urls(index_raw: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for item in index_raw.get("items", []):
        url = item.get("source_url")
        if not isinstance(url, str) or not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def build_expected_product_path(out_dir: str | Path, source_url: str) -> Path:
    slug_hint = source_url.rstrip("/").split("/")[-1].replace(".html", "")
    slug_fields = split_model_fields(slug_hint)
    slug = build_product_slug(slug_fields)
    out_dir = Path(out_dir)
    return out_dir / DEFAULT_PRODUCTS_DIR / f"{slug}.json"


def filter_missing_detail_urls(urls: list[str], out_dir: str | Path) -> list[str]:
    missing: list[str] = []
    for url in urls:
        expected = build_expected_product_path(out_dir, url)
        if not expected.exists():
            missing.append(url)
    return missing


def run_pipeline(index_raw_path: str | Path, crawl_date: str, out_dir: str | Path, limit: int | None = None) -> list[str]:
    index_raw = load_index_raw(index_raw_path)
    urls = extract_detail_urls(index_raw)
    pending = filter_missing_detail_urls(urls, out_dir)
    if limit is not None:
        pending = pending[:limit]

    outputs: list[str] = []
    for url in pending:
        out_path = run_detail_extractor(url=url, crawl_date=crawl_date, out_dir=out_dir)
        outputs.append(str(out_path))
    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shimano 一覧rawから詳細 extractor を実行する")
    parser.add_argument("index_raw_path", help="一覧 raw JSON のパス")
    parser.add_argument("--crawl-date", required=True, help="取得日。形式: YYYY-MM-DD")
    parser.add_argument("--out-dir", default=".", help="出力先ディレクトリ")
    parser.add_argument("--limit", type=int, default=None, help="実行上限件数")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    outputs = run_pipeline(
        index_raw_path=args.index_raw_path,
        crawl_date=args.crawl_date,
        out_dir=args.out_dir,
        limit=args.limit,
    )
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
