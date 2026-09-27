# Attention Pet

English | [日本語](README.md)

Attention Pet is a local experiment that separates two questions: whether the
selected model is estimated to meet the work's capability requirements, and
whether a lower inference-cost candidate may also fit. It displays Model Fit,
Cost Fit, input coverage, and unevaluated confidence separately so people can
use them when deciding how to allocate models.

Attention Pet does not measure token usage. It estimates the structural
complexity of the work context the AI must handle: retained items,
dependencies, constraints, decision depth, conflicts, and dispersed evidence.
It does not read model-internal attention values or the remaining context-window
capacity.

When launched from Codex, the Pet reads new user messages and runtime settings
from the launching chat's local session record. It briefly moves when it sees a
new message, while its expression follows the evaluation result. Capability,
behavior, and cost values are uncalibrated hypotheses. The Pet does not measure
model-internal attention or remaining capacity, and it never switches models
automatically.

## Codex-only preview

The ready-to-run automatic integration is currently limited to Codex. It reads
the work information and runtime settings visible in the launching Codex chat,
then uses the Pet's expression and short message to show whether the current
model is estimated to have enough capacity for that work and whether a
lower-cost comparison candidate exists. This is an observation and estimate;
it does not change the Codex model, reasoning depth, or chat content.

In this guide, model "headroom" means the comparison between the currently
visible work-context complexity and an experimental model capability profile.
It does not mean remaining tokens.

1. Open a Codex terminal for the chat you want to observe and go to the root of
   this repository.
2. Start the Pet:

   ```powershell
   python -m xrefkit.attention_pet serve --port 8769
   ```

3. Open the printed `http://127.0.0.1:8769/` address in the Codex browser panel.
4. Press Ctrl+C in the launching terminal to stop it.

The Pet is bound to the chat that launched it. Selecting another chat in Codex
does not switch the Pet automatically; launch it again from the other chat for
a separate view. Model and reasoning controls in the UI change only the
comparison estimate and do not change Codex settings.

Provider-neutral client-state integration is a separate path. This release
does not include a client adapter that detects conversation selection in Codex
or VS Code.

## Running Attention Pet

Run from the worktree root with Python 3.11 or later and Pydantic 2:

```powershell
python -m xrefkit.attention_pet serve --port 8769
```

Formal client integrations should use client-state mode instead of reading
JSONL directly:

```powershell
xrefkit attention-pet serve --client --port 8769
```

Client-state mode writes one compact JSON object to its first stdout line. It
contains the endpoint, protocol version, instance ID, and per-process write
token. A client performs an authenticated handshake before sending the active
session and its complete structured WorkingSet. See the
[client protocol](CLIENT_PROTOCOL.md) for the contract.

When `CODEX_THREAD_ID` is available, direct JSONL reading remains an
experimental compatibility path. It stays bound to the launching chat and does
not follow UI chat selection. A Codex record-format change may break it.

The display does not require authentication. Its language follows the
browser's preferred languages: Japanese is used when Japanese is preferred,
with English as the fallback. The browser sends the same `lang=ja|en` value to
the evaluation API so headings, reasons, and suggested actions use one
language.

The primary view keeps the model and cost allocation card and Pet visible. It
shows capability fit, cost comparison, input coverage, and confidence. In a
chat-bound view, the recorded Codex model and reasoning level initialize the
comparison controls. Changing those controls does not modify the Codex run.

Open **Show values, candidates, and reasons** to inspect Base RAL, the three
capability axes, candidates, relative inference-cost indices, and reasons. A
lower-cost candidate means that an experimental profile at the same reasoning
depth is estimated to meet all three capability requirements at a lower
relative inference cost. It does not establish equal real-world quality or a
lower total cost.

Terra is an experimental comparison profile between Luna and Sol. The profile
order and coefficients do not claim a real model performance ranking.

## Reading the evaluation

