<!-- xid: B4F1C8D2A611 -->
<a id="xid-B4F1C8D2A611"></a>

# Brownfield phase workflow

Use the phase sequence `requirements -> planning -> design -> manufacturing ->
testing`. Preserve upstream references and carry forward decisions, unknowns,
evidence, owners, and handoff conditions.

Planning has two checkpoints. First produce the initial work policy from the
available Requirement and current-system evidence: impacted targets,
dependencies, order, tools, versions, fixtures, environment, test data,
cleanup, result storage, compatibility, migration, release, rollback, risks,
stop conditions, gates, and handoffs. After the design-phase specification
reconciliation, refine this policy from approved delta rows before
manufacturing or test-case approval. Tool preparation belongs here; execution
belongs to testing. See
`delta-detail-planning.md#xid-B4F1C8D2A610` for the second planning checkpoint.
