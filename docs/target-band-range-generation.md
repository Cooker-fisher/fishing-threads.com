# target-band-ranges 生成メモ

## ファイル構成

| ファイル | 種別 | 説明 |
|---------|------|------|
| `raw/target-band-ranges.json` | 手動 | v0.1.0 仮レンジ。触らない。 |
| `raw/target-band-ranges.generated.json` | 自動生成・生に近い確認用 | 集計名称そのまま（「類」付き等）。構造確認・デバッグ用。 |
| `raw/target-band-ranges.normalized.json` | 自動生成・UI/比較接続用 | 魚種名を `FISH_NAME_MAP` で統一済み。UIが参照するのはこちら。 |

## 生成スクリプト

```
scripts/run_target_band_ranges_generator.py
```

### 入力

`runs/tmp/standard-band-summary.json`（`build_standard_band_summary.py` の出力）

### 出力

両ファイルとも `bands` / `brand_bands` は手動 JSON から引き継ぎ、`target_ranges` のみ自動導出。

#### generated（生に近い確認用）

- 集計名称そのまま出力（`ブリ類`, `イカ類` 等）
- 構造確認・抽出ロジックのデバッグ用途

#### normalized（UI/比較接続用）

- `FISH_NAME_MAP` で魚種名を正規化（`ブリ類 → ブリ` 等）
- 正規化後に同名になったレコードは `start_band=min / end_band=max` で統合

### 導出ルール（共通）

1. `standard-band-summary.json` の各エントリ（帯×ブランド）を走査
2. `fish_targets` の各魚種名について、出現した `band` を収集
3. 最小値 → `start_band`、最大値 → `end_band`
4. 空文字・null は除外

### 正規化辞書（FISH_NAME_MAP）

スクリプト内の `FISH_NAME_MAP` で管理。現在の定義:

| 生データ名 | 正規化後 |
|-----------|---------|
| ブリ類 | ブリ |
| イカ類 | イカ |
| ムツ類 | ムツ |
| マグロ類 | マグロ |
| ハタ類 | ハタ |
| カサゴ類 | カサゴ |
| ゾイ類 | ゾイ |
| サケ・マス類 | サケ・マス |

辞書にない名称はそのまま通す。

## 手動仮値を残す理由

- `raw/target-band-ranges.json`（手動）は設計上の意図値（UIに出す魚種の選別・名称）
- `generated.json` は実データ由来の確認用
- `normalized.json` は UI/比較用接続の実用版
- 3ファイルは別責務。削除せず並存させる。

## 再生成

```bash
python scripts/run_target_band_ranges_generator.py
```

`standard-band-summary.json` を更新した後に再実行すれば `generated.json` が上書きされる。
