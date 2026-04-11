# Shimano 電動リール一覧 extractor 実装タスク分解

## 役割
- 一覧ページHTMLを取得する
- `VIEW PRODUCT` をアンカーに商品候補を抽出する
- `1ページ = 1 JSON` の raw を保存する

## やらないこと
- 詳細ページ取得
- spec 抽出
- normalized 生成

## 最小タスク
1. HTML取得
2. ページ番号抽出
3. 商品ノード抽出
4. item抽出
5. JSON組み立て
6. 保存
7. CLI
8. テスト
