# XRefKit Base Runtime Contract

- [must] skill.os_contract_required: New Skills include the Skill operating contract.
- [must] skill.run_first: Start Skill execution through the runtime envelope before loading the Skill body.
- [must] skill.workitem_required: Record concrete work items before closure.
- [must] skill.artifact_required: Record output and evidence artifacts before closure.
- [must] skill.concern_required: Record closure-relevant unknowns, risks, and judgments.
- [must] skill.verify_separate: Advance check through deterministic verification, not the producer context.
- [must] work.log_required: Write execution logs and retrospectives under work.
- [must] work.date_prefix: Use date-prefixed work-record filenames.
- [must] work.session_before_complete: Update a session log before completion, commit, or push.
- [must] work.promote_stable: Promote stabilized facts and decisions to canonical locations.
- [must] uncertainty.explicit: Classify and expose material uncertainty, search Knowledge, and pause risky work.
- [must] claims.no_unsupported_fact: Do not present unsupported claims as facts; expose the evidence gap and route material uncertainty through the uncertainty protocol.
- [must] memory.write: Write logs after significant discussions, decisions, or work sessions.
- [must] memory.session: Ensure a work session entry exists before final response.
- [must] memory.before_publish: Update logs before commit or push.
- [must] memory.promote: Promote stabilized work content into canonical docs or Knowledge.
- [must] memory.filename: Prefix work record filenames with the date.

Conditional loads:
- skill_execution: xid B7A2C94F0E61
