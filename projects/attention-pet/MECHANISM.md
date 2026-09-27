<!-- xid: A4D0C1E89B73 -->
<a id="xid-A4D0C1E89B73"></a>

# Attention Pet の仕組み

更新：2026-09-26。現行評価は `fit-experiment-v1`。能力適合・推論コスト比較・表情を独立させた改訂版。

## 目的と流れ

選択モデルが仮の必要能力を満たすかと、現在の仮定の範囲でより低い推論コストの適合候補が存在するかを分けて示す。利用者がモデル配分を判断するための参考情報である。最終目標は、品質を満たしながら推論・再試行・修正・失敗損失を含む総コストを抑えること。
数値は実験的な仮定で、実モデルの性能・料金を表すものではない。モデル内部のAttentionや残り能力は測定しない。

```text
注釈付き会話／確認した作業項目・依存関係・結果の記録
  → Base RAL（入力された作業の複雑さ）
  ＋ ModelProfile（能力3軸、挙動6項目、相対推論コスト）
  ＋ ReasoningDepth（能力補正、探索倍率、相対コスト倍率）
  → 各候補の Model Expansion / Effective RAL / 必要能力
  → Model Fit / Cost Fit / 理由と比較候補
  → Presentation.petState（表示専用の状態）
  → Petの表情・詳細画面 → 利用者の判断
```

評価はPython側に集約。ブラウザはAPIの `fit` を表示し、3秒ごとに更新する。観測した利用者発言数が増えたときだけ短い動きで受信を示す。この動きは評価結果や表情を変更せず、動きのオフ設定と端末の動き低減設定に従う。
Codex内で起動すると `CODEX_THREAD_ID` のローカルJSONL記録へ固定して連動する。利用者発言の数と、明示的な修正語・前方参照語だけを汎用の作業項目へ投影する。本文は保存しない。添付本文、意味上の依存、作業の完了、実際の成功・失敗は推定しない。したがって常に `Coverage=partial`、`EvaluationConfidence=Unknown` とする。最大100件の利用者発言を対象にし、古い発言は作業集合から外す。テスト用の合成例は利用者向け画面・API・CLIに公開しない。
`turn_context` のモデル識別子と `effort` を読み取り、既知のモデル系列（Luna/Terra/Sol/Astra）と `light/standard/high` の仮設定へ対応付ける。これを試算条件の初期値にし、利用者は画面で別のモデルと深さを比較できる。比較条件はFitEvaluationだけに使い、Codex本体の実行設定やWorkingSetを変更しない。未対応の識別子はModelFit=Unknown。これはモデルの実能力・価格の測定ではない。対象チャットは起動時に固定し、他チャットへの画面切替には追従しない。チャット連動APIは読み取り専用で、手動入力・整理操作は非表示・拒否する。手動モードでは従来の構造注釈を利用できる。
一部の作業しか把握できていない場合は `coverage=partial` として理由欄に表示する。

## Base RAL：入力された作業の複雑さ

各要素の強さを0〜1に正規化し、重みを掛けて合計・丸め処理する。Pythonの `round` を使用。

| 要素 | 正規化する値（上限1） | 既定の最大点 |
|---|---|---:|
| 有効項目 | 有効項目数 / 40 | 30 |
| 依存関係 | 有効edge数 / 関係評価対象の項目数 / 2 | 25 |
| 制約の結び付き | 制約を含むedge数 / 関係評価対象の項目数 | 10 |
| 判断の深さ | 最大判断深度 / 6 | 10 |
| 矛盾・未解決事項 | (矛盾数×3＋質問数＋例外数) / 12 | 15 |
| 根拠の分散 | max(0, 根拠の参照先数−1) / 8 | 10 |

関係評価対象の項目数は履歴を除いた有効項目数（最小1）。有効項目同士を結ぶedgeを数える。
Base RALは0〜100で、モデル選択に依存しない。詳細画面には寄与0を含む全6項目を表示する。

## 仮のプロファイル

能力は0〜100、挙動は0〜1。実装を検証するための仮設定であり、製品比較の根拠ではない。

