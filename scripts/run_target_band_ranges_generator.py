"""
Generate raw/target-band-ranges.generated.json from standard-band-summary.json.

Purpose
-------
Keep top-UI band-range data as a generated artifact, not hand-maintained truth.

Default flow
------------
- input summary : runs/tmp/standard-band-summary.json
- template      : raw/target-band-ranges.json
- output        : raw/target-band-ranges.generated.json

Expected source signal
----------------------
Each band entry should contain a numeric band and a fish-target list.
Typical shapes accepted by this script:

1) list of entries
   [
     {"band": 100, "fish_targets": ["マダイ", "アジ"]},
     {"band": 200, "fish_targets": ["マダイ", "ブリ"]}
   ]

2) wrapped list
   {"bands": [...]} or {"entries": [...]} or {"band_summary": [...]} 

3) dict keyed by band
   {
     "100": {"fish_targets": ["マダイ", "アジ"]},
     "200": {"fish_targets": ["マダイ", "ブリ"]}
   }

Output
------
The generated file keeps bands / brand_bands from the template when available,
and replaces target_ranges with data-driven start_band / end_band values.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "runs" / "tmp" / "standard-band-summary.json"
DEFAULT_TEMPLATE = ROOT / "raw" / "target-band-ranges.json"
DEFAULT_OUTPUT = ROOT / "raw" / "target-band-ranges.generated.json"

_TARGET_KEYS = ("fish_targets", "targets", "target_fish", "fish", "fishes")
_NAME_KEYS = ("target", "name", "fish", "label")
_LIST_CONTAINER_KEYS = ("bands", "entries", "band_summary", "items")


def _is_band_like(value: Any) -> bool:
    if isinstance(value, int):
        return True
    if isinstance(value, str) and value.strip().isdigit():
        return True
    return False


def _coerce_band(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValueError(f"band must be int-like, got: {value!r}")


def _extract_target_names(raw_targets: Any) -> list[str]:
    if raw_targets is None:
        return []
    if isinstance(raw_targets, list):
        out: list[str] = []
        for item in raw_targets:
            if isinstance(item, str):
                name = item.strip()
                if name:
                    out.append(name)
                continue
            if isinstance(item, dict):
                for key in _NAME_KEYS:
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        out.append(value.strip())
                        break
        return out
    if isinstance(raw_targets, dict):
        out = []
        for key, value in raw_targets.items():
            if value in (False, None, 0, "", []):
                continue
            if isinstance(key, str) and key.strip():
                out.append(key.strip())
        return out
    return []


def _extract_targets_from_entry(entry: dict[str, Any]) -> list[str]:
    for key in _TARGET_KEYS:
        if key in entry:
            return _extract_target_names(entry.get(key))
    return []


def _iter_band_entries(summary: Any) -> Iterable[tuple[int, dict[str, Any]]]:
    if isinstance(summary, list):
        for entry in summary:
            if not isinstance(entry, dict):
                continue
            band_raw = entry.get("band", entry.get("standard_band"))
            if _is_band_like(band_raw):
                yield _coerce_band(band_raw), entry
        return

    if not isinstance(summary, dict):
        raise ValueError("summary must be dict or list")

    for key in _LIST_CONTAINER_KEYS:
        container = summary.get(key)
        if isinstance(container, list):
            for entry in container:
                if not isinstance(entry, dict):
                    continue
                band_raw = entry.get("band", entry.get("standard_band"))
                if _is_band_like(band_raw):
                    yield _coerce_band(band_raw), entry
            return

    # dict keyed by band number
    band_like_keys = [key for key in summary.keys() if _is_band_like(key)]
    if band_like_keys:
        for key in sorted(band_like_keys, key=_coerce_band):
            value = summary[key]
            if isinstance(value, dict):
                yield _coerce_band(key), value
        return

    raise ValueError(
        "Could not find band entries. Expected list, wrapped list, or dict keyed by band."
    )


def build_target_ranges(summary: Any) -> list[dict[str, Any]]:
    per_target: dict[str, dict[str, int]] = {}

    for band, entry in sorted(_iter_band_entries(summary), key=lambda x: x[0]):
        for target in _extract_targets_from_entry(entry):
            state = per_target.setdefault(target, {"start_band": band, "end_band": band})
            state["start_band"] = min(state["start_band"], band)
            state["end_band"] = max(state["end_band"], band)

    return [
        {
            "target": target,
            "start_band": info["start_band"],
            "end_band": info["end_band"],
        }
        for target, info in sorted(
            per_target.items(), key=lambda item: (item[1]["start_band"], item[1]["end_band"], item[0])
        )
    ]


def _bands_from_summary(summary: Any) -> list[int]:
    return sorted({band for band, _ in _iter_band_entries(summary)})


def build_output(summary: Any, template: dict[str, Any] | None, source_path: str) -> dict[str, Any]:
    bands = []
    brand_bands: dict[str, Any] = {}
    if isinstance(template, dict):
        bands = list(template.get("bands") or [])
        brand_bands = dict(template.get("brand_bands") or {})

    if not bands:
        bands = _bands_from_summary(summary)

    return {
        "_comment": "トップUI用 生成データ。target_ranges は standard-band-summary.json から自動導出。",
        "_version": "0.2.0-generated",
        "_source": source_path,
        "bands": bands,
        "brand_bands": brand_bands,
        "target_ranges": build_target_ranges(summary),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate target band ranges from standard-band-summary.json")
    ap.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to standard-band-summary.json")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Path to manual target-band-ranges.json")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to write generated JSON")
    args = ap.parse_args()

    input_path = Path(args.input)
    template_path = Path(args.template)
    output_path = Path(args.output)

    summary = json.loads(input_path.read_text(encoding="utf-8"))
    template = None
    if template_path.exists():
        template = json.loads(template_path.read_text(encoding="utf-8"))

    out = build_output(summary, template, str(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[SAVED] {output_path}")
    print(f"bands={out['bands']}")
    print(f"target_count={len(out['target_ranges'])}")


if __name__ == "__main__":
    main()
