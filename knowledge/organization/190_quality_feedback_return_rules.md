<!-- xid: 7A2F4C8D1901 -->
<a id="xid-7A2F4C8D1901"></a>

# Quality Feedback Return Rules

This fragment defines the standard loop between quality review and
implementation work.

## Rule

When a quality review, source review, or gate check finds a concrete issue in
an implementation artifact, the issue is returned to the implementation owner
as a feedback item.

The implementation owner handles the item directly when all of the following
are true:

- the issue is concrete and evidence-backed
- the intended fix stays inside the approved implementation scope
- no tradeoff exists between this item and another active finding
- no design, requirement, release, security, or business decision is required
- no dependency or license decision is required

If any condition does not hold, implementation must not decide locally. The
item is escalated to the responsible design, quality, release, security,
business, or coordination owner.

## Required Feedback Shape

Quality-side feedback must preserve:

- finding id
- severity or gate impact
- evidence path and line when possible
- violated condition
- remediation direction
- whether the item is implementation-local or requires escalation
- any dependency on pending runtime, integration, or manual validation

Implementation-side response must preserve:

- linked source finding id
- fix or explicit non-fix disposition
- tradeoff assessment
- verification evidence
- handoff back to the quality source

## Pending Test Boundary

Pending runtime, integration, or manual tests do not block source-quality
review by themselves. Quality can still review source artifacts and return
source findings to implementation.

Pending tests remain visible as validation handoff items. They are not used to
hide source findings, and source findings are not used to claim runtime
validation is complete.

## Tradeoff Rule

When multiple findings conflict, implementation records the conflict and
escalates instead of choosing locally.

When no conflict exists, implementation fixes the findings within scope and
returns evidence to the quality owner for re-disposition.

## Recheck Rule

After implementation returns a fix response, the quality source must re-run the
relevant quality check or explicitly re-dispose the original finding from the
new evidence before the source-quality gate can proceed.

Implementation may provide verification evidence, but implementation does not
approve its own quality finding closure. The quality owner records the final
disposition as `pass`, `pass-after-fix`, `needs-review`, `escalated`, or the
local gate vocabulary used by that review Skill.