| プロファイル | 推論 | 制約保持 | 根拠処理 | 探索 | 依存展開 | 制約発見 | 不確実性発見 | 代替案生成 | 圧縮 | 相対推論コスト |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Luna | 48 | 48 | 45 | .2 | .2 | .2 | .2 | .2 | .2 | 1 |
| Terra | 60 | 62 | 58 | .35 | .35 | .35 | .35 | .35 | .25 | 1.5 |
| Sol | 72 | 74 | 70 | .5 | .5 | .5 | .5 | .5 | .3 | 2 |
| Astra | 90 | 92 | 90 | .8 | .8 | .8 | .8 | .8 | .4 | 4 |

| 考える深さ | 各能力への補正 | 探索倍率 | 相対コスト倍率 |
|---|---:|---:|---:|
| light（軽め） | −8 | .6 | .7 |
| standard（標準） | 0 | 1 | 1 |
| high（深く考える） | ＋8 | 1.6 | 1.6 |

能力への補正後は0〜100に制限。深く考えると探索も増えるため、能力向上だけを扱わない。
モデル世代、料金プラン、キャッシュ、実トークン使用量、作業分野の得意不得意は未反映。

## 作業展開と必要能力の式

`D,C,U,J,E` は順に依存関係・制約・未解決事項・判断深度・根拠分散の強さ（0〜1）。既存stateの小数3桁のseverityを使用する。
`b` は選択モデルの挙動。`d` は深さの探索倍率。

```text
探索量 a = .10×b.exploration
         + .10×b.dependency_expansion×D
         + .08×b.constraint_discovery×C
         + .08×b.uncertainty_discovery×U
         + .08×b.alternative_generation×J

Expansion = round(clamp(Base RAL×a×d − Base RAL×.06×b.compression, 0, 30), 1)
Effective RAL = round(Base RAL + Expansion, 1)

必要な推論能力 = min(100, round(.65×Effective RAL + 20×J + 15×D, 1))
必要な制約保持 = min(100, round(.65×Effective RAL + 25×C + 10×U, 1))
必要な根拠処理 = min(100, round(.65×Effective RAL + 35×E, 1))

候補の能力 = clamp(プロファイルの各能力 ＋ 深さの能力補正, 0, 100)
相対推論コスト = round(プロファイルの相対コスト × 深さのコスト倍率, 2)
```

Effective RALは最大130。Expansionは仮の展開量で、実際に発見した依存関係ではない。
圧縮は展開を抑える扱いであり、Base RALより下にはしない。比較しても入力項目・依存関係・保存履歴は変わらない。

## 独立した評価と表示

Model Fitは選択モデルの3軸の能力だけで判断する。他モデルの価格・コスト・適合結果を使わない。

| ModelFit | 条件 |
|---|---|
| Unknown | 作業なし・モデル未選択など、能力評価に必要な材料がない |
| Underpowered | 必要能力3軸のいずれかを下回る |
| Sufficient | 仮の必要能力3軸をすべて満たす |

Cost Fitは能力評価と推論コストの仮比較、現文脈の結果記録を使う。

| CostFit | 条件と意味 |
|---|---|
| Unknown | コスト比較の材料がない |
| RetryRisk | 必要能力を満たさず、再試行等で総コストが増える可能性。ただし失敗原因とは断定しない |
| NoLowerCostCandidate | 現在モデルが必要能力を満たし、同じ深さの登録候補に、より低い相対推論コストで必要能力を満たす候補がない。品質・総コスト・未登録モデルは未比較 |
| LowerCostCandidateAvailable | 能力を満たし、同じ深さで低い相対推論コストの適合候補がある |
| ReviewNeeded | 現文脈に失敗・修正の記録がある。他のコスト判定に優先 |

各候補は自分自身のExpansionを含めて必要能力を計算する。低い推論コストの候補があるという評価は、現在モデルの能力が過剰であること、実品質の同等性、総コストの低下、モデル変更の必要性を意味しない。

Petはモデル内部の状態や感情を表現しない。ModelFit、CostFit、Coverage、Confidence、結果記録を人間が短時間で認知できる形に圧縮するPresentationである。PetStateは評価データではなくPresentation stateであり、最も重大な評価を選ぶ順位付けでもない。表情の導出は独立した `presentation.py` に置き、UIは `presentation.petState` のみを使う。