| Evaluation | Values |
|---|---|
| Model Fit, capability only | Unknown / Underpowered / Sufficient |
| Cost Fit, hypothetical inference-cost comparison plus outcome records | Unknown / RetryRisk / NoLowerCostCandidate / LowerCostCandidateAvailable / ReviewNeeded |
| Pet State, presentation only | Unknown / Strained / Balanced / Relaxed / Review |

Meeting all three capability requirements produces `Sufficient`, regardless of
other candidates' prices. A fitting candidate with lower relative inference
cost at the same depth produces `LowerCostCandidateAvailable`. The `Relaxed`
expression means that a lower-cost candidate can be compared; it does not mean
the current model has excessive capability.

Failure, retry, or correction records produce `ReviewNeeded / Review` and stay
separate from Model Fit. `Balanced` means that no lower-cost fit candidate was
found under the current assumptions, while `Relaxed` means that one was found.
Neither state measures actual quality or total cost.

Actual inference cost, retry cost, correction cost, failure loss, and total
cost remain `null`. Coverage and Confidence are independent; Confidence is
currently `Unknown`. See [How it works](MECHANISM.md) for formulas, API fields,
scenario tables, and unverified assumptions.

## Technical API input

The browser does not provide file import or work-organization controls. Use the
manual HTTP API when testing structured annotations. Chat-bound mode keeps
update APIs read-only.

Machine-readable contracts are available in:

- `schema/working-set.schema.json`
- `schema/conversation.schema.json`
- `schema/fit.schema.json`
- `schema/client-state.schema.json`

Keep stable IDs and preserve `source`, dependency `evidence`, and observation
`evidence/context` references. Timestamps are UTC epoch seconds. Leave
`coverage=partial` until the input scope has been reviewed.

The evaluator can also run without the browser:

```powershell
python -m xrefkit.attention_pet evaluate projects/attention-pet/examples/working-set.json
python -m xrefkit.attention_pet evaluate projects/attention-pet/examples/working-set.json --model sol --reasoning standard
python -m xrefkit.attention_pet evaluate projects/attention-pet/examples/conversation.json --conversation
```

HTTP endpoints:

| Method and path | Purpose |
|---|---|
| GET `/api/state` | Return the current WorkingSet, Attention State, latest 100 history entries, recovery records, and FitEvaluation |
| GET `/api/client/handshake` | Verify service, protocol, instance, and capabilities |
| POST `/api/active-session` | Notify the active session and complete WorkingSet |
| POST `/api/snapshot` | Evaluate and save a WorkingSet |
| POST `/api/conversation` | Extract, evaluate, and save an annotated Conversation |
| POST `/api/recover` | Apply `action` with `expectedObservedAt`; stale operations are rejected |

`GET /api/state` is unauthenticated. The client handshake and all POST requests
require the per-process `Authorization: Bearer <token>` value; POST requests
also require `Content-Type: application/json`.

Query parameters such as `?model=luna&reasoning=standard` affect only the
returned comparison. `lang=ja|en` affects only presentation text. Supported
models are `luna|terra|sol|astra`, and supported reasoning depths are
`light|standard|high`. Unknown and duplicate parameters are rejected before an
update. External origins are rejected; request limits are 2 MB, 500 items,
2,000 edges, and 500 observations.

## Validation

```powershell
python -m pytest tests/test_attention_pet.py tests/test_attention_pet_fit.py tests/test_decision_trace.py -q
node --check xrefkit/resources/attention_pet/pet.js
```

See [validation results](VALIDATION.md) and the
[design and limitations](../../docs/designs/100_attention_pet.md#xid-38C97BA1E4D2).
The evaluator lives in `xrefkit/attention_pet/evaluator.py`; display assets live
in `xrefkit/resources/attention_pet/`. A custom weight file must total 100 and
can be supplied with `serve/evaluate --weights <path>`. Evaluation calibration
and whether people understand the expressions remain separate validation
questions.
