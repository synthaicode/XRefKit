<!-- xid: 7A2F4C8D1711 -->
<a id="xid-7A2F4C8D1711"></a>

# XDDP Supporting Methods

This page summarizes the two supporting methods described as foundations of XDDP: `USDM` and `PFD`.

## Purpose

Explain how XDDP is supported by methods that strengthen requirement precision and process-design rationality in derivative development.

## Core Position

XDDP is supported by two methods:

- `USDM`
- `PFD`

These methods support typical derivative-development constraints such as:

- short delivery time
- partial understanding of the whole system
- risk of assumptions and misunderstandings during change work

## USDM

USDM is used to express requirements and specifications in a structured way.

Main points:

- specifications are treated as being primarily embedded in the verbs inside requirements
- requirements and specifications are expressed in a hierarchical structure
- specification extraction is moved earlier, into requirement definition rather than delayed until later design

For change work, this supports:

- separating `change requirement` and `change specification`
- expressing change with `before / after`
- reducing omission and duplication in change specification
- clarifying the reason for change

Operational implication:

- a high-precision change requirement specification reduces later specification drift
- clearer requirement/specification structure makes change control more effective under short schedules

## PFD

PFD is used to design a rational process and artifact chain.

Main points:

- it expresses the generation relationship between artifacts and processes
- it shows which process creates which artifact and from which prior artifacts
- it only works fully when the artifact definitions and process definitions are written alongside the diagram

This supports:

- discovering missing process steps
- discovering when the target artifact cannot actually be generated from the current process
- reducing wasteful work
- adjusting estimates and progress management based on artifact-size and process linkage

## Combined Role In XDDP

Together, USDM and PFD support XDDP by making:

- requirement and specification precision stronger
- process and artifact linkage more rational
- change impact handling more controlled
- short-schedule derivative work less dependent on guesswork

In short:

- `USDM` supports accurate specification capture
- `PFD` supports rational process and artifact sequencing
- `XDDP` uses both to make derivative change work stable

## Operational Implication For This Repository

For this repository, the two-method view implies:

- use structured requirement and specification separation when defining change artifacts
- keep artifact-to-process relationships explicit in `flows/` and related docs
- do not treat impact analysis as an informal coding-side activity
- use artifact linkage to narrow review scope to the intended difference

## Sources

- source_type: web
- source_url: https://affordd.jp/derivative-development/xddp/method/
- captured_path: ../sources/web/affordd.jp/xddp-method-2026-04-10.html
- captured_at: 2026-04-10
