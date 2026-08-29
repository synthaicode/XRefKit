<!-- xid: 22164A51A745 -->
<a id="xid-22164A51A745"></a>

# AI Decision Trace Protocol

## 目的

AIと人間が共同で成果物を作るとき、判断の変更、仮適用、差し戻し、再評価を
追跡可能にするための、XRefKit標準プロトコルである。

本プロトコルはADRを置き換えない。ADRが担う「判断と理由の記録」を、AIの
作業中に発生する判断イベント、Gitの復元地点、影響範囲、評価イベントと
接続する実行層として扱う。

## 標準採用範囲

- `skill run` と `workflow run` の開始時に、AIが自動checkpointを作成する。
- 作業中の判断、調査、検証、計画、成果物は、人間が確定するまで
  `provisional` とする。
- 過去の判断は直接変更せず、新しい判断変更イベントとして記録する。
- 過去へ戻るときは、現在地点を保存し、対象地点、変更内容、理由を確認する。
- AIは判断変更の影響候補を示すが、変更の採用、却下、再採用、復帰実行は
  人間の判断を経てから実行する。
- 仮説の並列作業はGit branch/worktreeで分離し、採用しなかった仮説は
  実体を削除しても、その判断イベントと理由を残す。
- ソース成果物が別リポジトリにある場合は、source repository、commit、path
  をイベントまたは成果物記録から参照できるようにする。
- 現在有効な判断だけを後続AIのコンテキストに渡し、却下・旧版の判断を
  現在の前提として混入させない。

## 既存プロトコルとの関係

本プロトコルは、既存のWorkflow Protocolの作業開始・実行・検証・handoff・
closureを置き換えず、判断の時間的変化を記録する横断的な実行層として追加する。

```text
Goal / Workflow Protocol
  -> Skill または instruction-backed run
    -> AI Decision Trace
       checkpoint / provisional work / impact / return / evaluation
    -> verify / quality review / human evaluation / closure
  -> 成果物と現在有効な判断
```

既存の人間評価契約は、run単位の評価と次の扱いを定義する。本プロトコルは
その下位イベントとして判断の変更と影響候補を記録する。`skill verify`、
`skill close`、品質評価、人間の責任を代替しない。

## ADRとの関係

XRefKitでは、新しいADRファイルを追加せず、文書更新方針に従ってGit履歴、
`work/`の実行記録、判断記録を利用する。外部リポジトリなどでADRを採用する
場合は、MADR等の既存形式を最終判断の記録形式として利用できる。

したがって、ADRは最終的な判断記録、本プロトコルはその判断に至るAI協働作業の
可逆性・追跡性・評価境界を担う。

## 実行インターフェース

AIは人間の自然言語による指示を、`xrefkit trace` のイベントへ変換する。
`xrefkit trace` は人間向け操作画面ではなく、プロトコル実行用の内部アダプター
である。観測は既存DashboardのDecision Traceで行う。

詳細なイベント形式、停止条件、影響表示粒度、復帰手順は
[AI Decision Trace Protocol Guide](../../guides/092_ai_decision_trace_protocol_for_ai.md#xid-88830262A85D)
を正本とする。

## 採用状態

この契約の追加以後、AIがXRefKitで実行するSkill Runおよびinstruction-backed
workflow runでは、本プロトコルを標準として適用する。プロトコル自体の目的、
権限、停止条件を変更する場合は、人間の判断対象として停止し、別途評価する。
