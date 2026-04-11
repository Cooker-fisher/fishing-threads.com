# Data Schema 初稿

## 目的
この文書は、Tsuri-threads の初期データ構造を固定するための初稿である。

初期方針は次の通り。
- 主役は relation / setup
- まずは電動リール軸
- raw → normalized → derived の3層
- 最初から全カテゴリを厳密網羅しない

---

## 1. entity

### reels
リール本体。

主な項目:
- id
- maker
- brand
- category_mechanism
- category_usage
- water_type
- series_name
- model_name
- variant_name
- official_spec
- notes
- source_refs

### targets
対象魚種や釣り物。

主な項目:
- id
- name
- aliases
- area_type
- boat_shore
- depth_range
- sinker_range
- line_range
- notes

### lines
ライン規格。

主な項目:
- id
- line_type
- pe_number
- lb_class
- material
- notes

### rod_conditions
ロッド型番ではなく、まずは条件で持つ。

主な項目:
- id
- length_min
- length_max
- sinker_min
- sinker_max
- action
- line_min
- line_max
- notes

### rigs
仕掛けカテゴリ。

主な項目:
- id
- rig_type
- hook_type
- sinker_range
- line_range
- notes

### articles
補助コンテンツ。

主な項目:
- id
- title
- slug
- article_type
- related_entities
- related_relations

---

## 2. relation

### reel_to_target
- reel_id
- target_id
- fit_level
- official_basis
- practical_basis
- beginner_basis
- notes

### reel_to_line
- reel_id
- line_id
- official_basis
- practical_basis
- beginner_basis
- notes

### reel_to_rod_condition
- reel_id
- rod_condition_id
- fit_level
- notes

### target_to_rig
- target_id
- rig_id
- fit_level
- notes

### target_to_line
- target_id
- line_id
- fit_level
- notes

### condition_to_target
- condition_id
- target_id
- fit_level
- notes

---

## 3. setup
setup は relation を束ねた実用単位。

主な項目:
- id
- target_id
- reel_id
- line_id
- rod_condition_id
- rig_id
- confidence_level
- official_basis
- practical_basis
- beginner_safe_basis
- notes

---

## 4. raw layer
raw は取得事実の正本。

### raw/index
1ページ = 1 JSON

### raw/products
1商品 = 1 JSON

主な raw 項目:
- source_site
- source_url
- crawl_date
- source_hash
- maker
- category_raw
- category_mechanism
- series_name
- model_name
- variant_name
- price_raw
- sku_raw
- jan_upc_raw
- status_raw
- description_raw
- notes_raw
- image_urls
- spec_rows_raw
- subtype
- extra

---

## 5. normalized layer
normalized は比較しやすさのための層。

例:
- price_number
- weight_g
- pe_capacity_standardized
- drag_kg
- slug
- maker_normalized

注意:
- raw を壊さない
- normalized は再生成可能にする

---

## 6. derived layer
derived は UI や導線のための派生層。

例:
- 番手帯ごとの候補一覧
- 魚種ごとの推奨リール一覧
- 比較表
- setup bundle
- 関連ページリンク

---

## 7. ID / slug 方針
- id は安定性優先
- slug は表示やURLのための派生値
- product slug は人が読める形を優先するが、将来は source_id 併用を許容する

---

## 8. 初期の割り切り
- ロッドは型番ではなく条件で持つ
- 公式値と経験則を分ける
- setup は完全自動生成にこだわらない
- 最初から全カテゴリ共通の完璧 schema を狙わない

---

## 一文要約
初期 schema は、entity を最小限に抑えつつ、relation / setup を主役にして、電動リール軸の raw → normalized → derived を支える構造にする。
