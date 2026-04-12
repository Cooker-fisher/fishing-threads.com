"""
evaluate_ai_correction.py — compare baseline vs AI-corrected normalization.

Goal: decide whether AI correction of derived fields adds meaningful value
      over a strict label-dictionary baseline.

Approach
--------
* Baseline  : normalize_all() — expanded LABEL_DICT (v2) + description
              fallback for spool_capacity_text.
* AI (mock) : same pipeline + any remaining extended aliases.
              Simulates max gain a real LLM could add without hallucination.
              Never overwrites a field the baseline already extracted.

Each field comparison is classified as:
  improvement  — baseline=None, ai=<value>     (field recovered)
  no_change    — same value (including both None)
  mutation     — both non-None but different    (manual review required)
  regression   — baseline=<value>, ai=None      (should not occur with mock)

Output
------
  normalized/products/electric/<maker>/<id>_baseline.json
  normalized/products/electric/<maker>/<id>_ai.json
  docs/ai-correction-evaluation-results.json
  stdout: summary table

Usage
-----
  # both DAIWA + SHIMANO (default):
  python scripts/evaluate_ai_correction.py

  # single seed file:
  python scripts/evaluate_ai_correction.py \\
    --index-json samples/daiwa-electric-first10-raw-index-clean.json

  # explicit multi-seed:
  python scripts/evaluate_ai_correction.py \\
    --index-json samples/daiwa-electric-first10-raw-index-clean.json \\
                 samples/shimano-electric-first5-raw-index-clean.json
"""
from __future__ import annotations

import argparse
import json
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
    normalize_all,
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

# Remaining aliases not yet in the baseline LABEL_DICT.
# After the v2 dictionary expansion these are very few — they represent
# genuinely rare or ambiguous label variants that we deliberately kept
# out of the baseline to avoid false-positive matches.
AI_LABEL_ALIASES: dict[str, str] = {
    # All LABEL_DICT entries are already in baseline; these are extras
    # a real LLM might handle that we chose not to hard-code.
    "ハンドル長":              "handle_length_mm",  # no unit at all (high ambiguity)
    "ベアリング":              "bearing_desc",       # single-word (high ambiguity)
    "ラインキャパシティ":      "spool_capacity_text",  # English-derived
    "対応バッテリー":          "electric_power_desc",  # already in LABEL_DICT but kept for symmetry
    "本体重量(g)":            "weight_g",            # very rare alternate
}

# Import the same description regex the baseline already uses so the AI mock
# does not double-count the one case it handles.
from scripts.normalizers.electric_reel_minimal import (                 # noqa: E402
    _SPOOL_FROM_DESC_RE,
)


def run_ai_correction(
    spec_rows_raw: list[dict],
    description_raw: list[str],
    baseline: dict[str, str | None],
) -> dict[str, str | None]:
    """
    Simulate AI correction on top of *baseline*.

    Rules (in order):
    1. Extended alias matching for the few labels still outside LABEL_DICT.
    2. Description fallback — already applied by baseline normalize_all(),
       so this step is effectively a no-op after the v2 expansion.

    Never overwrites a field that baseline already populated.
    """
    corrected = dict(baseline)

    # Step 1: remaining alias matching
    for row in spec_rows_raw:
        label = (row.get("label") or "").strip()
        field = AI_LABEL_ALIASES.get(label)
        if field and corrected.get(field) is None:
            value = row.get("value")
            if value:
                corrected[field] = str(value).strip()

    # Step 2: description fallback (baseline already handles this in v2)
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

def _detect_maker_from_url(url: str) -> str:
    """Infer product maker from URL/path hint."""
    url_lower = url.lower()
    if "shimano" in url_lower:
        return "shimano"
    return "daiwa"


def build_raw_with_spec(url: str, crawl_date: str = "2026-04-12") -> dict:
    """
    Fetch (or load from local path) an HTML page, run detail + spec
    extraction, and return a merged raw dict with spec_rows_raw populated.
    Maker is inferred from the URL so SHIMANO fixtures get the right brand.
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

    # correct maker/brand/id for non-DAIWA fixtures
    maker = _detect_maker_from_url(url)
    if maker != "daiwa" and raw.get("id", "").startswith("daiwa-"):
        slug_part = raw["id"][len("daiwa-"):]
        raw["id"] = f"{maker}-{slug_part}"
        raw["maker"] = maker
        raw["brand"] = maker

    return raw


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def run_evaluation(
    index_jsons: list[str],
    out_dir: str = ".",
    crawl_date: str = "2026-04-12",
) -> None:
    root = Path(out_dir)

    # collect URLs from all seed files
    urls: list[str] = []
    for index_json in index_jsons:
        index_path = Path(index_json)
        seed = json.loads(index_path.read_text(encoding="utf-8"))
        urls += [item["url"] if isinstance(item, dict) else item for item in seed]

    all_comparisons: list[dict] = []

    for url in urls:
        try:
            raw = build_raw_with_spec(url, crawl_date)
        except Exception as exc:
            print(f"SKIP {url}: {exc}", file=sys.stderr)
            continue

        product_id = raw["id"]
        maker = raw.get("maker", "unknown")
        spec_rows = raw.get("spec_rows_raw") or []
        desc = raw.get("description_raw") or []

        baseline = normalize_all(spec_rows, desc)
        ai_corrected = run_ai_correction(spec_rows, desc, baseline)

        comparison = compare_outputs(product_id, baseline, ai_corrected)
        all_comparisons.append(comparison)

        # save per-product normalized files
        b_dir = root / "normalized" / "products" / "electric" / maker
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

    total_impr = sum(stats[f]["improvement"] for f in TARGET_FIELDS)
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
        nargs="+",
        default=[
            "samples/daiwa-electric-first10-raw-index-clean.json",
            "samples/shimano-electric-first5-raw-index-clean.json",
        ],
        help="one or more seed JSON files with product URLs",
    )
    p.add_argument("--out-dir", default=".", help="output root directory")
    p.add_argument("--crawl-date", default="2026-04-12")
    return p


def main() -> None:
    args = _build_arg_parser().parse_args()
    run_evaluation(args.index_json, args.out_dir, args.crawl_date)


if __name__ == "__main__":
    main()
