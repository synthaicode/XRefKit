<!-- xid: 40886C8A5D1A -->
<a id="xid-40886C8A5D1A"></a>

# Attention Pet

選択モデルが仮の必要能力を満たすかと、より低い推論コストの適合候補があるかを分けて示すローカル実験版です。
利用者がモデル配分を判断するための参考情報として、Model Fit・Cost Fit・入力範囲・未評価の確からしさを別々に表示します。
Codex内で起動した場合、このチャットのローカル記録から新しい利用者発言と実行設定（モデル名・考える深さ）を読み取り、Petを自動更新します。新しい発言を受け取ると短く動き、表情は評価結果に従います。能力・挙動・コストは未校正の仮説値で、AI内部のAttentionや残り能力の測定、自動モデル切替は行いません。

## Codex限定プレビュー

現時点で利用者がそのまま起動できる自動連動機能はCodex限定です。Attention Petは、起動したCodexチャットのローカル記録から確認できる作業内容と実行設定を読み取り、「このモデルで進める余力」と低コスト比較候補をPetの表情と短い文で示します。表示は観測と試算であり、Codexのモデル、考える深さ、チャット内容を変更しません。

1. 対象チャットのCodexターミナルで、このリポジトリのルートを開きます。
2. 次のコマンドを実行します。

   ```powershell
   python -m xrefkit.attention_pet serve --port 8769
   ```

3. 表示された `http://127.0.0.1:8769/` をCodexのブラウザパネルで開きます。
4. 終了するときは、起動したターミナルでCtrl+Cを押します。

Petは起動時のチャットに固定されます。Codexで別のチャットを選んでも自動では切り替わらないため、別チャットを観測する場合は、そのチャットのターミナルから改めて起動します。画面のモデルと深さの選択は試算の比較だけに使い、Codex本体の設定は切り替えません。

provider-neutralなclient-state連携は別の統合経路です。現時点ではCodexやVS Codeの画面選択を検知するクライアントアダプターを同梱していません。

## 起動

このworktreeのルートで実行します。既存のPython環境（Python >= 3.11 / Pydantic 2）を使います。

```powershell
python -m xrefkit.attention_pet serve --port 8769
```

正式なクライアント連携では、JSONLを直接読まずclient-stateモードを使います。

```powershell
xrefkit attention-pet serve --client --port 8769
```

このモードは最初の標準出力にendpoint、protocol version、instance ID、書き込みtokenを1行JSONで返します。クライアントは認証付きhandshakeで通信相手を確認してから、アクティブセッションの完全な構造化スナップショットを送ります。契約は[クライアントプロトコル](CLIENT_PROTOCOL.md)を参照してください。

起動元の `CODEX_THREAD_ID` がある場合のJSONL読み取りは、従来の実験的フォールバックです。そのチャットのローカル記録に固定され、別チャットへの画面切替には追従しません。Codex側で記録形式が変わると更新できなくなる可能性があります。正式なクライアントアダプターは `--client` を起動し、セッション切替をloopback APIへ明示通知します。

表示された `http://127.0.0.1:8769/` をCodexのブラウザパネルで開きます。画面の表示に認証は不要です。
表示言語はブラウザーの優先言語に従います。日本語を優先している環境では日本語、それ以外では英語を表示します。評価APIにも同じ `lang=ja|en` を送り、見出し、理由、次の行動を同じ言語に揃えます。
画面にはモデルとコストの配分カードとPetを常時表示します。一部の作業だけを評価している場合は、その範囲もPetの横に表示します。
カードには能力・コスト・入力範囲・確からしさを表示します。チャット連動時はCodexの実行記録を試算条件の初期値にします。プルダウンで別のモデルや深さを比較できますが、Codex本体の実行設定は変更しません。
「数値・候補・評価理由を見る」を開くと、RALや必要能力3軸、候補、推論コスト指数と理由を確認できます。
低コスト比較候補があればPetの横に「低コスト比較候補: Luna」のように表示します。詳細では、同じ考える深さで仮の必要能力3軸を満たす候補のうち、相対推論コスト指数が最も低いモデルを示します。実品質や総コストの優位性を示す案内ではありません。
候補がない場合はその旨を表示します。能力不足や結果記録の確認が必要な場合は、低コスト候補の案内を保留します。
チャット連動時は記録中のモデル識別子の系列と考える深さを実験プロファイルへ対応付けます。未対応の識別子では能力を未判定にします。モデル世代ごとの実能力や実品質、総コストの優位性は未確認です。
TerraはLunaとSolの間に置いた仮の比較候補です。現行の表示順や係数は実モデルの性能順位を示しません。
停止は起動したターミナルでCtrl+Cです。

見出し・補足・Petの短文・次の行動はPythonのPresentationMapperから一括生成します。
Partialなら「現在確認できている範囲では」、確からしさUnknown/Lowなら「現在の入力範囲では」を見出しに添えます。
CostFit=NoLowerCostCandidateの表示は「低コスト適合候補なし / No lower-cost candidate」です。登録済み候補・現在の仮定だけの比較です。
同じ `--session` の記録は再起動後も読み込まれます。チャット連動時はチャットID別のファイルを使います。別作業は別のport/sessionを指定してください。
新規セッションは観測なしです。モデル未選択・作業内容なしでは判定しません。

## 評価の見方

| 評価 | 状態 |
|---|---|
| Model Fit（能力適合のみ） | Unknown / Underpowered / Sufficient |
| Cost Fit（推論コストの仮比較と結果記録） | Unknown / RetryRisk / NoLowerCostCandidate / LowerCostCandidateAvailable / ReviewNeeded |
| Pet State（表示専用） | Unknown / Strained / Balanced / Relaxed / Review |

