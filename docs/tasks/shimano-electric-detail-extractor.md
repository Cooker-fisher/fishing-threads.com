# Shimano 電動リール詳細ページ extractor 実装タスク分解

## 目的
Shimano 電動リール詳細ページから、商品本文側の raw を安定して生成する extractor 実装タスクを、Codex に渡せる粒度まで分解する。

対象ページの考え方：
- Shimano 公式の電動リール詳細ページ本体
- 商品名、価格、主要説明、注記、メイン画像を主対象にする
- `スペック表を見る` の先はこの extractor の責務に含めない
- 出力先は `raw/products/shimano/{product_slug}.json`

## この文書で決めること
- 詳細ページ extractor の責務分離
- どこまでを本文 extractor の仕事にするか
- Codex に渡す時の最小タスク単位
- acceptance criteria

## この extractor がやること
- 詳細ページHTMLを取得する
- パンくずから category を取る
- 商品名と価格を取る
- 主要説明文を段落配列で取る
- 注記を `notes_raw` として分離する
- メイン画像URLを取る
- 基本メタを含む product raw JSON を組み立てる

## この extractor がやらないこと
- spec表ページを取りに行くこと
- `スペック表を見る` 遷移先の解析
- related information の抽出
- 動画や feature 全文の大量回収
- normalized 生成
- diff 判定

## 出力スキーマ（この extractor が主に埋める範囲）
```json
{
  "id": null,
  "maker": "shimano",
  "brand": "shimano",
  "source_site": "shimano_official",
  "source_url": "...",
  "source_hash": null,
  "crawl_date": "YYYY-MM-DD",
  "extractor_version": "v1",
  "schema_version": "raw-reel-v1",
  "category_raw": ["リール", "電動"],
  "category_mechanism": "electric",
  "category_usage": [],
  "water_type": "unknown",
  "series_name": "...",
  "model_name": "...",
  "variant_name": "...",
  "price_raw": "...",
  "sku_raw": null,
  "jan_upc_raw": null,
  "status_raw": null,
  "description_raw": ["..."],
  "notes_raw": ["..."],
  "image_urls": ["..."],
  "spec_rows_raw": [],
  "subtype": {
    "reel_type": "electric",
    "electric_raw": {
      "motor_note_raw": null,
      "max_drag_raw": null,
      "weight_raw": null,
      "pe_capacity_raw": null,
      "flouro_capacity_raw": null,
      "max_winding_speed_raw": null,
      "practical_winding_power_raw": null
    },
    "spinning_raw": null,
    "bait_raw": null,
    "conventional_raw": null,
    "lever_brake_raw": null,
    "fly_raw": null
  },
  "extra": {
    "technology_labels": [],
    "movie_links": [],
    "manual_links": [],
    "compatibility_links": [],
    "awards": [],
    "campaign_tags": [],
    "feature_section_titles": [],
    "hero_copy": []
  }
}
```

## 実装タスク分解

### Task 1: URL入力とHTML取得
責務：
- 詳細URLを受け取る
- HTMLを取得する
- エラー時は失敗を返す

成果物：
- 取得関数

acceptance criteria：
- 詳細URLを渡すとHTML文字列を返す
- 404/タイムアウト時に例外または失敗結果を返す

---

### Task 2: パンくず抽出
責務：
- パンくずから category を取る
- `リール`, `電動` を拾う

成果物：
- `extract_breadcrumb_categories(dom) -> list[str]`

acceptance criteria：
- `category_raw` に `リール`, `電動` が入る
- ノイズナビを拾わない

---

### Task 3: 商品名と価格抽出
責務：
- 商品名の大見出しを取る
- 価格の元表記を取る
- 商品名から `series_name / model_name / variant_name` を作る

成果物：
- `extract_title_and_price(dom) -> dict`
- `split_model_fields(title) -> dict`

acceptance criteria：
- 商品名が空でない
- `price_raw` は元表記のまま
- 分離が難しい場合、`series_name` と `model_name` を同値にできる
- 番手差分が明確なら `variant_name` を埋める

