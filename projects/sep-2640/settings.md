<!-- xid: 3E81B6D29A40 -->
<a id="xid-3E81B6D29A40"></a>

# SEP-2640 task settings

Revision: 3, 2026-11-25. Scope: SEP-2640 implementation and GitHub Projects coordination.

## Applicable authority and evidence

The current user instructions establish the goal and sequence:

1. `XRefKit MCP ServerをSEP-2640に対応させる。最優先で実施`.
2. `ローカル規程で進める`, in response to the MCP/local-governance source conflict.
3. `Project management skillでprojectsへ作業分割してから実装とレビューテストを実施`.
4. The user additionally requested tests proving existing XID search and retrieval
   still work after the change, then identified missing Projects registration.
5. The user clarified the destination as `GitHub Projects`.

The active repository startup/Workflow contracts govern execution, checks and
closure. Project Management 0.1.3 supplies coordination procedures, loaded from
an unchanged local copy of the installed package under `work/sep2640/pm-package`.
Its trial governance is bound to each opened definition. Package publication is
not evidence of operational quality.

The user authorizes planning, implementation, review, tests and GitHub Projects
registration. The earlier interpretation that local `projects/` files alone
completed delivery was incorrect and is superseded by the explicit destination
clarification. Local Markdown remains technical/coordination evidence. The
parent must identify the existing intended board, record task items through an
available authenticated route, and read back their actual identities and fields.
No additional permission is needed for that authorized registration. The parent
registered and read back six issues on GitHub Project 7, `XRefKit — SEP-2640 MCP
Skills Extension`, at https://github.com/users/synthaicode/projects/7. The local
plan maps each issue to its task IDs and observed board state. Release and
production activation remain outside scope. No calendar, duration estimate,
schedule baseline or stakeholder assignment was requested or is inferred.

## Record mapping and responsibilities

| Record | Authoritative local destination | Responsible role | Evidence of delivery |
| --- | --- | --- | --- |
| Intent and task authorization | This file, citing the current user instructions | Parent coordinator preserves scope | File readback and references in the plan |
| GitHub Project task registration and board fields | [synthaicode Project 7](https://github.com/users/synthaicode/projects/7), issues #297–302 | Parent coordinator | Actual board/item URLs, saved fields and destination readback |
| Work split, dependencies, current results and next actions | `projects/sep-2640/plan.md` | Parent coordinator consumes executor/reviewer evidence | Saved plan with actual status and evidence links |
| Protocol/design basis and acceptance mapping | `projects/sep-2640/` technical record created by technical analysis | Technical analysis executor | Exact source references and explicit compatibility decision |
| Code and test artifacts | `xrefkit/mcp/`, selected `tests/` files | Implementation executor | Diff linked to plan IDs and validation evidence |
| Independent review and defect disposition | `work/sep2640/` plus references in the plan | Separate reviewer; parent coordinates fixes | Version-scoped findings, fixes and reviewer disposition |
| Test execution | `work/sep2640/` plus references in the plan | Test executor | Command, environment, exit code and result |
| Runtime progression and handoff | `work/sessions/2026-11-25_skill_run_*.md` | Assigned runtime roles | Runtime artifacts, deterministic verify and close |

Local file save/readback completes only the local evidence step. Project
registration requires actual destination readback; final chat must link the
registered board/items or identify the unresolved delivery blocker. Do not infer
team access merely from file creation or a submitted write. Update current
results in place, retaining historical evidence in run logs and Git. A changed
requirement or compatibility choice must identify affected tasks and invalidate
stale review/test claims.

## Start and completion boundaries

Technical analysis is authorized by the current instruction. Implementation
requires a concrete source-backed technical basis resolving its affected
protocol, resource mapping and governance questions. Review requires an
identified diff; tests require identified behavior and commands. Fixes return
to review and rerun the affected tests. Overall completion requires evidence
covering the current change and an explicit account of unverified client or
deployment behavior. PM coordination records that evidence and does not issue
the technical quality verdict itself.

There is no configured deterministic cross-stage condition matcher for this
task. The plan records explicit dependencies and evidence requirements; it does
not claim machine-evaluated readiness. Actual execution and quality gates stay
with the repository Runtime and the technical review/test routes.
