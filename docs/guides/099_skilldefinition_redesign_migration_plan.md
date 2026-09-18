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
SkillDefinitionに残す。

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

bulk conversion開始には、代表的な複雑Skillの観測、管理adoption経路のlive検証、
v1 maturity/promotion schema、人によるactive source切替判断が必要である。
