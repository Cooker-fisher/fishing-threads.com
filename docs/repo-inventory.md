# 正本一覧表（Inventory）

## 目的
この文書は、Tsuri-threads の main に **存在しているべき正本ファイル** を固定するための一覧表である。

目的は次の3つ。
- 消失事故を早く検知する
- 復旧時に「何を戻せば正常か」を明確にする
- docs / scripts / tests の責務境界を崩さない

---

## 1. docs の正本

### ルート
- `README.md`

### コア設計
- `docs/architecture.md`
- `docs/repo-structure.md`
- `docs/raw-extraction-design.md`
- `docs/extraction-flow.md`

### 運用ルール
- `docs/pull-request-rules.md`
- `docs/codex-collaboration-rules.md`
- `docs/repo-inventory.md`

### selector 方針
- `docs/selectors/shimano-electric-index.md`
- `docs/selectors/shimano-electric-detail.md`
- `docs/selectors/shimano-electric-spec.md`

### task 分解
- `docs/tasks/shimano-electric-implementation-order.md`
- `docs/tasks/shimano-electric-index-extractor.md`
- `docs/tasks/shimano-electric-detail-extractor.md`
- `docs/tasks/shimano-electric-spec-extractor.md`

---

## 2. scripts の正本

### 依存
- `requirements-extractors.txt`

### パッケージ境界
- `scripts/__init__.py`
- `scripts/extractors/__init__.py`

### extractor 本体
- `scripts/extractors/shimano_electric_index.py`
- `scripts/extractors/shimano_electric_detail.py`
- `scripts/extractors/shimano_electric_spec.py`
- `scripts/extractors/shimano_electric_pipeline.py`

---

## 3. tests の正本
- `tests/test_shimano_electric_index.py`
- `tests/test_shimano_electric_detail.py`
- `tests/test_shimano_electric_spec.py`
- `tests/test_shimano_electric_pipeline.py`

---

## 4. 各層の責務

### docs
- 設計と判断基準の正本
- 実装前に読むもの
- 実装判断の根拠を固定するもの

### scripts
- extractor の実装本体
- raw 生成と接続処理
- LLM なしでも再実行できる部分

### tests
- 最低限の破壊検知
- selector / 抽出 / マージの最低保証

---

## 5. inventory 運用ルール
- 新しい正本ファイルを増やしたら、この inventory も同じPRで更新する
- 一時ファイル、tmp、logs、生成物は inventory に入れない
- docs / scripts / tests の削除を含むPRでは、inventory 更新を必須にする
- inventory にあるのに main に無い場合、それは事故として扱う

---

## 6. 復旧優先順位
事故時は次の順に戻す。
1. `README.md`
2. docs のコア設計
3. scripts の extractor 本体
4. tests
5. selector / task docs

---

## 一文要約
この inventory は、Tsuri-threads の docs / scripts / tests で **何が正本として存在しているべきか** を固定するための文書である。
