## 2026-08-19: Optional human evaluation at run boundaries

### Event

Implemented an optional workflow-protocol observation for a human's evaluation
of a completed run when issuing a subsequent request. The record is written by
`xrefkit skill evaluate` to the preceding run log.

### Decision

- Handoff remains unconditional; the agent does not wait for or demand human
  evaluation.
- The human-confirmed relationship classification is authoritative, while an AI
  may supply only a proposed classification.
- The record supports run-level evaluation plus optional scoped findings for
  work items, artifacts, evidence contexts, or target systems.
- The record includes evaluated time, prior run identity, optional context refs,
  and an explicit comparability gap state. It does not record private model
  chain-of-thought.
- No PyPI release or package/version change is included in this change; release
  is downstream of PR review and merge.

### Human Stated Reason

The user requested an auditable workflow-protocol extension that is optional
and ergonomic for ordinary continuation, supports correction/scope/new-work/
clarification classification, and exposes time-based context drift for
multi-target or long-separated evaluations.

### Deferred

- Authenticated human identity and external approval signatures remain outside
  this minimal local record interface.
- Automatic next-run classification proposal/execution remains a harness-level
  integration concern; this CLI records an optional proposal beside the
  human-confirmed classification.
- PyPI publication and release/versioning remain deferred until explicit user
  authorization after PR review and merge.

### Open

- XRef check still reports pre-existing repository baseline issues outside the
  changed contract and implementation paths.
- The evaluation schema cannot establish substantive correctness of a human's
  basis or model-internal reproducibility.

### Verification

- `python -m pytest tests/test_human_evaluation.py tests/test_instruction_workflow.py tests/test_skill_runtime_audit.py tests/test_dashboard.py tests/test_xrefkit_v2_models.py -q --basetemp .tmp/pytest-human-evaluation-final` -> `46 passed`
- `python -m xrefkit skill evaluate --help` -> command and fields exposed
- `git diff --check` -> passed
- `python -m xrefkit xref check --include docs xrefkit tests --json` -> existing baseline issues reported; no changed-scope conclusion inferred from the aggregate result
