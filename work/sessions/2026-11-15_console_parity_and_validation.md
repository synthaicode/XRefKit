# Quality Issue console implementation evidence

## Scope and basis

- User request sections 6–10: Python dashboard as one Management Console,
  existing approval boundaries, no missing diagnostics, conditional Next.js
  retirement, synthetic test data.
- Constraint derivation: `work/constraint_derivation/2026-11-15_constraint_derivation_routing_quality_issues.md`.
- Python execution run: `work/sessions/2026-11-15_skill_run_quality_issue_console.md`.
- Owned changes: `xrefkit/dashboard.py`, dashboard CLI help label in
  `xrefkit/operations_cli.py`, `tests/test_quality_issue_dashboard.py`, guide 118,
  docs index, changelog, Next.js README.

## UI parity inventory

| Surface | Next.js source | Python console |
| --- | --- | --- |
| Data source | `lib/dashboard-data.ts`, `app/api/runs/route.ts` invoke Python dashboard data | Existing `/api/runs` and CLI payload retained |
| Search/status filtering | `app/skill-run-dashboard.tsx` | Existing runtime search, status filtering, selection and refresh retained |
| Run detail/closure | Run selection and recorded status | Runtime Diagnostics Overview/Closure and selected-run details retained |
| Evidence/handoff | Run artifacts and concerns | Evidence/Handoff panels retained |
| XID usage/missing information | Recorded payload fields | XID Usage, Missing Information, rankings retained |
| Prompt Flow/recovery | Not in Next.js payload type | Existing Python panels retained |
| Plans/Decision Trace | Not in Next.js payload type | Existing Python panels retained |
| Quality Issues | Absent | List/filter, compact evidence, explicit hypotheses/unknowns, related reports, signed decision form |
| Contribution governance | Absent | Existing inbox/export plus separate existing review/adoption actions |
| Quality Evaluation | Recorded quality fields | Links to existing quality gates/evidence plus Issue improvement records |

Actual deployment and usage inventory is unknown. Source comparison is not
evidence that nobody uses Next.js. The Next.js files, scripts, route, and
dependencies remain unchanged except the README. Removal is not claimed.

## Validation

- Before governance action UI extension: focused new HTTP tests plus existing
  dashboard tests: 26 passed in 15.25 seconds.
- HTTP tests exercise list/detail/filter, explicit missing-record responses,
  protected signed decisions, replay/stale revisions, no direct Knowledge
  mutation, read-only configuration, Origin/Host/CSRF rejection, untrusted text,
  and exact input types.
- Governance test separately accepts an inert synthetic observation using an
  external test issuer, verifies no publication on acceptance, then adopts with
  the correct token through existing catalog machinery. Invalid assertion/token
  fail; the Quality Issue's state remains independently `reported`.
- Final focused run: `python -m pytest tests/test_quality_issue_dashboard.py
  tests/test_dashboard.py -q`: **31 passed in 16.65 seconds**.
- `python -m py_compile xrefkit/dashboard.py xrefkit/operations_cli.py` passed.
- JavaScript extracted from rendered console HTML passed `node --check`.
- Final Bandit review: B608 matched natural-language/select markup inside
  `_console_html`'s static HTML f-string. The string is returned to the browser;
  this function does not construct or execute SQL. A B608-only suppression on
  that literal, with an adjacent explanation, preserves the rendered prose and
  does not suppress other checks. `python -m bandit xrefkit/dashboard.py -ll -f
  json -o work/sessions/2026-11-15_console_bandit.json` exited 0 with no reported
  medium/high findings. Only Python comments changed; rendered HTML is unchanged.
- Final browser observations are recorded by the coordinating session after the
  completed diff.

## Review responses

- QI-R01: missing contribution/Issue `KeyError` is mapped to HTTP 404 for both
  mutation endpoints and covered by an HTTP regression test.
- QI-R02 related UI coverage: false/zero/object/non-string evidence values are
  rejected by the backend's strict decision validation, exercised through HTTP.
- Parent browser feedback: compact human-readable evidence replaced exposed
  report JSON in the main view; technical data is optional; console area is
  preserved through runtime navigation updates; document title updated.

## Explicit limitations and handoff

- Production trusted identity-provider issuance, real host callback access,
  real-client redaction, and actual Next.js usage are unverified.
- New management evidence and write endpoints are local only. Existing remote
  runtime diagnostics have no added authentication and require a trusted network.
- Browser governance actions produce existing signed contribution events, not
  fabricated MCP audit correlation.
- No source identity/revision, Brownfield or Project Management business logic
  changed. Issue approval is not canonical adoption.
- Executor hands off code/evidence for independent Python review and parent
  deterministic verification/closure; executor does not close its run.
