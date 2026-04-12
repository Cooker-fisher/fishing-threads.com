"""
electric_reel_minimal.py — baseline normalizer for electric reel spec rows.

Maps spec_rows_raw (as produced by daiwa_electric_spec.extract_spec_rows) to
derived fields using an *exact-match* label dictionary.  No AI, no fuzzy
matching — this is the strict baseline against which AI correction is
evaluated.

Usage (batch):
    python -m scripts.normalizers.electric_reel_minimal --raw-dir . --out-dir .

Output per product:
    normalized/products/electric/<maker>/<product-id>.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Label dictionary — keys are the exact label strings expected in spec_rows_raw
# ---------------------------------------------------------------------------
LABEL_DICT: dict[str, str] = {
    "自重(g)":           "weight_g",
    "ギア比":             "gear_ratio",
    "最大ドラグ力(kg)":   "max_drag_kg",
    "ハンドル長(mm)":     "handle_length_mm",
    "ベアリング数(BB/RB)": "bearing_desc",
    "巻糸量(PE号-m)":     "spool_capacity_text",
    "対応電源":           "electric_power_desc",
}

DERIVED_FIELD_NAMES: list[str] = list(LABEL_DICT.values())

NORMALIZER_NAME = "electric_reel_minimal"
NORMALIZER_VERSION = "v1"


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


def build_normalized(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build a normalized record from a raw product JSON dict.
    Preserves identity fields; adds derived fields and _meta.
    """
    spec_rows_raw = raw_data.get("spec_rows_raw") or []
    derived = normalize_from_spec_rows(spec_rows_raw)
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