必要能力3軸を満たせば、他候補の価格に関わらずSufficientです。
同じ深さで低い推論コストの適合候補があれば、Cost FitにLowerCostCandidateAvailableを表示し、候補名と指数を示します。
Relaxedの表情は「低コスト候補を比較できます」という意味です。能力が過剰だという判定ではありません。
現文脈に失敗・修正の記録がある場合はReviewNeeded / Reviewを優先し、Model Fitとは分けます。

Base RAL、仮の作業展開量、Effective RAL、必要能力3軸、RALの全6要素は維持しています。
入力範囲Coverageと評価の確からしさConfidenceを独立表示し、今回はConfidenceをUnknownとします。
Balancedは低コスト比較候補が確認されなかった表示、Relaxedは候補がある表示です。どちらも実際の品質や総コストを示しません。
実際の推論・再試行・修正・失敗損失・総コストはnull。仮の推論指数が低くても、総コストが低いとは判断しません。
式・APIフィールド・シナリオ表・未検証事項は [仕組みの説明](MECHANISM.md) を参照してください。

## API入力（技術向け）

ブラウザー画面からのファイル入力や作業整理操作は提供しません。技術検証で構造注釈を入力する場合は、手動モードのHTTP APIを使います。チャット連動時は更新APIも読み取り専用になります。
`examples/conversation.json`はturn別の構造注釈例です。
`schema/working-set.schema.json`, `schema/conversation.schema.json`が機械検証用の入力契約です。
`schema/fit.schema.json`はAPI応答の `fit` の契約です。入力契約と既存セッション形式は維持しています。
Itemsの `source`、dependenciesの `evidence`、observationsの `evidence/context` を必ず残してください。
時刻はUTC epoch秒。更新時に増加させ、IDを安定させます。範囲の確認が済んでいなければ `coverage=partial` のままにしてください。

CLI単独でも評価できます。

```powershell
python -m xrefkit.attention_pet evaluate projects/attention-pet/examples/working-set.json
python -m xrefkit.attention_pet evaluate projects/attention-pet/examples/working-set.json --model sol --reasoning standard
python -m xrefkit.attention_pet evaluate projects/attention-pet/examples/conversation.json --conversation
```

HTTP API:

| Method / Path | 入出力 |
|---|---|
| GET `/api/state` | 現在のWorking Set、Attention State、直近100履歴、回復記録、FitEvaluation |
| GET `/api/client/handshake` | クライアントがservice、protocol、instance、capabilityを確認 |
| POST `/api/active-session` | クライアントがアクティブセッションと完全なWorkingSetを通知 |
| POST `/api/snapshot` | WorkingSet JSONを評価・保存 |
| POST `/api/conversation` | 注釈付きConversationを抽出・評価・保存 |
| POST `/api/recover` | `action`, `expectedObservedAt`。古い画面操作を拒否 |

GET `/api/state` は認証なしで利用できます。client handshakeとPOSTには起動時に別途渡される `Authorization: Bearer <token>` が必要で、POSTには `Content-Type: application/json` も必要です。
各APIに `?model=luna&reasoning=standard` などを付けると、応答の `fit` にその比較条件の評価が入ります。チャット連動時、モデル指定がなければ記録中のモデル・深さを初期値にし、指定があれば読み取り専用の比較として使います。応答の `source` には実際の連動状態が入り、比較条件を変えてもCodex本体は変更しません。
`lang=ja|en` は評価文の表示言語だけを変更し、判定値や作業内容は変更しません。
モデルは `luna|terra|sol|astra`、深さは `light|standard|high`。モデル省略時は `Unknown`、深さの既定値は `standard`。Terraを含むプロファイルと相対推論コストは未校正の実験値です。
未知値・重複パラメータは更新前に拒否します。GETでの比較は作業内容と履歴を変更しません。
CLIは `--model` 指定時に `{state, fit}` を返し、省略時の既存出力を維持します。
外部Originは拒否します。上限2MB、Item500件、edge2000件、観測500件です。
独立入力アダプターからこのAPIを呼べます。初期版はMCPの登録やCodex設定変更を行いません。

```powershell
$petHeaders = @{ Authorization = 'Bearer <手動モード起動時のtoken>' }
$petBody = Get-Content projects/attention-pet/examples/working-set.json -Raw
Invoke-RestMethod http://127.0.0.1:8769/api/snapshot -Method Post -Headers $petHeaders -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($petBody))
```

## 回復の意味

Summarize/Archiveは参照されなくなった履歴や完了項目を退避します。有効な制約と根拠を消してスコアを下げません。
Fixは判断の固定、Externalizeは保存。Split/Resolve/Rebase/Restartは引継ぎファイルを作成します。
Restartボタン自体がCodexの新チャットを作るわけではありません。新文脈で確認できた結果を入力するとTrajectoryが再評価されます。

## 検証

```powershell
python -m pytest tests/test_attention_pet.py tests/test_attention_pet_fit.py tests/test_decision_trace.py -q
node --check xrefkit/resources/attention_pet/pet.js
```

[設計・拡張点調査・式・限界](../../docs/designs/100_attention_pet.md#xid-38C97BA1E4D2)と、[検証結果](VALIDATION.md)を参照してください。
評価器は `xrefkit/attention_pet/evaluator.py`、表示は `xrefkit/resources/attention_pet/` に分離しています。
重みを変更する場合は合計100のJSONを `serve/evaluate --weights <path>` に渡します。
推定値の妥当性と、人にとって表情が理解しやすいかは別の検証です。
