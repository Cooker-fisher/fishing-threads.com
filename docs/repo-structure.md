# リポジトリ構成

```text
repo/
├─ app/
├─ docs/
├─ prompts/
├─ scripts/
├─ raw/
│  ├─ index/
│  └─ products/
├─ normalized/
├─ derived/
├─ tmp/     # gitignore対象
├─ logs/    # gitignore対象
└─ samples/
   └─ html/ # 代表サンプルのみ
```

## 原則
- `raw` = 実務上の正本
- `normalized` = 再生成可能
- `derived` = 再生成可能
- `tmp` と `logs` はコミットしない
- HTML全保存は通常運用に含めない
- 画像の実体は repo に大量保存しない

## 保存単位
- 一覧ページ: 1ページ = 1 JSON
- 商品ページ: 1商品 = 1 JSON
