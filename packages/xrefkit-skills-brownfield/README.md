# xrefkit-skills-brownfield

Public XRefKit Skill Package for brownfield change work.

The package provides `brownfield.workflow`, which carries upstream work items
through requirements, planning, design, manufacturing, and testing. Each phase
returns a summary first and exposes unresolved items explicitly.

Compatibility: requires XRefKit >=0.6.1,<0.7.0 and Python >=3.11.
The manifest requirement >=2.0.0 <3.0.0 names the Core protocol,
separately from the Python distribution version. The installed-package tests
exercise discovery, manifest/Skill schemas, contract inheritance, required
Knowledge and review-axis resolution, and all packaged workflow references
against the published XRefKit 0.6.1 runtime.

The six directly required Knowledge fragments are included. Their further
XID links remain lookup handles for the host's knowledge provider; this package
does not bundle the entire repository corpus or a project's system evidence.
The deterministic checks do not certify AI judgments or business-specific
execution of all five phases.
