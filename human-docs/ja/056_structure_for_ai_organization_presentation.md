# AI にこの構造をどう持たせるか スライド案

- 想定時間: 8-12 分
- 想定読者: AI 組織を設計したいチーム、または AI 運用構造を説明したい関係者
- 目的: `責務 / 判断 / 知識 / 牽制` を AI に持たせる具体要素として `Skill / ドメイン知識 / Workflow protocol / Semantic routing` を説明する
- 構成: 問い -> 4要素 -> 対応関係 -> まとめ
- 形式: 画像ベース

> 注記: 以下のスライド画像は skill-centric 統合前の旧モデル（Flow / Group）を描いています。発表メモは新モデル（Workflow protocol / Semantic routing）に更新済みで、画像は再描画待ちです。

---

![はじめに](assets/056_structure_for_ai_organization/00_intro.png)

発表メモ:
前の資料では、AI にも責務、判断、知識、牽制を持たせる必要があると整理しました。ここでは、その構造を具体的にどう持たせるかを見ていきます。

---

![AI に構造を持たせるには](assets/056_structure_for_ai_organization/01_title.png)

発表メモ:
問いは、AI に必要な構造を何で実装するかです。ここでは Skill、ドメイン知識、Workflow protocol、Semantic routing という4つで整理していきます。

---

![4つの構成要素](assets/056_structure_for_ai_organization/02_four_elements.png)

発表メモ:
4つは役割が違います。Skill は能力と責務、ドメイン知識は判断材料、Workflow protocol は進め方、Semantic routing は依頼から適切な Skill を選ぶ経路として捉えられます。牽制（実行とチェックの分離）は、専用の単位ではなく Workflow protocol と起動時の入力制御ガードが担います。

---

![Skill とは何か](assets/056_structure_for_ai_organization/03_skill.png)

発表メモ:
Skill は、AI に何をさせるかを限定し、専門能力として再利用できる形にしたものです。

---

![ドメイン知識とは何か](assets/056_structure_for_ai_organization/04_domain_knowledge.png)

発表メモ:
ドメイン知識は、判断に必要な前提やルールです。AI の判断は、ここがないと安定しにくくなります。

---

![Flow とは何か](assets/056_structure_for_ai_organization/05_flow.png)

発表メモ:
Workflow protocol は、判断と実行をどの順序で進め、実行とチェックを分離し、完了ゲートを通すかを決める汎用の決定論制御です（旧モデルの Flow に相当）。個人依存の手順を、再利用しやすい進め方へ変える役割を持ちます。

---

![Group とは何か](assets/056_structure_for_ai_organization/06_group.png)

発表メモ:
牽制（責務分離）は、専用の Group を作らずとも、Workflow protocol の実行/チェック分離と完了ゲート、そして起動時の入力制御ガードで成り立ちます。どの Skill を動かすかは Semantic routing が選びます（旧モデルの Group に相当）。

---

![4つの対応関係](assets/056_structure_for_ai_organization/07_mapping.png)

発表メモ:
この4つは独立ではなく、責務、判断、知識、牽制の関係に対応しています。

---

![結論](assets/056_structure_for_ai_organization/08_conclusion.png)

最後の一言:
AI に構造を持たせるとは、Skill、ドメイン知識、Workflow protocol、Semantic routing を分けて置くことではありません。責務、判断、知識、牽制が機能するように、これらを組み合わせて持たせることが重要になります。
