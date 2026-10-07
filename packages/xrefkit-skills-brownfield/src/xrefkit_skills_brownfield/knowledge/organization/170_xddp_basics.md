<!-- xid: 7A2F4C8D1701 -->
<a id="xid-7A2F4C8D1701"></a>

# XDDP Basics

This page summarizes the basic XDDP view for derivative development and brownfield change work, with emphasis on the three main artifacts and the practical `Why / What`, `Where`, and `How` sequence.

## Purpose

Use XDDP to make change work reviewable before coding by treating change and addition explicitly and by managing differences through stable intermediate artifacts.

## Core Position

- XDDP is a process specialized for derivative development.
- It aims to prevent misses, mistakes, and waste by front-loading change clarification before implementation.
- It separates acts with different cognitive demands instead of mixing requirement interpretation, impact checking, change-method design, and code editing in one loop.
- The practical center is the three-artifact set:
  - USDM-based change requirement specification
  - traceability matrix
  - change design

Code modification should not begin until those artifacts are prepared well enough.

## Practical Four-Step View

The practical XDDP flow can be read as four steps:

1. capture and specify the change
2. identify the impacted locations
3. decide how to change them
4. implement after the difference is reviewed and stabilized

This can also be read as:

- `Why / What`: clarify the change and specification
- `Where`: identify impacted modules and files
- `How`: determine the change method
- implementation: apply the change after the difference is fixed

## Problems In Conventional Change Work

Two failure modes are emphasized:

- sequential change execution:
  - take one request
  - search for a code location
  - modify immediately
  - discover misses, interference, or side effects later
- new-development-like document updating:
  - fold the change directly into official documents and then into code
  - lose visibility of what exactly changed and how the impact propagated

In both cases, review becomes weak because the change difference is not isolated clearly enough.

## Two XDDP Processes

XDDP treats `change` and `addition` as different processes.

- change process:
  - handles changes to existing assets
  - uses explicit change artifacts before code modification
- addition process:
  - handles newly added function or feature content
  - follows the organization's normal design process after the addition scope is clarified

The two processes may proceed in parallel, but they are not treated as the same kind of work.

## Why / What: Capture The Change

The first task is to capture the concrete content of the change and define it as a change requirement specification.

Typical inputs include:

- existing specifications and design documents
- source code when documents are weak or stale
- change requests and rationale

When documents are weak or source and documents diverge, spec-out is used:

- read source code selectively
- reconstruct structure and behavior
- extract the places and items that must change
- leave a traceable investigation artifact

The captured content is then written using a structured requirement format such as USDM.

Important points:

- separate `requirements` and `specifications`
- include the reason for the change
- use `before / after` style when it helps localize impact
- make the specification concrete enough to act as an implementation instruction

## Where: Identify Impacted Locations

The traceability matrix maps the change specification to the assets affected by the change.

Typical mapping shape:

- rows: change requirements or change specifications
- columns: files, functions, modules, documents, build parameters, or other affected assets

The traceability matrix is used to confirm:

- whether the identified function or file set is sufficient
- whether other affected locations exist
- whether another change touches the same place
- whether the module structure shows high coupling or poor maintainability

The traceability matrix connects the change requirement specification and the later change design.

## How: Decide The Change Method

After impacted locations are identified, determine how each location should be changed and write it as change design.

Important points:

- write the change method in natural language before touching code
- review the change method with knowledgeable reviewers
- when argument or return-value changes are found, return to impact analysis and expand the traceability matrix
- when multiple changes overlap, consolidate them before implementation

Implementation should begin after the change requirement specification and change design have been reviewed sufficiently.

## Change Process

The change process is built around preparing the change before touching code.

Typical sequence:

1. describe the change in the change-requirement specification
2. investigate affected locations and surrounding constraints
3. extract the change-side specification caused by additions when needed
4. build the change traceability matrix
5. determine the change method in the change design
6. modify source code after the required change artifacts are aligned

This keeps code editing late and makes review possible at each stage.

## Addition Process

The addition process handles newly added function or feature content.

Typical sequence:

1. clarify the additional requirement
2. design the additional function
3. design added functions or units
4. implement the added function

This process should still fit the architecture of the existing software rather than behave like isolated greenfield work.

## Change Three-Artifact Set

XDDP emphasizes a change-oriented artifact set:

- change-requirement specification
- change traceability matrix
- change design

These artifacts together support:

- identifying change targets
- understanding impact range
- consolidating overlapping changes before code modification
- reviewing the intended difference before implementation

## Main Artifacts

### Change-Requirement Specification

- written with a requirements-structuring approach such as USDM
- expresses what is changing and why
- helps derive concrete specification changes
- often benefits from `before/after` expression to localize impact
- can act as a precise work instruction for later design and implementation

### Change Traceability Matrix

- rows represent change requirements or change specifications
- columns represent functions, source files, modules, or other affected assets
- helps expose overlap, impact spread, complexity, and possible refactoring pressure
- should focus on difference information rather than reproducing all base specifications
- bridges the change requirement specification and the change design

### Change Design

- describes the concrete change method in natural language before code editing
- should consolidate multiple overlapping changes at one location
- enables one-shot source modification instead of repeated local fixes
- should be reviewed before code editing begins

### Additional-Requirement Specification

- describes added function requirements when true addition exists
- should fit the existing system architecture

### Additional Design

- designs newly added function behavior according to the organization's design process
- should consider interaction with existing shared functions and state

### Spec-Out

- used when official documents are weak or missing
- reconstructs design-relevant structure from source code and existing evidence
- helps identify change locations and impact range under partial understanding

## XDDP Triangle

XDDP stands on two supporting techniques:

- USDM:
  - helps write requirement specifications without omission or duplication
- PFD:
  - helps design a rational development approach with minimal waste

The XDDP view is strongest when:

- requirements are structured clearly
- the development flow is designed explicitly
- derivative changes are managed through stable difference artifacts

## Benefits

- reduces mixed "while doing everything at once" work
- improves pre-code reviewability
- helps find defects before source modification
- makes defect-cause identification easier because the change method is documented
- encourages changing source code in one coordinated pass rather than repeated local edits

## Operational Implication For This Repository

For brownfield AI-assisted work, the XDDP view implies:

- treat a request as a difference, not only as a task
- make requirement difference, specification difference, and implementation difference explicit
- narrow review to the appropriateness of the difference
- preserve the mapping between change reason, change target, and change method

## Sources

- source_type: web
- source_url: https://www.exmotion.co.jp/solution/xddp-1.html
- captured_path: ../sources/web/exmotion.co.jp/xddp-1-2026-04-10.html
- captured_at: 2026-04-10
- source_type: pdf
- source_path: ../sources/pdf/xddp/ET2018_04.pdf
- source_locator: page=1-24
- extracted_at: 2026-04-10
