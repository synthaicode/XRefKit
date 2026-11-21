# Project Management current records trial with Issue #201

## Observed sources

- [Issue #201](https://github.com/synthaicode/XRefKit/issues/201), body revision
  `2026-11-21T06:56:41Z`. The earlier migration used GitHub's file upload and
  Issue editor. The released package did not create or maintain that archive.
  The body has a managed Human View and an index of 17 older fragments.
- [Exact Original](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md),
  captured from the earlier Issue revision `2026-11-21T06:26:35Z`.
  Its 19,537 UTF-8 bytes have SHA-256
  `37ed0a8f8e54cd318e3e71d5365f736ea6c0cf6ee5e9ce7bf910a721f4931fc8`.
- [Project #3](https://github.com/users/synthaicode/projects/3) showed `Todo`
  on #201 at the earlier Issue update. The native blocker was #200.
- [Issue #200](https://github.com/synthaicode/XRefKit/issues/200), revision
  `2026-11-21T06:59:23Z`, records six passing offline cases and an independent
  rereview of the first contract candidate. Human acceptance remains pending.

The deployed Issue has no machine-readable current design or evidence
references. The board, Issue and PM records already carry complementary
authorities. A current owner, locator and accepted revision for every #201
technical deliverable could not be established from those sources. The
fixture uses proposed design and verification records to exercise that
relationship without asserting production adoption.

## Classification of the old record

| Information in Original | Owner and use |
| --- | --- |
| Purpose, required bounded context, acceptance and egress limits | The Issue owns the current work contract. Its Human View projects the immediately relevant criteria. |
| Epic, native blocker, decision and work-start holds, handoff to downstream Issues | Preserve native Issue relationships. Resolve the current Decision and Execution scope through the existing PM and approval records. Project owns the board status. |
| Startup and XID resolution, trusted control, outbound input and provenance design | The design proposal is a separate versioned technical deliverable. Existing startup, Runtime Binding and selected Knowledge remain its sources, scoped by XID and revision where applicable. |
| Fixture criteria, limited old resolver observation, planned verification, source baseline | Verification records own what ran, which revision it covered and the open checks. The limitation of the 50-byte resolver observation and absence of #201 fixture results survive migration. |
| Proposed model, usage cap and next handoff | Keep execution planning in PM and run evidence in the existing Runtime. Operational authorization remains in the applicable Decision records. |
| Historic prose, links, question wording and fragment targets | Keep the exact immutable Original for audit. GitHub's history and comments retain provenance and conversations. Preserve all current fragment aliases and compare against their archived counterparts. |

The integration examples are in
`integration/brownfield_project_management/tests/fixtures/issue_201/`.
The design and verification files are classified fixture records. The
Original stays unchanged. A current handoff resolves only Issue work,
Project/PM, applicable Decision and technical inputs. It succeeds with
history offline. A delivery validates all links it publishes, including
history. The prototype uses the existing pointer/readback and writer contracts
with in-memory adapters. It adds no database, external adapter, or Runtime,
Knowledge, Brownfield, or Quality Issue authority.

## Before and after

The observed Issue says that #200 started its approved offline work. The
fixture after view says #201 remains unstarted and explains why the upstream
contract is still a blocker after engineering checks passed. It shows the
next owner roles, the offline acceptance criteria, and labeled links to the
proposed design, verification record and older Issue snapshot. There is no
current decision request for #201. None of the fixture records sets an
approval or starts work.

Excluding the closing marker, the top block was 1,187 bytes before and 1,142
bytes after, with links. The raw Issue body was 5,029 versus 6,583 bytes
because the candidate also carries exact requirements and typed references.
The 17 aliases and all content after the old managed view survive unchanged.
Repeat projection over the same records is byte-identical. Broken or stale
current evidence, stale management state, concurrent human/AI changes and
uncertain delivery all have explicit stops or exact readback reconciliation.

Production migration still requires confirmed current record owners, the
GitHub readback and guarded delivery route, and separate human approval.
The shared Skill procedure remains a staged candidate until governed
reflection. This trial authorizes no GitHub or PyPI mutation.

## Test results

The full local suite across Issue projection, Brownfield handoff, scheduling,
packaging and materialization passed 107 tests. Two existing tests ran into
Windows sandbox limits while creating a hard link and a directory junction.
The same two failures were recorded with the previous wheel. The candidate
wheel was installed in an isolated target and passed all 66 selected Issue,
Runtime, and materialization tests. Package asset parity checked all 17
managed files and the XID link check found zero issues.
