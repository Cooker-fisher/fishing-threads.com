# DAIWA 電動リール一覧 selector 方針

対象ページ例:
- `https://www.daiwa.com/jp/product/productlist?category1=リール`

## ページ観察の要点
- 絞り込みUI内に `電動リール` カテゴリが存在する
- 検索結果は `検索結果 0161件（1～50件を表示）` の形式で表示される
- 一覧の各商品は 1リンクでまとまり、`電動リール シーボーグ G1800M-RJ メーカー希望本体価格 374,500円` のように、カテゴリ + 商品名 + 価格が並ぶ
- 電動以外の商品も同一一覧に混在するため、一覧全体から `電動リール` 行だけを拾う必要がある

## 主アンカー
- 検索結果一覧内の product link
- そのリンクテキストに `電動リール` を含むもの

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

## 方針
- `電動リール` をカテゴリ判定の主キーに使う
- `メーカー希望本体価格` 以降を `price_raw` に使う
- 商品名は `電動リール` と価格の間を採る
- 同一一覧にスピニングや両軸が混在していても混ぜない
