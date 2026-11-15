# Quality Issue intake and Management Console

## 2026-11-15: Authorized implementation

### Event
- User supplied the Quality Issue implementation and UI consolidation request in an attachment (sections 1–13).
- Original checkout `C:/dev/itsm/XRefKit` has pre-existing staged, unstaged, and untracked changes; none were removed.
- GitHub origin is `https://github.com/synthaicode/XRefKit.git`; authenticated repository permission is ADMIN.
- Fetched origin and created branch `codex/quality-issue-intake-ui` in `C:/dev/itsm/XRefKit-quality-issues` from `origin/main` at `bfa3a9fd707fbdd9ec6f8e071efe0f9da9407c33`.
- Connected MCP reports runtime 0.7.9 and cannot resolve `constraint_derivation_index`. User explicitly selected latest-main local governance for this task, disabling MCP-only loading for this repository development.
- Baseline: `python -m pytest tests/test_contribution_returns.py tests/test_gateway_mcp.py tests/test_dashboard.py -q`: 67 passed in 41.80 seconds, before product edits.

### Decision
- Execute the required constraint derivation and Python implementation in isolated executors under successfully opened repository Skill Runs.
- Reuse existing Feedback, Contribution Return, dashboard, audit, and approval mechanisms. Preserve source worktree changes and existing contracts.
- Create a reviewable PR; do not push main or merge the PR.

### Human Stated Reason
- Quality Issues support continuous improvement of XRefKit itself, separately from ordinary business outputs.
- Existing features must be reused; new execution platforms, databases, and unnecessary Skills or Workflows are outside scope.

### Deferred
- Merge and release are not authorized by this request.

### Open
- Host-specific automatic correction-event access must be verified or explicitly reported as unsupported.
- Next.js retirement requires functional parity and actual-use evidence; absence of such evidence is not evidence of non-use.

## Preflight
- route: constraint_derivation_index, applicable primary derivations, python_implementation_flow, independent review.
- goal: safe Quality Issue intake, Client AI submission capability, Python Management Console with human decisions, regression evidence, PR.
- context: dedicated worktree on current origin/main; source boundary is XRefKit only.
- constraints: unchanged human approval authority, Contribution adoption, Run/Audit contracts, XID identity; no Brownfield/PM business changes.
- done_when: implemented and tested authorized behavior with reviewable diff and explicit limits.
- out_of_scope: new execution engine, new DB, automatic source adoption, automatic PR merge, release.
- verification_commands: focused pytest suites, MCP integration, dashboard regression, full feasible core tests, package build/install smoke, XID link validation.
- stop_conditions: unresolved material authority/security behavior, missing mandatory governance, failed checks requiring a user decision.
- handoff_location: this session, Skill run records, constraint derivation notes, PR.

## Implementation checkpoint
- Backend and console executors paused at a coherent initial implementation snapshot for the mandatory independent review startup checkpoint. This is a work-in-progress commit, not a completion or release claim.
- Backend executor reports 13 focused tests passed; broader and HTTP/MCP integration checks remain in progress.
- Independent constraint review requested an explicit state/action matrix before quality acceptance; findings remain open.

