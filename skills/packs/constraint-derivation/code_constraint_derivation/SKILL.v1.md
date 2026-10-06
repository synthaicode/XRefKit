---
schema_version: 1
skill_id: code_constraint_derivation
xid: 7C4E9A1B2D60
aliases:
  - D4701BFC6EA4
  - D4701BFC6EA5
summary: derive hidden assumptions and selected business constraints from explicit C# code choices
applies_when:
  - AI-generated or manually reviewed C# code may embed asymmetric branches, implicit preconditions, or hidden business thresholds that need human confirmation
exclusions:
  - Generic runtime possibilities without an explicit code choice are outside this Skill
  - Language-level exception noise is outside business constraint derivation
  - Implementation policy is not decided unless explicitly requested
inputs:
  - C# code files
  - optional target classes or methods
  - optional related design context
outputs:
  - CCD-prefixed derivation basis table written to a Markdown file
  - high-priority business-layer confirmation items
  - implementation-layer notes when justified
  - written output path
criteria:
  - id: explicit_code_choice
    statement: Every derivation is grounded in an explicit code choice such as a guard, branch, threshold, silent failure, multiplicity assumption, transaction span, or visibility choice
    verification: Inspect each derivation against the cited code evidence and record unsupported interpretations as unresolved
  - id: confirmation_boundary
    statement: Signals are classified as business-layer confirmation or implementation-layer recording
    verification: Review the classification and hand off unsupported business meaning rather than inferring it
  - id: output_closure
    statement: The derivation file exists at the declared output path and reports high-priority confirmation items and remaining gaps
    verification: Check the output path and closure report before handing off
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for deriving and classifying code-choice signals
    seed_xids:
      - 81A6C4E2B190
  - id: code_constraint_derivation_catalog
    query: code constraint derivation catalog
    required_when: Required for selecting applicable code signal categories
    seed_xids:
      - A1D4E8C93B71
control_refs:
  - 111D282CA0EA
---
<!-- xid: 7C4E9A1B2D60 -->
<a id="xid-7C4E9A1B2D60"></a>

# Skill: code_constraint_derivation

## Purpose

Derive hidden assumptions and selected business constraints from explicit C#
code choices without treating generic runtime possibilities as business
signals.

## Inputs

- C# code files
- optional target classes or methods
- optional related design context

## Outputs

- CCD-prefixed derivation basis table written to a Markdown file
- high-priority confirmation items
- implementation-layer notes when justified
- written output path

## Startup

- Confirm the code input exists.
- Load the framework and the code-constraint catalog.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_code_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Detect explicit code-choice signals such as guard-plus-throw, silent failure, multiplicity assumptions, magic values, transaction spans, and visibility choices.
2. Ignore generic runtime possibilities that do not represent an explicit code choice.
3. Classify each signal by whether it requires business-layer confirmation or implementation-layer recording.
4. Write the result by using `references/upward_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not turn generic exceptions such as overflow or out-of-memory into business confirmation items.
- Stop if the interpretation depends on business meaning that is not supported by the code shape.

## Closure

- Return the written derivation path.
- Return the high-priority confirmation items and remaining gaps.
