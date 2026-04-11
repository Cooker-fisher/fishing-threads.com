# raw 抽出設計

## 基本方針
- raw JSON を正本とする
- HTML は必要時のみ保存する
- 一覧は広く拾う
- 詳細は深く拾う
- LLM は解釈だけに使う

## 対象カテゴリ
初期はリール全般を視野に入れつつ、まずは電動リール軸で進める。

## raw の設計
### 一覧
- source_site
- source_url
- crawl_date
- maker
- category_raw
- category_mechanism
- page_no
- items[]

### 商品詳細
- 基本メタ
- category_raw
- series_name / model_name / variant_name
- price_raw / sku_raw / jan_upc_raw / status_raw
- description_raw
- notes_raw
- image_urls
- spec_rows_raw
- subtype
- extra

## 分割原則
- core: 比較と導線に効く最小項目
- extra: 後で使えるが主役ではない項目
- ignore: 今は使わない項目

## 保存単位
- 一覧: `raw/index/{maker}/{mechanism}/{page_no}.json`
- 商品: `raw/products/{maker}/{product_slug}.json`
