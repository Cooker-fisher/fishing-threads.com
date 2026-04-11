# Shimano 電動リール spec表ページ extractor 実装タスク分解

## 目的
Shimano 電動リールの spec表ページから、比較・正規化の元になる `spec_rows_raw` と注記を安定して生成する extractor 実装タスクを、Codex に渡せる粒度まで分解する。

対象ページの考え方：
- `SPECIFICATION スペック表` セクション、または `スペック表を見る` の遷移先
- 主役は `spec_rows_raw`
- `注記` と `※` 脚注も対象にする
- `RELATED INFORMATION` 以降は対象外にする
- 出力先は `raw/products/shimano/{product_slug}.json` の spec 部分、または一時的な spec raw 構造

## この文書で決めること
- spec extractor の責務分離
- どこまでを spec extractor の仕事にするか
- Codex に渡す時の最小タスク単位
- acceptance criteria

## この extractor がやること
- spec表ページHTMLを取得する
- `SPECIFICATION スペック表` セクションを見つける
- 見出し群と値群を対応づける
- `spec_rows_raw` を生成する
- `商品コード` と `JANコード` を個別にも拾う
- `注記` と `※` 脚注を `notes_raw` に分ける

## この extractor がやらないこと
- 商品本文ページの説明文抽出
- 動画や feature 本文の抽出
- related information の抽出
- 数値の正規化や単位変換
- normalized 生成
- diff 判定

## 出力スキーマ（この extractor が主に埋める範囲）
```json
{
  "price_raw": "...",
  "sku_raw": "...",
  "jan_upc_raw": "...",
  "spec_rows_raw": [
    {
      "section": "スペック表",
      "label": "ギア比",
      "value": "4.6",
      "unit": null,
      "note": null,
      "source_text": "ギア比 4.6"
    }
  ],
  "notes_raw": ["..."]
}
```

## 実装タスク分解

### Task 1: URL入力とHTML取得
責務：
- spec表ページURLを受け取る
- HTMLを取得する
- エラー時は失敗を返す

成果物：
- 取得関数

acceptance criteria：
- spec表URLを渡すとHTML文字列を返す
- 404/タイムアウト時に例外または失敗結果を返す

---

### Task 2: specセクション起点抽出
責務：
- `SPECIFICATION スペック表` 見出しを見つける
- そこから spec 範囲のDOMを特定する
- `RELATED INFORMATION` より前で止める

成果物：
- `find_spec_section(dom) -> node`

acceptance criteria：
- spec表本体の範囲を取れる
- related information 側を含めない

---

### Task 3: 見出し群抽出
責務：
- spec表の列見出しまたは項目名を抽出する
- `品番 / ギア比 / 最大ドラグ力 / 自重 / 糸巻量PE / 商品コード / JANコード` などを拾う

成果物：
- `extract_spec_labels(node) -> list[str]`

acceptance criteria：
- 主要見出しが取得できる
- 空文字やノイズ見出しを混ぜない

---

### Task 4: 値群抽出
責務：
- 見出しに対応する値群を抽出する
- 値は元表記のまま保持する

成果物：
- `extract_spec_values(node) -> list[str]`

acceptance criteria：
- 値群の個数が見出し群と概ね対応する
- 数値変換しない
- 改行込みでも1値として保持できる

---

### Task 5: label/value 対応づけ
責務：
- 見出し群と値群を対応づけて `spec_rows_raw` を作る
- `source_text` は `label + value` の元表現にする

成果物：
- `build_spec_rows(labels, values) -> list[dict]`

acceptance criteria：
- `spec_rows_raw` が配列で出る
- `section` は `スペック表`
- `label` と `value` の対応が崩れにくい

---

### Task 6: 商品コード / JANコード 抽出
責務：
- `商品コード` の値を `sku_raw` に入れる
- `JANコード` の値を `jan_upc_raw` に入れる

成果物：
- `extract_code_fields(spec_rows) -> dict`

acceptance criteria：
- `sku_raw` が埋まる
- `jan_upc_raw` が埋まる
- spec_rows_raw 側にも行は残る

---

### Task 7: 注記抽出
責務：
- `注記` 行と `※` 脚注を抽出する
- `notes_raw` に分離する

成果物：
- `extract_spec_notes(node) -> list[str]`

acceptance criteria：
- 注記が `notes_raw` に入る
- spec_rows_raw に混ざらない

---

### Task 8: 価格抽出
責務：
- spec表ページ側で価格表記が見える場合は `price_raw` を取る
- なければ null のままでよい

成果物：
- `extract_spec_price(dom) -> str | null`

acceptance criteria：
- 表示がある場合のみ元表記で返す
- 無ければ null

---

### Task 9: spec抽出結果の束ね
責務：
- `price_raw / sku_raw / jan_upc_raw / spec_rows_raw / notes_raw` を1つに束ねる
- 既存 product raw にマージしやすい形にする

成果物：
- `build_spec_payload(...) -> dict`

acceptance criteria：
- spec由来項目だけを返す
- 本文由来項目を混ぜない

---

### Task 10: 保存またはマージ
責務：
- 初期段階では一時ファイル保存でもよい
- もしくは既存 product raw に spec 部分だけマージする

成果物：
- `save_spec_payload(...)` または `merge_spec_into_product_raw(...)`

acceptance criteria：
- spec 部分だけを安全に保存できる
- 本文部分を壊さない

---

### Task 11: CLI入口
責務：
- spec表URLを受けて extractor を実行できるようにする

成果物：
- CLIコマンドまたはスクリプト入口

acceptance criteria：
- 1コマンドで spec payload を出せる
- エラー時に失敗理由が見える

---

### Task 12: 最低限テスト
責務：
- サンプルHTMLまたは fixture で壊れないことを確認する

成果物：
- テスト2〜4本

最低限のテスト対象：
- specセクション起点抽出
- 見出し群抽出
- 値群抽出
- 注記分離

acceptance criteria：
- related information を混ぜない
- label/value 対応が極端に崩れない
- 注記が spec rows に混ざらない

## 実装順序
1. HTML取得
2. specセクション起点抽出
3. 見出し群抽出
4. 値群抽出
5. label/value 対応づけ
6. 商品コード / JANコード抽出
7. 注記抽出
8. 価格抽出
9. payload束ね
10. 保存またはマージ
11. CLI
12. テスト

## Codex に渡す時の最小指示例
### 例1
`Shimano電動リール spec extractor の Task 5 だけ実装。見出し群と値群を対応づけて spec_rows_raw を作る処理に限定し、保存やCLIは触らない。`

### 例2
`docs と既存 schema を変えずに、Task 7 の extract_spec_notes(node) だけ実装。注記と※脚注の分離に限定する。`

## review観点
merge前に確認すること：
- spec extractor が本文ページ責務を混ぜていないか
- related information を拾っていないか
- `商品コード / JANコード` を個別にも引き上げられているか
- 注記が spec_rows_raw に混ざっていないか
- 数値変換をしていないか

## 一文要約
Shimano 電動リール spec extractor は、`SPECIFICATION スペック表` を起点に見出しと値を raw のまま対応づけ、商品コード・JAN・注記を別で引き上げる小さな実装単位に分けて進める。
