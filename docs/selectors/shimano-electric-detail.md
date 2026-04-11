# Shimano 電動リール詳細ページ selector 方針

対象例：
- `https://fish.shimano.com/ja-JP/product/reel/electricaccessories/a075f00003u1bmwqau.html`

## この文書の目的
Shimano の電動リール詳細ページから、壊れにくく事実情報を抽出するための selector 方針を定義する。

## ページ観察の要点
- パンくずで `製品情報 > リール > 電動 > 商品名` まで取れる
- 商品名はページ中央の大見出しに出る
- 価格は商品名直下に `円 (税別)` 形式で出る
- 主要説明文は、短い見出し + 本文段落 + 注記で構成される
- `フィーチャー / ラインナップ / スペック表 / 関連情報` のタブがある
- `CONCEPT MOVIE` と `KEY FEATURE` セクションがあり、ここは extra 寄り
- `スペック表を見る` への導線があり、ラインナップ・スペック情報の入口になる

## 重要な考え方
このページでは、まず **共通coreを deterministic に取る**。
その後、必要な場合だけ subtype core や extra を補助抽出する。

## 最優先で取る項目
- `maker`
- `brand`
- `source_url`
- `category_raw`
- `category_mechanism`
- `series_name`
- `model_name`
- `variant_name`
- `price_raw`
- `description_raw`
- `notes_raw`
- `image_urls`

## 値の方針
### maker
固定で `shimano`

### brand
まずは `shimano`

### category_raw
パンくずから取得する。
例：
- `リール`
- `電動`

### category_mechanism
このURL配下では固定で `electric`

### series_name / model_name / variant_name
#### 基本方針
- ページの大見出しを起点にする
- まず商品名全体を `model_name` として保持する
- 厳密分離が難しい場合、`series_name` と `model_name` を同値にしてよい
- 番手や左右差分が明示される場合のみ `variant_name` を分ける

例：
- `ビーストマスター MD 3000`
  - `series_name`: `ビーストマスター MD`
  - `model_name`: `ビーストマスター MD`
  - `variant_name`: `3000`

### price_raw
商品名直下の `170,200 円 (税別)` のような表記をそのまま取る。
数値変換しない。

## description_raw の方針
### 取る場所
商品名・価格直下の主要説明ブロックを最優先にする。

### 取るもの
- 短いキャッチ見出し
- 本文段落
- 直下の補足注記

### 取らないもの
- 動画セクションのタイトル一覧
- 長い feature 解説全文の全回収
- 関連情報ブロック

## notes_raw の方針
注記として扱うもの：
- `※` で始まる注意書き
- 電源に関する注意文
- 使用条件や制約文

本文ではなく、`notes_raw` に分ける。

## image_urls の方針
### 最優先
商品メイン画像を取る。

### 補足
- `main.jpg` 系や `cq5dam.web...jpeg` など、商品本体画像を優先
- 動画サムネや feature 用画像は初期段階では無理に拾わない
- まずは代表画像1枚で十分

## extra として扱うもの
### extra に回してよい
- `CONCEPT MOVIE`
- 動画URL
- `KEY FEATURE` の見出し群
- technology 的なラベル
- 関連情報リンク

### 初期段階で無理に取らない
- 動画サムネ一覧
- キーフィーチャー全文
- 関連ページ群

## spec / lineup の考え方
このページには `ラインナップ` と `スペック表を見る` 導線がある。
ただし、詳細ページ本体とスペック表ページは分離して考える。

### 初期ルール
- 詳細ページ本体で見えている範囲だけ deterministic に取る
- `スペック表を見る` の先は、必要なら別 extractor の対象にする
- 無理に1 extractor に詰め込まない

## selector 方針
### 主アンカー
- 商品名の大見出し
- 価格行
- パンくず
- 説明文ブロック
- 注記ブロック
- メイン画像

### 避けるもの
- グローバルナビ
- フッター
- 動画一覧
- 長大な feature セクション全文
- 画像ギャラリー全件取得

## 禁止事項
- feature 全文を raw 本文として丸ごと抱え込むこと
- 動画や関連記事を core 扱いすること
- variant を無理やり分解すること
- スペック表ページまで1回で取り切ろうとすること

## 初期実装の一文要約
Shimano 電動リール詳細ページでは、まずパンくず・商品名・価格・主要説明・注記・メイン画像だけを deterministic に取り、スペック表導線の先は別抽出として切り分ける。
