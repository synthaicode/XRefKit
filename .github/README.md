# CI workflow responsibilities

Pull requests run the following independent checks. Core and Slides also run
on pushes to `main`; Skill package push triggers use their release tag patterns.
Job names identify the target so failures can be located without confusing
Core checks with Skill package checks.

| Workflow | Responsibility |
| --- | --- |
| `python-package.yml` | Core full repository quality gate, source security and dependency audits; Core build, artifact inspection, clean wheel/sdist installation and official Skill compatibility. |
| `python-skill-brownfield-package.yml` | Brownfield package tests, build, artifact inspection and clean wheel/sdist installation. |
| `python-skill-csharp-package.yml` | CSharp package tests, build, artifact inspection and clean wheel installation. |
| `python-skill-batch-regression-package.yml` | Batch regression package tests and security audits, build, artifact inspection and clean wheel/sdist installation. |
| `xref-check.yml` (`slides-app-quality`) | Standalone Slides application quality gate, including Node dependencies. |

The full Core quality gate runs once in `python-package.yml`; the Slides
workflow does not repeat it. Package artifact inspections and installation
checks remain separate release gates and use the distributions built by their
respective build jobs. Core release compatibility checks cover both published
Skills and repository candidates, with a fresh published-Skill check before
publication.

New runs cancel older runs only for the same pull request and workflow.
Push and tag runs use a unique run ID as their concurrency group suffix, so
neither running nor pending release runs replace each other. This distinction
matters because a shared group replaces pending runs even when cancellation
of running jobs is disabled; see the [GitHub concurrency documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
Publication remains
restricted to each package's existing release tag pattern and depends on all
of its quality, inspection, installation and compatibility gates. Pull
requests do not publish packages.
