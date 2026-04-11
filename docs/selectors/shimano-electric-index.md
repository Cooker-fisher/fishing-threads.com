# Shimano 電動リール一覧 selector 方針

## 主アンカー
- `VIEW PRODUCT` を含む商品リンク列
- ページネーション `1 / 2 / NEXT` は別扱い

## 重要な注意
一覧中の `リール スピニングリール` 表示を mechanism 判定に使わない。
URL 文脈と商品群の実体を優先して `electric` とする。

## 一覧で取る項目
- maker
- category_raw
- category_mechanism
- page_no
- items[].series_name_or_model_name
- items[].price_raw
- items[].source_url
- items[].image_url
- items[].badge_raw
- items[].status_raw
