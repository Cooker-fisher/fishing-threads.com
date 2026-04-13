"""
run_target_band_ranges_generator の最小テスト
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run_target_band_ranges_generator import derive_target_ranges, normalize_target_ranges


def _make_entry(band: str, fish: list[str]) -> dict:
    return {"band": band, "brand": "daiwa", "fish_targets": fish}


def test_single_fish_single_band():
    summary = [_make_entry("300", ["マダイ"])]
    result = derive_target_ranges(summary)
    assert result == [{"target": "マダイ", "start_band": 300, "end_band": 300}]


def test_start_end_band_from_multiple_entries():
    summary = [
        _make_entry("200", ["ブリ類"]),
        _make_entry("400", ["ブリ類"]),
        _make_entry("600", ["ブリ類"]),
    ]
    result = derive_target_ranges(summary)
    assert len(result) == 1
    r = result[0]
    assert r["target"] == "ブリ類"
    assert r["start_band"] == 200
    assert r["end_band"] == 600


def test_empty_and_null_fish_excluded():
    summary = [_make_entry("100", ["", None, "アジ"])]
    result = derive_target_ranges(summary)
    targets = [r["target"] for r in result]
    assert "アジ" in targets
    assert "" not in targets
    assert None not in targets


# --- normalize_target_ranges テスト

def test_normalize_renames_with_suffix():
    """「類」付き名称が正規化辞書で表示名に変換される。"""
    raw = [{"target": "ブリ類", "start_band": 200, "end_band": 500}]
    result = normalize_target_ranges(raw)
    assert len(result) == 1
    assert result[0]["target"] == "ブリ"
    assert result[0]["start_band"] == 200
    assert result[0]["end_band"] == 500


def test_normalize_merges_same_name_min_max():
    """正規化後に同名になったレコードは start_band=min / end_band=max で統合される。"""
    # 仮に 2 種類のレコードが同じ正規化後名称になるケースを直接作る
    raw = [
        {"target": "テスト類A", "start_band": 100, "end_band": 300},
        {"target": "テスト類A", "start_band": 400, "end_band": 600},
    ]
    result = normalize_target_ranges(raw)
    assert len(result) == 1
    assert result[0]["start_band"] == 100
    assert result[0]["end_band"] == 600


def test_generated_and_normalized_are_independent():
    """generated と normalized は別々に作れる（generated を壊さない）。"""
    summary = [
        _make_entry("200", ["ブリ類"]),
        _make_entry("400", ["ブリ類"]),
    ]
    generated = derive_target_ranges(summary)
    normalized = normalize_target_ranges(generated)

    # generated は元の名称を保持する
    assert generated[0]["target"] == "ブリ類"
    # normalized は正規化後の名称になる
    assert normalized[0]["target"] == "ブリ"
    # generated は変更されていない
    assert generated[0]["target"] == "ブリ類"
