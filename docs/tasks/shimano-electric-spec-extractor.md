# Shimano 電動リール spec表ページ extractor 実装タスク分解

## 役割
- `SPECIFICATION スペック表` セクションを見つける
- 見出し群と値群を対応づけて `spec_rows_raw` を作る
- `商品コード / JANコード / 注記` を引き上げる

## やらないこと
- 本文ページ説明抽出
- related information 取得
- normalized 生成

## 最小タスク
1. HTML取得
2. spec セクション起点抽出
3. 見出し群抽出
4. 値群抽出
5. label/value 対応づけ
6. 商品コード / JANコード抽出
7. 注記抽出
8. 価格抽出
9. payload束ね
10. 保存またはマージ
11. CLI
12. テスト
