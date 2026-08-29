<!-- xid: 88830262A85D -->
<a id="xid-88830262A85D"></a>

# AI Decision Trace Protocol Guide

このガイドは、AIが人間との共同作業で判断の変更、仮適用、評価、復帰、成果物の履歴を管理するための実行規約である。

`xrefkit trace`は人間向けの操作画面ではなく、AIがプロトコルを実行するための内部アダプターとして利用する。人間は自然言語または別のUIで判断を伝え、AIがこのガイドに従ってコマンドと記録へ変換する。

既存のSkill Run Observation Dashboardには、`Decision Trace`セクションとしてイベント、status、resolution、branch、理由、Mermaid依存グラフを表示する。Dashboardは観測専用であり、採用、却下、復帰、branch削除を実行しない。

## 基本原則

- 作業途中の判断、計画、調査、検証、成果物は、最終評価が完了するまで`provisional`とする。
- 過去のイベントや判断を直接書き換えない。
- 過去へ戻る場合は、現在地点をcheckpointしてから、過去のcommit/tagを基点に新しい仮説branchを作る。
- 採用、却下、再採用、修正は、元イベントの状態変更ではなく新しい`resolution`イベントで記録する。
- AIは影響候補と評価材料を提示するが、最終判断を作らない。
- AIが記録したイベントには`recorded_by: ai_protocol`を付与する。

## AI作業開始時の手順

AIの作業開始処理に次の手順を組み込む。

```text
1. 現在の目的とactive contextを確定する
2. `trace checkpoint`を自動実行する
3. 仮説変更を伴う場合はcheckpointからbranchを作成する
4. 作業・調査・検証を実行する
5. イベントと証拠を記録する
```

XRefKitの`skill run`と`workflow run`はこの開始処理を実装している。Git worktreeでは`CP-RUN-<run_id>`を自動作成し、run logにもcheckpointを記録する。Git管理外ではcheckpoint状態を`unavailable`として明示し、既存の汎用run log互換性を保つ。Git管理下で通常変更を安全にcheckpointできない場合はrunを開始しない。

checkpointは人間に実行させない。作業ツリーに通常の未commit変更がある場合は停止し、変更の扱いを人間へ確認する。ただし、`work/decision-trace`内の台帳変更だけはcheckpoint対象として許可する。

## 連続作業としてAIが進める範囲

次の作業は、既定の目的、対象範囲、データ境界、人間判断の境界を変更しない限り、AIが自分で順序を決めて連続実行してよい。

- AI作業開始フックへのcheckpoint接続
- `trace`コマンドの実装、テスト、エラー処理、冪等性改善
- 評価ポイント、resolution、return処理の記録機能
- contextのactive/current-only抽出
- `depends_on`、成果物差分、source commitの決定的な検証
- branch/worktreeの一覧、再開、廃棄処理
- Mermaidまたは同等形式の表示改善
- ガイド、テスト、検証ログの更新

AIは各作業単位の開始前にcheckpointを作り、変更を`provisional`として進める。実装上の選択に複数案がある場合は、目的・既存契約・テスト可能性・可逆性を根拠に選び、判断イベントへ記録する。選択がプロトコルの目的や権限を変更する場合は停止する。

## AIが停止する判断点

次の場合は連続作業を止め、人間の判断を求める。

- 目的、スコープ、権限、責任の解釈が複数に分かれる
- 過去の判断へ戻る対象やcommitが特定できない
- 影響候補に重大な`unknown`が残る
- 採用、却下、再採用、最終評価を確定する必要がある
- 外部環境や他者のデータを変更する許可が必要になる
- 通常の未commit変更を巻き込む可能性がある
- 既定のプロトコル契約を変更する必要がある

停止時は、AIは作業を完了したとは報告せず、確認した事実、未確定事項、選択肢、必要な人間判断を提示する。

## イベントの記録

判断変更は次のように記録する。

```powershell
xrefkit trace event `
  --event-id DEC-002 `
  --event-type decision-change `
  --from-decision "X" `
  --to-decision "Y" `
  --reason "new verification evidence" `
  --evidence VER-008 `
  --branch hypothesis/decision-Y `
  --base-ref checkpoint/CP-001 `
  --json
```

AIはイベントを`work/decision-trace/events.jsonl`へ追記する。人間向けの説明には、コマンド出力をそのまま提示せず、目的、事実、根拠、影響候補、unknown、次の判断点を要約する。

別リポジトリの成果物と関係する場合は、次を記録する。

```text
source_repo
source_commit
source_path
```

AIはsource参照を記録した後、別リポジトリの実体を機械検証する。

```powershell
xrefkit trace source-check `
  --event-id SRC-001 `
  --source-root ..\source-repository `
  --json
```

commitまたはpathが存在しない場合は、参照を有効と扱わず停止する。

AIは次の作業へ進む前に、台帳の整合性も確認する。

```powershell
xrefkit trace validate --json
```

`valid: false`の場合は、未知の依存、resolution対象不在、循環依存などを修正または人間へ確認するまで継続しない。

