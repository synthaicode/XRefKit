# xrefkit-skills-brownfield

Public XRefKit Skill Package for brownfield change work.

The package provides `brownfield.workflow`, which carries upstream work items
through requirements, planning, design, manufacturing, and testing. Each phase
returns a summary first and exposes unresolved items explicitly.

Four individual Skills are available at trial maturity:

- `investigation_flow` scopes a change investigation and records its evidence.
- `requirements_flow` drafts requirements and preserves explicit differences.
- `design_flow` prepares review-ready design and test handoff.
- `db_current_state_analysis` documents existing database and persistence behavior.

Compatibility requires XRefKit >=0.7.10,<0.8.0 and Python >=3.11.
The manifest requirement >=2.0.0 <3.0.0 names the Core protocol.
The installed-package tests exercise discovery, contract inheritance, native
Skill governance, and Knowledge resolution.

Directly required Knowledge fragments are included. Their further
XID links remain lookup handles for the host's knowledge provider; this package
does not bundle the entire repository corpus or a project's system evidence.
The deterministic checks do not certify AI judgments or business-specific
execution of all five phases.
