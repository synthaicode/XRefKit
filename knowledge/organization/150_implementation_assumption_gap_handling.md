<!-- xid: 7A2F4C8D1501 -->
<a id="xid-7A2F4C8D1501"></a>

# Implementation Assumption Gap Handling

This page defines how to handle an implementation assumption gap during manufacturing work.

## Definition

- An `implementation assumption gap` exists when implementation depends on an unstated or unverified assumption about:
  - specification intent
  - design intent
  - runtime behavior
  - framework behavior
  - external dependency behavior
  - data shape or operational condition

## Core Rule

- Manufacturing must not silently close an implementation assumption gap by inventing intent.
- The gap must be converted into an explicit managed state.

## Classification

Classify each gap as one of the following:

| Class | Meaning | Required handling |
|------|------|------|
| `clarification_needed` | likely in scope, but intent is unclear | record as `unknown` and request clarification |
| `evidence_missing` | required design, spec, or runtime evidence is absent | record as `unknown` and request evidence |
| `scope_conflict` | resolving the gap would change approved scope or design policy | record as `out_of_scope` and escalate |
| `local_choice_allowed` | local implementation choice is explicitly delegated by design or rule | record the evidence for delegation and continue |

## Allowed Responses

1. Continue implementation only if:
   - the gap is `local_choice_allowed`
   - delegation evidence is explicit
   - the choice is recorded in notes and metrics
2. Pause and mark `unknown` if:
   - clarification or evidence is missing
   - the implementation would otherwise rely on guessed intent
3. Escalate as `out_of_scope` if:
   - resolving the gap changes design policy, business meaning, or approved scope

## Required Record

Every implementation assumption gap must record:

- affected target
- assumption statement
- why implementation depends on it
- current classification
- missing evidence or escalation reason
- likely next owner if known

## Management Table Rule

- Store the row as:
  - `status: unknown` for `clarification_needed` and `evidence_missing`
  - `status: out_of_scope` for `scope_conflict`
  - `status: done` only for `local_choice_allowed` with explicit delegation evidence

## Closure Rule

- A manufacturing task must not close while an implementation assumption gap remains unrecorded.
- Closure may proceed with recorded `unknown` gaps only if they are handed off explicitly.

## Review Rule

- Manufacturing self-check and QA review must verify that assumption gaps were:
  - recorded
  - classified
  - handled according to this rule
