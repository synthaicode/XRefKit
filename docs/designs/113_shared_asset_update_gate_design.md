<!-- xid: A93D741E6BC2 -->
<a id="xid-A93D741E6BC2"></a>

# Shared Asset Update Gate Design

Status: **review-ready proposal**, dated 2026-10-10. This document proposes a
common management check; it does not adopt a rule, implement a gate, or change
Skill, Knowledge, Flow, QA, or publication authority.

## Purpose and Agreed Boundary

Skill and Knowledge updates have specialized authoring responsibilities. A
single shared gate would check their common management obligations instead of
copying those checks into each consuming Skill. The initial rule distinguishes
an external reference retained as a fixed evidential basis from a reference
intended to supply current information. It does not repeatedly ask humans to
approve an already trusted site.

The existing sequence remains: QA checks requirements and predefined items;
the human reviews its findings and chooses corrective instructions; the
producer fixes the result; QA runs again. Gate completion is neither QA
acceptance nor human adoption. Host permissions and downstream authorization
enforcement remain outside this design.

The core scope is managed Skill and Knowledge additions and updates. Docs may
use the same check through explicitly selected update routes, but blanket Docs,
agent, Flow, capability, package, or filesystem enforcement is not authorized
by this proposal. Applicability is recorded for mechanical edits as well as
semantic edits; an unnecessary specialist check has a recorded reason rather
than a bypass. Existing references need not all be investigated on every use.

## Existing Mechanisms and Proposed Delta

