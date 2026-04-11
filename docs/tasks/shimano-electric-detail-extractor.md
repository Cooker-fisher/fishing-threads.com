# Shimano 電動リール詳細ページ extractor 実装タスク分解

## 役割
- パンくずを取る
- 商品名 / 価格を取る
- 主要説明 / 注記 / 画像を取る
- `1商品 = 1 JSON` の product raw を保存する

## やらないこと
- spec表ページ解析
- related information 取得
- normalized 生成

## 最小タスク
1. HTML取得
2. パンくず抽出
3. 商品名 / 価格抽出
4. 説明抽出
5. 注記抽出
6. 画像抽出
7. JSON組み立て
8. slug生成
9. 保存
10. CLI
11. テスト
