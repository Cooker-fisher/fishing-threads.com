# DAIWA 電動リール spec ノート

## 既知の列バリエーション

### オプション列（欠落しても正常）

| 列名 | 理由 |
|------|------|
| `標準巻糸量ナイロン（号ｰm）` | PE専用機（例: レオブリッツ S400）には存在しない |
| `ハンドルアーム長（mm）` | 一部シリーズで未掲載 |

normalizer では `OPTIONAL_COLUMNS` に定義し、欠落時は `None` として扱う（エラーにしない）。

## アクセサリー除外

`リモート JOG` のようなリモコン・アクセサリー類は spec 列数が 4 と少なく、リールではない。

除外条件: **spec ヘッダ数 < 10**

これにより comparison スクリプト（`scripts/run_daiwa_electric_comparison.py`）は
- 入力 24 件 → アクセサリー 1 件除外 → リール 23 件
を出力する。

## ファイル構成

```
raw/daiwa-electric-detail-spec-20260412.json  # クロール生データ (24 items)
raw/daiwa-electric-comparison-YYYY-MM-DD.json  # 比較サマリー (23 reels)
scripts/normalizers/electric_reel_minimal.py   # normalizer
scripts/run_daiwa_electric_comparison.py       # comparison 生成スクリプト
tests/test_daiwa_electric_normalizer.py        # normalizer テスト
```
