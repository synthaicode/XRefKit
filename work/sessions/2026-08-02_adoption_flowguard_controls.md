## 2026-08-02: adopt bounded flowguard controls

### Event
The user approved adopting the previously evaluated `flowguard` pattern. The adopted scope is limited to preflight boundaries, meaningful execution checkpoints, fresh current-run verification, stop-and-reroute conditions, and resumable handoff context audits.

### Decision
Updated the Skill Operating Contract, Skill Reporting Contract, and Skill authoring body template. The existing semantic Skill routing, XID model, Run Log work items/artifacts/concerns/phases, deterministic verification, and closure gates remain authoritative. The external Skill is not installed and is not used as a new lifecycle entrypoint.

### Human Stated Reason
The user said `採用する` after the limited-adoption proposal.

### Deferred
No external Skill installation, no new runtime command, and no automatic migration of existing Skill bodies were requested or performed.

### Open
Behavioral runtime testing of the new guidance on a multi-step Skill run remains future work. XRef validation passed with `missing_xid: []` and `issues: []`.