| 優先順 | 条件 | PetState | 表情 |
|---:|---|---|---|
| 1 | CostFit=ReviewNeeded | Review | 疑問符と首かしげ。結果の記録の確認を促す |
| 2 | ModelFit=Unknown | Unknown | 灰色の疑問符 |
| 3 | ModelFit=Underpowered | Strained | 困った顔、汗、小さく揺れる |
| 4 | Sufficient / NoLowerCostCandidate | Balanced | 落ち着いた笑顔、ゆっくり動く |
| 5 | Sufficient / LowerCostCandidateAvailable | Relaxed | 暇そうな目、穏やかな揺れ |

Balancedは現在の比較条件で低コストの適合候補が確認されない状態であり、配分の最適性ではない。Relaxedは低コスト比較候補がある状態であり、能力過剰の判定ではない。
Reviewは能力不明・不足でも優先する。失敗・再試行・修正の実結果がある場合、仮の能力判定だけで結論を進めず、次に実結果を確認する行動を示すためである。ModelFitを上書きせず、詳細にはModelFitとCostFitの両方を表示する。Underpowered / ReviewNeeded / Reviewは矛盾ではない。
通信失敗や選択変更の待機中は、表情をUnknownにして以前の能力・コスト評価・候補・内訳・整理操作を消す。再接続後に再表示する。

## Presentation：文章と表情を一箇所で生成

### 低コスト比較候補の案内

同じ考える深さで各候補自身の作業展開を含めて必要能力3軸を試算する。選択モデルがSufficientで結果記録によるReviewNeededがない場合、`lowerCostCandidates` のうち相対推論コスト指数が最も低い候補を「低コスト比較候補」として表示する。例：A5でAstraの比較候補はLuna、B3でAstraまたはSolの比較候補はTerra。比較候補と指数は詳細にも示す。品質同等性や総コスト低下は未確認。

該当候補がない場合は「現在の比較条件では、より低い相対推論コストで仮の必要能力を満たす候補は確認されていません」。Underpoweredでは低コスト候補を案内しない。ReviewNeededでは結果記録の確認まで案内を保留する。Unknownでは作業内容とモデル選択を求める。
Partialでは入力された一部の作業に限ると注記する。案内は実験プロファイルの仮比較であり、Codex記録からモデル識別子を読んでも、実能力・実品質・総コストは測定していない。モデル変更は自動実行しない。

APIの`presentation.modelGuide`、`modelGuideShort`、`modelGuideDetail`、`modelGuideStatus`が案内の唯一の文章と状態の出所。ブラウザは短い案内をPet横、長い案内を中央と詳細に表示し、候補選択を再計算しない。

評価式は変えず、Pythonの `present_fit(model_fit, cost_fit, coverage, confidence)` が以下を返す。
APIの `presentation` に `headline/summary/shortMessage/detailReason/actionHint/scopeNote/confidenceNote` と4種類の評価ラベルを追加した。
ブラウザはCSS表情との対応と表示だけを担当する。常時表示するカードのheadline・summaryはPresentationの値を使う。

| PetState | 基本見出し | 補足の意味 | 次の行動 |
|---|---|---|---|
| Unknown | まだ評価できません。 | 評価に必要な情報が不足 | 入力とモデル選択を確認 |
| Strained | この作業には、能力が不足する可能性があります。 | 仮の必要能力の一部を満たさない。失敗原因とは断定しない | 能力の高い候補や分割・整理を検討 |
| Balanced | 必要な能力を満たす試算です。 | 現在の仮定で低い推論コストの適合候補は未確認 | 現設定で進めるか判断し、実結果も確認 |
| Relaxed | 必要能力を満たす、より低い推論コストの候補があります。 | 現モデルも候補も仮の能力条件を満たす。総コストは未比較 | 候補の条件を比較 |
| Review | 実際の結果を含めて、配分を見直す必要があります。 | 結果の記録がある。モデル能力だけが原因とは判断しない | 失敗・修正記録を確認 |