| Existing owner | Existing responsibility | Proposed connection |
| --- | --- | --- |
| [Skill authoring](../../skills/os/skill_flow_authoring/SKILL.v1.md#xid-B8D1A4C7E260) | Procedure, boundaries, continuity, maturity evidence | Supplies final candidate and specialist evidence |
| [Knowledge management](../../skills/os/knowledge_ontology_management/SKILL.v1.md#xid-F8A2C6D1B370) | Concept identity, scope, duplication, source and semantic conflict | Retains semantic judgment; supplies assessment evidence |
| [Ontology assessment evidence](../../skills/os/knowledge_ontology_management/scripts/ontology_assessment_evidence.md#xid-D93FA1068B27) | Machine-checkable assessment; semantic acceptance remains unverified | Preserve specialist refusal and unresolved conflicts |
| [Document shipping](../../skills/os/doc_ship/SKILL.v1.md#xid-B4E8A1C7D260) | Authorized work-to-canonical promotion | Candidate integration point, not proof that every write is covered |
| [SkillDefinition](../core/contracts/096_skill_definition_contract.md#xid-E6A19D4B72C3) and [maturity governance](../core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20) | Structure, definition identity, adoption and maturity boundaries | Reuse existing checks; do not invent header fields or approval enums |
| [Sources](../reference/020_sources.md#xid-2FAD591BF725) | Original/source-copy storage, acquisition date and locator; explicit xddp exception | Reference classification supplements storage, never replaces it |
| [Operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61) | Execution, deterministic progression, quality and handoff separation | Gate evidence is linked into existing records |

This is a bounded comparison of inspected mechanisms, not an exhaustive proof
that no equivalent common check exists in any update route. At the authoring
base, `doc_ship` is draft and runtime invocation is refused. Citing its intended
role does not authorize executing it or bypassing that refusal.

## Operation and Responsibilities

1. At intake, the updating route identifies target class, purpose, permitted
   scope and intended canonical destination. The shared gate determines
   applicable common checks; the producer prepares a candidate in work or an
   isolated change area.
2. The specialized authoring route creates the content and records specialist
   checks and required QA. Human corrective instructions invalidate affected
   evidence and require relevant checks to be repeated.
3. Before formal reflection/publication, the **same gate** examines the final
   candidate and its common management evidence. Intake and exit are two
   timings, not two different gates.
4. Missing records return to the producer. Meaning, adoption and publication
   decisions follow existing human decision routes; there is no new link-by-link
   approval prompt.
5. The reflection owner checks candidate identity and the existing authorization
   boundary, then uses an eligible adopted route. Work promotion and direct
   updates require explicit connections to the shared check.
6. Post-reflection checks establish actual XID/link/catalog/adoption consistency.
   A changed candidate cannot reuse the earlier gate result silently.

Specialists own content and meaning; the shared gate owns management evidence
completeness; QA owns requirement checking; humans own corrective directions
and adoption; the reflection owner owns authorized application.

## Proposed Input and Output

### Deterministic Dispatch and Receipt Boundary

The latest user direction is to make an integrated update route require gate
execution deterministically, rather than rely on the main AI remembering to
call it. The proposed sequence is:

`update request -> deterministic applicability/envelope validation -> host
dispatch of an isolated gate-Skill subagent -> structured execution receipt ->
deterministic receipt/candidate validation -> existing human approval/application
-> actual reflection evidence`.

The deterministic layer validates dispatch requirements and evidence; the host
owns actual agent creation. Existing gateway and execution-binding mechanisms
should be reused where suitable, not presented as code that already spawns
host agents. The gate Skill is proposed and private by default; no definition,
publication or runtime execution is included in this PR.

An integrated application endpoint fails closed when a required execution
receipt is absent, invalid or belongs to another candidate. The receipt binds
candidate hash/version, applicable rule references, specialist evidence,
per-check findings, unknowns and decision authority. A recorded dispatch plan
alone is not execution evidence. Neither a valid receipt nor gate completion
implies human approval. Reference role and semantic applicability are judged
by the isolated analyst with evidence, not by deterministic keyword matching.
Actual enforcement remains limited to explicitly integrated update endpoints;
their inventory and coverage are unresolved, and raw filesystem writes are
not intercepted.

Inputs: originating run/work item; target class/path/XID; purpose and change
kind; authorization evidence; current and final candidate identities (including
an explicit new-target case); applicable rule references; specialist and QA
evidence or non-applicability reasons; external-reference roles, use locations,
source pointers and stored material, fixed identifiers or current-information
confirmation conditions.

Output: a candidate-bound check record with each obligation's result, evidence,
missing information, non-applicability reason, next owner and action. Link its
body as `output`, validation as `evidence`, nontrivial reasoning as `judgment`
and onward ownership as `handoff` in existing run records. These are proposed
record contents, not a deployed API or an extension of the SkillDefinition or
ontology sidecar schema.

Progress may reuse existing `pending`, `in_progress`, `done`, `blocked`,
`unknown`, and `escalated` values according to their owning contract. `done`
means that this check completed: it does not establish semantic truth, QA
acceptance, maturity, adoption or permission to publish. Per-obligation findings
remain distinct from overall progression and human decisions. The producer
does not assume the protocol's separate check or quality role.

## External Reference Roles

| Role | Record | Shared check |
| --- | --- | --- |
| Fixed evidential basis | Supported claim/procedure, source locator, acquisition date, stored source, reproducible version/commit | Basis and recorded evidence identify the content actually used |
| Current-information reference | Purpose, target and when current information is needed | Intended update use is explicit; continuous monitoring is not inferred |
| Navigation/reference only | Guidance role and absence of evidential dependency | No indiscriminate fixed-version requirement or source reapproval |

A source may have both fixed and current roles. A GitHub specification used to
derive a procedure records its used commit/locator **and** material required by
the current source-storage contract. A commit URL alone does not satisfy that
storage obligation. A link for checking a later product version records that
purpose and occasion. Classifying references does not relax the external-input
guard or decide source truth from a domain name.

## Enforcement Limits and Evaluation Plan

Calling a shared Skill is initially a procedural gate. Connecting only work
promotion does not cover direct edits, imports, generators, scripts, external
packages or another checkout. A later enforcement design must inventory the
selected update routes and place common validation at actual publication/CI
boundaries. A local commit hook alone is insufficient evidence of full coverage.
Candidate edits to canonical paths are not equivalent to final adoption: this
design does not intercept every filesystem write.

Keep the first trial narrow. Select only applicable common rules, hold each
rule in one source and avoid consumer-Skill copies. Use deterministic checks
for candidate identity, dispatch receipts and record structure; retain meaning
judgments in the separate gate analyst and existing specialist/human roles.
The trial must observe missed checks, unnecessary work and duplicated approval
requests as well as correctness. A design with more explicit rules does not
prove that an AI complies with them; no compliance assurance or numeric burden
threshold is claimed before observation.

The following are **planned checks, not executed results**:

- Fixed evidence identifies stored material and version; an updating URL alone
  produces a missing-evidence finding.
- Current-information and navigation references do not cause repeated source
  approval or indiscriminate commit pinning; source-storage rules still apply.
- Knowledge semantic conflicts remain refused by specialist checks; definition
  changes do not reuse stale governance/adoption identities.
- QA failures and post-check candidate changes require appropriate rechecking;
  gate completion cannot override them.
- Work promotion and direct updates share the rule only when explicitly
  connected; uncovered routes remain visible. Core Skill/Knowledge operation
  does not silently require adoption for all Docs.
- Missing execution receipt, a dispatch plan without execution, stale candidate
  identity or changed rule/evidence references cannot authorize application at
  an integrated endpoint; valid evidence retains human approval requirements.

## Open Decisions and Handoff

Unresolved: canonical rule placement and owner; executable gate identity; formal
reflection boundary; full update-route inventory and enforcement point; bounded
Docs applicability; migration scope for existing references; any requested
source-storage exception; candidate snapshot/receipt schema integration.

The design reviewer and human owner assess these choices before implementation.
No evaluation, deployed enforcement, live-host proof, active rule promotion or
Flow implementation is claimed. Approved improvements from the
[correction retrospective design](114_correction_retrospective_design.md#xid-D4F83A17B9C6)
would enter this gate only after their own human adoption decision.

## Design Provenance

The user asked for a common gate rather than repeated consumer-Skill rules,
retained existing QA/human responsibilities, rejected repeated trusted-site
approval, and authorized exactly two designs for a design-only pull request.
The Japanese working proposal and conversation decisions are retained in local
work records for authoring provenance; those ignored records are not published
dependencies of this design.
Its operational history remains in work; this page presents the current design
proposal and does not transcribe the full conversation.
