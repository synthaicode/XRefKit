# Quality Issue secondary commonality pass

Completed primary input: `2026-11-15_constraint_derivation_routing_quality_issues.md`, DCD/UCD/LCD/ICD/AACD tables. Framework `81A6C4E2B190` and signals `9C27AE51D648` were read after the primary lists existed. This pass proposes shared implementation candidates, not new business rules.

| ID | Source IDs and pattern | Candidate | Integration benefit | Non-integration risk / boundary |
| --- | --- | --- | --- | --- |
| CD-01 | DCD-01/02, ICD-01/02/03: repeated intake constraints | Reuse contribution validators/store and upload/submit path | One identity, payload and storage contract | Separate issue intake may drift in quotas, identity or idempotency; optional metadata must not alter old records |
| CD-02 | UCD-03, LCD-05, AACD-02/03: repeated decision integrity | Shared issue decision function used by MCP and Dashboard | Same assertion/revision/history validation at every entry | UI-only checks permit direct API bypass; verifier reuse does not merge Issue judgment with adoption |
| CD-03 | DCD-04, LCD-01, ICD-04: unknown evidence | Keep existing feedback reason/scope semantics and explicit absent values | Unknown remains visible across client and console | Separate normalization may invent causality or acceptance; no new generic uncertainty engine |

| ID | Boundary check | Disposition |
| --- | --- | --- |
| CB-01 | UI and MCP mutate the same issue decision history | Domain mutation function owns validation and lock; UI is only presentation/transport |
| CB-02 | Similar-looking Issue and Contribution approval | Distinct decisions and assertion claims; no automatic canonical adoption |
| CB-03 | Client and server both inspect sensitivity | Client permission check precedes transmission; server validation is defense in depth, not a retroactive prevention of leaked network content |
| CB-04 | Shared Python data and Next.js UI | Existing data delegation supports reuse, not proof of deployment migration; retain Next.js pending usage evidence |

User §1 already explicitly selected maximum reuse and prohibited duplicate execution foundations. These candidates implement that direction, without authorizing any additional common workflow, database, or automatic adoption. No additional consolidation decision is needed for these bounded reuse candidates. Any wider abstraction remains outside scope and requires separate human direction. Independent quality review remains outstanding.
