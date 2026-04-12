"""
DAIWA electric reel comparison generator.

Reads  raw/daiwa-electric-detail-spec-YYYYMMDD.json
Writes raw/daiwa-electric-comparison-YYYYMMDD.json

Usage:
    python scripts/run_daiwa_electric_comparison.py
    python scripts/run_daiwa_electric_comparison.py --input raw/daiwa-electric-detail-spec-20260412.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.normalizers.electric_reel_minimal import (
    OPTIONAL_COLUMNS,
    is_accessory,
    normalize_items,
)


def _latest_detail_spec(raw_dir: Path) -> Path:
    files = sorted(raw_dir.glob("daiwa-electric-detail-spec-*.json"))
    if not files:
        raise FileNotFoundError(f"No detail-spec JSON found in {raw_dir}")
    return files[-1]


def build_comparison(raw_data: dict) -> dict:
    """Return a comparison summary dict from *raw_data*."""
    total_in = len(raw_data.get("items", []))
    skipped: list[str] = [
        item["product_name"]
        for item in raw_data.get("items", [])
        if is_accessory(item)
    ]

    rows = normalize_items(raw_data)

    # Collect union of all column headers (excluding internal _-prefixed keys)
    all_columns: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r:
            if not k.startswith("_") and k not in seen:
                seen.add(k)
                all_columns.append(k)

    # Per-product summary
    product_summary: list[dict] = []
    by_product: dict[str, list[dict]] = {}
    for r in rows:
        pname = r["_product_name"]
        by_product.setdefault(pname, []).append(r)
    for pname, product_rows in by_product.items():
        missing = sorted(
            col
            for col in all_columns
            if all(r.get(col) is None for r in product_rows)
            and col not in OPTIONAL_COLUMNS
        )
        optional_absent = sorted(
            col
            for col in OPTIONAL_COLUMNS
            if all(r.get(col) is None for r in product_rows)
        )
        product_summary.append(
            {
                "product_name": pname,
                "variant_count": len(product_rows),
                "missing_required": missing,
                "optional_absent": optional_absent,
            }
        )

    return {
        "generated_date": date.today().isoformat(),
        "source_file": raw_data.get("source_index", ""),
        "total_items_in_source": total_in,
        "accessories_skipped": skipped,
        "reel_count": len(product_summary),
        "variant_row_count": len(rows),
        "columns": all_columns,
        "products": product_summary,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="DAIWA electric reel comparison generator")
    ap.add_argument("--input", help="Path to detail-spec JSON (default: latest in raw/)")
    ap.add_argument("--out-dir", default="raw", help="Output directory (default: raw/)")
    args = ap.parse_args()

    raw_dir = ROOT / "raw"
    if args.input:
        src = Path(args.input)
        if not src.is_absolute():
            src = ROOT / src
    else:
        src = _latest_detail_spec(raw_dir)

    print(f"[INFO] input: {src}")
    raw_data = json.loads(src.read_text(encoding="utf-8"))

    comparison = build_comparison(raw_data)

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"daiwa-electric-comparison-{comparison['generated_date']}.json"
    out_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SAVED] {out_path}")

    print(f"\nSummary")
    print(f"  source items   : {comparison['total_items_in_source']}")
    print(f"  accessories    : {comparison['accessories_skipped']}")
    print(f"  reels          : {comparison['reel_count']}")
    print(f"  variant rows   : {comparison['variant_row_count']}")
    print(f"  columns        : {len(comparison['columns'])}")
    for p in comparison["products"]:
        flags = ""
        if p["missing_required"]:
            flags += f"  MISSING:{p['missing_required']}"
        if p["optional_absent"]:
            flags += f"  optional_absent:{p['optional_absent']}"
        print(f"  {p['product_name']:30}  variants={p['variant_count']}{flags}")


if __name__ == "__main__":
    main()
