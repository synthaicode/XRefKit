<!-- xid: E7034812B5E8 -->
<a id="xid-E7034812B5E8"></a>

# Topic Involvement Map

## 1. Scope

- Root topic: API retry policy
- Period: 2026-06-20 09:00 - 2026-06-27 11:00 JST
- Source systems: sample-chat
- Evidence set: m001-m009
- Handling classification: internal planning only
- Handling rationale: participant involvement and coordination candidates are interpreted from internal conversation evidence.

## 2. Topic List

| Topic ID | Label | Parent | Current state | First seen | Last activity | Open point | Confidence |
|---|---|---|---|---|---|---|---|
| T0 | API retry policy | - | open | 2026-06-20 | 2026-06-27 | payment idempotency confirmation and batch cutoff proposal | high |
| T1 | Payment API idempotency confirmation | T0 | confirmation_waiting | 2026-06-20 | 2026-06-27 | Cora confirmation on idempotency key | high |
| T2 | Batch retry cutoff and maintenance conflict | T0 | proposal_pending | 2026-06-20 | 2026-06-27 | cutoff proposal to release note | high |

## 3. Topic Detail

### T1. Payment API idempotency confirmation

- current state: confirmation_waiting
- open point: whether idempotency key is required for payment retry
- next useful confirmation: Cora confirmation
- local terms:
  - payment API
  - API owner route
  - idempotency key
- evidence: m002, m005, m006, m007, m008

### T2. Batch retry cutoff and maintenance conflict

- current state: proposal_pending
- open point: cutoff proposal needs to be added to the release note
- next useful confirmation: release note update
- local terms:
  - retry cutoff
  - maintenance window
- evidence: m003, m004, m005, m009

## 4. Participant Involvement By Topic

### T1. Payment API idempotency confirmation

| Participant | Current involvement | Involvement type | Evidence | Last activity | Confidence | Caveat |
|---|---|---|---|---|---|---|
| Bo | high | owner_candidate / continuing concern owner | m002 raises idempotency; m006 accepts drafting; m007 keeps the question open | 2026-06-21 | high | not formal authority |
| Cora | high | confirmation_target | m008 names Cora as the confirmation target | 2026-06-27 | medium | direct Cora response is absent |
| Ema | medium | bridge_participant | m008 connects API owner route to Cora confirmation | 2026-06-27 | medium | route source is not independently verified |
| Aki | medium | initial organizer | m005 splits payment and batch topics | 2026-06-20 | high | current involvement is lower than initial involvement |

### T2. Batch retry cutoff and maintenance conflict

| Participant | Current involvement | Involvement type | Evidence | Last activity | Confidence | Caveat |
|---|---|---|---|---|---|---|
| Dina | high | owner_candidate | m004 accepts maintenance-window confirmation; m009 accepts cutoff proposal update | 2026-06-27 | high | formal operations authority is not supplied |
| Chen | medium | active_participant | m003 identifies maintenance conflict | 2026-06-20 | medium | no current activity |
| Aki | low | initial organizer | m005 separates batch from payment topic | 2026-06-20 | medium | no current batch follow-up |

## 5. Involvement Changes

### T1. Payment API idempotency confirmation

| Date | Main movement | High | Medium | Low / inactive |
|---|---|---|---|---|
| 2026-06-20 | idempotency issue appears and Bo accepts drafting | Bo | Aki | Cora |
| 2026-06-21 | idempotency remains open | Bo | - | Aki |
| 2026-06-27 | Cora becomes confirmation target | Bo, Cora | Ema | Aki |

### T2. Batch retry cutoff and maintenance conflict

| Date | Main movement | High | Medium | Low / inactive |
|---|---|---|---|---|
| 2026-06-20 | maintenance conflict appears and Dina accepts checking | Dina | Chen, Aki | - |
| 2026-06-27 | cutoff proposal becomes next action | Dina | - | Chen, Aki |

## 6. Central And Bridge Candidates

### T1. Payment API idempotency confirmation

- current central candidates:
  - Bo
  - Cora
- initial organizer: Aki
- continuing concern owner: Bo
- confirmation target: Cora

| Candidate | Coordination signal | Evidence | Confidence | Caveat |
|---|---|---|---|---|
| Bo | keeps the idempotency question open and owns the draft confirmation point | m002, m006, m007 | high | not formal authority |
| Cora | current confirmation target | m008 | medium | no direct response in evidence |

### T2. Batch retry cutoff and maintenance conflict

- current central candidates:
  - Dina
- initial organizer: Aki
- continuing concern owner: Dina
- confirmation target: Dina

| Candidate | Coordination signal | Evidence | Confidence | Caveat |
|---|---|---|---|---|
| Dina | owns maintenance-window check and cutoff proposal update | m004, m009 | high | formal authority unknown |

## 7. Bridge Participants

| Participant | Connected topics | Bridge evidence | Recommended use |
|---|---|---|---|
| Aki | T1, T2 | m005 explicitly separates payment and batch topics | ask Aki only for original split context, not current confirmation |
| Ema | T1, API owner route | m008 identifies Cora as the current confirmation target | ask Ema for source of the route if Cora cannot confirm |

## 8. Local Semantic Map

| Local term | Local meaning in this conversation | Evidence | Confidence | Competing meaning | Promotion candidate |
|---|---|---|---|---|---|
| API owner route | path for confirming payment API idempotency handling | m007, m008 | medium | formal API ownership process | human_review |
| retry cutoff | time boundary that prevents retry from overlapping maintenance | m009 | high | general timeout setting | no |

## 9. Unknowns And Human Review

- unknowns:
  - Whether Cora has formal authority or only confirmation knowledge for T1.
  - Whether Dina has formal authority or only update ownership for T2.
- human review items:
  - Confirm whether Bo and Cora are acceptable coordination contacts for T1.
  - Confirm whether Dina can close T2 after the release note update.

## 10. Knowledge Promotion Candidates

| Local term or pattern | Observed meaning | Stability | Existing Knowledge relation | Recommended action |
|---|---|---|---|
| API owner route | route used to identify the API behavior confirmation target | one conversation | unknown | keep_local until repeated or human-confirmed |
| retry cutoff vs maintenance window | operational constraint pattern for retry design | candidate | unknown | route_to_ontology_skill after human review if repeated |

## 11. Recommended Next Actions

| Topic ID | Next action | Owner / target | Reason | Blocking unknown |
|---|---|---|---|---|
| T1 | confirm whether idempotency key is required | Cora | current open point blocks retry-policy closure | Cora's formal authority |
| T2 | add retry cutoff proposal to release note | Dina | current owner candidate accepted this update | formal maintenance authority |

## 12. Handling and Use Restrictions

- permitted audience: internal project planning participants
- redactions or exclusions: keep sample identities internal if copied outside the project
- Do Not Use For warning, when required: not triggered by this sample evidence
