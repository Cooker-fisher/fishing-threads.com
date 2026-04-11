# Tsuri-threads.com

Tsuri-threads.com は、釣り具・規格・釣り物・ライン・仕掛けの関係をたどれる接続型データベースです。

## このリポジトリの原則
- 正本は GitHub
- 主役は entity より relation / setup
- データは raw → normalized → derived の3層
- まずは電動リール軸から始める
- UI は条件 → 必要番手帯 → メーカー比較 → 上位下位比較 → setup の導線を重視する

## まず読む文書
- `docs/architecture.md`
- `docs/repo-structure.md`
- `docs/raw-extraction-design.md`
- `docs/extraction-flow.md`
- `docs/pull-request-rules.md`
- `docs/codex-collaboration-rules.md`
