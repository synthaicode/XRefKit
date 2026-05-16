# Flow Skill Knowledge Handoff

![Flow Skill Knowledge Handoff](03_flow_skill_knowledge_handoff.png)

## 一文要約

Flow, Skill, Knowledge, and Handoff separate progression, execution, judgment basis, and transfer points in AI work.

## この図で伝えたい主張

AI が継続的に業務を扱うには、進み方、実行手順、判断根拠、受け渡し点を分ける必要があります。
この分離がないと、プロンプト一塊の中に流れ、根拠、実行、レビュー、引継ぎが混ざります。
図の目的は、XRefKit が何を分けて管理しているかを最初に理解させることです。

## 用語の固定定義

- Flow: 業務の進み方、境界、handoff 順序を定義する単位
- Skill: AI がある作業単位を実行するための具体手順
- Knowledge: 判断根拠としてロードされる業務知識、ルール、観点
- Handoff: 今の作業結果を次の Skill や人間へ渡す受け渡し点
- OS core: AI Agent の実行制御、guard、routing、closure、audit を担う共通層
- Business Pack: 特定業務を動かす Flow、Skill、Knowledge、handoff boundary の束
- Dashboard: AI の実行ログを人間が観測するための monitor-side layer
- Operational Memory: 監査証跡であると同時に、Skill、Knowledge、guard、quality gate の改善材料となる作業記録
- Guard: AI の実行前後で逸脱や不適切な進行を防ぐ制約
- Quality Gate: closure 前に満たすべき検証条件

## 読み方

- まず 4 要素がそれぞれ何を担当するかを見る
- 次に、それらが混ざると何が壊れるかを見る
- 最後に、この分離が OS core と Business Pack にどうつながるかを考える

## 非対象（誤解防止）

- 単なる用語集ではない
- ドキュメント分類だけの話ではない
- 一回の回答生成だけを説明するものではない
- 人間だけの業務フロー図ではない

## 関連図

- [01 XRefKitは、AIに業務を依頼するための基盤](01_xrefkit_as_ai_agent_os.md)
- [02 Business Pack Explained](02_business_pack_explained.md)
- [04 Code Review as Split Checks](04_code_review_as_split_checks.md)

`04` は、この分離をコードレビューに落とした具体例であり、capability をどのように狭い観点へ分けて安定化させるかを見るための図です。
