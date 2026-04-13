# target-band-ranges 自動生成メモ

## 目的

`raw/target-band-ranges.json` は手動仮値のまま残し、
`raw/target-band-ranges.generated.json` を生成物として追加する。

これで:
- 手動仮値
- 自動導出結果

を分離できる。

## 生成ルール

`standard-band-summary.json` の各帯を走査し、魚種ごとに:

- 最初に出現した帯 → `start_band`
- 最後に出現した帯 → `end_band`

を持たせる。

## 入力の想定

最低限、各帯ごとに次のどちらかがあればよい。

- `band` または `standard_band`
- `fish_targets`（推奨）

`fish_targets` は次の形を許容する。

- `['マダイ', 'アジ']`
- `{'マダイ': true, 'アジ': 2}`
- `[{ 'target': 'マダイ' }, { 'name': 'アジ' }]`

## スクリプト

`python scripts/run_target_band_ranges_generator.py`

既定値:

- input: `runs/tmp/standard-band-summary.json`
- template: `raw/target-band-ranges.json`
- output: `raw/target-band-ranges.generated.json`

## 既存手動ファイルとの関係

スクリプトは template から次を引き継ぐ。

- `bands`
- `brand_bands`

そして `target_ranges` だけを自動導出で差し替える。

## 次にやること

1. 実データで一度生成する
2. 手動仮値との差分を見る
3. ずれが大きい魚種だけ命名ゆれ / 抽出ゆれを調整する
4. 問題なければ UI は generated 側を読む

## 注意

この段階ではまだ UI を触らない。
先に data-driven の帯レンジを固定する。
