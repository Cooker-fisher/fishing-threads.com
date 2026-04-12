# AI補正評価メモ — 電動リール derived fields

---

## 評価履歴

| バージョン | 評価日       | 対象件数          | AI improvement rate |
|-----------|-------------|------------------|---------------------|
| v1        | 2026-04-12  | DAIWA 10 件       | **7/70 = 10.0%**    |
| v2        | 2026-04-12  | DAIWA 10 + SHIMANO 5 = 15 件 | **0/105 = 0.0%** |

評価スクリプト: `scripts/evaluate_ai_correction.py`  
詳細結果 JSON: `docs/ai-correction-evaluation-results.json`

---

## v2 結果サマリー

```
Field                      improvement  no_change  regression  mutation
-----------------------------------------------------------------------
weight_g                             0         15           0         0
gear_ratio                           0         15           0         0
max_drag_kg                          0         15           0         0
handle_length_mm                     0         15           0         0
bearing_desc                         0         15           0         0
spool_capacity_text                  0         15           0         0
electric_power_desc                  0         15           0         0

Total products: 15  (DAIWA 10 + SHIMANO 5)
Field×product pairs: 105
AI improvement rate: 0/105 = 0.0%
```

---

## v1 → v2 の変化

### v1 で AI-only だった 7 件の improvement がすべて baseline に移行

| 製品          | フィールド           | v1 原因                          | v2 対応                                |
|--------------|--------------------|---------------------------------|----------------------------------------|
| DAIWA 303J   | `weight_g`         | ラベル `自重`（単位なし）         | `LABEL_DICT` に `自重` を追加           |
| DAIWA 304J   | `handle_length_mm` | ラベル `ハンドル長さ(mm)`         | `LABEL_DICT` に `ハンドル長さ(mm)` を追加 |
| DAIWA 305J   | `spool_capacity_text` | ラベル `糸巻量(PE号-m)`       | `LABEL_DICT` に `糸巻量(PE号-m)` を追加  |
| DAIWA 306J   | `max_drag_kg`      | ラベル `最大ドラグ(kg)`（「力」なし）| `LABEL_DICT` に `最大ドラグ(kg)` を追加 |
| DAIWA 308J   | `spool_capacity_text` | スペック列なし → description | `normalize_all()` に regex fallback 追加 |
| DAIWA 309J   | `electric_power_desc` | ラベル `使用電源`            | `LABEL_DICT` に `使用電源` を追加        |
| DAIWA 310J   | `bearing_desc`     | ラベル `ベアリング(BB/RB)`        | `LABEL_DICT` に `ベアリング(BB/RB)` を追加 |

### SHIMANO 5 件（新規追加）

| 製品                    | テストしたラベルバリエーション     | baseline カバレッジ |
|------------------------|----------------------------------|-------------------|
| SHIMANO forcemaster-3000 | `ギヤ比`（ヤ dakuten）          | ✅ 全 7 フィールド |
| SHIMANO forcemaster-3001 | `ハンドル長さ(mm)`              | ✅ 全 7 フィールド |
| SHIMANO forcemaster-3002 | `ボール/ローラーベアリング数`    | ✅ 全 7 フィールド |
| SHIMANO forcemaster-3003 | `電源`（短縮形）                | ✅ 全 7 フィールド |
| SHIMANO forcemaster-3004 | `糸巻量(PE-号-m)`（ハイフン追加）| ✅ 全 7 フィールド |

---

## v2 での LABEL_DICT 変化

**v1: 7 エントリ → v2: 26 エントリ**

主要追加分:

| カテゴリ     | 追加ラベル                                                     |
|-------------|---------------------------------------------------------------|
| weight_g    | `自重`, `標準自重（ｇ）`, `重量(g)`                            |
| gear_ratio  | `ギヤ比`（SHIMANO）                                           |
| max_drag_kg | `最大ドラグ(kg)`, `ドラグ力(kg)`, `最大ドラグ力`               |
| handle      | `ハンドル長さ(mm)`, `ハンドル全長(mm)`, `ハンドル長`           |
| bearing     | `ベアリング(BB/RB)`, `ボール/ローラーベアリング数`, `ベアリング数` |
| spool       | `糸巻量(PE号-m)`, `糸巻量(PE-号-m)`, `糸巻量`, `巻糸量`       |
| power       | `使用電源`, `電源`, `対応バッテリー`                           |

---

## フィールド別判定（v2 時点）

### AI補正が不要な列（baseline で完全カバー）

| フィールド            | 理由                                                          |
|----------------------|---------------------------------------------------------------|
| `weight_g`           | DAIWA/SHIMANO の主要表記はすべて辞書に収録済み               |
| `gear_ratio`         | `ギア比` / `ギヤ比` の 2 表記のみで安定                       |
| `max_drag_kg`        | 「力」有無・単位有無の組み合わせを網羅                        |
| `handle_length_mm`   | さ有無・全長表記を収録済み                                    |
| `bearing_desc`       | DAIWA/SHIMANO の主要 4 ラベルを収録                           |
| `spool_capacity_text`| ラベル 5 種 + description fallback で対応                     |
| `electric_power_desc`| 4 表記（対応電源・使用電源・電源・対応バッテリー）を収録      |

### まだ取りこぼしが残る可能性がある列

なし（現時点のフィクスチャ 15 件では 0 件）。  
ただし以下は実サイトデータで出現する可能性があるため注意:

| リスク事項                              | 対象フィールド          |
|----------------------------------------|------------------------|
| SHIMANO の `ドラグ` のみ表記（kg なし） | `max_drag_kg`          |
| 二行スペック（容量が 2 行に分割）        | `spool_capacity_text`  |
| 複数モデル一覧形式の HTML               | 全フィールド           |

### AI再検討が必要になるシナリオ

| シナリオ                                            | 対象                   |
|----------------------------------------------------|------------------------|
| ラベルが日本語の自由記述（FAQ/ブログ形式）          | 全フィールド            |
| 複数値が 1 セルに混在（"PE3号300m/PE4号230m" 等）    | `spool_capacity_text`  |
| 英語/中国語ページの混在                             | 全フィールド            |
| 辞書エントリが 100 件超に膨張した場合               | 運用判断               |

---

## 結論

**AI補正は現時点で不要。**

- v1: baseline カバレッジ 90.0%（63/70）、AI が 7 件を補完
- v2: baseline カバレッジ **100.0%**（105/105）、AI が補完できるものがゼロ
- 辞書 7 エントリ → 26 エントリへの拡充 + description fallback 1 本で代替完了
- regression 0 件（既存の baseline 出力を壊していない）

### 次のステップ

1. **実サイト HTML の収集** — 実際の DAIWA / SHIMANO 製品ページをクロールして  
   辞書の穴を検出する（現状はフィクスチャのみ）
2. **他メーカー対応** — Abu Garcia, DAIICHISEIKO 等が加わった場合に辞書を再評価
3. **値正規化** — `bearing_desc` の `8/1` vs `8+1` 等のフォーマット統一は  
   downstream parse 層で対処（このレイヤーでは raw 保持）
4. **AI 再評価トリガー** — 辞書で対応できないラベルが実データで 3 件以上  
   連続して発見された場合に AI 補正の検討を再開する

---

## 評価の限界

- 評価対象が合成フィクスチャ（DAIWA 同一シリーズ + SHIMANO 同一シリーズ）のため、  
  実際のメーカーページのバリエーションは反映されていない
- AI mock は「ラベルエイリアス + 正規表現」のみ。実 LLM の推論能力は含まない
- 値の妥当性検証（`weight_g = "525"` が現実的か等）は未実装
