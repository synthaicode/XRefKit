<!-- xid: C8E4B6F20D31 -->
<a id="xid-C8E4B6F20D31"></a>

# SkillDefinition redesign migration plan

この計画は、legacy split Skillからone-document SkillDefinitionへ段階移行する。
互換性の維持より新しい概念モデルの一貫性を優先するが、切替前のactive sourceと
既存MCP transportを暗黙に置換しない。

## Target model

| Concern | Canonical owner |
| --- | --- |
| method, applies_when, I/O, Skill固有criteria/stop/handoff | one-document SkillDefinition |
| capability, tuning, responsibility, execution_mode | instruction-derived runtime routing and ExecutionBinding |
| facts, rules, evidence basis | Knowledge catalog; XID resolution on demand |
| phases, roles, logging, unknown/risk, common escalation, closure | Workflow Protocol |
| package delivery | `xrefkit.skill_packages` plus manifest path |
| upload candidate delivery | existing management transport; staging outside active catalog |
| quality and production adoption | human review and explicit adoption record |

Workflow Protocolは継続する。Skill本文から削るのは共通制御の重複であり、実行時の
worklist、check separation、unknown/risk、escalation、closure、handoffを削ることではない。
共通escalationはWorkflow Protocolが所有し、Skill固有の停止・適用外・専門判断の移譲条件だけを
SkillDefinitionに残す。初期化で供給されるWorkflow、Reporting、Logging、Context Guardは
`control_refs`にも重複記載せず、Skill固有の追加制御がない場合は空配列とする。

## Migration order

1. **Runtime read boundary** — run logからdefinition path/XID/hashとruntime routing fieldsを
   ExecutionBindingへ固定し、subagent開始時にexact documentを読む。
2. **Catalog and Knowledge** — routing一覧をheader由来metadataへ限定し、選択後にmethodを渡す。
   `knowledge_needs`のactive IDを親が判断し、候補本文をXIDで必要時解決する。
3. **Representative complex Flow** — 固有methodを保持したまま共通controlを削り、parent routing、
   subagent execution、check、escalation、handoffを一つのrun chainで確認する。
4. **Distribution** — package manifestがone-document pathを指せるようにし、raw hashを保持する。
   legacy YAML packageは移行対象として形式を明示する。
5. **Management adoption** — upload、validation、staging、seal/review、adoptionを別状態にする。
   このcheckoutに実装がない場合は、所有serviceへhandoffしてlive検証する。
6. **Docs and bulk conversion** — canonical docsを新モデルへ揃え、代表runの観測後に変換単位を決める。
   最後にlegacy meta validatorとsplit sourceを廃止する。

ここでいうbulk conversionは、tracked v1をlegacyと並べて追加するdefinition migrationと、
productionの既定sourceを切り替えるadoptionを分ける。前者は検証済みの変換単位ごとに進められる。
後者とlegacy削除はmanagement adoption、人の受入れ、利用時の観測が揃うまで行わない。

## Current definition migration status

