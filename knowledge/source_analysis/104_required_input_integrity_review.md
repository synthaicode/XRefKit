<!-- xid: 5F21C8A41104 -->
<a id="xid-5F21C8A41104"></a>

# Required Input Integrity Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## Required Input Integrity Review

When code derives billing, authorization, routing, eligibility, tax, rate,
limit, entitlement, compliance, or other decision-critical behavior from
external configuration, cache state, file/message content, DB rows, or an API,
review both visible failures and silent fallbacks.

Check paired paths for the same required input class:

- lookup that throws on missing input
- `try get`, `contains`, optional, nullable, or missing-key paths that return a
  default value
- zero, false, empty collection/string, default enum/status, null, or skipped
  branch fallback
- catch-and-default behavior after config/API/cache/file/message/DB failure

If the value is required to decide whether processing may continue, a missing
input must become a controlled outcome such as blocked, failed, needs
configuration, dead-letter, retry, quarantine, or explicit handoff. Do not
treat a syntactically valid fallback as safe merely because it does not throw.

Escalate to `major` or higher when a silent fallback can cause billing,
payment, entitlement, tax, authorization, routing, eligibility, limit, or
compliance behavior to proceed with an invented value.

Report at least:

- required input name and business decision it gates
- input source, such as cache, API, DB, file, message, or config
- missing-input behavior: throw, default substitution, catch-and-default,
  optional/default fallback, default enum/status/null/empty value, or skipped
  branch
- whether the default value is explicitly configured or invented by code
- controlled disposition that should replace the missing-input path

### Required Input Result Facts

Do not reduce this category to only "business input is present/absent" or
"library scope". The reviewer must preserve the detector facts needed to make
the decision basis visible.

Preserve this shape for report composition:

| input / candidate | decision gated | source | missing or invalid behavior | default provenance | disposition | status |
|---|---|---|---|---|---|---|

- `input / candidate`: the reviewed value, or an explicit absence row when no
  business input candidate exists in the reviewed scope.
- `decision gated`: the business decision or `none` when no business decision
  is gated in the scope.
- `source`: API, DB, config, cache, file, message, external API, or `none`.
- `missing or invalid behavior`: reject, throw, retry, dead-letter,
  quarantine, explicit handoff, default substitution, catch-and-default,
  skipped branch, or `not_applicable`.
- `default provenance`: explicitly configured, derived from source, invented
  by code, none, or unknown.
- `disposition`: pass, fail, needs_confirmation, or not_applicable with the
  absence or decision reason.
- `status`: the category status contribution for that row.

For `not_applicable`, state the absence basis. For `pass`, name the controlled
behavior found by the detector.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
