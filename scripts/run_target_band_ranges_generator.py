#!/usr/bin/env python3
"""
target-band-ranges 生成スクリプト

【前提】
  このスクリプトは repo 外の runs/ を読む。
  runs/ はクロール・中間集計の一時出力置き場であり、repo に含まない。

  デフォルト入力パス:
    <repo>/../runs/tmp/standard-band-summary.json
    （= fishing-threads/runs/tmp/standard-band-summary.json）

  パスを変えたい場合は --input オプションで絶対パスを指定できる:
    python scripts/run_target_band_ranges_generator.py --input /path/to/standard-band-summary.json

出力（repo 内）:
  raw/target-band-ranges.generated.json  生データに近い確認用
  raw/target-band-ranges.normalized.json UI/比較接続用（魚種名正規化済み）

- bands / brand_bands は raw/target-band-ranges.json（手動）から引き継ぎ
- target_ranges のみを自動導出する
- 既存の raw/target-band-ranges.json は触らない
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent

# runs/ は repo 外 (_BASE_DIR の親) に置く設計。
# クロール一時出力を repo に混ぜないための境界。
_DEFAULT_SUMMARY_PATH = _BASE_DIR.parent / "runs" / "tmp" / "standard-band-summary.json"

_MANUAL_PATH    = _BASE_DIR / "raw" / "target-band-ranges.json"
_OUT_GENERATED  = _BASE_DIR / "raw" / "target-band-ranges.generated.json"
_OUT_NORMALIZED = _BASE_DIR / "raw" / "target-band-ranges.normalized.json"

# 魚種名正規化辞書: 生データの名称 → UI/比較用表示名
FISH_NAME_MAP: dict[str, str] = {
    "ブリ類":       "ブリ",
    "イカ類":       "イカ",
    "ムツ類":       "ムツ",
    "マグロ類":     "マグロ",
    "ハタ類":       "ハタ",
    "カサゴ類":     "カサゴ",
    "ゾイ類":       "ゾイ",
    "サケ・マス類": "サケ・マス",
}


def derive_target_ranges(summary: list[dict]) -> list[dict]:
    """
    standard-band-summary の各エントリの fish_targets × band から
    魚種ごとの start_band / end_band を導出する。
    """
    fish_bands: dict[str, list[int]] = {}

    for entry in summary:
        band_val = entry.get("band")
        fish_list = entry.get("fish_targets") or []

        if not band_val:
            continue
        try:
            band = int(band_val)
        except (ValueError, TypeError):
            continue

        for fish in fish_list:
            if not fish or not fish.strip():
                continue
            fish_bands.setdefault(fish, []).append(band)

    result: list[dict] = []
    for fish, bands in fish_bands.items():
        result.append({
            "target": fish,
            "start_band": min(bands),
            "end_band": max(bands),
        })

    # 魚種名の辞書順で安定出力
    result.sort(key=lambda x: x["target"])
    return result


def normalize_target_ranges(raw_ranges: list[dict]) -> list[dict]:
    """
    derive_target_ranges の出力を FISH_NAME_MAP で正規化し、
    同名に集約した上で start_band=min / end_band=max を再計算する。
    """
    merged: dict[str, list[int]] = {}

    for entry in raw_ranges:
        name = FISH_NAME_MAP.get(entry["target"], entry["target"])
        merged.setdefault(name, [])
        merged[name].append(entry["start_band"])
        merged[name].append(entry["end_band"])

    result = [
        {
            "target": name,
            "start_band": min(bands),
            "end_band": max(bands),
        }
        for name, bands in merged.items()
    ]
    result.sort(key=lambda x: x["target"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="standard-band-summary.json から target-band-ranges を生成する",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=_DEFAULT_SUMMARY_PATH,
        help=(
            "standard-band-summary.json のパス（デフォルト: repo外 runs/tmp/）。"
            " runs/ が別の場所にある場合に使用。"
        ),
    )
    args = parser.parse_args()
    summary_path: Path = args.input

    if not summary_path.exists():
        print(
            f"[ERROR] 入力ファイルが見つかりません: {summary_path}\n"
            f"\n"
            f"  runs/ は repo 外の一時出力ディレクトリです。\n"
            f"  build_standard_band_summary.py を先に実行してください:\n"
            f"\n"
            f"    python crawler/build_standard_band_summary.py\n"
            f"\n"
            f"  別のパスに出力した場合は --input で指定できます:\n"
            f"\n"
            f"    python scripts/run_target_band_ranges_generator.py --input /path/to/standard-band-summary.json",
            file=sys.stderr,
        )
        sys.exit(1)

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manual  = json.loads(_MANUAL_PATH.read_text(encoding="utf-8"))

    common = {
        "bands":       manual["bands"],
        "brand_bands": manual["brand_bands"],
    }
    source_str = str(summary_path)

    # --- generated (生に近い確認用)
    generated_ranges = derive_target_ranges(summary)
    _OUT_GENERATED.write_text(
        json.dumps({
            "_comment": "自動生成・生データに近い確認用。手動ファイル target-band-ranges.json は別途維持。",
            "_version": "generated",
            "_source": source_str,
            **common,
            "target_ranges": generated_ranges,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # --- normalized (UI/比較接続用)
    normalized_ranges = normalize_target_ranges(generated_ranges)
    _OUT_NORMALIZED.write_text(
        json.dumps({
            "_comment": "正規化済み。UI/比較用途。魚種名を FISH_NAME_MAP で統一。",
            "_version": "normalized",
            "_source": source_str,
            **common,
            "target_ranges": normalized_ranges,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"generated 魚種数: {len(generated_ranges)}")
    print(f"normalized 魚種数: {len(normalized_ranges)}")
    for r in normalized_ranges:
        print(f"  {r['target']:14s}  {r['start_band']}〜{r['end_band']}")
    print(f"\n[SAVED] {_OUT_GENERATED}")
    print(f"[SAVED] {_OUT_NORMALIZED}")


if __name__ == "__main__":
    main()
