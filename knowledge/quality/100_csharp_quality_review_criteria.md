<!-- xid: 8C4D2A7E5101 -->
<a id="xid-8C4D2A7E5101"></a>

# CSharp Quality Review Criteria

This page defines C# review criteria for quality checks used by manufacturing self-check and quality review.

## Scope

The target review domains are:

- code quality
- performance
- security
- license

## Code Quality

Check the following items.

| Item | What to confirm |
|------|-----------------|
| Design alignment | implementation stays within approved design boundaries |
| Readability | names, structure, and control flow remain understandable |
| Error handling | exceptions are handled or propagated intentionally |
| Testability | code can be unit-tested without unreasonable coupling |
| Dependency control | new dependencies are necessary and explicitly justified |
| Attribute necessity | unnecessary attributes are not added to types, members, or parameters |
| Attribute value correctness | attribute values are appropriate for the intended behavior |
| Attribute usage correctness | attributes are applied in the correct location and usage pattern |
| Dead code | no unused or abandoned logic is silently introduced |
| Unknowns | evidence gaps are recorded explicitly instead of guessed |

## Performance

Check the following items.

| Item | What to confirm |
|------|-----------------|
| Allocation behavior | avoid unnecessary allocations in hot paths |
| Collection usage | collection choice matches access and mutation patterns |
| I/O and network usage | no avoidable repeated I/O, blocking, or chattiness |
| Database access | queries, batching, and round-trips are reasonable |
| Async behavior | async code does not block synchronously without justification |
| Throughput risk | obvious bottlenecks are identified and recorded |
| Measurement evidence | when performance claims are made, evidence or assumptions are explicit |

## Security

Check the following items.

| Item | What to confirm |
|------|-----------------|
| Input handling | untrusted input is validated, normalized, or constrained |
| Secrets handling | secrets are not hardcoded or logged improperly |
| Auth and authz | authorization expectations are preserved |
| Data protection | sensitive data is encrypted, masked, or protected as required |
| Dependency risk | introduced packages do not create known security concerns without review |
| Logging safety | logs do not leak credentials or sensitive values |
| Security unknowns | unresolved security evidence gaps are recorded explicitly |

## License

Check the following items.

| Item | What to confirm |
|------|-----------------|
| Package license | newly added packages have acceptable licenses |
| License compatibility | package licenses do not conflict with project constraints |
| Notice obligations | notice or attribution obligations are identified |
| Source provenance | copied or adapted code has traceable provenance |
| Review escalation | uncertain license status is recorded and escalated |

## Result Rule

- Every finding must cite evidence.
- If evidence is insufficient, record `unknown`.
- Confidence `2` or below must not be treated as normal completion.

