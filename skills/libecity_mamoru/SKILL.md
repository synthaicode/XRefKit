# Skill: libecity_mamoru

## Purpose

Support users in strengthening "Mamoru Chikara" by identifying personal and household risks, then converting gaps into concrete, prioritized actions.
Use a confidential knowledge record for current state management.
Read schema: `references/confidential_state_schema.md`.

## Inputs

- user profile (age range, family structure, work style, residence)
- current status (savings, insurance, emergency fund, contracts, account security)
- top concerns (illness, job loss, fraud, disaster, legal trouble, etc.)
- optional constraints (monthly budget, execution deadline, risk tolerance)
- input source path (prefer outside repo or under ignored paths such as `.private/`)
- confidential current-state file (default: `.private/libecity_mamoru/current_state.md`)
- optional learning data inputs (bills, receipts, account statements, household logs, past decisions)

## Outputs

- risk map by category (`high`, `medium`, `low`)
- protection gap list with evidence from user inputs
- prioritized action plan (`now`, `next`, `later`)
- action checklist with owner/date/cost estimate
- review cadence (monthly/quarterly triggers)
- updated confidential current-state record
- retention notification for user (what was stored, where, and update timestamp)
- learning-data ingestion summary (source type, extracted fields, confidence, unresolved items)

## Procedure

1. Establish private data handling boundary:
   - store raw personal data only in non-tracked locations
   - prefer paths outside repository, or ignored local paths (`.private/`, `work/private/`)
   - never place raw personal data in tracked files under `skills/`, `docs/`, `knowledge/`, or `work/`
2. Prepare confidential knowledge record:
   - if missing, create `.private/libecity_mamoru/current_state.md` using `references/confidential_state_schema.md`
   - load current-state sections as the single source of truth for this skill
   - append session snapshots in `.private/libecity_mamoru/history/YYYY-MM-DD.md` when major updates occur
3. Confirm objective and scope:
   - define whether the focus is personal, household, or both
   - define timeline and budget constraints
4. Ingest confidential learning data:
   - parse provided data sources and extract reusable state signals
   - map extracted values into `current_state.md` sections using `references/confidential_state_schema.md`
   - label uncertain extraction as `needs_confirmation`
   - retain source provenance (`source_type`, `source_date`, `ingested_at`) in learning-data section
5. Build a baseline snapshot:
   - income stability and dependency risks
   - cash buffer and fixed-cost resilience
   - insurance and contract coverage
   - digital/account security posture
   - disaster/legal/document readiness
6. Score risk by impact x probability:
   - impact: financial, operational, emotional
   - probability: likely, possible, unlikely
   - classify into `high`, `medium`, `low`
7. Detect gaps:
   - list missing controls or weak controls
   - separate hard gaps (not present) from quality gaps (present but weak)
8. Propose prioritized actions:
   - `now`: low-cost, high-impact actions
   - `next`: medium effort actions
   - `later`: long-term or optional optimizations
9. Produce execution checklist:
   - each action must include owner, due date, expected effect, estimated cost
10. Define review loop:
   - set monthly quick check and quarterly deep review
   - define triggers (job change, family change, move, major purchase)
11. Persist confidential updates:
   - automatically write resolved assumptions and changed status to `.private/libecity_mamoru/current_state.md`
   - append change snapshot to `.private/libecity_mamoru/history/YYYY-MM-DD.md`
   - keep only redacted summaries in tracked files when sharing outcomes
12. Notify retained items to user:
   - return a retention summary including:
     - storage path
     - timestamp
     - fields added/updated
     - learning data sources ingested and mapped fields
     - fields intentionally not stored

## Rules

- Keep recommendations practical and order them by risk reduction per effort.
- State assumptions explicitly when data is missing.
- Mark uncertain items as `needs_confirmation`.
- Keep personal data out of Git-tracked files.
- If output needs to be shared in-repo, redact or aggregate personal identifiers first.
- Always perform automatic confidential persistence unless user explicitly opts out.
- Always notify the user what was retained after each persistence.
- Keep learning data ingestion minimal: store derived state and provenance, not unnecessary raw payloads.
- Do not make definitive legal/tax/insurance determinations.
- Encourage consultation with licensed professionals for high-stakes decisions.

## Failure Handling

- If user data is insufficient, return a "minimum input checklist" first.
- If budget or timeline is unknown, create two scenarios (`lean` and `standard`).
- If constraints conflict (high safety target with near-zero budget), show trade-offs clearly and re-prioritize.
