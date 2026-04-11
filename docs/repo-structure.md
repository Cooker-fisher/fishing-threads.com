# リポジトリ構成

このリポジトリには、**すでに決まっているものだけ**を置く。
最初から盛り込みすぎない。

## 構成
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

## ルール
- `raw` = 実務上の正本
- `normalized` = 再生成可能
- `derived` = 再生成可能
- `tmp` と `logs` はコミットしない
- `samples/html` は代表サンプルだけ置く
- HTML全保存は通常運用に含めない
- 商品画像の実体は repo に置かない

## raw の保存単位
### 一覧ページ
**1ページ = 1 JSON** で保存する

例：
`raw/index/shimano/electric/001.json`

### 商品ページ
**1商品 = 1 JSON** で保存する

例：
`raw/products/shimano/force-master-200.json`
