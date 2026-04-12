# Label Dictionary — Electric Reel Derived Fields

`spec_rows_raw` の `label` フィールドから derived fields へのマッピング定義。

> **v2 更新** (2026-04-12): DAIWA バリエーション 6 件 + SHIMANO 固有ラベル 5 種を  
> Baseline 辞書に昇格。AI-only エイリアスは大幅に縮小。

---

## Baseline 辞書 v2（厳密一致）

`scripts/normalizers/electric_reel_minimal.py` の `LABEL_DICT` に対応。  
ラベルテキストが**完全一致**した場合のみフィールドに値を充填する。

### weight_g

| ラベル              | 出典                              |
|--------------------|-----------------------------------|
| `自重(g)`          | DAIWA 標準                        |
| `自重`             | DAIWA 簡略表記（303J-style）      |
| `標準自重（ｇ）`   | 全角括弧・全角 g（テスト inline）  |
| `重量(g)`          | 代替表現                          |

### gear_ratio

| ラベル    | 出典                            |
|----------|---------------------------------|
| `ギア比` | DAIWA 標準                      |
| `ギヤ比` | SHIMANO 固有（ヤ / dakuten）    |

### max_drag_kg

| ラベル             | 出典                                      |
|-------------------|-------------------------------------------|
| `最大ドラグ力(kg)` | 標準                                      |
| `最大ドラグ(kg)`  | 「力」なし簡略表記（DAIWA 306J-style）    |
| `ドラグ力(kg)`    | 短縮形                                    |
| `最大ドラグ力`     | 単位なし                                  |

### handle_length_mm

| ラベル               | 出典                                          |
|---------------------|-----------------------------------------------|
| `ハンドル長(mm)`    | DAIWA 標準                                    |
| `ハンドル長さ(mm)`  | さ付き（DAIWA 304J-style / SHIMANO 共通）     |
| `ハンドル全長(mm)`  | 全長表記バリアント                            |
| `ハンドル長`        | 単位なし（高曖昧度のため AI-only に留めることも検討） |

### bearing_desc

| ラベル                       | 出典                              |
|-----------------------------|-----------------------------------|
| `ベアリング数(BB/RB)`        | DAIWA 標準                        |
| `ベアリング(BB/RB)`          | 「数」なし（DAIWA 310J-style）    |
| `ボール/ローラーベアリング数` | SHIMANO 固有フォーマット           |
| `ベアリング数`               | 単位なし                          |

*値フォーマット注意*: DAIWA は `8/1`（BB/RB）、SHIMANO は `8+1` が多い。  
どちらも raw 文字列として保持（下流の parse 層で正規化すること）。

### spool_capacity_text

| ラベル              | 出典                                        |
|--------------------|---------------------------------------------|
| `巻糸量(PE号-m)`   | DAIWA 標準                                  |
| `糸巻量(PE号-m)`   | DAIWA 305J-style / SHIMANO（語順逆）        |
| `糸巻量(PE-号-m)`  | SHIMANO 固有: 「号」前にハイフン追加        |
| `糸巻量`           | 単位なし                                    |
| `巻糸量`           | 単位なし                                    |

*Description fallback*: ラベルが**存在しない**場合、`description_raw` を  
正規表現 `PE\d+号-\d+m` で検索して raw テキストを回収する。  
（`normalize_all()` / `build_normalized()` が自動適用）

### electric_power_desc

| ラベル         | 出典                                        |
|---------------|---------------------------------------------|
| `対応電源`    | DAIWA 標準                                  |
| `使用電源`    | DAIWA 309J-style / SHIMANO                 |
| `電源`        | SHIMANO 短縮形                              |
| `対応バッテリー` | バッテリー表記バリアント                  |

---

## AI-only エイリアス（v2 時点で残存）

v2 で大幅縮小。以下は曖昧度が高いか出現頻度が低いため  
baseline 辞書に入れず AI mock にのみ保持している。

| ラベル             | → field               | 理由                                              |
|-------------------|-----------------------|---------------------------------------------------|
| `ハンドル長`       | `handle_length_mm`    | 単位なし → 別フィールドとの混同リスクあり         |
| `ベアリング`       | `bearing_desc`        | 単語単体 → 他の文脈でも出うる                     |
| `ラインキャパシティ`| `spool_capacity_text`| 英語由来 / 出現頻度不明                           |
| `本体重量(g)`     | `weight_g`            | 非常にまれ                                        |

---

## Description Fallback（v2 で baseline に組み込み済み）

スペック表に巻糸量行が**存在しない**場合、`normalize_all()` が  
`description_raw` に対して以下のパターンを検索する：

```
PE\s*\d+(?:\.\d+)?号\s*[\-/]\s*\d+(?:\s*m)?
```

例: `"PE3号-300mの糸巻量で…"` → `spool_capacity_text = "PE3号-300m"`

- raw 値をそのまま保持（変換しない）
- フォールバックの連鎖は 1 段のみ（複数フィールドに拡張しない）

---

## 辞書の管理方針

1. **Additive 運用** — 既存エントリは削除しない
2. **昇格基準** — 実データ確認済み・複数メーカーで出現・曖昧度が低い
3. **ギア比** は DAIWA/SHIMANO とも `ギア比` / `ギヤ比` の 2 表記のみで安定
4. **数値列の fallback** は安全なものだけ（文字列列は raw 値保持優先）
5. 新ラベル追加時は `LABEL_DICT` と `AI_LABEL_ALIASES` を同時更新して gap を維持

---

## 追加が必要になったら

```
scripts/normalizers/electric_reel_minimal.py  → LABEL_DICT に追記
scripts/evaluate_ai_correction.py             → AI_LABEL_ALIASES も同期
docs/minimal-label-dictionary-electric-reel-derived-fields.md → この文書を更新
```
