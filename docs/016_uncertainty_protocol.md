<!-- xid: 8A666C1FD121 -->
<a id="xid-8A666C1FD121"></a>

# Uncertainty Protocol ("I don't know" policy)

This repository explicitly allows and requires AI to say "I don't know" when needed.
The objective is to prevent confident guessing and protect trust.

## Principles

- Declaring uncertainty is valid and expected.
- Uncertainty is a signal, not a failure.
- Do not proceed on unverified assumptions when uncertainty is material.

## Two Cases

- `I don't know`: knowledge gap (missing or unknown factual/API knowledge)
- `I don't get it`: context gap (missing constraints, assumptions, or requirements)

Both must be surfaced explicitly.

## Required Behavior

When uncertain, AI MUST:

1. State uncertainty explicitly.
2. Classify it as knowledge gap or context gap.
3. List the minimum information needed to proceed.
4. Log the uncertainty in `work/sessions/` for traceability.
5. Pause risky implementation until uncertainty is resolved.

## Escalation

If uncertainty blocks major design or irreversible changes:

- escalate to human confirmation
- propose 1-3 safe options
- resume only after direction is chosen

## Prohibited Behavior

- No confident guesses presented as facts.
- No hedged pseudo-answers that still encourage execution.
- No silent assumption on critical boundaries (API, version, constraints, security).

## Related

- [Shared memory operations](015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Working area policy](014_working_area_policy.md#xid-111D282CA0EA)
- [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
