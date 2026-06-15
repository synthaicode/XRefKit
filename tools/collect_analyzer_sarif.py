"""Collection stage: run a Roslyn analyzer build and emit SARIF v2.1 for the
131 normalizer (``tools/sarif_to_locator.py``).

This is the missing front of the pipeline:

    collect_analyzer_sarif.py  ->  <project>.sarif (v2.1)  ->  sarif_to_locator.py  ->  131 candidates

Verified incantation (2026-06-15, .NET SDK 10.0.301): the MSBuild ``ErrorLog``
property defaults to **SARIF v1.0.0**, which the normalizer rejects as a
collection error. To get v2.1 the comma before ``version`` MUST be escaped as
``%2c`` so MSBuild does not split the property value:

    -p:ErrorLog=<file>%2cversion=2.1

The collection profile (severity for *collection*, not the project's build
policy) lives in ``tools/profiles/error_policy_collection.editorconfig``; pass
a ruleset via ``--ruleset`` or apply the editorconfig in the target tree.
Enabling default-off rules (e.g. CA1849) through a build profile is not yet
verified here and is a follow-up.

This module builds/runs the command; it does not parse SARIF (that is the
normalizer's job).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def build_command(
    target: str,
    out_sarif: str,
    *,
    config: str = "Debug",
    ruleset: str | None = None,
    extra_props: dict[str, str] | None = None,
) -> list[str]:
    """Return the `dotnet build` argv that emits SARIF v2.1 to out_sarif.

    The ``%2c`` in the ErrorLog value is intentional: MSBuild decodes it to a
    comma so csc receives ``ErrorLog=<file>,version=2.1``. Passing a literal
    comma makes MSBuild split the value and the build silently falls back to
    SARIF v1.0.0.
    """
    cmd = [
        "dotnet",
        "build",
        target,
        "-c",
        config,
        "--no-incremental",
        "-p:EnableNETAnalyzers=true",
        "-p:RunAnalyzersDuringBuild=true",
        f"-p:ErrorLog={out_sarif}%2cversion=2.1",
    ]
    if ruleset:
        cmd.append(f"-p:CodeAnalysisRuleSet={ruleset}")
    for key, value in (extra_props or {}).items():
        cmd.append(f"-p:{key}={value}")
    return cmd


def collect(
    target: str,
    out_sarif: str,
    *,
    config: str = "Debug",
    ruleset: str | None = None,
    run: bool = False,
) -> dict:
    cmd = build_command(target, out_sarif, config=config, ruleset=ruleset)
    result = {"command": cmd, "ran": run, "sarif": out_sarif}
    if run:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        result["returncode"] = proc.returncode
        result["sarif_exists"] = Path(out_sarif).exists()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a C# target with analyzers and emit SARIF v2.1 for the 131 normalizer"
    )
    parser.add_argument("target", help="path to .csproj or .sln")
    parser.add_argument("--out", required=True, help="output SARIF path")
    parser.add_argument("--config", default="Debug")
    parser.add_argument("--ruleset", default=None, help="optional .ruleset collection profile")
    parser.add_argument("--run", action="store_true", help="execute the build (default: print command only)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = collect(args.target, args.out, config=args.config, ruleset=args.ruleset, run=args.run)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("command:", " ".join(result["command"]))
        if result["ran"]:
            print(f"returncode: {result['returncode']}  sarif_exists: {result['sarif_exists']}")
            print(f"next: python tools/sarif_to_locator.py {args.out} --root <repo>")
        else:
            print("(dry run; pass --run to execute, then feed --out to sarif_to_locator.py)")

    # collection failure is reported via returncode but the locator never auto-fails downstream
    if result.get("ran") and result.get("returncode") not in (0, None) and not result.get("sarif_exists"):
        return result["returncode"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
