# Shimano 電動リール詳細ページ selector 方針

## 主対象
- パンくず
- 商品名
- 価格
- 主要説明
- 注記
- メイン画像

## 原則
- まず共通 core を deterministic に取る
- `CONCEPT MOVIE` や `KEY FEATURE` は extra 扱い
- `スペック表を見る` の先は別 extractor に分ける

## 取る項目
- maker
- brand
- source_url
- category_raw
- category_mechanism
- series_name / model_name / variant_name
- price_raw
- description_raw
- notes_raw
- image_urls
