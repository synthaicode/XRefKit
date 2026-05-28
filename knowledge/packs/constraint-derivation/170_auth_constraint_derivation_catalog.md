<!-- xid: 8B14D9E70326 -->
<a id="xid-8B14D9E70326"></a>

# Auth Constraint Derivation Catalog

## Derivation Areas

| Design element | Confirm as requirement | Decision class |
|---|---|---|
| login flow | lockout threshold and unlock method | requirement |
| session | timeout period, timeout-response behavior, multi-login policy | requirement |
| token auth | refresh policy and expired-refresh behavior | requirement |
| password lifecycle | expiration, forced change, reset verification | requirement |
| role definition | unauthorized response style and unassigned-role behavior | requirement |
| multi-role user | rule for combining permissions | requirement |
| data access control | behavior for another user's or another tenant's data | requirement |
| hidden-vs-forbidden target | `404` vs `403` behavior for out-of-scope direct access | requirement |
| update without write right | behavior on direct API invocation beyond read-only rights | requirement |
| API key | expired key, rate limit, and out-of-scope operation behavior | requirement |
| client certificate | behavior on revoked certificate | requirement |
| account disable | behavior for still-active sessions | requirement |
| account delete | treatment of retained data and historical ownership display | requirement |
| last admin account | behavior when the final admin tries self-removal | requirement |

## Matrix Guidance

- Expand a permission matrix whenever role and operation combinations are explicit.
- Expand a session-state matrix whenever multiple invalid session modes exist.

## Output Shape

- derivation basis table with `AACD-` ids
- grouped confirmation items by auth surface
- explicit permission or session matrix when required

