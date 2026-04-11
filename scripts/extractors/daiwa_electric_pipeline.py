from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.extractors import daiwa_electric_detail, daiwa_electric_spec


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, data: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_spec_url_from_detail_url(detail_url: str) -> str:
    return detail_url


def merge_spec_into_product_raw(product_raw: dict[str, Any], spec_payload: dict[str, Any]) -> dict[str, Any]:
    merged = dict(product_raw)
    merged["price_raw"] = spec_payload.get("price_raw") or merged.get("price_raw")
    merged["sku_raw"] = spec_payload.get("sku_raw") or merged.get("sku_raw")
    merged["jan_upc_raw"] = spec_payload.get("jan_upc_raw") or merged.get("jan_upc_raw")
    merged["spec_rows_raw"] = spec_payload.get("spec_rows_raw") or merged.get("spec_rows_raw") or []

    existing_notes = merged.get("notes_raw") or []
    spec_notes = spec_payload.get("notes_raw") or []
    merged["notes_raw"] = list(dict.fromkeys([*existing_notes, *spec_notes]))
    return merged


def collect_detail_urls_from_index(index_raw: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for item in index_raw.get("items", []):
        url = item.get("source_url")
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def run_pipeline(index_json_path: str | Path, crawl_date: str, out_dir: str | Path) -> list[Path]:
    index_raw = load_json(index_json_path)
    detail_urls = collect_detail_urls_from_index(index_raw)
    outputs: list[Path] = []

    for detail_url in detail_urls:
        detail_path = daiwa_electric_detail.run(detail_url, crawl_date=crawl_date, out_dir=out_dir)
        product_raw = load_json(detail_path)

        spec_url = build_spec_url_from_detail_url(detail_url)
        spec_path = daiwa_electric_spec.run(spec_url, out_dir=out_dir)
        spec_payload = load_json(spec_path)

        merged = merge_spec_into_product_raw(product_raw, spec_payload)
        final_path = save_json(detail_path, merged)
        outputs.append(final_path)

    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DAIWA 電動リール 一覧→詳細→spec pipeline")
    parser.add_argument("index_json", help="一覧 raw JSON のパス")
    parser.add_argument("--crawl-date", required=True, help="取得日。形式: YYYY-MM-DD")
    parser.add_argument("--out-dir", default=".", help="出力先ディレクトリ")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    outputs = run_pipeline(args.index_json, crawl_date=args.crawl_date, out_dir=args.out_dir)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
