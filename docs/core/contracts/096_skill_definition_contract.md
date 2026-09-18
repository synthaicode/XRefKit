<!-- xid: E6A19D4B72C3 -->
<a id="xid-E6A19D4B72C3"></a>

# SkillDefinition v1 と派生catalog

この契約は、実装済みのSkillDefinition parserとcatalog生成器が受理する候補形式を定める。
既存のMCP `get_skill`、package discoveryはまだこの形式へ切り替えていない。
構造検証の成功を、Skillの実行可能化・品質受入れ・移行完了とみなさない。

## 編集正本と責務

Skillの編集正本は一つのMarkdownファイルとし、YAML headerに発見・適用・入出力・
必要材料・確認条件を置き、headerの後に方法本文を置く。JSON形式のheaderもYAMLの
部分集合として利用できる。catalogは正本から生成し、手編集する第二のmeta正本にしない。

`capability` / `tuning` / `responsibility`、model名やmodel tierはheaderに置かず、
今回の指示に基づくroutingと
[ExecutionBinding](../../guides/095_subagent_startup_read.md#xid-D7A4C9E2B861)で扱う。
共通のWorkflow、guard、unknown、検査分離、エスカレーションをSkillごとに再定義しない。
Skill固有の適用外条件・方法・停止条件・handoffは本文に残す。

## 物理形式

```text
---
<YAML mapping または JSON object>
---
<XID comment / anchor と Markdown method>
```

UTF-8（file先頭のBOMは可）。先頭とheader末尾は単独行の`---`と改行が必要。
methodの改行や末尾を正規化せず保持する。fileの`content_hash`はBOMと改行を含む
raw bytesのSHA-256で、版が変われば再生成する。parser APIへ文字列を渡す場合は
その文字列のUTF-8 bytesをhash対象とする。

headerの必須項目:

| key | 内容 |
|---|---|
| `schema_version` | 整数`1` |
| `skill_id` | 小文字で始まる英小文字・数字・underscoreの識別子 |
| `xid` | 自身の12桁uppercase hexadecimal XID。method内のcomment/anchorと一致 |
| `summary` | 発見時の短い目的説明。詳細Purposeはmethodに保持 |
| `applies_when` | 適用する状況の文字列配列 |
| `exclusions` | 適用外の文字列配列。空配列も可 |
| `inputs` / `outputs` | 入出力要求の文字列配列 |
| `criteria` | 下記の確認条件。1件以上 |
| `knowledge_needs` | 下記のKnowledge検索要求。空配列も可 |
| `control_refs` | 適用する既存制御契約のXID配列。1件以上 |

任意項目は`aliases`のみ。旧metaなどのXIDを同じSkillへ対応付けるための配列であり、
自身のXIDや重複を含めない。これは生成catalog内の対応で、既存XID resolverへの
登録や旧ファイルの削除を自動で行う機能ではない。

`criteria`の各要素は`id`、`statement`、`verification`の非空文字列を持つ。
ここでは再利用する確認条件を表現する。Task固有の基準・権限を確定したことや、
Criterion/Decisionの将来の全スキーマを実装したことを意味しない。

`knowledge_needs`の各要素は`id`、`query`、`required_when`の非空文字列と、
`seed_xids`配列を持つ。実行主体は必要な時点でcatalogを検索し、適用範囲を確認して
XIDで本文を解決する。seedは既知の入口を保持するもので、関連文書の再帰ロードや
Knowledge本文のheaderへの埋込みを許可しない。必須かどうかは`required_when`と
Skillの方法に従い、検索結果の存在だけで判断条件を満たしたとしない。

未定義key、重複mapping key、重複criterion/need ID、不正XID、YAML alias/anchorや
unsafe tagは拒否する。documentは512,000 bytes、headerは64,000 bytes、methodは
256,000 bytesまで。参照XIDの存在・権限・意味的適合は構造parserでは検証しない。

## CatalogとCLI

```powershell
python -m xrefkit skill definition-check --path <candidate-SKILL.md> --json
python -m xrefkit skill definition-catalog --path <candidate-A> --path <candidate-B> --json
```

catalogには検証済みheader、定義へのpath/hash、XID/alias対応を出す。method本文は
含めない。生成処理は定義fileを検査するが、Knowledge本文や参照先を取得しない。
指定file全件を検査し、Skill IDまたはXID/aliasが衝突すれば部分catalogを返さず拒否する。
最大2,048定義、skill_id順で出力し、同じpathとbytesなら入力順に依存しない。

APIは`load_skill_definition(path)`、`parse_skill_definition(text, source=...)`、
`build_definition_catalog(paths)`。CLIはJSONをstdoutへ返し、正本や既存catalogを
上書きしない。catalogの検索順位付けやmodel評価は含まない。

## 明示選択した定義の実行

```powershell
python -m xrefkit skill run `
  --definition skills/<skill>/SKILL.md `
  --task "<task>" `
  --capability "<instruction-derived capability>" `
  --tuning "<instruction-derived tuning>" `
  --responsibility "<delegated responsibility>" `
  --execution-mode subagent_required `
  --json
```

`--definition`と`--meta`は排他的である。定義形式にはrouting結果を保存せず、
`capability` / `tuning` / `responsibility` / `execution_mode`を実行開始時に必須入力として
run logへ固定する。run logの`maturity: definition_v1`は形式識別であり、`stable`への
品質昇格を表さない。`meta: -`とし、同じ`SKILL.md`を唯一の実行本文として参照する。

run logには定義のXID、root-relative path、raw bytesのSHA-256を記録する。
`workflow bind-execution`はこれらをrequestから受け取らずrun logから
`definition_identity`へ転記し、runtime三要素がrequestと一致することを確認する。
local subagent readerは本文を渡す直前とreceipt記録前にXIDとSHA-256を再検証する。
したがって、run開始後に定義が変更された場合は新しいrun/bindingが必要になる。

## MCPでの明示的な有効化

MCP serverでは、自動scanではなく起動時に対象を明示する。

```powershell
python -m xrefkit.mcp.server `
  --repo <repository> `
  --skill-definition skills/<skill>/SKILL.md
```

`XRefCatalog.build(..., skill_definition_paths=[...])`とcatalog CLIの
`--skill-definition`も同じ境界を使う。指定pathはrepository内のfileに限定し、
重複pathや定義間の`skill_id` / XID / alias衝突を拒否する。同じ`skill_id`の旧Skillが
存在する場合、明示指定した定義をactive catalog entryとし、旧entryとの二重routingを
行わない。指定しない候補はMCP catalogへ現れない。

catalog entryの`definition_format`は`skill_definition_v1`、旧meta+本文形式は
`legacy_split_v1`である。routing一覧にはheader由来metadataだけを載せ、method本文は
`get_skill`で選択後に一文書だけ返す。その文書はBOM・改行を含むraw UTF-8 bytesと
同じSHA-256を持つ。MCP subagent readerは`ExecutionBinding.definition_identity`の
path / XID / SHA-256とcatalog responseを照合してから本文を受け取り、receiptを記録する。
legacy entryは従来どおりmetaと本文の二文書を返す。

protocol選択、管理upload、旧`--meta`実行経路は変更しない。管理upload後の定義を
`--skill-definition`へ採用する操作と、package discoveryでの配布形式切替は別作業である。

## 代表変換と切替条件

```powershell
python -m tools.convert_dotnet_skill_definition --root .
```

代表変換は`skills/dotnet_change_analysis`を読み、
`work/skill-definition-candidate/dotnet_change_analysis/`に候補と`migration.json`を作る。
元の本文はbyte単位で保持し、9つのClosure Gate条件と5つのKnowledge要求をheaderへ
対応付ける。元metaの全項目・値・移行先をmanifestに記録し、動的実行項目は
`runtime_cutover_pending`、観測・昇格履歴などはprovenanceとして保持する。
編集済み候補の上書きは拒否する。

これは一つの正本へまとめる物理形式の実証であり、本文の共通制御を削除・統合する
意味的な簡易化はまだ行っていない。旧Skillの本文とmetaを現在の実行正本として残し、
候補を第二の有効Skillとして登録しない。後続の切替で必要なのは次の確認である。

- 固有の方法・観点・停止条件を保持したまま共通制御を参照へ統合する。
- Knowledgeと方法の所有関係を確認し、既存XIDと必須取得条件を保つ。
- 代表定義をactive catalogへ採用し、複雑Flowを検証する。
- source、catalog、package、管理upload、docsの対象版を揃える。

[Workflow Protocol](../../guides/088_instruction_workflow_protocol.md#xid-9F4C2A7D1B60)の
verify/closeと、人による出力品質・採用の判断は引き続き別である。
