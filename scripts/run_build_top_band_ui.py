#!/usr/bin/env python3
"""
top-band.html 生成スクリプト

入力: ../../runs/tmp/standard-band-summary.json
出力: ui/top-band.html（自己完結 HTML）

X軸: 全番手を均等配置 [100,200,300,400,500,600,1000,2000,3000,4000,6000]
DAIWA / SHIMANO 各1行（3桁4桁統合）
魚種: ブランド別2本バーで同軸表示
"""

from __future__ import annotations

import json
from pathlib import Path

_BASE_DIR     = Path(__file__).resolve().parent.parent
_SUMMARY_PATH = _BASE_DIR.parent / "runs" / "tmp" / "standard-band-summary.json"
_OUT_PATH     = _BASE_DIR / "ui" / "top-band.html"

FISH_NAME_MAP: dict[str, str] = {
    "ブリ類": "ブリ", "イカ類": "イカ", "ムツ類": "ムツ",
    "マグロ類": "マグロ", "ハタ類": "ハタ", "カサゴ類": "カサゴ",
    "ゾイ類": "ゾイ", "サケ・マス類": "サケ・マス",
}

# 全番手を均等配置する統一軸
UNIFIED_TICKS = [100, 200, 300, 400, 500, 600, 1000, 2000, 3000, 4000, 6000]


def build_fish_brand_ranges(summary: list[dict]) -> dict:
    """魚種×ブランド別の start/end を統一軸番手で返す。"""
    fish_maker_bands: dict[str, dict[str, list[int]]] = {}
    for entry in summary:
        maker = entry.get("brand", "")
        band = int(entry.get("band", 0))
        if band not in UNIFIED_TICKS:
            continue
        for raw_fish in entry.get("fish_targets") or []:
            if not raw_fish:
                continue
            fish = FISH_NAME_MAP.get(raw_fish, raw_fish)
            fish_maker_bands.setdefault(fish, {}).setdefault(maker, []).append(band)

    result: dict[str, dict] = {}
    for fish, maker_map in fish_maker_bands.items():
        result[fish] = {}
        for maker, bands in maker_map.items():
            result[fish][maker] = {"start": min(bands), "end": max(bands)}
    return result


def build_brand_active(summary: list[dict]) -> dict:
    """ブランドごとのアクティブ番手リストを返す。"""
    active: dict[str, set[int]] = {}
    for entry in summary:
        maker = entry.get("brand", "")
        band = int(entry.get("band", 0))
        if band in UNIFIED_TICKS:
            active.setdefault(maker, set()).add(band)
    return {k: sorted(v) for k, v in active.items()}


_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>電動リール 番手帯チャート</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: "Hiragino Sans", "Noto Sans JP", sans-serif;
       font-size: 13px; padding: 24px; background: #f0f4f8; color: #333; }}
