from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import XRefCatalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit-mcp-catalog")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_repo_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("--repo", required=True)
        command.add_argument(
            "--domain-knowledge-root",
            action="append",
            default=[],
            help="External XID-addressable domain knowledge root. Can be repeated.",
        )

    catalog = sub.add_parser("catalog", help="build and print catalog summary")
    add_repo_arguments(catalog)

    identity = sub.add_parser(
        "repository-identity",
        help="print the repository cache identity",
    )
    add_repo_arguments(identity)

    startup = sub.add_parser("startup-context", help="print required startup references")
    add_repo_arguments(startup)

    pack_hashes = sub.add_parser(
        "startup-pack-hashes",
        help="print the Based On hash lines for the startup contract pack document",
    )
    add_repo_arguments(pack_hashes)

    pack_check = sub.add_parser(
        "check-startup-pack",
        help="exit non-zero when the startup contract pack is stale against its sources",
    )
    add_repo_arguments(pack_check)

    knowledge = sub.add_parser("search-knowledge", help="search knowledge catalog")
    add_repo_arguments(knowledge)
    knowledge.add_argument("--query", required=True)
    knowledge.add_argument("--limit", type=int, default=10)

    expand = sub.add_parser("expand-knowledge", help="expand one knowledge body")
    add_repo_arguments(expand)
    expand.add_argument("--xid", required=True)

    document = sub.add_parser("get-document", help="expand any managed Markdown document by XID")
    add_repo_arguments(document)
    document.add_argument("--xid", required=True)
    document.add_argument("--known-version")

    context = sub.add_parser("build-knowledge-context", help="expand bounded knowledge context")
    add_repo_arguments(context)
    context.add_argument("--query", required=True)
    context.add_argument("--limit", type=int, default=5)

    skills = sub.add_parser("list-skills", help="list Skill catalog")
    add_repo_arguments(skills)
    skills.add_argument("--limit", type=int)
    skills.add_argument(
        "--include-content",
        action="store_true",
        help="Include full meta.md and SKILL.md bodies (metadata-only by default)",
    )

    skill = sub.add_parser("get-skill", help="get one Skill catalog entry with transferred content")
    add_repo_arguments(skill)
    skill.add_argument("--skill-id", required=True)

    prepare_edit = sub.add_parser("prepare-skill-edit", help="copy a Skill into a local editable overlay")
    add_repo_arguments(prepare_edit)
    prepare_edit.add_argument("--skill-id", required=True)
    prepare_edit.add_argument("--package-id")

    edits = sub.add_parser("list-skill-edits", help="list local Skill edit overlays")
    add_repo_arguments(edits)

    export_edit = sub.add_parser("export-skill-edit", help="produce an upstream diff for a local Skill edit")
    add_repo_arguments(export_edit)
    export_edit.add_argument("--skill-id", required=True)
    export_edit.add_argument("--write-patch", action="store_true")

    deactivate_edit = sub.add_parser("deactivate-skill-edit", help="stop using a local Skill edit")
    add_repo_arguments(deactivate_edit)
    deactivate_edit.add_argument("--skill-id", required=True)

    create_knowledge = sub.add_parser("create-local-knowledge", help="create a project-local Knowledge document")
    add_repo_arguments(create_knowledge)
    create_knowledge.add_argument("--xid", required=True)
    create_knowledge.add_argument("--content-file", required=True)
    create_knowledge.add_argument("--filename")
    create_knowledge.add_argument("--domain")

    local_knowledge = sub.add_parser("list-local-knowledge", help="list local Knowledge additions")
    add_repo_arguments(local_knowledge)

    export_knowledge = sub.add_parser("export-local-knowledge", help="produce an upstream diff for local Knowledge")
    add_repo_arguments(export_knowledge)
    export_knowledge.add_argument("--xid", required=True)
    export_knowledge.add_argument("--write-patch", action="store_true")

    deactivate_knowledge = sub.add_parser("deactivate-local-knowledge", help="stop using local Knowledge")
    add_repo_arguments(deactivate_knowledge)
    deactivate_knowledge.add_argument("--xid", required=True)

    rank = sub.add_parser("rank-skills", help="rank Skill candidates for a purpose")
    add_repo_arguments(rank)
    rank.add_argument("--purpose", required=True)
    rank.add_argument("--limit", type=int, default=5)

    contracts = sub.add_parser("tool-contracts", help="list read-only tool contracts")
    add_repo_arguments(contracts)

    tool_manifest = sub.add_parser("client-tool-manifest", help="list distributable client-side tool files")
    add_repo_arguments(tool_manifest)

    tool_file = sub.add_parser("get-client-tool-file", help="get one distributable client-side tool file")
    add_repo_arguments(tool_file)
    tool_file.add_argument("--path", required=True)

    tool_bundle = sub.add_parser("client-tool-bundle", help="get all distributable client-side tool files")
    add_repo_arguments(tool_bundle)

    tool_package = sub.add_parser("client-tool-pip-package", help="get a pip-installable client tool package")
    add_repo_arguments(tool_package)

    version_check = sub.add_parser("check-client-tool-versions", help="check installed client tool versions")
    add_repo_arguments(version_check)
    version_check.add_argument(
        "--installed",
        action="append",
        default=[],
        help="Installed package version as package_id=version. Can be repeated.",
    )

    args = parser.parse_args(argv)
    model = XRefCatalog.build(
        Path(args.repo),
        args.domain_knowledge_root,
        discover_packages=args.command == "prepare-skill-edit",
    )

    if args.command == "catalog":
        payload = {
            "catalog_version": model.catalog_version,
            "knowledge_count": len(model.knowledge),
            "skill_count": len(model.skills),
            "tool_contract_count": len(model.tools),
        }
    elif args.command == "repository-identity":
        payload = model.get_repository_identity()
    elif args.command == "startup-context":
        payload = model.get_startup_context()
    elif args.command == "startup-pack-hashes":
        references = model.get_startup_context()["references"]
        for reference in references:
            print(f"- {reference['xid']}: `{reference['content_hash']}`")
        return 0
    elif args.command == "check-startup-pack":
        pack = model.get_startup_context()["startup_contract_pack"]
        payload = {
            "pack_source": pack["pack_source"],
            "pack_doc_xid": pack["pack_doc_xid"],
            "stale": pack["stale"],
            "stale_sources": pack["stale_sources"],
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 1 if pack["stale"] else 0
    elif args.command == "search-knowledge":
        payload = model.search_knowledge_catalog(args.query, args.limit)
    elif args.command == "expand-knowledge":
        payload = model.expand_knowledge(args.xid)
    elif args.command == "get-document":
        payload = model.get_document_by_xid(args.xid, args.known_version)
    elif args.command == "build-knowledge-context":
        payload = model.build_knowledge_context(args.query, args.limit)
    elif args.command == "list-skills":
        payload = model.list_skills(args.limit, args.include_content)
    elif args.command == "get-skill":
        payload = model.get_skill(args.skill_id)
    elif args.command == "prepare-skill-edit":
        payload = model.prepare_skill_edit(args.skill_id, args.package_id)
    elif args.command == "list-skill-edits":
        payload = model.list_skill_edits()
    elif args.command == "export-skill-edit":
        payload = model.export_skill_edit(args.skill_id, args.write_patch)
    elif args.command == "deactivate-skill-edit":
        payload = model.deactivate_skill_edit(args.skill_id)
    elif args.command == "create-local-knowledge":
        content = Path(args.content_file).read_text(encoding="utf-8")
        payload = model.create_local_knowledge(args.xid, content, args.filename, args.domain)
    elif args.command == "list-local-knowledge":
        payload = model.list_local_knowledge()
    elif args.command == "export-local-knowledge":
        payload = model.export_local_knowledge(args.xid, args.write_patch)
    elif args.command == "deactivate-local-knowledge":
        payload = model.deactivate_local_knowledge(args.xid)
    elif args.command == "rank-skills":
        payload = model.rank_skills_for_purpose(args.purpose, args.limit)
    elif args.command == "tool-contracts":
        payload = model.list_tool_contracts()
    elif args.command == "client-tool-manifest":
        payload = model.get_client_tool_manifest()
    elif args.command == "get-client-tool-file":
        payload = model.get_client_tool_file(args.path)
    elif args.command == "client-tool-bundle":
        payload = model.get_client_tool_bundle()
    elif args.command == "client-tool-pip-package":
        payload = model.get_client_tool_pip_package()
    elif args.command == "check-client-tool-versions":
        installed = dict(item.split("=", 1) for item in args.installed)
        payload = model.check_client_tool_versions(installed)
    else:
        parser.error(f"unknown command: {args.command}")

    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
