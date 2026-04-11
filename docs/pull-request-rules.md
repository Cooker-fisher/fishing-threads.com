# Pull Request運用ルール

このプロジェクトでは、更新の基本手段を pull request にする。
`main` への直接pushは避ける。

## この方針にする理由
- 変更内容が見える
- 確定事項と提案事項を分けやすい
- ロールバックしやすい
- 設計のズレを発見しやすい

## 基本ルール
- `main` に直接pushしない
- 1PR = 1テーマに寄せる
- architecture、raw schema、UI、crawlerロジックを1PRに混ぜない
- レビュー可能な大きさに保つ
- 明示的に提案PRでない限り、すでに決まったことだけを入れる

## PRの分類
各PRは、できるだけ次のどれか1種類に寄せる。
- architecture
- schema
- raw extraction
- normalization
- derived logic
- UI
- content / docs
- operations

## PRサイズ
小さいPRを優先する。
例：
- 設計書1枚
- schema更新1件
- extractor1種類
- normalization変更1件

巨大な混合PRは避ける。

## PRタイトル
直接的に書く。
例：
- `raw抽出設計書を追加`
- `リールrawサンプルJSONを追加`
- `normalized reel schema v1を定義`
- `Shimano電動リール一覧extractorを実装`

## PR本文に書くこと
- 含めたもの
- 意図的に含めていないもの
- 確定事項だけか、提案を含むか
- raw / normalized / derived への影響があればその説明

## レビュー時の確認
merge前に最低限これを確認する。
- relation / setup優先の設計に沿っているか
- raw -> normalized -> derived の分離を壊していないか
- 不要な重いファイルをrepoに入れていないか
- 論点を混ぜすぎていないか

## merge条件
次を満たした時だけmergeする。
- スコープが明確
- 命名が一貫している
- 未確定コードが確定済みのような顔で入っていない
- repoが軽量に保たれている

## mainブランチの意味
`main` は最新のレビュー済み状態を表す。
草案置き場にはしない。
