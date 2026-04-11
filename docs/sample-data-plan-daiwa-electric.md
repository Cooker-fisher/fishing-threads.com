# DAIWA 電動リール sample data plan

## 目的
最初の少量サンプルとして、DAIWA 電動リールから 10件前後を投入する。

## 方針
- いきなり全件投入しない
- まずは番手帯の広がりが出るように選ぶ
- 上位大型機、中型、入門寄りを混ぜる
- raw と normalized の両方で少量 seed を置く

## 初期候補 10件
1. シーボーグ G1800M-RJ
2. シーボーグ G1200M
3. シーボーグ G800MJ
4. シーボーグ 500MJ-AT
5. シーボーグ 600MJ
6. シーボーグ 500MJ
7. シーボーグ G400J
8. シーパワー 1200
9. レオブリッツ 400J
10. レオブリッツ 300J

## この10件を選ぶ理由
- 深海 / 大物向けの上位帯が入る
- 400〜600クラスの中核帯が入る
- レオブリッツで価格帯と入門寄りも入る
- setup や比較導線のテストに向く

## 初期投入物
- 一覧 raw サンプル
- 商品 normalized seed
- 比較用の最低限項目

## 初期 normalized 項目
- maker
- series_name
- variant_name
- category_mechanism
- price_number
- weight_g
- gear_ratio
- pe_capacity_raw
- max_drag_kg
- jafs_power_kg
- jafs_speed_mpm
- jan_upc