| Skill | tracked v1 | coverage | active-source boundary |
| --- | --- | --- | --- |
| `dotnet_change_analysis` | [9883EF4E8CA9](../../skills/dotnet_change_analysis/SKILL.v1.md#xid-9883EF4E8CA9) | complex analysis method、Knowledge、Skill固有handoff | explicit `--definition`; legacy kept |
| `code_constraint_derivation` | [7C4E9A1B2D60](../../skills/packs/constraint-derivation/code_constraint_derivation/SKILL.v1.md#xid-7C4E9A1B2D60) | Knowledge selection、unsupported business meaning stop | explicit `--definition`; legacy kept |
| constraint-derivation family | [A4C9E2B7D160](../../skills/packs/constraint-derivation/constraint_derivation_index/SKILL.v1.md#xid-A4C9E2B7D160) | 11/11 Skills、family routing、domain-specific stop conditions | explicit `--definition`; legacy kept |
| `security_review` | [7C4E9A2D1F60](../../skills/security_review/SKILL.v1.md#xid-7C4E9A2D1F60) | evidence、security viewpoints、unknown、handoff | explicit `--definition`; legacy kept |
| `editorial_intake` | [7C4E9A2D6F81](../../skills/packs/editorial-ops/editorial_intake/SKILL.v1.md#xid-7C4E9A2D6F81) | context boundary、reader capability、publication stop | explicit `--definition`; legacy kept |
| editorial-ops family | [C8E1A6D3B270](../../skills/packs/editorial-ops/editorial_ops_index/SKILL.v1.md#xid-C8E1A6D3B270) | 6/6 Skills、evidence review、reader review、human publication authority | explicit `--definition`; legacy kept |
| simple top-level batch | [D4A7C91E2B60](../../skills/requirements_flow/SKILL.v1.md#xid-D4A7C91E2B60) | 8/8 Skills、review/planning/traceability、human decision boundaries | explicit `--definition`; legacy kept |
| artifact and short OS batch | [D5A8C1E6B740](../../skills/import_skill/SKILL.v1.md#xid-D5A8C1E6B740) | 8/8 Skills、artifact verification、judgment and promotion boundaries | explicit `--definition`; legacy kept |
| medium OS batch | [F8A2C6D1B370](../../skills/os/knowledge_ontology_management/SKILL.v1.md#xid-F8A2C6D1B370) | 5/5 Skills、goal continuity、migration、research、canonical publication boundaries | explicit `--definition`; legacy kept |
| implementation and review batch | [D7B4E9A2C610](../../skills/implementation_flow/SKILL.v1.md#xid-D7B4E9A2C610) | 7/7 Skills、bounded implementation/test、language review、QA gate、report composition boundaries | explicit `--definition`; legacy kept |
| design planning and business-intake batch | [6A4F8C2D1E70](../../skills/design_flow/SKILL.v1.md#xid-6A4F8C2D1E70) | 6/6 Skills、planning/design approval、goal-first learning、provisional scoping、evidence-bound conversation analysis | explicit `--definition`; legacy kept |
| final brownfield DB catalog batch | [E1A7C4D9B260](../../skills/brownfield-workflow/SKILL.v1.md#xid-E1A7C4D9B260) | 9/9 Skills、source/DB evidence、safe deterministic regression、catalog publication、Skill/Flow authoring boundaries | explicit `--definition`; legacy kept |

各tracked v1は新しいown XIDを持ち、旧本文XIDと旧meta XIDを`aliases`に保持する。
外部governance recordがないため、明示実行時のmaturityは`unassessed`である。

## Low-level model work packets

Lunaなどのlow-level modelへ渡すwork itemは、一つの判断境界と決定的な完了条件に限定する。

- 読むXID、対象path、変更可能fileを列挙する。
- runtime fieldをSkillDefinitionへ書き戻さないなど、禁止事項を一文で示す。
- outputをparser、catalog projection、test、doc sectionなど一種類にする。
- exact commandと期待結果をcompletion criterionにする。
- transport変更、production adoption、複数契約の意味変更は親へ返す。

親AIは要件、routing、work item分割、統合、full verificationを所有する。subagentは割り当てられた
作業を実行し、採用判断や仕事全体の責任を引き受けない。

## Gates

各段階はWorkflow Protocolの`verify`と`close`を通す。加えて次を満たす。

- parser/catalog/runtime間でdefinition XIDとraw bytes SHA-256が一致する。
- Knowledge activation未評価を不要扱いせず、`unresolved`として保持する。
- legacyとv1の形式がcatalogで判別でき、同じactive Skillを二重routingしない。
- reader/admin protocol selectionとmanagement upload transportを回帰させない。
- human adoption前のcandidateをproduction active sourceとして扱わない。
- docsのXID checkと関連testが通る。

production既定sourceの一括切替には、代表的な複雑Skillの利用観測、管理adoption経路のlive検証、
外部v1 maturity/promotion recordの運用観測、人によるactive source切替判断が必要である。
それまではtracked v1の追加と明示実行による検証を続け、legacy経路を削除しない。
