# トップUI 帯レンジ設計メモ

## コンセプト

トップUIは「番手帯 × 魚種」を帯グラフで見せる。
文字で「200〜400」と書くのではなく、帯の範囲（start_band / end_band）で表現する。

## 構造

```
bands          標準ラインナップ帯: [100, 200, 300, 400, 500, 600]
brand_bands    メーカーごとの対応帯
target_ranges  魚種ごとに start_band / end_band を持つ
```

## ファイル

`raw/target-band-ranges.json`

## target_ranges の読み方

| フィールド | 意味 |
|-----------|------|
| target | 魚名（個別。カテゴリではない） |
| start_band | この帯から対応機種が存在し始める |
| end_band | この帯まで対応機種が存在する |

例: `{ "target": "キンメダイ", "start_band": 400, "end_band": 600 }`
→ キンメダイは 400〜600 帯の幅で帯表示する

## 現在の値は仮

`_version: 0.1.0` は手動設定の仮レンジ。
runs/tmp/standard-band-summary.json（全43製品の集計）をもとに目視で設定。

data-driven に差し替える際は:
1. standard-band-summary.json の各帯 fish_targets を走査
2. 魚種が最初に出現する帯 → start_band
3. 魚種が最後に出現する帯 → end_band
4. このファイルを自動生成スクリプトで上書き

## brand_bands の根拠

| maker | 対応帯 | 備考 |
|-------|--------|------|
| daiwa | 100〜600 全帯 | 100J〜600MJ をラインナップ |
| shimano | 200〜600 | 100帯相当なし。FM200が最小（ただし200帯扱い） |

注: shimano の 100帯は FM200/300（SHIMANO番手体系では1000/2000）が近いが、
PE号・用途とも 200帯相当として扱う。
