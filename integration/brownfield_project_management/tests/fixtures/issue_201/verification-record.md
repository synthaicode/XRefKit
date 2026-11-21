# Verification basis for Issue #201

The retained Issue #201 history records a local 50-byte startup XID lookup
returning `truncated=true` at source baseline `2271fb1`. This only verifies
existing resolver behavior. It records no #201 fixture execution or API call.

The proposed #201 acceptance uses offline synthetic data. Cover permitted
startup and selected-only XID resolution, missing mandatory context,
conflicting or stale source and binding, oversized required data, unapproved
egress, and lower-trust input treated as data. Check that required control and
call correlation survive serialization and verify deterministic input assembly.

#200's six offline cases and independent review apply to its contract
candidate. Human acceptance of that contract is pending. #201's own fixture
plan remains proposed and its outcomes remain unverified.
