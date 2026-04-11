# Shimano 電動リール一覧 selector 方針

対象ページ：
- `https://fish.shimano.com/ja-JP/product/list.html?pcat1=cg1SHIFJpReel&pcat2=cg2SHIFJpReelElectricAccessories&pcat3=&pcat4=&fs=&series=&price_min=&price_max=`

## この文書の目的
Shimano の電動リール一覧ページから、壊れにくく raw 候補を抽出するための selector 方針を定義する。

## ページ観察の要点
- 検索結果ブロックは `検索結果` → `19件` の直後に始まる
- 商品は `VIEW PRODUCT` を含むリンクとして並んでいる
- 末尾にページネーション `1 / 2 / NEXT` がある
- 一覧中の商品は電動リールだが、検索結果直後に `リール スピニングリール` という表記が出る

## 重要な注意
`リール スピニングリール` は、この一覧ページでは category 判定の根拠にしない。
このページの実データは電動リールであり、URL の `pcat2=cg2SHIFJpReelElectricAccessories` と商品群の実体を優先する。

## 抽出単位
各商品は `VIEW PRODUCT` を含むリンク 1件を 1レコードとして扱う。

例：
- `ビーストマスター MD 3000 ... VIEW PRODUCT`
- `フォースマスター 200/200DH/201/201DH ... VIEW PRODUCT`

## 一覧で取る項目
- `maker`
- `category_raw`
- `category_mechanism`
- `page_no`
- `items[].series_name_or_model_name`
- `items[].price_raw`
- `items[].source_url`
- `items[].image_url`
- `items[].badge_raw`
- `items[].status_raw`

## 値の方針
### maker
固定で `shimano`

### category_mechanism
この一覧URLでは固定で `electric`

### category_raw
元サイト由来の表現を保持するが、表示ノイズに引っ張られすぎない。
まずは `リール`, `電動` を採用する。

### page_no
ページネーションから取得する。
1ページ目なら `1`。

## selector 方針
### 主 selector
商品レコードの起点は、`VIEW PRODUCT` を含むリンク。

優先条件：
1. 検索結果ブロック配下であること
2. `VIEW PRODUCT` を含むこと
3. 商品URLを持つこと
4. ページネーションやノイズ導線ではないこと

### title 抽出
リンクテキストから `価格 + VIEW PRODUCT` より前の部分を `series_name_or_model_name` として使う。

### price 抽出
リンクテキスト中の `円 (税別)` を含む部分を正規表現で抜く。
元表記のまま `price_raw` に入れる。

### source_url 抽出
商品リンクの href をそのまま使う。
相対URLなら絶対URL化する。

### image_url 抽出
商品カード内に対応画像が安定して存在する場合のみ取得する。
安定しない場合は null を許容する。
一覧で無理に画像取得を成立させようとしない。

### badge_raw / status_raw
NEW などのバッジや、生産終了・在庫系の表示が一覧で明示されている場合のみ取る。
無ければ null。

## 実装ルール
- class名の完全依存は避ける
- テキストアンカーと構造位置を併用する
- `VIEW PRODUCT` を商品抽出のアンカーに使う
- `NEXT` やページ番号は pagination として別処理する
- `NEW PRODUCTS` や `SPECIAL SITE` 以降は商品一覧ではないので除外する

## 禁止事項
- `リール スピニングリール` をそのまま mechanism 判定に使うこと
- 一覧だけで SKU や JAN を推測すること
- 価格やタイトルを正規化しすぎること
- 一覧の並び順に意味を持たせること

## 一文要約
Shimano 電動一覧では、`VIEW PRODUCT` を含む商品リンク列を主軸に拾い、category は URL 文脈を優先する。