仮適用後の全体評価点は、AIが条件と証拠を構造化して登録する。

```powershell
xrefkit trace evaluation-point `
  --event-id EVP-001 `
  --target-event-id DEC-002 `
  --criteria "performance under threshold" `
  --criteria "source diff is traceable" `
  --evidence VER-008 `
  --reason "whole evaluation after provisional application" `
  --json
```

評価点自体も最終resolutionまでは`provisional`であり、条件を満たしたことや判断の採用を自動確定しない。

## AI contextの構築

AIが次の作業へ進む前に、対象イベントをrootにして現在の依存系列だけをcontextへ渡す。

```powershell
xrefkit trace context `
  --event-id EVAL-004 `
  --json
```

`current-only` contextにはrootイベントとその`depends_on`の祖先だけを含める。別の仮説系列、却下済みの系列、rootから到達できない古いイベントは`excluded_event_ids`として分離し、通常のAI判断材料へ混ぜない。依存関係に循環がある場合は実行を停止する。

## 影響範囲の確認

判断変更後は、採用や却下を決める前に影響候補を抽出する。

```powershell
xrefkit trace impact --event-id DEC-002 --json
```

出力は次のグループを使う。

```text
decision
plan
investigation_verification
provisional
evaluation
artifact
source
unknown
```

`direct`は直接依存、`transitive`は間接依存である。AI推定や未確認事項は確定影響として扱わず、`review_required: true`または`unknown`として人間へ提示する。

## 人間判断の受領

人間の指示が採用・却下・再採用を含む場合、AIは対象イベント、評価イベント、理由を特定する。対象が曖昧、評価根拠が不足、影響範囲が確認できない場合は実行せず、確認を求める。

最終評価結果は新しいイベントとして記録する。

```powershell
xrefkit trace resolve `
  --event-id RES-001 `
  --target-event-id DEC-002 `
  --evaluation-event-id EVAL-004 `
  --resolution rejected `
  --reason "performance condition was not met" `
  --json
```

元のイベントは`provisional`のまま保存し、`resolution`イベントで最終結果を表す。

```text
adopted       変更案を採用
rejected      変更案を却下
re-adopted    過去の判断を再採用
revised       修正版を新しい仮説として継続
```

## 過去へ戻る場合

人間の「DEC-001の時点に戻って再検討する」という指示を受けた場合、AIは先に確認だけを行う。

```powershell
xrefkit trace return-check `
  --target-event-id DEC-001 `
  --to-ref checkpoint/CP-001 `
  --json
```

人間に次を提示する。

- 戻り先のイベントとcommit
- 現在地点との差分
- 失われるのではなく保持される現在checkpoint
- 影響候補
- 復帰後に作成するbranch

人間の明示的な実行許可を受けた後だけ、AIは次を実行する。

```powershell
xrefkit trace return-execute `
  --event-id RET-001 `
  --target-event-id DEC-001 `
  --to-ref checkpoint/CP-001 `
  --branch hypothesis/resume-DEC-001 `
  --checkpoint-id CP-RETURN-001 `
  --reason "reconsider historical decision" `
  --confirmed `
  --json
```

復帰後のbranch、判断、成果物、評価はすべて`provisional`である。復帰はGitのresetによる履歴消去ではない。

複数の仮説を並列評価する場合は、AIがbranchごとの隔離worktreeを作成する。

```powershell
xrefkit trace worktree `
  --path ..\worktree-decision-Y `
  --branch hypothesis/decision-Y `
  --from-ref checkpoint/CP-001 `
  --purpose "parallel hypothesis evaluation" `
  --json
```

worktreeの作成は並列作業場所の準備だけであり、採用・merge・廃棄の確定ではない。

## 仮説branchの廃棄

採用しなかった仮説branchは、ADRを残したうえで廃棄する。

```powershell
xrefkit trace branch-delete `
  --branch hypothesis/decision-Y `
  --event-id ADR-002 `
  --reason "evaluation failed" `
  --force `
  --json
```

この処理は、廃棄要求を先に記録し、削除成功後に完了イベントを追記する。branch名、最終commit、評価理由、廃棄事実は台帳に残る。

## 実行してはいけないこと

- 人間の明示的な許可なしに`return-execute`を実行しない。
- 元イベントを書き換えて、過去の判断をなかったことにしない。
- 影響候補を影響確定として報告しない。
- `unknown`を推測で埋めない。
- 作業ツリーの通常の未commit変更をcheckpointへ黙って含めない。
- branchの採用・merge・削除を、評価結果だけからAIが自動確定しない。
- AIの内部推論を保存したものとしてイベントを説明しない。

## AIの報告形式

各操作後の人間向け報告は、次の順でまとめる。

```text
結論
現在の状態
確認した事実
使用した証拠
影響候補
unknown / 未確認事項
人間に求める判断
次の操作
```

判断が不要な記録・検証・表示はAIが継続する。採用、却下、再採用、復帰実行、標準化は人間の判断点として停止する。
