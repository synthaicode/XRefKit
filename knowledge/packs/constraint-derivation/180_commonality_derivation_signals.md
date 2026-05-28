<!-- xid: 9C27AE51D648 -->
<a id="xid-9C27AE51D648"></a>

# Commonality Derivation Signals

## Signal Groups

### Repeated confirmation items

| Signal | Detection condition | Candidate kind |
|---|---|---|
| repeated zero-result behavior | zero-result behavior appears in three or more places | common zero-result handler |
| repeated error code | the same error code is confirmed in multiple places | shared error response or constant |
| repeated validation rule | the same max length, format, or range appears repeatedly | shared validation function |
| repeated null handling | the same null-path behavior appears repeatedly | null object or default rule |
| repeated timeout value | the same timeout value appears across integrations | shared timeout constant |

### Repeated error-handling patterns

| Signal | Detection condition | Candidate kind |
|---|---|---|
| unified auth error | many APIs define the same unauthorized behavior | auth filter or middleware |
| unified FK violation | many tables define the same missing-reference behavior | shared FK handler |
| unified retry policy | the same retry count and interval appear repeatedly | shared retry policy |
| unified rollback unit | multiple batch flows use the same full rollback behavior | shared transaction policy |

### Repeated cross-cutting concerns

| Signal | Detection condition | Candidate kind |
|---|---|---|
| repeated session checks | session verification appears across many APIs | auth interceptor |
| repeated audit logging | operation logs are confirmed in many places | shared audit service |
| repeated failure notification | the same admin notification pattern repeats | shared notification service |
| repeated optimistic locking | many updates confirm the same conflict handling | shared lock-conflict handler |

### Repeated state patterns

| Signal | Detection condition | Candidate kind |
|---|---|---|
| repeated status pattern | multiple entities use the same status structure | shared status component |
| repeated approval flow | many entities share similar approval steps | workflow engine |
| repeated logical delete | many tables confirm the same logical-delete semantics | shared delete filter |

### Scope-boundary ambiguity

| Signal | Detection condition | Boundary check |
|---|---|---|
| multiple paths to same data | different APIs update the same field | ownership of consistency and conflict handling |
| duplicated validation | UI and API both confirm the same validation | which layer is canonical and whether duplication is intentional |
| duplicate notifications | different triggers may send the same notification | duplicate notification prevention ownership |

## Priority Rule

- three or more appearances: strong commonality candidate
- two appearances: weak candidate worth confirmation
- one appearance: no commonality flag

## Output Shape

- `CD-` table for commonality candidates
- `CB-` table for scope-boundary checks
- explicit benefits and non-integration risks for every `CD-` item
