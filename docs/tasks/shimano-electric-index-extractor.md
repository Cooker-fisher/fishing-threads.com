# Shimano 電動リール一覧 extractor 実装タスク分解

## 目的
Shimano 電動リール一覧ページから、`1ページ = 1 JSON` の raw を安定して生成する extractor 実装タスクを、Codex に渡せる粒度まで分解する。

対象ページの考え方：
- Shimano 公式の電動リール一覧
- `VIEW PRODUCT` を含む商品リンク列を主アンカーにする
- 出力先は `raw/index/shimano/electric/{page_no}.json`

## この文書で決めること
- 実装の責務分離
- どこまでを一覧 extractor の仕事にするか
- Codex に渡す時の最小タスク単位
- acceptance criteria

## この extractor がやること
- 一覧ページHTMLを取得する
- 商品カード候補を抽出する
- `VIEW PRODUCT` をアンカーに商品レコードを作る
- `maker / category / page_no / items[]` を raw JSON に保存する

## この extractor がやらないこと
- 詳細ページを取りに行くこと
- SKU や JAN の推測
- 用途タグの過剰推定
- spec表の抽出
- normalized 生成
- diff 判定

## 出力スキーマ
```json
{
  "source_site": "shimano_official",
  "source_url": "...",
  "crawl_date": "YYYY-MM-DD",
  "maker": "shimano",
  "category_raw": ["リール", "電動"],
  "category_mechanism": "electric",
  "page_no": 1,
  "items": [
    {
      "series_name_or_model_name": "...",
      "price_raw": "...",
      "source_url": "...",
      "image_url": "...",
      "badge_raw": null,
      "status_raw": null
    }
  ]
}
```

## 実装タスク分解

### Task 1: URL入力とHTML取得
責務：
- 一覧URLを受け取る
- HTMLを取得する
- エラー時は失敗を返す

成果物：
- 取得関数

acceptance criteria：
- 一覧URLを渡すとHTML文字列を返す
- 404/タイムアウト時に例外または失敗結果を返す

---

### Task 2: ページ番号抽出
責務：
- 現在ページ番号を抽出する
- 抽出できなければ 1 を暫定採用してよい

成果物：
- `extract_page_no(html) -> int`

acceptance criteria：
- 1ページ目で `1` を返す
- `1 / 2 / NEXT` などのページネーションがあっても壊れない

---

### Task 3: 商品リンク候補抽出
責務：
- `VIEW PRODUCT` を含む商品リンク群を候補として抽出する
- ページネーションやノイズ導線を除外する

成果物：
- `extract_product_nodes(dom) -> list[node]`

acceptance criteria：
- 商品ごとに1ノード取れる
- `NEXT` やナビリンクを混ぜない
- `NEW PRODUCTS` や `SPECIAL SITE` 以降の導線を混ぜない

---

### Task 4: 商品1件のフィールド抽出
責務：
- 1ノードから次を抽出する
  - `series_name_or_model_name`
  - `price_raw`
  - `source_url`
  - `image_url`
  - `badge_raw`
  - `status_raw`

成果物：
- `extract_item(node) -> dict`

acceptance criteria：
- 製品名が空でない
- `source_url` が商品詳細を指す
- `price_raw` は元表記のまま
- 画像が不安定なら null を返してよい

---

### Task 5: 一覧JSON組み立て
責務：
- 一覧共通メタと items を束ねる
- schemaどおりの辞書を作る

成果物：
- `build_index_raw(...) -> dict`

acceptance criteria：
- `maker=shimano`
- `category_mechanism=electric`
- `category_raw=["リール", "電動"]`
- `page_no` が入る
- `items` が配列で入る

---

### Task 6: JSON保存
責務：
- `raw/index/shimano/electric/{page_no}.json` に保存する
- ディレクトリが無ければ作る

成果物：
- `save_index_raw(data, out_dir)`

acceptance criteria：
- 001.json などの命名で保存される
- UTF-8で保存される
- 既存ファイル上書き可否を明示できる

---

### Task 7: CLI入口
責務：
- URLを受けて extractor を実行できるようにする
- 出力先を指定できるようにする

成果物：
- CLIコマンドまたはスクリプト入口

acceptance criteria：
- 1コマンドで一覧raw JSONを出せる
- エラー時に失敗理由が見える

---

### Task 8: 最低限テスト
責務：
- サンプルHTMLまたは fixture で壊れないことを確認する

成果物：
- テスト1〜3本

最低限のテスト対象：
- 商品リンク候補抽出
- 商品1件抽出
- JSON組み立て

acceptance criteria：
- 少なくとも主要ケースで赤にならない
- `VIEW PRODUCT` ノイズ混入を防げる

## 実装順序
1. HTML取得
2. 商品リンク候補抽出
3. 商品1件抽出
4. JSON組み立て
5. 保存
6. CLI
7. テスト

## Codex に渡す時の最小指示例
### 例1
`Shimano電動リール一覧 extractor の Task 3 だけ実装。VIEW PRODUCT を含む商品ノード抽出に限定し、保存処理やCLIは触らない。`

### 例2
`docs と既存 schema を変えずに、Task 4 の extract_item(node) だけ実装。price は元表記保持、source_url は絶対URL化。`

## review観点
merge前に確認すること：
- 一覧 extractor が詳細ページ責務を混ぜていないか
- `VIEW PRODUCT` 以外のノイズを拾っていないか
- 価格やタイトルを勝手に正規化していないか
- output path が `raw/index/shimano/electric/` に固定されているか

## 一文要約
Shimano 電動リール一覧 extractor は、`VIEW PRODUCT` アンカーで商品行を拾い、`1ページ = 1 JSON` を出力する小さな実装単位に分けて進める。
