# Shimano 電動リール extractor 実装着手順

## 目的
Shimano 電動リールの extractor 実装を、責務が混ざらない順番で進めるための着手順を固定する。

この文書は、
- 一覧 extractor
- 詳細本文 extractor
- spec表 extractor
のどれから実装すべきかを定める。

## 結論
実装順は次の通り。

1. 一覧 extractor
2. 詳細本文 extractor
3. spec表 extractor
4. 一覧 → 詳細 の接続
5. 詳細本文 → spec のマージ
6. 最低限の統合テスト

## なぜこの順番か
### 1. 一覧 extractor を最初にやる理由
- 候補URLの母集団ができる
- `1ページ = 1 JSON` の運用を先に固められる
- selector や保存パスの初期実装が軽い
- ここで壊れると後続全部が崩れる

### 2. 詳細本文 extractor を次にやる理由
- 商品名、価格、説明、注記、画像などの core が取れる
- `raw/products/` の基礎構造がここで固まる
- spec表と混ぜないことで責務が明確になる

### 3. spec表 extractor を最後にやる理由
- spec は比較上重要だが、構造対応が一段難しい
- label/value 対応づけの処理が必要
- 本文 extractor と混ぜると設計が汚れる
- 先に product raw の土台があった方がマージしやすい

## 実装単位の原則
- 1PR = 1テーマ
- 一覧、詳細本文、spec を同じPRに混ぜない
- まず文書どおりの最小実装を通す
- いきなり汎用化しない

## 推奨PR順
### PR-A
`Shimano電動リール一覧 extractor 実装`

含めるもの：
- HTML取得
- 商品ノード抽出
- item抽出
- index raw JSON保存
- CLI
- 最低限テスト

### PR-B
`Shimano電動リール詳細本文 extractor 実装`

含めるもの：
- HTML取得
- パンくず抽出
- 商品名/価格抽出
- 説明/注記/画像抽出
- product raw JSON生成
- CLI
- 最低限テスト

### PR-C
`Shimano電動リール spec表 extractor 実装`

含めるもの：
- specセクション起点抽出
- label/value 抽出
- spec_rows_raw 生成
- 商品コード/JAN抽出
- notes抽出
- spec payload 保存またはマージ
- 最低限テスト

### PR-D
`Shimano電動リール一覧→詳細 接続`

含めるもの：
- 一覧から詳細URL抽出
- 既取得除外
- 実行順の整理

### PR-E
`Shimano電動リール本文→spec マージ`

含めるもの：
- 既存 product raw への spec 部分マージ
- 上書き規則
- 欠損時ルール

### PR-F
`Shimano電動リール 統合テスト`

含めるもの：
- 一覧→詳細→spec の通し確認
- 保存結果確認
- 最低限の差分確認

## 最初にやってはいけないこと
- 一覧・詳細・spec を1本で実装すること
- 最初から Daiwa や Abu まで広げること
- normalized まで同時に作ること
- LLM補助を先に入れること
- 画像最適化や外部ストレージまで同時にやること

## Codex への渡し方
最初は PR-A だけ渡す。

例：
`Shimano電動リール一覧 extractor を実装。docs/tasks/shimano-electric-index-extractor.md に従い、一覧raw JSON出力まで。詳細ページ取得、spec抽出、normalized生成はやらない。1PRで完結する最小実装に限定。`

次に PR-B を渡す。

例：
`Shimano電動リール詳細本文 extractor を実装。docs/tasks/shimano-electric-detail-extractor.md に従い、パンくず・商品名・価格・説明・注記・画像の抽出まで。spec表ページは扱わない。`

## review観点
merge前に確認すること：
- 今のPRが順番どおりの責務だけを持っているか
- 後続責務を先取りしていないか
- raw の保存単位を壊していないか
- LLM補助が勝手に入っていないか

## 一文要約
Shimano 電動リールの実装は、**一覧 → 詳細本文 → spec → 接続 → マージ → 統合テスト** の順で進める。
