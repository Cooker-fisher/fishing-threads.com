"""
electric_reel_minimal.py — baseline normalizer for electric reel spec rows.

Maps spec_rows_raw (as produced by daiwa_electric_spec.extract_spec_rows) to
derived fields using an *exact-match* label dictionary.  No AI, no fuzzy
matching — this is the strict baseline against which AI correction is
evaluated.

v2 changes
----------
* LABEL_DICT expanded with DAIWA and SHIMANO label variants (aliases now in
  baseline; moved from AI-only aliases).
* Added _apply_spool_description_fallback and normalize_all convenience
  function (regex fallback for spool_capacity_text when spec table row
  is absent).

Usage (batch):
    python -m scripts.normalizers.electric_reel_minimal --raw-dir . --out-dir .

Output per product:
    normalized/products/electric/<maker>/<product-id>.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Label dictionary — keys are exact label strings expected in spec_rows_raw.
# Both DAIWA-standard and known SHIMANO variants are included so AI
# correction is not required for common label variations.
#
# Ordering within each field group: most-common first.
# ---------------------------------------------------------------------------
LABEL_DICT: dict[str, str] = {
    # ------------------------------------------------------------------ weight
    "自重(g)":               "weight_g",   # DAIWA standard
    "自重":                   "weight_g",   # no unit (DAIWA variant, 303J-style)
    "標準自重（ｇ）":         "weight_g",   # full-width parens / kana unit
    "重量(g)":               "weight_g",   # alternate wording

    # -------------------------------------------------------------- gear ratio
    "ギア比":                 "gear_ratio",  # DAIWA standard
    "ギヤ比":                 "gear_ratio",  # SHIMANO variant (ヤ dakuten)

    # --------------------------------------------------------------- max drag
    "最大ドラグ力(kg)":       "max_drag_kg",  # standard
    "最大ドラグ(kg)":         "max_drag_kg",  # no 力 (DAIWA variant, 306J-style)
    "ドラグ力(kg)":           "max_drag_kg",  # abbreviated
    "最大ドラグ力":            "max_drag_kg",  # no unit

    # ---------------------------------------------------------- handle length
    "ハンドル長(mm)":         "handle_length_mm",  # DAIWA standard
    "ハンドル長さ(mm)":       "handle_length_mm",  # さ suffix (DAIWA 304J / SHIMANO)
    "ハンドル全長(mm)":       "handle_length_mm",  # full-length variant
    "ハンドル長":              "handle_length_mm",  # no unit

    # --------------------------------------------------------------- bearings
    "ベアリング数(BB/RB)":    "bearing_desc",  # DAIWA standard
    "ベアリング(BB/RB)":      "bearing_desc",  # no 数 (DAIWA 310J-style)
    "ボール/ローラーベアリング数": "bearing_desc",  # SHIMANO format
    "ベアリング数":            "bearing_desc",  # no unit

    # --------------------------------------------------------- spool capacity
    "巻糸量(PE号-m)":         "spool_capacity_text",  # DAIWA standard (巻糸量)
    "糸巻量(PE号-m)":         "spool_capacity_text",  # DAIWA variant 305J / SHIMANO (糸巻量)
    "糸巻量(PE-号-m)":        "spool_capacity_text",  # SHIMANO: hyphen before 号
    "糸巻量":                  "spool_capacity_text",  # no unit
    "巻糸量":                  "spool_capacity_text",  # no unit

    # --------------------------------------------------------- electric power
    "対応電源":               "electric_power_desc",  # DAIWA standard
    "使用電源":               "electric_power_desc",  # DAIWA 309J-style / SHIMANO
    "電源":                    "electric_power_desc",  # SHIMANO short form
    "対応バッテリー":          "electric_power_desc",  # battery-focused variant
}

DERIVED_FIELD_NAMES: list[str] = [
    "weight_g",
    "gear_ratio",
    "max_drag_kg",
    "handle_length_mm",
    "bearing_desc",
    "spool_capacity_text",
    "electric_power_desc",
]

NORMALIZER_NAME = "electric_reel_minimal"
NORMALIZER_VERSION = "v2"

# ---------------------------------------------------------------------------
# Description fallback — spool_capacity_text only
# Used when the spec table has no spool-capacity row at all.
# Pattern covers: PE3号-300m, PE4号/280m, PE 3-300, etc.
# ---------------------------------------------------------------------------
_SPOOL_FROM_DESC_RE = re.compile(
    r"PE\s*\d+(?:\.\d+)?号\s*[\-/]\s*\d+(?:\s*m)?"
    r"|PE\s*\d+(?:\.\d+)?\s*\-\s*\d+",
    re.IGNORECASE,
)


def _apply_spool_description_fallback(
    derived: dict[str, str | None],
    description_raw: list[str],
) -> dict[str, str | None]:
    """
    If spool_capacity_text is still None after label matching, attempt a
    simple regex extraction from the product description text.

    Only fires when the field is absent — never overwrites an existing value.
    Stores the matched raw text as-is (no transformation).
    """
    if derived.get("spool_capacity_text") is not None:
        return derived
    desc_text = " ".join(description_raw)
    m = _SPOOL_FROM_DESC_RE.search(desc_text)
    if m:
        derived["spool_capacity_text"] = m.group(0).strip()
    return derived


# ---------------------------------------------------------------------------
# Core normalization
# ---------------------------------------------------------------------------

def normalize_from_spec_rows(
    spec_rows_raw: list[dict[str, Any]],
) -> dict[str, str | None]:
    """
    Apply LABEL_DICT to *spec_rows_raw*.

    Returns a dict keyed by DERIVED_FIELD_NAMES; missing fields are None.
    First match wins (no overwrite).
    """
    derived: dict[str, str | None] = {f: None for f in DERIVED_FIELD_NAMES}
    for row in spec_rows_raw:
        label = (row.get("label") or "").strip()
        field = LABEL_DICT.get(label)
        if field and derived[field] is None:
            raw_value = row.get("value")
            if raw_value is not None:
                derived[field] = str(raw_value).strip()
    return derived


def normalize_all(
    spec_rows_raw: list[dict[str, Any]],
    description_raw: list[str] | None = None,
) -> dict[str, str | None]:
    """
    Full baseline normalization: label dict + description fallback.

    Preferred entry point for callers that have description_raw available.
    """
    derived = normalize_from_spec_rows(spec_rows_raw)
    if description_raw:
        derived = _apply_spool_description_fallback(derived, description_raw)
    return derived


def build_normalized(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build a normalized record from a raw product JSON dict.
    Preserves identity fields; adds derived fields and _meta.
    """
    spec_rows_raw = raw_data.get("spec_rows_raw") or []
    description_raw = raw_data.get("description_raw") or []
    derived = normalize_all(spec_rows_raw, description_raw)
    return {
        "id": raw_data["id"],
        "maker": raw_data.get("maker"),
        "series_name": raw_data.get("series_name"),
        "model_name": raw_data.get("model_name"),
        "variant_name": raw_data.get("variant_name"),
        **derived,
        "_meta": {
            "normalizer": NORMALIZER_NAME,
            "normalizer_version": NORMALIZER_VERSION,
            "source_raw_id": raw_data["id"],
        },
    }


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def run_on_raw_file(raw_path: Path, out_dir: Path) -> Path:
    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
    normalized = build_normalized(raw_data)
    maker = normalized.get("maker") or "unknown"
    product_id = normalized["id"]
    out_path = (
        out_dir / "normalized" / "products" / "electric" / maker / f"{product_id}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path


def run_batch(raw_dir: Path, out_dir: Path) -> list[Path]:
    outputs: list[Path] = []
    for raw_path in sorted(raw_dir.glob("raw/products/**/*.json")):
        out_path = run_on_raw_file(raw_path, out_dir)
        outputs.append(out_path)
        print(f"normalized: {out_path}")
    return outputs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Electric reel minimal normalizer")
    p.add_argument("--raw-dir", default=".", help="Project root containing raw/products/")
    p.add_argument("--out-dir", default=".", help="Output root for normalized/")
    return p


def main() -> None:
    args = _build_arg_parser().parse_args()
    outputs = run_batch(Path(args.raw_dir), Path(args.out_dir))
    print(f"Done: {len(outputs)} file(s) normalized.")


if __name__ == "__main__":
    main()
