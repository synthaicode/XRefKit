"""Generate native package assets from canonical sources, or check exact parity."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml
# Tag checks run before installing Core. Use this checkout's stdlib-only
# governance validator rather than depending on an unrelated installed Core.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from xrefkit.skill_definition_governance import validate_governance_record

SKILLS = ("progress_rules_setup", "requirements_discovery_coordination", "work_progress_coordination", "pm_coordination_setup", "pm_decision_coordination")
PACKAGE = "packages/xrefkit-skills-project-management/src/xrefkit_skills_project_management"


def source_assets(root: Path):
    sources = [f"skills/packs/project-management/{sid}/SKILL.v1.md" for sid in SKILLS]
    sources += ["skills/packs/project-management/progress_rules_setup/references/persistence_handoff.md",
                "docs/packs/project-management/entry.md", "docs/packs/project-management/scheduling.md",
                "skills/packs/project-management/pack.md",
                "observations/2026-11-14_project_management_trial_authoring.md"]
    mapped = set(sources)
    result: dict[str, bytes] = {}
    provenance = []
    for relative in sources:
        path = root / relative
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        def link(match: re.Match) -> str:
            label, target, xid = match.groups()
            if "://" in target:
                return match.group(0)
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                raise ValueError(f"unresolved source link in {relative}: {target}")
            destination = resolved.relative_to(root.resolve()).as_posix()
            if destination in mapped:
                return match.group(0)
            return f"[{label}](https://github.com/synthaicode/XRefKit/blob/main/{destination}#xid-{xid})"
        text = re.sub(r"\[([^\]]+)\]\(([^)#]+)#xid-([A-F0-9]{12})\)", link, text)
        body = text.encode("utf-8")
        result[relative] = body
        provenance.append({"source": relative, "source_sha256": hashlib.sha256(raw).hexdigest(),
                           "packaged_sha256": hashlib.sha256(body).hexdigest()})
    return result, provenance


def generate(root: Path) -> dict[str, bytes]:
    result, provenance = source_assets(root)
    provided = []
    for sid in SKILLS:
        path = f"skills/packs/project-management/{sid}/SKILL.v1.md"
        meta = yaml.safe_load(result[path].decode("utf-8").split("---", 2)[1])
        gp = f"governance/skills/{sid}.json"
        governance = json.loads((root / gp).read_text(encoding="utf-8"))
        validate_governance_record(governance)
        if governance["skill_id"] != sid or governance["definition_xid"] != meta["xid"]:
            raise ValueError(f"canonical governance identity mismatch: {sid}")
        canonical_hash = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if governance["definition_content_hash"] != canonical_hash:
            raise ValueError(f"canonical governance is stale: {sid}")
        if result[path] != (root / path).read_bytes() and (
            governance["maturity"] != "draft" or governance["promotion"]["decision"] != "not_requested"
        ):
            separate = root / f"governance/packages/project-management/{sid}.json"
            if not separate.is_file():
                raise ValueError(f"transformed approved source needs separate package governance: {sid}")
            packaged = json.loads(separate.read_text(encoding="utf-8"))
            validate_governance_record(packaged)
            if any(packaged[k] != governance[k] for k in governance if k != "definition_content_hash"):
                raise ValueError(f"separate package governance differs from approved source scope: {sid}")
            if packaged["definition_content_hash"] != hashlib.sha256(result[path]).hexdigest():
                raise ValueError(f"separate package governance is stale: {sid}")
            governance = packaged
        else:
            governance["definition_content_hash"] = hashlib.sha256(result[path]).hexdigest()
        for reference in governance["observation_refs"] + governance["promotion"]["basis_refs"]:
            if reference not in result or not reference.startswith("observations/"):
                raise ValueError(f"promotion evidence must be bundled: {reference}")
        result[gp] = (json.dumps(governance, indent=2) + "\n").encode()
        provided.append({"id":sid,"xid":meta["xid"],"path":path,"governance_path":gp})
    manifest = {"package_id":"xrefkit.skills.project_management","package_type":"skill_package",
                "version":"0.1.0","requires":{"xrefkit_core":">=2.0.0 <3.0.0"},
                "provides":{"skills":provided},"contract":{},
                "metadata":{"display_name":"Project Management","maturity_note":"trial; authoring/readiness bootstrap, not operational validation",
                            "routing_entry":"docs/packs/project-management/entry.md"}}
    result["package_manifest.yaml"] = yaml.safe_dump(manifest,sort_keys=False).encode()
    result["source_manifest.json"] = (json.dumps({"schema_version":1,"sources":provenance,
        "transform":"repository-external XID links become navigation URLs; packaged governance rebinds exact transformed bytes"},indent=2)+"\n").encode()
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    target=args.root/PACKAGE
    expected=generate(args.root.resolve())
    mismatches=[]
    for scope in ("skills", "governance", "docs", "observations"):
        for path in (target/scope).rglob("*"):
            if path.is_file() and path.relative_to(target).as_posix() not in expected:
                mismatches.append("unexpected managed asset: " + path.relative_to(target).as_posix())
    if mismatches:
        raise SystemExit("stale packaged assets: " + ", ".join(mismatches))
    for relative,body in expected.items():
        path=target/relative
        if args.check:
            if not path.is_file() or path.read_bytes()!=body: mismatches.append(relative)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(body)
    if mismatches:
        raise SystemExit("stale packaged assets: " + ", ".join(mismatches))
    print(f"{'Checked' if args.check else 'Generated'} {len(expected)} package assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
