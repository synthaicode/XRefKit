<!-- xid: D6AFA8483950 -->
<a id="xid-D6AFA8483950"></a>

# Dev.to Check Spec (publisher guide)

This page defines the check specification used by `devto_check`.
It is derived from the publisher guide source.

## Scope

- pre-publish quality check for Dev.to articles
- title quality and CTR-oriented patterns
- structural clarity and trust/safety checks
- publish timing guardrails

## Required Checks

1. Title quality
   - prefer number-based or concrete-value patterns
   - include clear value/action signal (verb or strong value adjective)
   - avoid gerund-start titles (`...ing`)
   - target length around 40-60 chars
2. Content structure
   - clear flow: problem -> approach -> result
   - concrete, actionable steps
   - no abstract-only claims
3. Trust and safety
   - no fabricated facts
   - assumptions and limits are explicit
   - uncertainty is surfaced explicitly when facts are unverified
4. Timing check
   - avoid major holidays and low-traffic windows
5. Verdict
   - `PASS` only if no blocking issues
   - otherwise `REVISE` with concrete fixes

## Output Contract

- checklist results by category
- blocking issues
- non-blocking improvements
- revised title candidates (3-5)
- final verdict (`PASS` or `REVISE`)

## Source

- source_type: markdown
- source_path: ../sources/devto/devto-publisher-guide.md