---

### Task 4: 主要説明文抽出
責務：
- 商品名・価格直下の主要説明を段落配列で取る
- 直後の短いキャッチ見出しも含めてよい
- 長大な feature 全文は含めない

成果物：
- `extract_main_description(dom) -> list[str]`

acceptance criteria：
- `description_raw` が空配列になりにくい
- 動画説明や related blocks を混ぜない
- 過剰回収しない

---

### Task 5: 注記抽出
責務：
- `※` で始まる注意文
- 電源や条件に関する注意文
を `notes_raw` に分ける

成果物：
- `extract_notes(dom) -> list[str]`

acceptance criteria：
- `notes_raw` に注記が入る
- 本文段落と混ざらない

---

### Task 6: メイン画像抽出
責務：
- 商品メイン画像URLを1件以上取る
- 動画サムネや feature 用画像を優先しない

成果物：
- `extract_main_images(dom) -> list[str]`

acceptance criteria：
- 少なくとも代表画像1枚を返せる
- 画像が不安定な場合でも null ではなく空配列で扱える

---

### Task 7: product raw JSON 組み立て
責務：
- ここまでの抽出結果を product raw に束ねる
- `maker=shimano`, `brand=shimano`, `category_mechanism=electric` を入れる
- spec表由来の項目は空のままにする

成果物：
- `build_product_raw(...) -> dict`

acceptance criteria：
- JSONスキーマに沿う
- `spec_rows_raw` は空配列のままでよい
- `subtype.reel_type=electric`

---

### Task 8: product_slug 生成
責務：
- 商品名から slug を作る
- 番手差分がある場合は含める
- 安定しない場合は fallback を許容する

成果物：
- `build_product_slug(fields) -> str`

acceptance criteria：
- 小文字
- `-` 区切り
- series名だけで終わらない

---

### Task 9: JSON保存
責務：
- `raw/products/shimano/{product_slug}.json` に保存する
- ディレクトリが無ければ作る

成果物：
- `save_product_raw(data, out_dir)`

acceptance criteria：
- UTF-8で保存される
- ファイル名ルールに沿う

---

### Task 10: CLI入口
責務：
- URLを受けて詳細 extractor を実行できるようにする
- 出力先指定を可能にする

成果物：
- CLIコマンドまたはスクリプト入口

acceptance criteria：
- 1コマンドで product raw JSON を出せる
- エラー時に失敗理由が見える

---

### Task 11: 最低限テスト
責務：
- サンプルHTMLまたは fixture で壊れないことを確認する

成果物：
- テスト1〜4本

最低限のテスト対象：
- パンくず抽出
- 商品名/価格抽出
- 主要説明抽出
- 注記分離

acceptance criteria：
- 本文と注記が混ざらない
- spec表や related を拾いすぎない

## 実装順序
1. HTML取得
2. パンくず抽出
3. 商品名と価格抽出
4. 説明文抽出
5. 注記抽出
6. 画像抽出
7. JSON組み立て
8. slug生成
9. 保存
10. CLI
11. テスト

## Codex に渡す時の最小指示例
### 例1
`Shimano電動リール詳細 extractor の Task 4 だけ実装。商品名・価格直下の主要説明抽出に限定し、feature全文やrelatedは拾わない。`

### 例2
`docs と既存 schema を変えずに、Task 5 の extract_notes(dom) だけ実装。※注記と条件文の分離に限定する。`

## review観点
merge前に確認すること：
- 詳細 extractor が spec表ページ責務を混ぜていないか
- 注記が本文に混ざっていないか
- price や title を勝手に正規化していないか
- output path が `raw/products/shimano/` に固定されているか

## 一文要約
Shimano 電動リール詳細 extractor は、商品本文側だけを対象にして、パンくず・商品名・価格・主要説明・注記・メイン画像を小さな実装単位で積み上げる。