h2 {{ font-size: 15px; font-weight: 700; margin-bottom: 20px; color: #2c3e50; }}
.chart {{ max-width: 800px; }}

/* ブランド行 */
.brand-row {{
  display: flex; align-items: center; margin-bottom: 6px;
}}
.brand-label {{
  width: 100px; flex-shrink: 0;
  font-size: 12px; font-weight: 800;
  text-align: right; padding-right: 12px;
  color: #444; line-height: 1.3;
}}
.track {{
  position: relative; flex: 1; height: 30px;
}}
.track-bg {{
  position: absolute; inset: 3px 0;
  border-radius: 6px; background: #dee3ea;
}}
/* セグメント（連続アクティブ帯をまとめて描画） */
.seg {{
  position: absolute; top: 3px; height: calc(100% - 6px);
}}
.seg-daiwa   {{ background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%); }}
.seg-shimano {{ background: linear-gradient(135deg, #e07840 0%, #c96530 100%); }}
/* 番手ラベル（バーの上に白文字） */
.tick {{
  position: absolute; top: 0; height: 100%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700;
  color: rgba(255,255,255,0.92);
  pointer-events: none; white-space: nowrap;
}}

.section-gap {{ height: 18px; }}

/* 魚種行 */
.fish-row {{
  display: flex; align-items: stretch; margin-bottom: 4px;
}}
.fish-label {{
  width: 100px; flex-shrink: 0;
  font-size: 12px; font-weight: 500;
  text-align: right; padding-right: 12px;
  color: #444; white-space: nowrap;
  display: flex; align-items: center; justify-content: flex-end;
}}
.fish-tracks {{
  flex: 1; display: flex; flex-direction: column;
  gap: 2px; padding: 1px 0;
}}
.fish-track {{
  position: relative; height: 12px;
}}
.fish-bar {{
  position: absolute; top: 0; height: 100%;
  border-radius: 3px; opacity: 0.82;
}}
.fish-bar-daiwa   {{ background: #4a90d9; }}
.fish-bar-shimano {{ background: #e07840; }}

/* 凡例 */
.legend {{
  display: flex; gap: 16px; margin-bottom: 16px; font-size: 11px; color: #666;
}}
.legend-item {{ display: flex; align-items: center; gap: 4px; }}
.legend-swatch {{
  width: 14px; height: 10px; border-radius: 2px;
}}
</style>
</head>
<body>
<h2>電動リール 番手帯チャート</h2>
<div class="legend">
  <div class="legend-item"><div class="legend-swatch" style="background:#4a90d9"></div>DAIWA</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#e07840"></div>SHIMANO</div>
</div>
<div class="chart" id="chart"></div>
<script>
const RANGES = {ranges_json};
const BRAND_ACTIVE = {brand_active_json};

const TICKS = {ticks_json};
const N = TICKS.length;
const W = 100 / N;  // 各ティック幅 %

function tickIdx(v)   {{ return TICKS.indexOf(v); }}
function pctL(v)      {{ return tickIdx(v) * W; }}
function pctW(s, e)   {{ return (tickIdx(e) - tickIdx(s) + 1) * W; }}

function el(tag, cls)  {{ const e = document.createElement(tag); if (cls) e.className = cls; return e; }}

const chart = document.getElementById('chart');

// ===== ブランド行 =====
const BRANDS = [
  {{ key: 'daiwa',   label: 'DAIWA',   cls: 'seg-daiwa' }},
  {{ key: 'shimano', label: 'SHIMANO', cls: 'seg-shimano' }},
];

for (const brand of BRANDS) {{
  const row = el('div', 'brand-row');
  const lbl = el('div', 'brand-label');
  lbl.textContent = brand.label;
  row.appendChild(lbl);

  const track = el('div', 'track');
  track.appendChild(el('div', 'track-bg'));

  const active = BRAND_ACTIVE[brand.key] || [];
  // 連続区間をまとめて描画
  let segStart = null;
  for (let i = 0; i <= TICKS.length; i++) {{
    const t = TICKS[i];
    const on = t !== undefined && active.includes(t);
    if (on && segStart === null) segStart = t;
    if (!on && segStart !== null) {{
      const segEnd = TICKS[i - 1];
      const left  = pctL(segStart);
      const width = pctW(segStart, segEnd);
      const s = el('div', `seg ${{brand.cls}}`);
      s.style.left = left + '%';
      s.style.width = width + '%';
      const rL = left < 0.1 ? '6px' : '0';
      const rR = left + width > 99.9 ? '6px' : '0';
      s.style.borderRadius = `${{rL}} ${{rR}} ${{rR}} ${{rL}}`;
      track.appendChild(s);

      // 番手ラベル
      for (let j = tickIdx(segStart); j <= tickIdx(segEnd); j++) {{
        const tk = el('div', 'tick');
        tk.style.left = (j * W) + '%';
        tk.style.width = W + '%';
        tk.textContent = TICKS[j];
        track.appendChild(tk);
      }}
      segStart = null;
    }}
  }}

  row.appendChild(track);
  chart.appendChild(row);
}}

chart.appendChild(el('div', 'section-gap'));

// ===== 魚種行 =====
const allFish = [...new Set(Object.keys(RANGES))].sort((a, b) => a.localeCompare(b, 'ja'));

for (const fish of allFish) {{
  const data = RANGES[fish] || {{}};
  const hasDaiwa   = data.daiwa   && tickIdx(data.daiwa.start) >= 0;
  const hasShimano = data.shimano && tickIdx(data.shimano.start) >= 0;
  if (!hasDaiwa && !hasShimano) continue;

  const row = el('div', 'fish-row');
  const lbl = el('div', 'fish-label');
  lbl.textContent = fish;
  row.appendChild(lbl);

  const tracks = el('div', 'fish-tracks');

  for (const [key, cls] of [['daiwa', 'fish-bar-daiwa'], ['shimano', 'fish-bar-shimano']]) {{
    const tr = el('div', 'fish-track');
    const r = data[key];
    if (r && tickIdx(r.start) >= 0 && tickIdx(r.end) >= 0) {{
      const bar = el('div', `fish-bar ${{cls}}`);
      bar.style.left  = pctL(r.start) + '%';
      bar.style.width = pctW(r.start, r.end) + '%';
      tr.appendChild(bar);
    }}
    tracks.appendChild(tr);
  }}

  row.appendChild(tracks);
  chart.appendChild(row);
}}
</script>
</body>
</html>
"""


def main() -> None:
    summary = json.loads(_SUMMARY_PATH.read_text(encoding="utf-8"))
    fish_brand_ranges = build_fish_brand_ranges(summary)
    brand_active = build_brand_active(summary)

    html = _TEMPLATE.format(
        ranges_json       = json.dumps(fish_brand_ranges, ensure_ascii=False),
        brand_active_json = json.dumps(brand_active, ensure_ascii=False),
        ticks_json        = json.dumps(UNIFIED_TICKS),
    )

    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUT_PATH.write_text(html, encoding="utf-8")
    print(f"[SAVED] {_OUT_PATH}")


if __name__ == "__main__":
    main()
