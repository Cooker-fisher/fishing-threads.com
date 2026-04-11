# fishing-threads.com

fishing-threads.com / Tsuri-threads は、釣り具選定のための**接続型データベースサイト**です。

このプロジェクトの価値は、単体の商品ページではなく、**relation（関係）** と **setup（組み合わせ）** にあります。

## 固定された方向性
- 目的：釣り具選定のための接続型DBを作る
- 主役：entity単体ではなく relation / setup
- 初期スコープ：まずは電動リールから始める
- 正本：GitHub
- データ層：
  - `raw`
  - `normalized`
  - `derived`
- UIの核：
  - 横軸 = 番手 / バンド
  - 縦軸 = 魚種、錘負荷、その他条件
- 想定導線：
  - 魚種 / 条件
  - 必要番手帯
  - メーカー比較
  - 上位下位比較
  - setup

## 現在のドキュメント
- `docs/architecture.md`
- `docs/repo-structure.md`
- `docs/raw-extraction-design.md`
- `docs/pull-request-rules.md`
- `docs/codex-collaboration-rules.md`

## リポジトリ方針
- まだ決まっていないものは入れない
- 憶測のコードは入れない
- `raw JSON` を実務上の正本とする
- HTMLは必要時のみ保存する
- 重い生成物はrepoに置かない
