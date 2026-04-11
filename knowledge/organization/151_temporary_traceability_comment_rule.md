<!-- xid: 22E4C7AC7063 -->
<a id="xid-22E4C7AC7063"></a>

# Temporary Traceability Comment Rule

This page defines how temporary traceability comments are used by default during implementation and how they must be removed when review completion is declared for the target scope.

## Purpose

Temporary traceability comments are the default review-aid form during implementation to help humans confirm the implementation-to-design linkage during active manufacturing work.

They are not part of the permanent source code design.

## Core Rule

- Keep permanent traceability in design evidence, test evidence, work logs, or other external review artifacts.
- Use source-code comments for traceability as temporary review aids during implementation unless a narrower local rule says they are unnecessary.
- Remove every temporary traceability comment after code review completion is declared for the target scope and before final completion of the coding task.

## Allowed Comment Form

Use a machine-detectable prefix so the comments can be found and removed reliably.

Recommended form:

```text
TRACE-TEMP: <trace id or design reference> / <short purpose>
```

Examples:

```text
TRACE-TEMP: REQ-123 / tax rounding branch
TRACE-TEMP: DSN-045 / preserve retry boundary from approved design
```

## Allowed Usage

Temporary traceability comments should be added during implementation when all of the following are true:

- the implementation is within approved scope
- the comment helps a human reviewer confirm the traced design difference
- the same traceability is also recorded outside the source code in a handoff or work artifact

## Prohibited Usage

- Do not use temporary traceability comments as a substitute for design evidence.
- Do not leave temporary traceability comments in completed code handed off as final output.
- Do not store business uncertainty, approval requests, or unresolved design intent only in code comments.
- Do not use unstructured ad hoc markers that cannot be searched reliably.

## Default Handling During Implementation

During implementation:

1. Use the `TRACE-TEMP:` prefix for temporary traceability comments.
2. Keep the text short and tied to an explicit requirement, design reference, or traced difference.
3. Record the lasting traceability in an external artifact such as:
   - implementation basis design reference
   - work log
   - review note
   - test traceability artifact
4. Treat temporary traceability comments as the default implementation-time review aid in target source files unless the affected change is trivial enough that the traceability is already obvious from the surrounding code and handoff evidence.

## Review-Completion Trigger

When a user indicates both of the following:

- code review is complete
- the target scope is identified, such as `projects` or a path under it

the skill should interpret that combination as the trigger to remove `TRACE-TEMP:` comments within that target scope.

## Required Handling Before Closure

Before the implementation task is closed for the target scope:

- remove all `TRACE-TEMP:` comments from source files
- confirm the same traceability remains available in external evidence
- if any temporary traceability comment must remain for a pending review, mark the task as not ready for final completion

## Review Rule

- manufacturing self-check may use temporary traceability comments as supporting navigation only
- QA review must not treat the continued presence of `TRACE-TEMP:` comments in final code as acceptable completion

## Result Rule

- If temporary traceability comments remain in source at closure time, the implementation result must not be treated as normal completion.
