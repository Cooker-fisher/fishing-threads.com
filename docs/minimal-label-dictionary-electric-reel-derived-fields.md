# Label Dictionary — Electric Reel Derived Fields

`spec_rows_raw` の `label` フィールドから derived fields へのマッピング定義。

---

## Baseline 辞書（厳密一致）

`scripts/normalizers/electric_reel_minimal.py` の `LABEL_DICT` に対応。  
ラベルテキストが**完全一致**した場合のみフィールドに値を充填する。

| spec_rows_raw のラベル   | → derived field       | 備考                        |
|-------------------------|----------------------|-----------------------------|
| `自重(g)`               | `weight_g`           | 標準表記                    |
| `ギア比`                | `gear_ratio`         | 表記揺れが少ない            |
| `最大ドラグ力(kg)`      | `max_drag_kg`        | 「力」が入るのが DAIWA 標準 |
| `ハンドル長(mm)`        | `handle_length_mm`   | mm 入り表記が標準           |
| `ベアリング数(BB/RB)`   | `bearing_desc`       | 数字スラッシュ形式も混在    |
| `巻糸量(PE号-m)`        | `spool_capacity_text`| 「巻糸量」が DAIWA 標準     |
| `対応電源`              | `electric_power_desc`|                             |

---

## AI 拡張エイリアス

`scripts/evaluate_ai_correction.py` の `AI_LABEL_ALIASES` に対応。  
Baseline で取り逃がしたラベルを追加で補完する。

| spec_rows_raw のラベル（バリエーション）  | → derived field       | 例外・備考                           |
|------------------------------------------|----------------------|--------------------------------------|
| `自重`（単位なし）                        | `weight_g`           | 古い表記や簡略表記でよく出現         |
| `重量(g)`, `本体重量(g)`                 | `weight_g`           | 非 DAIWA メーカーや古いページ        |
| `標準自重（ｇ）`                         | `weight_g`           | 全角括弧・全角 g の表記              |
| `最大ドラグ(kg)`（「力」なし）           | `max_drag_kg`        | 簡略表記。実測で 1/10 件程度出現      |
| `ドラグ力(kg)`                           | `max_drag_kg`        |                                      |
| `最大ドラグ力`（単位なし）               | `max_drag_kg`        |                                      |
| `ハンドル長さ(mm)`                       | `handle_length_mm`   | 「さ」ありの表記                     |
| `ハンドル全長(mm)`                       | `handle_length_mm`   |                                      |
| `ハンドル長`（単位なし）                 | `handle_length_mm`   |                                      |
| `ベアリング(BB/RB)`（「数」なし）        | `bearing_desc`       | 簡略表記                             |
| `ベアリング数`, `ベアリング`             | `bearing_desc`       | 単位表記なし                         |
| `糸巻量(PE号-m)`                         | `spool_capacity_text`| 「巻糸量」と「糸巻量」の逆順         |
| `糸巻量`, `巻糸量`                       | `spool_capacity_text`| 単位表記なし                         |
| `ラインキャパシティ`                     | `spool_capacity_text`| 英語由来の表記                       |
| `使用電源`                               | `electric_power_desc`| 「対応」→「使用」の言い換え          |
| `電源`, `対応バッテリー`                 | `electric_power_desc`|                                      |

---

## Description テキストからの回収（AI のみ）

スペック表に `巻糸量` 系のラベルが**存在しない**場合、AI は `description_raw` の
テキストから以下の正規表現でスプール容量を回収する：

```
PE\s*\d+(?:\.\d+)?号\s*[\-/]\s*\d+(?:\s*m)?
```

例: `"PE3号-300mの糸巻量で…"` → `spool_capacity_text = "PE3号-300m"`

Baseline はこの fallback を持たない。

---

## 辞書の管理方針

1. **Baseline 辞書は最小に保つ**  
   標準ラベル（最も一般的な表記のみ）を登録する。
   辞書の肥大化は偽陽性（誤ラベルマッチ）を招く。

2. **AI エイリアスは評価後に判断**  
   AI エイリアスで significant な improvement が確認されたラベルのみ
   baseline 辞書に昇格させる。コストに見合わない場合は却下。

3. **ギア比は表記が安定しているため両辞書で共通**  
   今回の評価範囲では改善なし。

---

## 追加が必要になったら

`scripts/normalizers/electric_reel_minimal.py` の `LABEL_DICT` に追記し、
`scripts/evaluate_ai_correction.py` の `AI_LABEL_ALIASES` も同期させること。
