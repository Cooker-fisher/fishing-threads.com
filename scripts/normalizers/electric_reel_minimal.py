"""
DAIWA electric reel — minimal normalizer.

Rules
-----
- is_accessory: items with fewer than 10 spec columns are accessories
  (e.g. リモート JOG has 4 columns).  Accessories are excluded from
  comparison output.
- optional_columns: 標準巻糸量ナイロン（号ｰm） is absent for PE-only reels
  (e.g. レオブリッツ S400).  Missing value is normalised to None, not an error.
"""

from __future__ import annotations

from typing import Any

# Columns that may be absent in PE-only or older series reels.
OPTIONAL_COLUMNS: frozenset[str] = frozenset(
    ["標準巻糸量ナイロン（号ｰm）", "ハンドルアーム長（mm）"]
)

# Items with fewer headers are accessories, not reels.
_ACCESSORY_HEADER_THRESHOLD = 10


def is_accessory(item: dict[str, Any]) -> bool:
    """Return True when *item* is an accessory, not a reel.

    Detection heuristic: spec header count < _ACCESSORY_HEADER_THRESHOLD.
    """
    headers = (item.get("spec") or {}).get("headers", [])
    return len(headers) < _ACCESSORY_HEADER_THRESHOLD


def normalize_row(headers: list[str], row: dict[str, str]) -> dict[str, Any]:
    """Return a normalised dict for one spec row.

    All keys in *headers* are present in the result.
    Optional columns absent from *headers* are included as None.
    """
    result: dict[str, Any] = {}
    for h in headers:
        result[h] = row.get(h) or None
    for col in OPTIONAL_COLUMNS:
        if col not in result:
            result[col] = None
    return result


def normalize_items(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise *raw_data* from the detail+spec JSON.

    Accessories (is_accessory == True) are skipped entirely.
    Returns one dict per spec row (multiple rows for multi-variant products).
    """
    out: list[dict[str, Any]] = []
    for item in raw_data.get("items", []):
        if is_accessory(item):
            continue
        spec = item.get("spec") or {}
        headers = spec.get("headers", [])
        for row in spec.get("rows", []):
            norm = normalize_row(headers, row)
            norm["_product_name"] = item.get("product_name")
            norm["_detail_url"] = item.get("detail_url")
            out.append(norm)
    return out
