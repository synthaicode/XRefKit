<!-- xid: 38C97BA1E4D2 -->
<a id="xid-38C97BA1E4D2"></a>

# Attention Pet: モデル選択の適切性の観測

## 現行設計：能力適合・コスト比較・表示の分離（2026-09-26 改訂）

### UI意味整合の追加改訂

現行のローカル表示は、起動元の `CODEX_THREAD_ID` に対応するCodex記録から利用者発言と `turn_context` のモデル・考える深さを読み取る。チャットIDを固定し、他のチャットやツール出力を推測して取り込まない。発言本文を保存せず、語句の手掛かりと件数から汎用項目を作るため、依存関係・結果・完了は未確認でありCoverageはPartial、ConfidenceはUnknownとする。モデル識別子の系列を未校正の実験プロファイルへ対応付け、試算条件の初期値にする。画面では別のモデルと深さを読み取り専用で比較できるが、Codex本体の設定は変更しない。実能力や料金は測定しない。画面はモデルとコストの配分カードとPetだけを常時表示し、手動入力・整理操作・画面切替を提供しない。API書き込みも拒否する。対象チャットは起動時に固定し、画面で別チャットを開いても自動追従しない。

比較候補にTerraを追加した。LunaとSolの間に置く能力・挙動・相対推論コストは未校正の仮値であり、実モデルの性能順や価格を示すものではない。

低コスト比較候補の案内は、同じ考える深さで必要能力3軸を満たす低い相対推論コスト候補のうち、指数最小のものを仮の比較対象として示す。実運用でのモデル変更可否は判定しない。結果記録があれば案内を保留し、選択モデルの能力が不足していれば低コスト候補を案内しない。Partialと未校正の注記を維持し、実際のCodexモデルを検出した表現を避ける。APIのPresentationが文章を生成する。

評価式は維持し、`presentation.py`を文章の唯一の生成元とする。APIのpresentationにはpetStateに加えheadline、summary、shortMessage、detailReason、actionHint、scopeNote、confidenceNote、ModelFit/CostFit/Coverage/Confidenceの表示ラベルを含める。
ブラウザはAPIの文章をそのまま表示し、評価状態に応じた文章を独自生成しない。通信待ち・失敗は評価でなく通信状態として全表示面をUnknownへ揃える。
中央と詳細の見出し・補足は同一。Partialは見出しの範囲限定と「一部の作業のみ評価」表示、Unknown/Low confidenceは慎重な範囲表現と補助表示に反映し、ModelFitは変えない。
第1層はPet＋短い状態文＋入力範囲、第2層はModelFit/CostFit/Coverage/Confidence、第3層は折り畳んだ数値・必要能力・候補・コスト・理由。
Relaxedは低い推論コストの適合候補があることを表す比喩であり、モデル内部の暇や余力を観測するものではない。
詳しい状態文言表はMECHANISM.mdのPresentation節を参照。表情だけでの理解率、文言の長さによる読みやすさは未検証。

Attention Petは選択モデルが仮の必要能力を満たすかと、現在の仮定でより低い推論コストの適合候補があるかを分けて示す。
旧設計は低コスト候補の存在を能力過剰と分類しており、能力評価とコスト評価を混同していた。現行版では廃止する。

- ModelFitはUnknown / Underpowered / Sufficient。選択モデルの能力3軸だけで判定し、他モデルの価格や比較結果を使わない。
- CostFitはUnknown / RetryRisk / NoLowerCostCandidate / LowerCostCandidateAvailable / ReviewNeeded。同じ深さで各候補の作業展開を含めて比較する。NoLowerCostCandidateは登録済み候補に低コスト適合候補がないという範囲限定の判定である。
- PetStateはUnknown / Strained / Balanced / Relaxed / Review。`presentation.py` で導出し、UIがModelFitから直接表情を選ばない。Petはモデル内部の状態や感情ではなく、ModelFit、CostFit、Coverage、Confidence、結果記録を短時間で認知できる状態へ圧縮するPresentationである。PetStateは評価データではなくPresentation stateであり、最も重大な評価を表す順位でもない。結果記録に基づくReviewを最優先するのは、仮の能力判定だけで結論を進めず、実際の失敗・再試行・修正を次に確認すべき行動として示すためである。Underpowered / ReviewNeeded / ReviewでもModelFitとCostFitを詳細に併記する。
- coverageとevaluationConfidenceは独立項目。今回はConfidence=Unknownで、Sufficient＋partialを確実な品質判定と扱わない。
- 能力適合・低い推論コストは品質保証でも総コストの優位性でもない。候補がないことから現在モデルの推奨を導かない。
- 推論コスト指数以外の実コストは未推定。再試行・修正・失敗損失・Expected Total Costはnull。lower inference costからlower total costを推論しない。
- 自動ルーティングは行わない。整理操作・入力契約・保存形式・Base RAL・Expansion・必要能力3軸・モデルプロファイルと深さの係数を維持する。

