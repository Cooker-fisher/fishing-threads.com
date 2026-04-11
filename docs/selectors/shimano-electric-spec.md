# Shimano 電動リール spec表ページ selector 方針

対象の考え方：
- 商品詳細ページ本体とは別に、`スペック表` セクションまたは `スペック表を見る` の遷移先を対象にする
- 例として、ビーストマスター MD 3000 のページでは `スペック表を見る` 導線があり、ページ内には `SPECIFICATION スペック表` セクションが存在する

## この文書の目的
Shimano の電動リール spec表から、比較・正規化の元になる事実を壊れにくく抽出するための selector 方針を定義する。

## ページ観察の要点
- `SPECIFICATION スペック表` セクションがあり、見出し行と値行が続く
- 見出しとして `品番 / ギア比 / 最大ドラグ力 / 自重 / 糸巻量PE / 商品コード / JANコード` などが並ぶ
- その下に値の並びが続く
- さらに `注記` と `※` で始まる脚注が続く
- 後ろには `RELATED INFORMATION 関連情報` が続く

## 重要な考え方
このページでの主役は **spec_rows_raw** である。
ここでは feature説明や動画ではなく、表の見出し・値・注記だけを取る。

## 最優先で取る項目
- `category_raw`
- `category_mechanism`
- `series_name`
- `model_name`
- `variant_name`
- `spec_rows_raw`
- `notes_raw`
- `price_raw`
- `sku_raw`
- `jan_upc_raw`

## 値の方針
### category_raw
パンくずまたは上位文脈から `リール`, `電動` を保持する。

### category_mechanism
この配下では固定で `electric`

### series_name / model_name / variant_name
商品詳細ページと同じ規則に合わせる。
- 無理に厳密分離しない
- 番手差分が明確なら `variant_name` に入れる

### price_raw
spec セクション内またはその直近に価格表記があれば、そのまま取る。
例：`170,200円`

### sku_raw
`商品コード` に対応する値を取る。

### jan_upc_raw
`JANコード` に対応する値を取る。

## spec_rows_raw の中心ルール
### 主原則
- 見出しと値を **raw のまま** 残す
- 単位変換しない
- 丸めない
- 正規化しない

### 保存形
最低限、次の形を前提にする。

```json
[
  {
    "section": "スペック表",
    "label": "ギア比",
    "value": "4.6",
    "unit": null,
    "note": null,
    "source_text": "ギア比 4.6"
  }
]
```

### 行の作り方
- 見出し列の各項目を `label` にする
- 対応する値列を `value` にする
- `source_text` は `label + value` の元表現を残す
- 単位が見出し側に含まれているなら、最初は `label` 側に残してもよい
- `unit` は無理に分離しなくてよい。分けやすい場合のみ入れる

## 注記の扱い
### notes_raw に入れるもの
- `注記` 行
- `※` で始まる脚注
- 規制、通信互換、商標、転売禁止などの条件文

### spec_rows_raw に入れないもの
- 注記本文そのもの
- 関連情報リンク群

## selector 方針
### 主アンカー
- `SPECIFICATION スペック表` 見出し
- 見出し列の連続テキスト
- 値列の連続テキスト
- `注記` セクション

### 抽出の考え方
1. `SPECIFICATION スペック表` 見出しを見つける
2. 次に並ぶ見出し群を `label` 候補として取る
3. その直後の値群を `value` 候補として取る
4. 対応づけて `spec_rows_raw` を作る
5. `注記` 以降は `notes_raw` に切り分ける
6. `RELATED INFORMATION` 以降は無視する

### 実装上の注意
- class名依存を最小化する
- 表形式でなく、縦並びテキストに崩れていても対応できるようにする
- 値1行を丸ごと1セルとして保持してもよい。最初から細かく分解しすぎない
- `商品コード` と `JANコード` は別項目としても引き上げる

## 取らないもの
- `RELATED INFORMATION` 以下のリンク
- 動画
- feature本文
- 関連表（仕様一覧表、互換表など）への導線先の中身

## 禁止事項
- spec表と related information を混ぜること
- 数値を勝手に分解・換算すること
- `注記` を spec行に混ぜること
- 1 extractor で商品詳細本文と spec表と related links を全部抱え込むこと

## 一文要約
Shimano 電動リールの spec表ページでは、`SPECIFICATION スペック表` を起点に見出しと値を raw のまま対応づけ、`注記` は別で保持し、`RELATED INFORMATION` 以降は切り捨てる。
