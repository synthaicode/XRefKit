# AI Team Operating Boundary Explainer Script

この資料は、`063_ai_organization_explainer_clear` の次に見ることを想定した説明資料である。

前回は、なぜ AI Team が必要かを扱った。
今回は、AI Team の中で何を固定し、どこで人間へ返すのかを扱う。

## ゴール

- 視聴者が、AI Team の価値は AI を増やすことではなく、AI と人間の責任境界を固定することだと理解する。
- 視聴者が、execution / check / unknown / risk / judgment / closure / handoff が境界設計の中核だと理解する。
- 視聴後に、Skill を増やすだけでは不十分で、返却条件と記録条件まで固定する必要があると判断できる状態にする。

## 対象者

- `063` を見て AI Team の必要性は理解した人
- その次に、運用設計の中身を知りたい人
- AI を業務へ入れる際に、人間がどこで判断責任を持つべきかを整理したい人

## 中心メッセージ

- AI Team の目的は、人間を消すことではない。
- 目的は、人間が判断を引き受ける地点を明示し、それ以外を構造として固定することである。
- そのために必要なのが、役割分離、unknown/risk の明示、judgment の記録、closure gate、handoff である。

## スライド構成

1. 前回の続きとして、次に見るべき論点を置く
2. AI Team の本質は、AI と人間の責任境界を固定することだと定義する
3. 人間レビューを増やすことと、境界を設計することは別だと示す
4. unknown / risk を見えないまま流さないことを示す
5. execution と check を分ける理由を示す
6. non-trivial judgment を記録対象にする理由を示す
7. closure gate が「まだ閉じてはいけない」を止めることを示す
8. handoff で次の責任地点を固定することを示す
9. Skill maturity は、この境界がどこまで明確になったかを表すと示す
10. 最後に、AI Team は AI を便利にする話ではなく、責任境界を運用可能にする話だとまとめる