式、API契約、仮パラメータ、テスト用シナリオ表は `projects/attention-pet/MECHANISM.md` を現行定義とする。人工シナリオを利用者向け画面・API・CLIには提供しない。
FitEvaluationは応答時に計算するため旧保存データの移行不要。モデル未選択時にも現文脈に失敗記録があればReviewを表示し、能力はUnknownのまま保持する。
旧AttentionState.expressionは既存RAL診断用で、現行UIの表情には使用しない。

### 今回変更しない式と将来の候補

ExpansionはBase RALに比例するため、低いBase RALから多数の潜在問題を発見する作業を過小評価する可能性がある。
将来は `base-dependent expansion + discovery floor / discovery bias` を校正対象として検討する。今回は仮係数を追加しない。
Execution / Transformation Reliabilityは、大量ファイル変更・変換・修正・変更漏れの実行信頼性を扱う将来の能力軸候補。今回は追加しない。

### 検証

能力不足／充足、他候補の価格がModelFitに影響しないこと、コスト分類、Reviewの優先、partialの独立保持、表示マッピング、通信失敗時の古い評価消去を検証する。
実モデルの品質・料金・総コスト最適性・表情理解率は未検証。以下は歴史的な設計記録であり、現行分類は本節と上記MDに従う。

## 旧設計・実装経緯の記録（以下は履歴）

### 当初の目的と境界

依頼、制約、判断の関係が増える様子と、解釈のズレの観測を、小さなPetで認知できるようにする。
この実装は `task-structure-based estimated load` の実験版であり、モデル内部Attention、疲労、残り能力、成功確率の測定ではない。
ユーザー提供のAttention Pet仕様を実装根拠とする。独立UI、heuristic、初期閾値の選定は依頼で委任された `local_choice_allowed`。
スコアの実証的な予測性能は `unknown`。自動的なモデル停止・チャット作成・文脈削除は行わない。

## 環境・拡張点の調査

2026-09-26に以下を確認した。

