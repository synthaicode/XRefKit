<!-- xid: 5F21C8A41106 -->
<a id="xid-5F21C8A41106"></a>

# Time And Culture Review

Language-neutral criteria for this review axis. Apply with the structural
viewpoints and Planning / Unknown rules in
[Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001).
This topic is required when its review axis is active; a headline purpose does
not disable other active axes. The active Skill owns report composition.

## Time And Culture Review

Check at least the following:

- mixing local and UTC time in the same comparison, storage, scheduling, or
  retention flow
- missing or inconsistent timezone metadata across boundaries
- timezone and DST assumptions, including local-time arithmetic across DST
  transitions and server-timezone dependence in stored timestamps
- culture-sensitive formatting, parsing, comparison, collation, decimal, or
  calendar behavior used in protocol, persistence, serialization, or
  interchange contexts where invariant or explicitly configured behavior is
  required

Classify as `needs_confirmation` when the execution environment's timezone,
culture, collation, or calendar configuration cannot be established from local
evidence.

## Knowledge Relations

- part_of: [Common source analysis criteria](100_common_source_analysis_criteria.md#xid-5F21C8A41001)
