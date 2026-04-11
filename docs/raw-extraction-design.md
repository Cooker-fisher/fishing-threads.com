# Raw抽出設計

## 目的
Tsuri-threads は、釣り具選定のための接続型データベースサイトです。
価値の中心は、単体の商品ページではなく relation / setup にあります。
この文書は、リール情報の raw 抽出設計を固定し、将来拡張しても壊れにくい土台を作るためのものです。

## プロダクト前提
- Tsuri-threads は接続型DBサイトである
- 主役は entity 単体ではなく relation / setup
- 初期スコープは電動リール
- 正本は GitHub
- データ層は以下の3つ
  - `raw`
  - `normalized`
  - `derived`
- UIの核は
  - 横軸 = 番手 / バンド
  - 縦軸 = 魚種、錘負荷、その他条件
- 基本導線は
  - 魚種 / 条件
  - 必要番手帯
  - メーカー比較
  - 上位下位比較
  - setup

## raw抽出の基本方針
### 正本
- 実務上の正本は `raw JSON`
- HTMLは通常保存しない
- HTMLを保存するのは次の場合のみ
  - 抽出失敗
  - 構造変更検知
  - 代表サンプル保存

### この方針の理由
- raw JSON の方が軽く、差分比較しやすい
- HTMLだけで運用することは可能だが、実務では重い
- 全ページHTML保存は不要

## 抽出戦略
### deterministic優先
事実項目は CSS / DOM 抽出で取る。
LLMは解釈項目だけに使う。

### CSS / DOM で取る項目
- タイトル
- 価格
- 商品コード / sku
- JAN / UPC
- スペック表
- 注記
- 画像URL
- 一覧から詳細へのURL

### LLMで扱う項目
- `category_mechanism`
- `category_usage`
- `water_type`
- 特徴見出しの意味づけ
- 必要時の technology labels 整理
- 不規則なスペック表の補修

### 原則
- 事実はCSSで取る
- 解釈はLLMに任せる
- ページ本文丸ごとを毎回LLMに投げない

## ページ単位の分離
### 一覧raw
**1ページ = 1 JSON** で保存する。

例：
`raw/index/shimano/electric/001.json`

役割：
- 候補を広く集める
- 深読みしすぎない

典型項目：
- maker
- category_raw
- series_name_or_model_name
- price_raw
- source_url
- image_url
- badge_raw
- status_raw

### 商品raw
**1商品 = 1 JSON** で保存する。

例：
`raw/products/shimano/force-master-200.json`

役割：
- 商品事実を深く保存する
- normalized の元データにする

## 共通リールraw schema
raw schema は以下で組む。
- common core
- subtype core
- extra
- ignore

最初は Shimano / Daiwa / Abu の共通構造を優先する。
Major Craft / Megabass は初期schema決定要因ではなく、後から耐久テストに使う。

### common core
- `maker`
- `brand`
- `source_site`
- `source_url`
- `crawl_date`
- `category_raw`
- `category_mechanism`
- `category_usage`
- `water_type`
- `series_name`
- `model_name`
- `variant_name`
- `price_raw`
- `sku_raw`
- `jan_upc_raw`
- `status_raw`
- `description_raw`
- `spec_rows_raw`
- `notes_raw`
- `image_urls`

### subtype core
リール種別ごとの raw ブロックを持つ。
例：
- `electric_raw`
- `spinning_raw`
- `bait_raw`
- `conventional_raw`
- `lever_brake_raw`
- `fly_raw`

### extra
取れれば便利だが、なくても致命的ではないもの。
- `technology_labels`
- `movie_links`
- `manual_links`
- `compatibility_links`
- `awards`
- `campaign_tags`
- `feature_section_titles`
- `hero_copy`

### ignore
保存しないもの。
- パンくず
- ニュース
- SNSブロック
- 関連記事
- 販促バナー
- 企業導線
- 店舗導線
- 一覧の並び順そのもの

## spec保存ルール
スペック表は早すぎる正規化をしない。
まず raw 行として保存する。

推奨形：