| 対象 | 確認結果 | 判断への影響 |
|---|---|---|
| XRefKit source / projects | Pet / mini UI実装を特定できなかった。既存のskill-run-dashboardは別の観測対象 | 新規モジュールと独立表示を追加 |
| Windows package metadata | `OpenAI.Codex 26.924.1866.0` | desktop環境の識別。CLIとは別 |
| PATH上のCLI | `codex-cli 0.23.0`。helpにPet制御コマンドなし | desktop機能の不存在証明には使わない |
| ローカル `~/.codex/pets` | 調査時にファイルなし | 状態変更用の契約は得られない |
| このチャットで公開されたツール | チャット・ブラウザ・ファイル等。Pet状態を設定するツールなし | ツール名を推測しない |
| [公式プラグイン仕様](https://developers.openai.com/plugins/build/plugins) | Skills / MCP / hooks / 配布情報を文書化 | 配布やツール接続と、ネイティブPet制御は別 |
| [公式Features](https://learn.chatgpt.com/docs/features) / [App Server](https://learn.chatgpt.com/docs/app-server) | 取得したページにPet制御の契約を確認できなかった | 「公開仕様を確認できなかった」という限定的結論 |
| [公式MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) | 外部ツール接続の手段 | 将来の入力アダプター候補 |

ネイティブPetの実装箇所は未特定。非公開desktopバンドルの解析やprivate API呼出しを根拠にせず、ユーザーが明示的に許可した独立UIを採用する。
将来、公式制御APIが確認された時点で表示アダプターだけを差し替える。

## アーキテクチャ

```text
Annotated Conversation / Reviewed Working Set
    -> model.extract (stable-ID upsert, evidence validation)
    -> evaluator.evaluate (pure function, configurable weights)
    -> Store (time ordering, recovery, bounded history, atomic persistence)
    -> loopback HTTP Attention State API
    -> browser Pet adapter (SVG/CSS, polling)
```

`xrefkit/attention_pet/`に評価・API・CLI、`xrefkit/resources/attention_pet/`に表示を配置する。
既存CLIへの登録や既存MCP serverへの変更を避け、`python -m xrefkit.attention_pet`から独立起動する。
Pydanticは既存依存を利用し、外部CDNや新規フロントエンド依存は不要。

### 入力契約

`WorkingSet`: `schemaVersion`, `taskId`, `contextId`, `observedAt` (UTC epoch seconds), `coverage`, `items`, `dependencies`, `observations`。
`coverage=partial`が既定。注釈者が対象範囲を確認した場合のみ `reviewed` を送る。
入力欠落は正常値に置き換えず、必須フィールド不足・未知フィールド・無効参照・重複ID・非有限時刻を拒否する。

Itemは `goal|constraint|decision|question|exception|history|conflict`、状態は `active|done|archived`。
`source`とテキストを保持する。判断の深さ `depth` は注釈者が与える仮説で、自動推論の実測値ではない。
Dependenciesは有効な異なるItemのIDを結び、`evidence`を持つ。循環は保持し、再帰評価には使わない。
Observationは `context` と根拠を持つ。過去文脈の観測は保存するが現在のTrajectory計算から除外する。

Conversation入力は自然文のturnと構造注釈を受け取る。自由文の意味抽出器ではなく、明示注釈のreducerである。
同じItem IDの後続注釈で状態を更新し、根拠が実在turnを指すことを検査する。
未注釈turnがあれば `partial` に落とす。意味的な誤抽出・過少抽出は検出できない。
注釈は人間、または根拠確認を伴うAIが作成する。ユーザーのチャット全体を自動で読み取らない。

### RAL heuristic-v1

有効項目数を `N`、有効history以外の項目数を `R=max(1,N-history)`、有効依存数を `E` とする。
すべてのseverityを0〜1に制限し、寄与点を合計して整数に丸める。丸め前の寄与は原因として保存する。

| 要素 | 重み | severity |
|---|---:|---|
| Working Set | 30 | `N / 40` |
| Dependency Complexity | 25 | `E / R / 2` |
| Constraint Density | 10 | 制約を含む有効edge数 / R |
| Decision Depth | 10 | 有効判断の最大depth / 6 |
| Conflict Pressure | 15 | `(3*conflict + question + exception) / 12` |
| Context Dispersion | 10 | `(異なるsource数 - 1) / 8`、下限0 |

履歴退避によって依存数が増えたように見えないよう、密度の分母はhistoryを除く。
すべての依存を数えるが、edge種別・因果強度・グラフ中心性までは推定しない。
重みは合計100のJSONファイルで変更可能。状態出力に使った重みと `evaluatorVersion` を残す。

### Delta / Trend

同じtaskの直前スナップショットとの差。初回・別taskは `null`。
時刻が逆行・同時刻で内容が異なる入力は拒否する。同じ内容の再送は冪等。
直近300秒以内の最古のサンプルから15点以上増加すれば `rapid_rise`。直前の `deltaRal` と窓全体の `windowDeltaRal` は別に保持。
サンプリング頻度に依存する仮説であり、速度の絶対校正ではない。UIは5分を過ぎた観測を古いと明示する。

### Trajectory heuristic-v1

現在のcontextに観測がなければ `null`。根拠があるときだけ、基準85 + validatedの加点(各5、最大10) − ペナルティを0〜95に制限。
ペナルティは `repeated_error:18`, `correction_ignored:22`, `misread_explanation:18`, `decision_contradiction:15`, `intent_drift:18`, `no_improvement:15`, `repeated_failure:20`。
これは粗い警戒指標で、正解確率ではない。RALを入力に使わず、低RALの誤軌道を独立して表す。
同じ文脈で繰り返す誤りは累積する。時間減衰や、少数の成功による失敗の自動帳消しはしない。

## 状態と表情

| 条件 | State | Pet |
|---|---|---|
| RAL < 75、Trajectory >= 50、reviewed | NORMAL | RAL帯に応じる |
| RAL >= 75、Trajectory >= 50、reviewed | HIGH LOAD | 橙色・汗・警告 |
| RAL < 75、Trajectory < 50 | WRONG TRAJECTORY | 紫色・首を傾ける・方向転換記号 |
| RAL >= 75、Trajectory < 50 | CRITICAL | 赤系・目と口の警告 |
| Trajectory観測なし、またはpartial（誤軌道の観測を除く） | UNKNOWN | 表情は観測できたRAL帯を維持。未判定・抽出範囲は詳細に表示 |
| 有効な作業構造もなくpartial | UNKNOWN | 灰色・疑問符。負荷の入力待ち |

基本5帯は `0–39 stable`, `40–59 loaded`, `60–74 strained`, `75–89 high_pressure`, `90–100 unstable`。
Trajectory < 50は通常の表情を上書きする。Trajectoryの観測不足だけで負荷表情を上書きしない。`unstable`という表示名だけでRestartは推薦しない。
急増は矢印で示す。色だけに頼らず、眉・口・姿勢・記号を変える。通常状態で通知やモーダルを出さない。
状態・判断・入力範囲は常時表示し、数値・候補・評価理由は展開表示にする。reduced-motionをサポートする。

## 回復操作

| Action | 実装の効果 | スコアへの扱い |
|---|---|---|
| Fix | 現在の判断のfixedフラグを保存 | 関係は残るため自動減点なし |
| Summarize | 参照されていないhistory/完了項目を退避し、出典付き要約一覧を保存 | active setの実際の差で再計算 |
| Archive | 同じ保存安全条件で退避 | 同上 |
| Externalize | 構造と根拠をJSONとして保存できる | 状態不変 |
| Split / Resolve / Rebase | 作業構造を含む、目的別の引継ぎJSONを保存 | 構造変更はレビュー後の新規入力で反映 |
| Restart | 新しいチャットに持ち込む引継ぎJSONを保存 | チャット作成・正常化は自動実行しない |

Summarizeは生成AIによる意味的圧縮ではなく、根拠を保持する決定的な退避である。有効制約を削除せず、稼働中項目に依存で結び付く履歴は退避しない。
Restart候補は低Trajectoryから選ぶ。実際の新contextに観測がなければ `unknown`、訂正前提を確認した新観測によってのみ回復を表示する。
APIは観測時刻の比較で古い画面からの回復を拒否する。状態・履歴・回復記録は一緒にatomic保存し、保存失敗時は現状態を変えない。

## MCPと将来の入力アダプター

初期版は公開された通常のローカルHTTP APIへ、明示的なsnapshot/conversationを送る。
Codexは承認されたshell作業からHTTP入力を送れる。既存チャットを透過的に監視する機構ではない。
MCPを導入する場合は `publish_attention_working_set`, `get_attention_state` の薄いアダプターから同じStore/APIを呼ぶ。
この2つは設計候補名であり、本実装の登録済みMCPツールではない。既存XRefKit MCP server・Codex設定は変更しない。
official App Serverのイベントアダプターは、対象クライアントで公開イベント・権限・意味抽出契約を検証してから実装する。

## 検証と解釈

人工会話A〜Eで方向性と不変条件を検証し、単体テスト、HTTP統合テスト、ブラウザ操作を実施する。
数値の最新結果と検証した画面は `projects/attention-pet/` の実験結果を参照。
予測妥当性、誤警報率、実作業への有効性は人工テストだけでは確認できない。

| 評価質問 | 今回判断できること | 未検証のこと |
|---|---|---|
| 1. 制約取りこぼしとRALの相関 | 依存を増やすとRALが上がる | 実LLMの取りこぼしとの相関 |
| 2. Deltaが有効な場面 | 300秒以内の急増と単一スコアを区別できる | 実利用で絶対値を上回る予測性能 |
| 3. Trajectoryの独立性 | CでRAL一定のまま低下し、EでRAL一定のまま回復 | 注釈から独立した検出精度 |
| 4. false positive | Aの人工例は高負荷警告にならない | 実利用での頻度、最適閾値 |
| 5. 作業の妨げ | Petのみモード、モーダルなし、数値の常時表示なし | 利用者の注意負担 |
| 6. 直感的理解 | 負荷と誤軌道の表情を視覚的に区別 | 人による理解率 |
| 7. Restartの早期認知 | 低RALでも繰返し訂正失敗で候補化 | 従来とのリードタイム比較 |
| 8. 数値なしの理解 | 色・姿勢・眉口・記号が変わる | ラベルを隠した識別テスト |

したがって、作業構造の変化を知らせる手掛かりとして使える実験版である。一方、AI劣化の予兆検出器として有効だと結論づけるには実測が足りない。
次の実験では、課題ごとに入力注釈と出力の制約違反を独立採点し、事前登録した閾値を未使用課題で評価する。
ベースライン（項目数・文脈長のみ）との比較、ROC/precision-recall、誤警報回数/時間、検知リードタイム、表情理解・注意負担の利用者試験を行う。

## 制限

- 入力は人/AIによる明示注釈。未観測の矛盾や初期の誤前提は見逃す。根拠内容の真偽までは検証しない。
- `reviewed`は入力者の申告。スコアや固定フラグは正しさの保証ではない。
- 保存はローカル平文。履歴は直近100件、回復記録も100件。永続的な監査保管ではない。
- 一つのserverは一つの現在taskを表示する。taskを切り替えると履歴をリセットする。別taskには別port/sessionを使う。
- 一つのsessionファイルに複数serverを起動しない。プロセス間の排他は提供していない。
- ループバック、bearer token、Host/Origin検査、CSPを備えるローカル実験用。公開サービス用ではない。
- 同じOSユーザーの悪意あるプロセスからの隔離は提供しない。
- ネイティブPet制御・自動チャット監視・自動Restart・MCP登録は提供しない。

## 判断を変える条件

根拠付きの公式Pet control契約が得られれば表示アダプターを変更する。
注釈の再現性と検出性能が検証されれば自動Extractorを追加する。
実験から校正根拠が得られれば重み・Trajectoryペナルティ・閾値をversion付きで更新する。
具体的な意思決定のContext/Alternatives/Reason/Rejected/Change conditionsは、作業中の判断記録に保存する。


## 2026-09-26: Game UI and peripheral-display evidence

The phrase 「関係が増えています」 incorrectly inferred change from a current load band. It is replaced by 「推定負荷：中程度」 at RAL 40–59. All five load captions describe the current estimate, with thresholds unchanged. They do not represent calibrated AI capacity or feelings.

| Source and supported claim | Application in this UI | Limit |
| --- | --- | --- |
| [Plass et al., Emotional Design for Digital Games for Learning (2019 online), abstract](https://files.eric.ed.gov/fulltext/ED599078.pdf): expression and dimensionality had the strongest effects on the affective quality of game characters, color a medium effect. | Keep facial features as a deliberate signal; loaded uses a neutral mouth with concentrated brows instead of a smile paired with an increase statement. | The specific face-to-load mapping is our design inference. This study does not validate workload recognition or RAL. |
| [Matthews et al., A Toolkit for Managing User Attention in Peripheral Displays, pp. 2–3](https://www.madpickle.net/scott/pubs/p321-matthews.pdf): distinguish abstraction, notification levels, and display transitions; interruption is reserved for important information. | Separate the current load label, observed rapid-rise notice, and stale/direction notices. Keep detail behind the Pet button; no forced popup. | This is transfer from peripheral-display research, not a demonstrated reduction in this application's attention cost. |
| [Xbox Accessibility Guideline 103](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/103): supplement color with other signifiers and text alternatives. | Retain short visible labels alongside faces/colors; include notices in the button's accessible name. | Industry guidance, not an experiment. Screen-reader usability and full XAG compliance are unverified. |
| [Xbox Accessibility Guideline 117](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/117): avoid or allow disabling repetitive incidental motion. | Remove continuous breathing animation; state changes remain static. | This applies the motion recommendation only; update-frequency controls and complete guideline compliance are not claimed. |

Current-load labels: 0–39 低め; 40–59 中程度; 60–74 高め; 75–89 高い; 90–100 非常に高い. Empty partial input stays 未判定. Direction alerts do not replace the numerical load label; stale observations have a separate timestamp notice. Unknown trajectory does not imply low or high load. Constant values never produce an increase caption.

Unverified: whether users correctly distinguish all five faces, whether the display reduces interruptions, false-alert rates, and empirical validity of the RAL thresholds. Proposed evaluation: compare caption-only and face-plus-caption variants, measure identification accuracy/latency and interruption cost under a primary task, explicitly testing constant-load, rapid-rise, stale, and unknown-trajectory cases. No adoption or empirical acceptance is inferred from implementing these changes.

## 2026-09-26: Model-relative headroom

The primary Pet state is now a **model-relative headroom estimate**, not task load alone. Task complexity remains the RAL shown in details. The selected model and reasoning depth define a transparent provisional capacity profile; headroom is `capacity - RAL`.

| Profile | Base capacity | Reasoning adjustment |
| --- | ---: | ---: |
| Astra | 95 | light -15; standard 0; deep +10 |
| Sol | 75 | light -15; standard 0; deep +10 |
| Luna | 55 | light -15; standard 0; deep +10 |

The five expressions are driven by headroom: `>=20` 余裕あり, `>=5` 進められる, `>=-10` 注意が必要, `>=-25` より強いモデルを検討, and lower values 余力が足りない. The user selects the model and reasoning depth in details. The local Web UI does not receive Codex's currently selected model, so it deliberately starts as モデルを選ぶ rather than assuming a profile. The choice is stored only in the browser.

This calibration is a UI hypothesis, not a measurement of internal model capacity, context-window headroom, likely correctness, or remaining account usage. The official model guide supports that model and reasoning selection affect the intended task fit and that higher reasoning effort can improve complex-task results at a time/token cost; it does not supply these numeric capacities. Evaluation remains needed against real task outcomes and model switches.


### Plain-language UI correction
Replaced 方向の安定性 with 依頼との食い違い. The primary display shows 確認できず when evidence is absent, 記録あり when non-validated observations exist, and 記録なし otherwise; 記録なし does not guarantee correctness. The original trajectoryStability number remains in technical details with its original identifier, avoiding inversion of the metric. Localized action names and changed RAL to 負荷の目安 in the primary display. JavaScript syntax and live keyboard/browser rendering verified. Comprehension remains unverified.


### Default face-only mode
User requested expression-only as default. Initial HTML hides workspace and details before JavaScript loads; captions, notices and error text are visible only in details mode. Clicking or keyboard-activating the Pet toggles details and the file import workspace. Close, Escape and 表情だけに戻る return to face-only. No persistent mode preference: reload always starts face-only. Existing evaluation and stored data are unchanged.


### Load-specific motion revision
User found static faces unintuitive and requested motion. Supersedes the earlier removal of continuous animation: stable uses slow buoyancy; loaded uses focused eyes and a slow head movement; strained uses a compressed pose, worried mouth and sweat; high pressure uses a faster small restless movement; unstable uses half-closed eyes and a slumped heavy breath, replacing X eyes. Motion does not signify actual inference activity or model emotion. Face-only remains default. A saved details checkbox can disable animation; OS reduced-motion remains respected. Static poses preserve differences without movement. These specific mappings are design hypotheses, not research-validated comprehension results.


### Moderate-load expression correction
User reported that the current face does not look comfortable. Replaced moderate-load narrowed eyes/angled eyebrows/flat mouth with open eyes and a gentle smile; removed head tilting and used a slow small vertical movement. Strained expressions remain reserved for higher load. RAL and thresholds unchanged. Previous focused-face mapping is superseded; comprehension still requires user acceptance.