Partialの場合、Unknown以外の見出しに「現在確認できている範囲では、」を付け、補足に一部だけの評価と明記する。Pet横と中央にも「一部の作業のみ評価」を表示する。
ReviewedでもConfidenceがUnknown/Lowなら「現在の入力範囲では、」を付ける。Confidenceは別ラベルで表示し、ModelFitを上書きしない。
CostFit=NoLowerCostCandidateは「低コスト適合候補なし / No lower-cost candidate」と表示する。現在の比較条件に限定し、モデルの推奨を意味しない。
Relaxedの暇そうな見た目は候補の存在を示すUI上の比喩であり、内部状態の観測ではない。

情報は3層：Pet＋短文＋範囲 → 4種類の評価 → 折り畳み式の数値・3軸・候補・指数・理由。
候補比較には現在モデル／深さ／指数と候補名／深さ／指数を表示する。再試行・修正時間・失敗損失を総コスト比較に含めていない注記を維持する。
選択変更・入力更新の待機中は全見出しを「評価を更新中」に揃え、通信失敗なら「評価を取得できません」とUnknown表情に戻す。古い見出し・数値・候補を新評価として表示しない。

変更ファイル：presentation.py、model.py、evaluator.py（Presentationへの引数受け渡しのみ）、pet.html/js/css、fit.schema.json、test_attention_pet_fit.py、attention_pet_ui_check.cjs、README、設計書、本MDと検証記録。

## 入力範囲と確からしさ

`coverage=partial|reviewed|null` は評価結果とは独立した入力範囲。nullは作業なし。
UIはModel Fit、Coverage、Confidenceを別々に表示する。
`evaluationConfidence=Unknown|Low|Medium|High` を独立フィールドとして用意し、今回は常にUnknown。
reviewedでも性能予測の信頼性を保証しない。Sufficient＋partialは、入力された一部について仮の必要能力を満たす試算にとどまる。

## 総コストとAPI契約

```text
Expected Total Cost = Inference Cost + Retry Cost + Correction Cost + Failure Risk Cost
```

現在は `inferenceCostIndex` のみ仮の比較に使う。
実金額の `inferenceCost`、`retryCost`、`correctionCost`、`failureRiskCost`、`expectedTotalCost` はすべてnull。
LowerCostCandidateAvailableは相対推論コストの仮比較に限定する。lower inference cost → lower total costという推論は未検証であり、判定に使わない。

APIの `fit` は以下を持つ。旧分類の互換別名は返さない。保存済みセッションはfitを保持しないため移行不要。

- `baseRal`、`selected` 内の `expansion/effectiveRal/requiredCapability/capability`。
- `modelFit`、`costFit`、`presentation.petState`。
- `alternatives`（他候補すべて）、`lowerCostCandidates`（同じ深さ・必要能力を満たす・より低い推論コストの候補）。
- `coverage`、`evaluationConfidence`、`reasons`。
- `inferenceCostIndex` と上記の未推定コスト。
- `profile/depth`、`version=fit-experiment-v1`、`calibration=uncalibrated`。

元の `costComponents` 辞書は明示的なコストフィールドへ移行。`selected.relativeInferenceCost` は候補比較用の指数として維持。
入力スキーマ・Base RAL・Expansion・必要能力3軸・ModelProfile・ReasoningDepthの式は変更しない。

## テスト用シナリオ（画面には表示しない）

以下は標準深さの ModelFit / CostFit / PetState。実性能の実証結果ではない。

| シナリオ | Luna | Terra | Sol | Astra |
|---|---|---|---|---|
| A・5段階目 | Sufficient / NoLowerCostCandidate / Balanced | Sufficient / LowerCostCandidateAvailable / Relaxed | Sufficient / LowerCostCandidateAvailable / Relaxed | Sufficient / LowerCostCandidateAvailable / Relaxed |
| B・3段階目 | Underpowered / RetryRisk / Strained | Sufficient / NoLowerCostCandidate / Balanced | Sufficient / LowerCostCandidateAvailable / Relaxed | Sufficient / LowerCostCandidateAvailable / Relaxed |
| B・5段階目 | Underpowered / RetryRisk / Strained | Underpowered / RetryRisk / Strained | Underpowered / RetryRisk / Strained | Sufficient / NoLowerCostCandidate / Balanced |
| D・5段階目 | Underpowered / RetryRisk / Strained | Underpowered / RetryRisk / Strained | Underpowered / RetryRisk / Strained | Underpowered / RetryRisk / Strained |
| C・3段階目 | Sufficient / ReviewNeeded / Review | Sufficient / ReviewNeeded / Review | Sufficient / ReviewNeeded / Review | Sufficient / ReviewNeeded / Review |

