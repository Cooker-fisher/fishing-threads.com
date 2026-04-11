# DAIWA 電動リール spec extractor 実装タスク分解

## 役割
- 同一URL内の `製品スペック` セクションを見つける
- 見出し群と値行群を対応づけて `spec_rows_raw` を作る
- `メーカー希望本体価格 / JAN / 末尾注記` を引き上げる

## やらないこと
- 冒頭本文抽出
- technology / detail 本文の回収
- normalized 生成

## DAIWA 固有注意
- Shimanoのような別URL spec ではなく、detail/spec 同一URL前提
- 1つの見出し行に対して、複数バリエーションの値行が並ぶことがある
- `メーカー希望本体価格` は spec からも取れる

## 最小タスク
1. HTML取得
2. spec セクション起点抽出
3. 見出し行抽出
4. 値行群抽出
5. label/value 対応づけ
6. price / JAN 抽出
7. 注記抽出
8. payload束ね
9. 保存またはマージ
10. CLI
11. テスト
