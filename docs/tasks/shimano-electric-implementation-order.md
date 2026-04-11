# Shimano 電動リール extractor 実装着手順

## 結論
実装順は次の通り。
1. 一覧 extractor
2. 詳細本文 extractor
3. spec表 extractor
4. 一覧 → 詳細 の接続
5. 詳細本文 → spec のマージ
6. 最低限の統合テスト

## 原則
- 1PR = 1テーマ
- 一覧 / 詳細 / spec を同じPRに混ぜない
- いきなり汎用化しない
- LLM補助を先に入れない
