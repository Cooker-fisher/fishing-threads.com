"""
evaluate_ai_correction.py — compare baseline vs AI-corrected normalization.

Goal: decide whether AI correction of derived fields adds meaningful value
      over a strict label-dictionary baseline.

Approach
--------
* Baseline  : normalize_from_spec_rows() with exact-match LABEL_DICT
* AI (mock) : same pipeline + extended label aliases + description fallback.
              This simulates the maximum gain a real LLM could achieve
              *without* hallucinating.  It never overwrites a field the
              baseline already extracted.

Each field comparison is classified as:
  improvement  — baseline=None, ai=<value>     (field recovered)
  no_change    — same value (including both None)
  mutation     — both non-None but different    (manual review required)
  regression   — baseline=<value>, ai=None      (should not occur with mock)

Output
------
  normalized/products/electric/daiwa/<id>_baseline.json
  normalized/products/electric/daiwa/<id>_ai.json
  docs/ai-correction-evaluation-results.json
  stdout: summary table

Usage
-----
  python scripts/evaluate_ai_correction.py
  python scripts/evaluate_ai_correction.py --index-json samples/daiwa-electric-first10-raw-index-clean.json --out-dir .
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extractors.daiwa_electric_index import fetch_html          # noqa: E402
from scripts.extractors.daiwa_electric_detail import (                  # noqa: E402
    parse_html as parse_detail_html,
    extract_breadcrumb_categories,
    extract_title_and_price,
    split_model_fields,
    extract_main_description,
    extract_notes,
    extract_main_images,
    build_product_raw,
)
from scripts.extractors.daiwa_electric_spec import (                    # noqa: E402
    parse_html as parse_spec_html,
    extract_spec_rows,
)
from scripts.normalizers.electric_reel_minimal import (                 # noqa: E402
    normalize_from_spec_rows,
    DERIVED_FIELD_NAMES,
)

# ---------------------------------------------------------------------------
# Target fields for the evaluation
# ---------------------------------------------------------------------------
TARGET_FIELDS: list[str] = [
    "weight_g",
    "gear_ratio",
    "max_drag_kg",
    "handle_length_mm",
    "bearing_desc",
    "spool_capacity_text",
    "electric_power_desc",
]

# ---------------------------------------------------------------------------
# AI mock corrector
# ---------------------------------------------------------------------------

# Extended label aliases — covers known label variants found in the wild.
# A real LLM would handle arbitrary Japanese paraphrases; this mock covers
# the most common patterns so the evaluation gives a realistic upper bound.
AI_LABEL_ALIASES: dict[str, str] = {
    # weight
    "自重(g)":           "weight_g",
    "自重":              "weight_g",
    "重量(g)":           "weight_g",
    "本体重量(g)":       "weight_g",
    "標準自重（ｇ）":    "weight_g",   # full-width parens / kana unit
    # gear ratio
    "ギア比":            "gear_ratio",
    # max drag
    "最大ドラグ力(kg)":  "max_drag_kg",
    "最大ドラグ(kg)":    "max_drag_kg",
    "ドラグ力(kg)":      "max_drag_kg",
    "最大ドラグ力":      "max_drag_kg",
    # handle length
    "ハンドル長(mm)":    "handle_length_mm",
    "ハンドル長さ(mm)":  "handle_length_mm",
    "ハンドル全長(mm)":  "handle_length_mm",
    "ハンドル長":        "handle_length_mm",
    # bearings
    "ベアリング数(BB/RB)": "bearing_desc",
    "ベアリング(BB/RB)":   "bearing_desc",
    "ベアリング数":        "bearing_desc",
    "ベアリング":          "bearing_desc",
    # spool capacity
    "巻糸量(PE号-m)":    "spool_capacity_text",
    "糸巻量(PE号-m)":    "spool_capacity_text",
    "糸巻量":            "spool_capacity_text",
    "巻糸量":            "spool_capacity_text",
    "ラインキャパシティ": "spool_capacity_text",
    # electric power
    "対応電源":          "electric_power_desc",
    "使用電源":          "electric_power_desc",
    "電源":              "electric_power_desc",
    "対応バッテリー":    "electric_power_desc",
}

# Regex to extract spool capacity from description text when the spec table
# has no 巻糸量 row at all.
_SPOOL_FROM_DESC_RE = re.compile(
    r"PE\s*\d+(?:\.\d+)?号\s*[\-/]\s*\d+(?:\s*m)?"
    r"|PE\s*\d+(?:\.\d+)?\s*\-\s*\d+",
    re.IGNORECASE,
)


def run_ai_correction(
    spec_rows_raw: list[dict],
    description_raw: list[str],
    baseline: dict[str, str | None],
) -> dict[str, str | None]:
    """
    Simulate AI correction on top of *baseline*.

    Rules (in order):
    1. Extended alias matching — fill in fields the strict dict missed.
    2. Description fallback — recover spool_capacity_text from free text.

    Never overwrites a field that baseline already populated.
    """
    corrected = dict(baseline)

    # Step 1: extended label alias matching
    for row in spec_rows_raw:
        label = (row.get("label") or "").strip()
        field = AI_LABEL_ALIASES.get(label)
        if field and corrected.get(field) is None:
            value = row.get("value")
            if value:
                corrected[field] = str(value).strip()

    # Step 2: description fallback for spool_capacity_text
    if corrected.get("spool_capacity_text") is None:
        desc_text = " ".join(description_raw or [])
        m = _SPOOL_FROM_DESC_RE.search(desc_text)
        if m:
            corrected["spool_capacity_text"] = m.group(0).strip()

    return corrected


# ---------------------------------------------------------------------------
# Comparison / classification
# ---------------------------------------------------------------------------

VALID_CATEGORIES = ("improvement", "no_change", "regression", "mutation")


def classify_change(
    baseline_val: str | None,
    ai_val: str | None,
) -> str:
    """
    Classify the difference between baseline and AI-corrected values.

    improvement : baseline=None  → ai=<value>   (new information added)
    no_change   : same value (including both None)
    regression  : baseline=<value> → ai=None    (information lost)
    mutation    : both non-None but different    (manual review needed)
    """
    if baseline_val == ai_val:
        return "no_change"
    if baseline_val is None and ai_val is not None:
        return "improvement"
    if baseline_val is not None and ai_val is None:
        return "regression"
    return "mutation"


def compare_outputs(
    product_id: str,
    baseline: dict[str, str | None],
    ai_corrected: dict[str, str | None],
) -> dict:
    field_results: dict[str, dict] = {}
    for field in TARGET_FIELDS:
        b = baseline.get(field)
        a = ai_corrected.get(field)
        field_results[field] = {
            "baseline": b,
            "ai_corrected": a,
            "category": classify_change(b, a),
        }
    return {"product_id": product_id, "fields": field_results}


# ---------------------------------------------------------------------------
# Pipeline helper: fetch HTML → merge detail + spec into one raw dict
# ---------------------------------------------------------------------------

def build_raw_with_spec(url: str, crawl_date: str = "2026-04-12") -> dict:
    """
    Fetch (or load from local path) an HTML page, run detail + spec
    extraction, and return a merged raw dict with spec_rows_raw populated.
    """
    fetched = fetch_html(url)
    html = fetched.html

    # detail extraction
    detail_soup = parse_detail_html(html)
    categories = extract_breadcrumb_categories(detail_soup)
    title_price = extract_title_and_price(detail_soup)
    title_fields = split_model_fields(title_price["title"] or "")
    description_raw = extract_main_description(detail_soup)
    notes_raw = extract_notes(detail_soup)
    image_urls = extract_main_images(detail_soup, url)
    raw = build_product_raw(
        url, crawl_date, title_fields, title_price["price_raw"],
        categories, description_raw, notes_raw, image_urls,
    )

    # spec extraction (reuses same HTML)
    spec_soup = parse_spec_html(html)
    raw["spec_rows_raw"] = extract_spec_rows(spec_soup)

    return raw


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def run_evaluation(
    index_json: str = "samples/daiwa-electric-first10-raw-index-clean.json",
    out_dir: str = ".",
    crawl_date: str = "2026-04-12",
) -> None:
    root = Path(out_dir)
    index_path = Path(index_json)
    seed = json.loads(index_path.read_text(encoding="utf-8"))
    urls = [item["url"] if isinstance(item, dict) else item for item in seed]

    all_comparisons: list[dict] = []

    for url in urls:
        try:
            raw = build_raw_with_spec(url, crawl_date)
        except Exception as exc:
            print(f"SKIP {url}: {exc}", file=sys.stderr)
            continue

        product_id = raw["id"]
        spec_rows = raw.get("spec_rows_raw") or []
        desc = raw.get("description_raw") or []

        baseline = normalize_from_spec_rows(spec_rows)
        ai_corrected = run_ai_correction(spec_rows, desc, baseline)

        comparison = compare_outputs(product_id, baseline, ai_corrected)
        all_comparisons.append(comparison)

        # save per-product normalized files
        b_dir = root / "normalized" / "products" / "electric" / "daiwa"
        b_dir.mkdir(parents=True, exist_ok=True)

        (b_dir / f"{product_id}_baseline.json").write_text(
            json.dumps({"id": product_id, **baseline}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (b_dir / f"{product_id}_ai.json").write_text(
            json.dumps({"id": product_id, **ai_corrected}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # -----------------------------------------------------------------------
    # Aggregate stats
    # -----------------------------------------------------------------------
    stats: dict[str, dict[str, int]] = {
        f: {c: 0 for c in VALID_CATEGORIES} for f in TARGET_FIELDS
    }
    for comp in all_comparisons:
        for field, res in comp["fields"].items():
            stats[field][res["category"]] += 1

    report = {
        "evaluated_products": len(all_comparisons),
        "target_fields": TARGET_FIELDS,
        "per_field_stats": stats,
        "per_product": all_comparisons,
    }

    report_path = root / "docs" / "ai-correction-evaluation-results.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Report saved: {report_path}\n")

    # -----------------------------------------------------------------------
    # Print summary table
    # -----------------------------------------------------------------------
    col = {"improvement": 12, "no_change": 10, "regression": 10, "mutation": 8}
    header = f"{'Field':<26}" + "".join(f"{h:>{w}}" for h, w in col.items())
    print(header)
    print("-" * len(header))
    for field in TARGET_FIELDS:
        s = stats[field]
        row = f"{field:<26}" + "".join(f"{s[c]:>{w}}" for c, w in col.items())
        print(row)
    print(f"\nTotal products evaluated : {len(all_comparisons)}")
    print(f"Total field×product pairs: {len(all_comparisons) * len(TARGET_FIELDS)}")

    # headline improvement rate
    total_impr = sum(
        stats[f]["improvement"] for f in TARGET_FIELDS
    )
    total_pairs = len(all_comparisons) * len(TARGET_FIELDS)
    pct = (total_impr / total_pairs * 100) if total_pairs else 0
    print(f"AI improvement rate      : {total_impr}/{total_pairs} = {pct:.1f}%")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AI補正評価スクリプト")
    p.add_argument(
        "--index-json",
        default="samples/daiwa-electric-first10-raw-index-clean.json",
        help="seed JSON with product URLs",
    )
    p.add_argument("--out-dir", default=".", help="output root directory")
    p.add_argument("--crawl-date", default="2026-04-12")
    return p


def main() -> None:
    args = _build_arg_parser().parse_args()
    run_evaluation(args.index_json, args.out_dir, args.crawl_date)


if __name__ == "__main__":
    main()
