# DAIWA電動リール dry-run 手順

## 目的
DAIWA 電動リールの sample seed 10件を使って、一覧 → 詳細 → spec → merge が実際に通るか確認する。

## 実行コマンド
```bash
python scripts/run_daiwa_electric_dry_run.py
```

必要に応じて:
```bash
python scripts/run_daiwa_electric_dry_run.py --index-json samples/daiwa-electric-first10-raw-index-clean.json --crawl-date 2026-04-11 --out-dir .
```

## 期待する出力
- `generated=10` に近い件数
- `raw/products/daiwa/` 配下に product raw JSON が出る
- 各 product raw に `spec_rows_raw` と `jan_upc_raw` が入るものがある

## まず見るべき項目
- title / series_name / model_name / variant_name
- price_raw
- notes_raw
- spec_rows_raw
- jan_upc_raw

## 想定される失敗ポイント
- 一覧 seed の URL 切れ
- 詳細ページで本文と spec の境界がずれる
- spec の複数行対応づけが崩れる
- title parsing の例外

## ルール
- dry-run は実装検証であり、正本 raw の大量投入ではない
- 失敗したら seed を増やさず、extractor を直す
