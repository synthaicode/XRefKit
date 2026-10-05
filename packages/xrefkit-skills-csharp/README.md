# xrefkit-skills-csharp

Text-only XRefKit Skill Package for C# and .NET analysis.

This package exposes `package_root()` through the `xrefkit.skill_packages`
entry point group so XRefKit can discover `package_manifest.yaml`.

It does not include executable tools.

Compatibility: requires XRefKit >=0.6.1,<0.7.0 and Python >=3.11.
The manifest requirement >=2.0.0 <3.0.0 refers to the Skill Package
core protocol, separately from the Python distribution version.
