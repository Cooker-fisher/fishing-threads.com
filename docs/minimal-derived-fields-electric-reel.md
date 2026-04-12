# Minimal Derived Fields — Electric Reel

電動リール用の derived fields スキーマ定義（最小構成）。

## 目的

`spec_rows_raw`（spec extractor が出力するラベル・値ペアの配列）から、
評価・比較に使う7フィールドを導出する。  
ここで定義するフィールドは **AI補正評価の対象列** でもある。

---

## フィールド一覧

| フィールド名          | 型          | 説明                          | 例                  |
|----------------------|-------------|-------------------------------|---------------------|
| `weight_g`           | string\|null | 自重（グラム）                | `"490"`             |
| `gear_ratio`         | string\|null | ギア比                        | `"3.6"`             |
| `max_drag_kg`        | string\|null | 最大ドラグ力（kg）            | `"10"`              |
| `handle_length_mm`   | string\|null | ハンドル長（mm）              | `"130"`             |
| `bearing_desc`       | string\|null | ベアリング数 raw 記述         | `"8/1"`, `"8BB+1RB"` |
| `spool_capacity_text`| string\|null | 糸巻量テキスト raw            | `"3-300/4-230"`     |
| `electric_power_desc`| string\|null | 対応電源テキスト              | `"12V/24V"`         |

### 設計方針

- すべて **raw string** で保持する（数値パースや単位正規化はこのレイヤーでは行わない）
- `null` は「スペック表に該当ラベルが存在しない or 空値」を意味する
- `bearing_desc` は `"8/1"` (BB数/RB数) と `"8BB+1RB"` のような表記揺れが存在する。
  フォーマット正規化は downstream に委ねる。

---

## 出力スキーマ（normalized JSON）

```json
{
  "id": "daiwa-レオブリッツ-301j",
  "maker": "daiwa",
  "series_name": "レオブリッツ",
  "model_name": "レオブリッツ 301J",
  "variant_name": "301J",
  "weight_g": "490",
  "gear_ratio": "3.6",
  "max_drag_kg": "10",
  "handle_length_mm": "130",
  "bearing_desc": "8/1",
  "spool_capacity_text": "3-300/4-230",
  "electric_power_desc": "12V/24V",
  "_meta": {
    "normalizer": "electric_reel_minimal",
    "normalizer_version": "v1",
    "source_raw_id": "daiwa-レオブリッツ-301j"
  }
}
```

---

## 生成方法

```bash
# バッチ実行（raw/ 以下をすべて処理）
python -m scripts.normalizers.electric_reel_minimal --raw-dir . --out-dir .

# AI補正評価と同時生成（推奨）
python scripts/evaluate_ai_correction.py
```

出力先: `normalized/products/electric/<maker>/<product-id>.json`

---

## 関連ドキュメント

- [`minimal-label-dictionary-electric-reel-derived-fields.md`](./minimal-label-dictionary-electric-reel-derived-fields.md)
  — ラベル辞書の詳細（baseline vs AI alias）
- [`ai-correction-evaluation-memo.md`](./ai-correction-evaluation-memo.md)
  — AI補正の評価結果と判断メモ