Cでは低いコストの候補があっても、失敗・修正の記録に基づくReviewNeededを優先する。
低コスト比較候補の有無は実務上の品質同等・総コスト最小を意味しない。

## 整理操作との関係

| 操作 | 複雑さを下げる可能性 | 今のボタンで実際に行うこと |
|---|---|---|
| Fix | 判断を確定し、迷いを減らす | 判断項目に確定の印。RALを自動減点しない |
| Summarize | 有効項目・根拠の分散を減らす | 条件を満たす不要な記録を退避。文章の要約生成ではない |
| Archive | 完了項目を作業対象から外す | 参照不要な完了項目・履歴を退避 |
| Externalize | 手元で保持する情報を減らす | 引継ぎファイルの保存 |
| Split | 同時に扱う依存関係を減らす | 分割用の引継ぎファイルの保存 |
| Resolve | 未解決事項を減らす | 未解決事項を含む引継ぎファイルの保存 |
| Rebase | 目的・条件の整理で混乱を減らす | 見直し用の引継ぎファイルの保存 |
| Restart | 新しい文脈で確認し直す | 新チャット用の引継ぎファイルの保存 |

有効な制約や必要な根拠を削除して点数だけを下げない。保存だけでは実際の分割・問題解決・新チャット作成は行わない。
削減量は先に保証せず、操作後の入力と結果で確認する。

## 保存と画面

標準はモデルとコストの配分カード＋Pet。カードには状態文・入力範囲・比較モデル・深さを常時表示し、数値・候補・評価理由だけを展開表示にする。「5分以上更新されていません」は表示しない。
ブラウザー画面からの入力・整理操作・画面切替は提供しない。
モデル選択はブラウザ内に保存する。WorkingSetと履歴はローカルのセッションファイルに保存する。
Loopback APIは起動時のトークンで認証する。FitEvaluationは応答時に計算し、既存の保存形式・入力スキーマは変えない。

## 将来の校正候補と未検証事項

今回の変更ファイル：`xrefkit/attention_pet/model.py`、`evaluator.py`、新規`presentation.py`、`xrefkit/resources/attention_pet/pet.html`・`pet.js`・`pet.css`、`tests/test_attention_pet_fit.py`、新規`tests/attention_pet_ui_check.cjs`、`projects/attention-pet/schema/fit.schema.json`、ルートとプロジェクトのREADME、本MD、`docs/designs/100_attention_pet.md`、`VALIDATION.md`。検証記録は既存のskill runにも追記した。

関連テストは79件成功。APIのURL・入力スキーマは維持し、応答fitの分類とフィールドを改訂した。HTTPサーバーとCLIの転送処理自体に変更は不要だった。

現在のExpansionはBase RALに比例するため、入力の複雑さは小さくても探索で大量の潜在問題が見つかる作業を過小評価する可能性がある。
将来は `Expansion = base-dependent expansion + discovery floor / discovery bias` を検証候補とする。今回は仮の追加係数を入れない。
能力軸の将来候補はExecution / Transformation Reliability（大量ファイル変更・定型変換・コード修正・リファクタリング・変更漏れに関する実行信頼性）。今回は追加せず3軸を維持する。

- 作業分野ごとの合格基準と必要能力3軸。入力注釈の抜け漏れ。
- 能力・挙動・深さの係数、展開と圧縮の量、上限と境界。
- 実トークン・単価・再試行・人の修正時間・失敗時の損失。
- 同一課題を複数モデル／深さで実行した成功・失敗と総コスト。
- 表情だけで「能力不足／低コスト比較候補なし／候補あり」が伝わるか、誤認と注意負担。

匿名化した作業・選択・結果・費用を対応付け、評価用データを分離して仮の式を検証する。
自動テストは式の一貫性の確認であり、現実の予測力や表情の理解率は未検証。

実装・起動は [README](README.md)、設計経緯と研究参照は [設計書](../../docs/designs/100_attention_pet.md#xid-38C97BA1E4D2)、検証状況は [VALIDATION](VALIDATION.md) を参照。
