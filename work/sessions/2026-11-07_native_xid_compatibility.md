# Native XID package compatibility correction

Basis: released Core 0.7.8 rejected the official Brownfield 0.1.6 package
during MCP startup. Its six Knowledge declarations use `xid-` plus twelve
uppercase hexadecimal digits; the Markdown comments contain the same native
digits without that anchor prefix. Csharp 0.1.4 semantic identifiers are unchanged.

Correction: compare Markdown source identity with the optional legacy prefix
only for the exact twelve-uppercase-hexadecimal form. Preserve manifest IDs and
exact lookup keys. Apply the same bounded interpretation to embedded startup
protection, so the prefixed form cannot bypass that protection. Different hex
values, semantic IDs with extra prefixes, and suffix extensions still fail.
This does not introduce arbitrary suffix matching or catalog-wide alias lookup.

Validation environment: isolated C:/dev/itsm/xrefkit-079-smoke, Python 3.12,
official Brownfield 0.1.6 and Csharp 0.1.4 installed together, candidate Core
0.7.9. Existing real MCP subprocess tests perform startup, run binding, all
declared Knowledge retrieval/expansion (including Csharp review specification),
axes/schema retrieval and required-slot resolution. New regressions cover both
native prefix directions, different hex, semantic-prefix and suffix mismatches,
and prefixed embedded-startup rejection.

Candidate wheel SHA256:
afdf207294ebc262f237e7c6606fc68432ba5b629ecb914862d2e0f6e47c2226.
Parent and independent reviewer own installed-wheel Python 3.14 verification
and release. Windows symlink creation remains unavailable in the local suite;
no containment source changes were made in this correction.

Results: focused suite 22 passed, 2 skipped (Windows symlink and absent unrelated
batch package); routing suite 2 passed; standalone combined MCP probe 33 checks
passed. Compile and diff checks passed. Independent Python 3.14 wheel review
reproduced 0.7.8 startup failure and passed 29 actual MCP checks with 0.7.9;
its narrow guard suite passed 20 with 1 skipped. CI now installs the built Core
wheel and pinned official combination and runs the standalone MCP probe in a
temporary consumer directory, without PYTHONPATH injection.
