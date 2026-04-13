#!/usr/bin/env python3
"""
top-band.html 生成スクリプト

入力: raw/target-band-ranges.normalized.json
出力: ui/top-band.html（自己完結 HTML）

- JSON データをインライン埋め込みして生成
- ブラウザで直接開ける（サーバー不要）
- 帯だけ描画。文字レンジ表記なし。
"""

from __future__ import annotations

import json
from pathlib import Path

_BASE_DIR  = Path(__file__).resolve().parent.parent
_DATA_PATH = _BASE_DIR / "raw" / "target-band-ranges.normalized.json"
_OUT_PATH  = _BASE_DIR / "ui" / "top-band.html"

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>電動リール 番手帯チャート</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: sans-serif; font-size: 13px; padding: 24px; background: #f8f8f8; color: #333; }}
h2 {{ font-size: 14px; font-weight: 600; margin-bottom: 16px; color: #444; }}

.chart {{ max-width: 680px; }}

/* 各行: label 1列 + band 6列 */
.row {{
  display: grid;
  grid-template-columns: 96px repeat({band_count}, 1fr);
  column-gap: 3px;
  margin-bottom: 3px;
  align-items: center;
}}

/* ヘッダー */
.hdr-label {{ /* empty */ }}
.hdr-cell {{
  text-align: center;
  font-size: 11px;
  color: #999;
  padding-bottom: 4px;
}}

/* ブランド行 */
.brand-label {{
  font-size: 11px;
  font-weight: 600;
  text-align: right;
  padding-right: 8px;
  color: #555;
  letter-spacing: 0.03em;
}}
.band-cell {{
  height: 20px;
  border-radius: 3px;
  background: #e8e8e8;
}}
.band-daiwa   {{ background: #4a90d9; }}
.band-shimano {{ background: #e87040; }}

/* 区切り */
.gap {{ height: 10px; }}

/* 魚種行 */
.fish-label {{
  font-size: 12px;
  text-align: right;
  padding-right: 8px;
  color: #444;
}}
.fish-bar {{
  height: 18px;
  border-radius: 3px;
  background: #5a9e6f;
}}
</style>
</head>
<body>
<h2>電動リール 番手帯チャート</h2>
<div class="chart" id="chart"></div>
<script>
const DATA = {data_json};

const bands = DATA.bands;
const N = bands.length;

function el(tag, cls) {{
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}}

const chart = document.getElementById('chart');

// ヘッダー行
const hRow = el('div', 'row');
hRow.appendChild(el('div', 'hdr-label'));
for (const b of bands) {{
  const c = el('div', 'hdr-cell');
  c.textContent = b;
  hRow.appendChild(c);
}}
chart.appendChild(hRow);

// ブランド行（brand_bands）
const brandClass = {{ daiwa: 'band-daiwa', shimano: 'band-shimano' }};
for (const [maker, makerBands] of Object.entries(DATA.brand_bands)) {{
  const row = el('div', 'row');
  const lbl = el('div', 'brand-label');
  lbl.textContent = maker.toUpperCase();
  row.appendChild(lbl);
  for (const b of bands) {{
    const active = makerBands.includes(b);
    const cls = active ? `band-cell ${{brandClass[maker] || ''}}` : 'band-cell';
    row.appendChild(el('div', cls));
  }}
  chart.appendChild(row);
}}

// 区切り
chart.appendChild(el('div', 'gap'));

// 魚種行（target_ranges）
for (const t of DATA.target_ranges) {{
  const startIdx = bands.indexOf(t.start_band);
  const endIdx   = bands.indexOf(t.end_band);
  if (startIdx === -1 || endIdx === -1) continue;

  const row = el('div', 'row');
  const lbl = el('div', 'fish-label');
  lbl.textContent = t.target;
  row.appendChild(lbl);

  // バー: grid-column で帯位置を直接指定
  // label が column 1、bands が column 2〜N+1
  const bar = el('div', 'fish-bar');
  bar.style.gridColumn = `${{startIdx + 2}} / ${{endIdx + 3}}`;
  row.appendChild(bar);

  chart.appendChild(row);
}}
</script>
</body>
</html>
"""


def main() -> None:
    data = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    data_json = json.dumps(data, ensure_ascii=False)
    band_count = len(data["bands"])

    html = _TEMPLATE.format(data_json=data_json, band_count=band_count)

    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUT_PATH.write_text(html, encoding="utf-8")
    print(f"[SAVED] {_OUT_PATH}")


if __name__ == "__main__":
    main()