```json
[
  {
    "section": "基本スペック",
    "label": "ギア比",
    "value": "5.1",
    "unit": null,
    "note": null,
    "source_text": "ギア比 5.1"
  }
]
```

原則：
- まず元ラベルと元値を保持する
- 正規化は後で行う

## category設計
categoryは3軸で持つ。

### 1. raw category
サイト側の表記をそのまま保持する。
- `category_raw`

### 2. mechanism
統一的な機構分類。
- `electric`
- `spinning`
- `bait`
- `conventional`
- `lever_brake`
- `fly`
- `unknown`

### 3. usage
用途タグ。
例：
- boat
- offshore
- shore
- surf
- bass
- trout
- wakasagi
- rockfish

### 4. water type
- `salt`
- `fresh`
- `both`
- `unknown`

## ファイル命名規則
### 一覧raw
`raw/index/{maker}/{category_mechanism}/{page_no}.json`

例：
`raw/index/shimano/electric/001.json`

### 商品raw
`raw/products/{maker}/{product_slug}.json`

例：
`raw/products/shimano/force-master-200.json`

### product slug のルール
- 小文字のみ
- 区切りは `-` のみ
- 番手 / 左右 / HG / PG / XG の差分は必ず入れる
- series名だけでは命名しない
- 必要なら source ベースの補助IDを付ける

## 必須メタ項目
各商品JSONには最低限これを入れる。
- `id`
- `maker`
- `brand`
- `source_site`
- `source_url`
- `source_hash`
- `crawl_date`
- `extractor_version`
- `schema_version`

重要点：
- `source_hash` があるとページ変化と抽出器変化を分けられる
- `extractor_version` があると抽出ロジック更新を追跡できる

## 差分検知ルール
商品ページ単位で差分を見る。

最低限比較する項目：
- `source_hash`
- core項目
- `spec_rows_raw`
- `price_raw`
- `status_raw`

### change level
#### High
- `status_raw` 変更
- `sku_raw` / `jan_upc_raw` 変更
- `spec_rows_raw` の行追加 / 削除 / 値変更
- `category_mechanism` 変更
- setupに効く容量 / ドラグ / 糸巻量の変更

#### Medium
- `price_raw` 変更
- `description_raw` の大きな変更
- 画像差し替え
- 特徴見出しの変更

#### Low
- 注記の軽微修正
- 順番変更
- 表記揺れ修正
- 販促文変更

### diff保存例
`diff/{maker}/{product_slug}/{date}.json`

## 画像方針
### 基本方針
- 商品画像の実体は repo に保存しない
- 画像メタ情報だけ持つ
- まずは source image URL を保持する

### この方針の理由
GitHub容量を圧迫しやすいのは raw JSON ではなく、主に次のもの。
- 画像
- HTML全件保存
- CSV再生成物の大量コミット
- バイナリ

### 現段階
- `source_image_url` を保持する
- 必要になったら軽量 `thumb` / `detail` を repo外で管理する
- 最初から有料ストレージを前提にしない

## repo構成 v1
```text
repo/
├─ app/
├─ schema/
├─ prompts/
├─ scripts/
├─ raw/
│  ├─ index/
│  ├─ products/
│  └─ images/
├─ normalized/
├─ derived/
├─ tmp/          # gitignore対象
├─ logs/         # gitignore対象
└─ samples/
   └─ html/      # 代表サンプルのみ
```

ルール：
- `raw` = 実務上の正本
- `normalized` = 再生成可能
- `derived` = 再生成可能
- `tmp` と `logs` はコミットしない
- HTMLは代表サンプルだけ持つ

## 採用した運用方針
**A軽量運用** を採用する。

意味：
- 基本は raw JSON 保存
- HTMLは必要時のみ保存
- deterministic抽出を優先
- GitHubには code / schema / raw JSON / 最小限のnormalized を置く
- 重い生成物は無視する

## 次の作業
次に作るもの：
1. 一覧ページ raw JSONサンプル
2. 商品ページ raw JSONサンプル
3. 抽出プロンプトを以下に分割
   - 一覧ページ用
   - 詳細ページ用
4. Shimano電動リールの最初の extractor 実装
