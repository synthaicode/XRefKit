"""Derived, portable Markdown projection of stored local v2 plans."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from xrefkit.plan_observation import artifact_path, resolve_mapping
from xrefkit.work_management import (
    confined_directory, load_workspaces, read_json, safe_external_url,
    MAX_RECORDS, task_counts, package_task_counts, validate_plan_v2, writer_lock,
)

PREFIX = "<!-- xrefkit-plan-projection:v1 "
MAX_PROJECTION_BYTES = 8 * 1024 * 1024
LABELS = {"step_id": "作業ID", "status": "状態（記録値）", "status_evidence": "状態の証跡", "planned_skill": "予定Skill", "agent": "担当Agent", "completion_criterion": "完了条件", "candidate_version": "対象版", "revalidation_needed": "再検証の必要性", "revalidation_evidence": "再検証の証跡", "impact_status": "変更影響", "pbi_ids": "対応PBI", "validation_records": "検証記録", "dependencies": "依存関係", "outputs": "成果物", "artifact_refs": "参照資料", "judgment_refs": "判断記録", "concern_refs": "懸念記録", "confirmation_id": "確認ID", "question": "確認内容", "answer": "回答", "answer_ref": "回答の参照", "answer_status": "回答状態", "application_status": "反映状態", "application_evidence": "反映の証跡", "decision_ref": "判断の参照", "step_ids": "対象作業", "pbi_id": "PBI ID", "title": "名称", "purpose": "目的", "acceptance_criteria": "受入条件", "acceptance_status": "受入状態（記録値）", "acceptance_evidence": "受入の証跡", "priority": "優先度", "owner": "担当", "external_ref_ids": "外部参照ID", "external_ref_id": "外部参照ID", "service": "サービス", "organization": "組織", "project": "プロジェクト", "item_id": "項目ID", "url": "参照先", "revision": "版", "type_mapping": "種類の対応", "state_mapping": "状態の対応", "ownership_ref": "所有者の参照", "last_read_at": "読取日時", "last_success_at": "最終成功日時", "sync_status": "同期状態（記録値）", "pending_summary": "未反映内容", "recorded_at": "記録日時", "candidate_version": "対象版", "result": "検証結果（記録値）", "evidence_ref": "証跡", "baseline_id": "基準版ID", "source": "出典", "docs_revision": "文書版", "code_revision": "コード版", "acquired_at": "取得日時", "mismatches": "不一致", "artifacts": "基準資料", "change_id": "変更ID", "scope_in": "対象範囲", "scope_out": "対象外", "assumptions": "前提", "constraints": "制約", "exit_criteria": "終了条件", "decision_owner": "判断担当", "review_owner": "レビュー担当", "acceptance_owner": "受入担当", "quality_conditions": "品質条件", "condition_id": "条件ID", "verification_method": "確認方法", "reviewer": "確認担当", "evidence_refs": "証跡"}
LINK_FIELDS = {"status_evidence", "revalidation_evidence", "answer_ref", "application_evidence", "decision_ref", "acceptance_evidence", "ownership_ref", "evidence_ref", "source"}
LABELS.update({"reason": "確認する理由", "resolver": "回答担当", "due_at": "期限", "version_refs": "対象版", "impact": "影響", "application": "回答の反映", "text": "回答内容", "responder": "回答者", "target_refs": "反映先", "verified_by": "反映確認者", "validation_id": "検証ID", "target_version": "検証対象版", "environment": "検証環境", "input_data": "入力", "expected_result": "期待結果", "kind": "依存の種類", "recorded_at": "記録日時"})
LABELS.update({"work_package_id": "作業パッケージID", "expected_output": "期待成果物", "depends_on": "依存するパッケージ", "verification": "成果確認（記録値）"})


def text(value: object) -> str:
    """Inert text in paragraphs, headings, links and tables."""
    if value is None:
        return "未記録"
    if isinstance(value, list):
        return "、".join(text(item) for item in value) or "記録なし"
    if isinstance(value, dict):
        return " / ".join(f"{text(key)}: {text(item)}" for key, item in value.items()) or "記録なし"
    return "".join(f"&#{ord(char)};" if char in "\\`*_{}[]<>()#+-!|&\"'~" else " " if ord(char) < 32 else char for char in str(value))


def mermaid_label(value: object) -> str:
    # Mermaid's decimal entity syntax keeps the producer out of its grammar.
    return "".join(char if char.isalnum() or char in " .,:/" or (ord(char) >= 128 and not char.isspace()) else f"#{ord(char)};" for char in str(value if value is not None else "未記録"))


def status(value: object) -> str:
    return {"pending": "未着手", "in_progress": "進行中", "done": "完了", "blocked": "停止中", "unknown": "未確認"}.get(value, "未記録" if value is None else str(value))


def revalidation(value: object) -> str:
    return "必要" if value is True else "不要（記録値）" if value is False else "未記録"


def destination(value: str) -> str:
    if not safe_external_url(value):
        raise ValueError("destination must be HTTP/HTTPS without credentials")
    parts = urlsplit(value)
    if any(ord(char) < 33 or char in '<>\\(){}|%`"' for char in parts.netloc):
        raise ValueError("destination authority contains unsupported characters")
    parts.port  # Validate authority port without encoding IPv6 brackets as path data.
    return urlunsplit((parts.scheme, parts.netloc, quote(parts.path, safe="/%:"), quote(parts.query, safe="=&%?:/+"), quote(parts.fragment, safe="/%?:")))


def monitor_base(value: str | None) -> str | None:
    if value is None:
        return None
    parts = urlsplit(value)
    if parts.query or parts.fragment:
        raise ValueError("monitor base must not contain a query or fragment")
    return destination(value.rstrip("/") + "/")


def local_link(root: Path, output: Path, value: object) -> str:
    path = artifact_path(root, value)
    if path is None:
        return f"{text(value)}（ローカルリンク利用不可）"
    relative = Path(os.path.relpath(path, output.parent)).as_posix()
    return f"[{text(value)}]({quote(relative, safe='/')})"


def record_lines(root: Path, output: Path, record: dict) -> list[str]:
    result = []
    for key, value in record.items():
        if key in LINK_FIELDS:
            rendered = local_link(root, output, value)
        elif key in {"artifact_refs", "artifacts"}:
            rendered = "、".join(f"{local_link(root, output, item['path'])}（版: {text(item.get('revision'))}）" for item in value) or "記録なし"
        elif key in {"outputs", "judgment_refs", "concern_refs", "evidence_refs", "target_refs"}:
            rendered = "、".join(local_link(root, output, item) for item in value) or "記録なし"
        elif isinstance(value, dict):
            rendered = "、".join(line.removeprefix("- ") for line in record_lines(root, output, value))
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            rendered = " ／ ".join("、".join(line.removeprefix("- ") for line in record_lines(root, output, item)) for item in value) or "記録なし"
        elif key == "url" and safe_external_url(value):
            try:
                rendered = f"[外部参照]({destination(value)})（接続未確認）"
            except ValueError:
                rendered = f"{text(value)}（リンク利用不可）"
        else:
            rendered = text(value)
        result.append(f"- {LABELS.get(key, text(key))}: {rendered}")
    return result


def workspace_for(root: Path, source: Path, plan: dict) -> Path:
    root = root.resolve()
    source.resolve().relative_to(root)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != ".json":
        raise ValueError("stored JSON source file required")
    if Path(plan["repository_root"]).resolve() != root:
        raise ValueError("repository identity mismatch")
    rows = [row for row in load_workspaces(root) if row["workspace"] and row["workspace"]["workspace_id"] == plan["workspace_id"]]
    if len(rows) != 1 or rows[0]["issues"]:
        raise ValueError("workspace mapping missing or ambiguous")
    workspace = confined_directory(root, rows[0]["workspace"]["workspace_root"])
    if workspace is None:
        raise ValueError("workspace directory unavailable")
    directory = workspace / "work/plans"
    directory.resolve().relative_to(workspace)
    if source.parent.resolve() != directory.resolve():
        raise ValueError("source is outside the selected workspace plan directory")
    return workspace


def _runs(root: Path, workspace: Path) -> dict:
    from xrefkit.dashboard import collect_runs
    directory = workspace / "work/sessions"
    directory.resolve().relative_to(workspace)
    errors: list[str] = []
    runs = collect_runs(root, directory, audit_errors=errors, strict_scope=True)
    if errors:
        raise ValueError("Run scope parsing failed: " + "; ".join(errors))
    by_id: dict = {}
    for run in runs:
        value = asdict(run)
        by_id.setdefault(value["run_id"], []).append(value)
    return by_id


def render_body(root: Path, source: Path, plan: dict, *, base: str | None = None) -> str:
    issues = validate_plan_v2(plan, stored=True)
    if issues:
        raise ValueError("; ".join(issues))
    base = monitor_base(base)
    workspace = workspace_for(root, source, plan)
    output = source.with_suffix(".md")
    by_run = _runs(root, workspace)
    counts = task_counts(plan)
    lines = [f"# {text(plan['title'])}", "", "構造化された計画から生成した閲覧用文書です。編集は元の記録に反映されません。", "",
             f"正本: {local_link(root, output, str(source.relative_to(root.resolve())))}", ""]
    lines.append(f"作業領域: {text(plan['workspace_id'])} ／ 計画版: {text(plan['plan_revision'])} ／ 観測版: {plan['observation_revision']} ／ 記録日時: {text(plan.get('recorded_at'))}")
    lines += ["", "## 作業件数", "", f"予定（現行） **{counts['current']}** ／ 記録上の完了 **{counts['completed']}** ／ 残り **{counts['remaining']}**", "",
              f"当初: {text(counts['initial'])} ／ 追加: {text(counts['added'])} ／ 削除: {text(counts['removed'])} ／ 再検証待ち: {counts['revalidation']} ／ 状態未記録: {counts['unrecorded']} ／ 未認識: {counts['unrecognized']}", "",
              "件数は工数・残日数・品質承認ではありません。完了記録と証跡・版の確認を分けて表示します。", "", "## 工程別一覧", ""]
    lines[lines.index("## 工程別一覧"):lines.index("## 工程別一覧")] = [f"承認状態（記録値）: {text(plan.get('approval_status'))} ／ 証跡: {local_link(root, output, plan.get('approval_evidence'))}", ""]
    ids = {step["step_id"]: f"task-{index}" for index, step in enumerate(plan["steps"])}
    packages = plan.get("work_packages")
    if packages is not None:
        lines.remove("## 工程別一覧")
        lines += ["## 作業パッケージ", "", "所属Taskの完了と成果確認は別です。成果確認は記録値であり、現在の着手可否やPBI受入を意味しません。", ""]
        for index, package in enumerate(packages):
            c = package_task_counts(plan, package)
            verification = package.get("verification", {}).get("status")
            confirmed = {"verified": "確認済み", "not_verified": "未確認", "revalidation_needed": "再確認必要"}.get(verification, "未記録")
            lines += [f"### パッケージ {index}: {text(package['title'])}", "", f"予定 {c['current']} ／ 記録上の完了 {c['completed']} ／ 残り {c['remaining']} ／ 再検証待ち {c['revalidation']}", "", f"所属Taskすべて完了: {'はい' if c['remaining'] == 0 else 'いいえ'} ／ 成果確認（記録値）: {confirmed}", ""]
            if c["remaining"] and verification == "verified":
                lines += ["過去の成果確認記録が残っています。未完了・再検証中のTaskがあるため、現在の成果確認済みとは読み替えません。", ""]
            lines += record_lines(root, output, package)
            lines += ["", "所属Task:", ""] + [f"- [{text(member)}](#{ids[member]})" for member in package["step_ids"]] + [""]
        lines += ["## PBI・パッケージ・Taskの所属", "", "線は所属のみを示します。作業順序は別の依存図に記録します。", "", "```mermaid", "flowchart TB"]
        pbi_nodes = {pbi["pbi_id"]: f"p{index}" for index, pbi in enumerate(plan["pbis"])}
        for pbi in plan["pbis"]:
            lines.append(f'  {pbi_nodes[pbi["pbi_id"]]}["PBI: {mermaid_label(pbi["title"])}"]')
        for index, package in enumerate(packages):
            lines.append(f'  w{index}["{mermaid_label(package["title"])}"]')
            lines.append(f'  {pbi_nodes[package["pbi_id"]]} --- w{index}')
            for member in package["step_ids"]:
                lines.append(f'  w{index} --- m{ids[member].removeprefix("task-")}["{mermaid_label(member)}"]')
        if not plan["pbis"] and not packages:
            lines.append('  empty["所属の記録なし"]')
        lines += ["```", "", "## パッケージ成果の依存関係", "", "矢印は明示された先行パッケージの成果への依存です。Taskの順序や着手可能性へ展開しません。", "", "```mermaid", "flowchart LR"]
        package_nodes = {package["work_package_id"]: f"w{index}" for index, package in enumerate(packages)}
        for package in packages:
            lines.append(f'  {package_nodes[package["work_package_id"]]}["{mermaid_label(package["title"])}"]')
        for package in packages:
            for dependency in package["depends_on"]:
                lines.append(f'  {package_nodes[dependency]} --> {package_nodes[package["work_package_id"]]}')
        if not packages:
            lines.append('  empty["パッケージの記録なし"]')
        lines += ["```", "", "## 工程別一覧", ""]
    for stage in plan["stages"]:
        steps = [step for step in plan["steps"] if step["stage_id"] == stage["stage_id"]]
        c = task_counts({**plan, "steps": steps})
        lines += [f"### {text(stage['title'])}", "", f"予定 {c['current']} ／ 記録上の完了 {c['completed']} ／ 残り {c['remaining']}", ""]
        lines += [f"- [{text(step['title'])}](#{ids[step['step_id']]}) — 状態: {text(status(step.get('status')))} ／ 再検証: {text(revalidation(step.get('revalidation_needed')))}" for step in steps] or ["作業の記録なし"]
        lines.append("")
    lines += ["## 依存関係", "", "必須: 実線矢印 ／ 任意: 点線矢印 ／ 外部参照: 外部参照ノードからの点線矢印。順序・着手可能性を補って推測しません。", "", "```mermaid", "flowchart LR"]
    nodes = {step["step_id"]: f"n{index}" for index, step in enumerate(plan["steps"])}
    external = {ref["external_ref_id"]: f"e{index}" for index, ref in enumerate(plan["external_refs"])}
    used_external = {dep["external_ref_id"] for step in plan["steps"] for dep in step["dependencies"] if dep["kind"] == "external"}
    groups = packages if packages is not None else plan["stages"]
    for index, group in enumerate(groups):
        lines.append(f'  subgraph s{index}["{mermaid_label(group["title"])}"]')
        for step in plan["steps"]:
            member = step["step_id"] in group["step_ids"] if packages is not None else step["stage_id"] == group["stage_id"]
            if member:
                label = f'{step["title"]} / {status(step.get("status"))} / 再検証:{revalidation(step.get("revalidation_needed"))}'
                lines.append(f'    {nodes[step["step_id"]]}["{mermaid_label(label)}"]')
        lines.append("  end")
    if not plan["steps"] and not plan["stages"]:
        lines.append('  empty["作業の記録なし"]')
    for ref in plan["external_refs"]:
        if ref["external_ref_id"] in used_external:
            lines.append(f'  {external[ref["external_ref_id"]]}["外部参照: {mermaid_label(ref.get("title", ref["external_ref_id"]))}"]')
    for step in plan["steps"]:
        for dep in step["dependencies"]:
            predecessor = external[dep["external_ref_id"]] if dep["kind"] == "external" else nodes[dep["step_id"]]
            edge = "-->|必須|" if dep["kind"] == "mandatory" else "-.->|任意|" if dep["kind"] == "optional" else "-.->|外部|"
            lines.append(f'  {predecessor} {edge} {nodes[step["step_id"]]}')
    lines += ["  classDef complete fill:#dcfce7,stroke:#15803d", "  classDef active fill:#fef3c7,stroke:#b45309", "  classDef recheck fill:#dbeafe,stroke:#2563eb,stroke-dasharray:4 3"]
    for step in plan["steps"]:
        state = "recheck" if step.get("revalidation_needed") is True else "complete" if step.get("status") == "done" else "active" if step.get("status") == "in_progress" else None
        if state:
            lines.append(f'  class {nodes[step["step_id"]]} {state}')
    lines += ["```", "", "## 作業詳細", ""]
    for index, step in enumerate(plan["steps"]):
        lines += [f"### Task {index}", "", f"**{text(step['title'])}**", ""]
        lines += record_lines(root, output, {key: step.get(key) for key in ("step_id", "status", "status_evidence", "planned_skill", "agent", "completion_criterion", "candidate_version", "revalidation_needed", "revalidation_evidence", "impact_status", "pbi_ids")})
        lines += record_lines(root, output, {key: step.get(key, []) for key in ("validation_records", "dependencies", "outputs", "artifact_refs", "judgment_refs", "concern_refs")})
        if any(record.get("target_version") != step.get("candidate_version") for record in step.get("validation_records", [])):
            lines.append("検証記録には対象版と異なる版の結果が含まれます。現在版の検証結果へ読み替えません。")
        lines += ["", "実行履歴:", ""]
        for mapping in step["runs"]:
            resolved = resolve_mapping(root, plan, mapping, by_run)
            if not resolved["available"]:
                lines.append(f"- Run {text(mapping.get('run_id'))}: {text(resolved['reason'])}")
                continue
            link = local_link(root, output, resolved["run_path"])
            detail = f"- Run {text(mapping['run_id'])}: {link} ／ 記録日時: {text(mapping.get('recorded_at'))}"
            if base:
                query = urlencode({"panel": "closure", "workspace_id": plan["workspace_id"], "plan_id": plan["plan_id"], "plan_revision": plan["plan_revision"], "step_id": step["step_id"], "run_id": mapping["run_id"]})
                detail += f" ／ [補助モニタ]({base}?{query})（接続未確認）"
            lines.append(detail)
        if not step["runs"]:
            lines.append("実行の対応は未記録です。")
        lines.append("")
    for heading, key in (("確認事項", "confirmations"), ("PBI受入（作業完了とは別）", "pbis"), ("外部参照（記録値・接続未確認）", "external_refs")):
        lines += [f"## {heading}", ""]
        for index, record in enumerate(plan[key]):
            lines += [f"### {heading} {index + 1}", ""] + record_lines(root, output, record) + [""]
        if not plan[key]:
            lines.append("記録なし")
        lines.append("")
    lines += ["## 参照資料", "", f"- 計画の出典: {local_link(root, output, plan['source'])}", "", "### 変更内容", ""] + record_lines(root, output, plan["change"])
    lines += ["", "- 知識の参照: " + ("、".join(local_link(root, output, ref) for ref in plan.get("knowledge_refs", [])) or "記録なし")]
    lines += ["", "### 基準版", ""] + record_lines(root, output, plan["baseline"])
    lines += ["", "## 生成元の対応情報", ""]
    for label, key in (("作業領域", "workspace_id"), ("計画ID", "plan_id"), ("計画版", "plan_revision"), ("観測版", "observation_revision"), ("報告ID", "report_id"), ("報告ハッシュ", "report_sha256"), ("記録日時", "recorded_at")):
        lines.append(f"- {label}: {text(plan.get(key))}")
    lines += ["", "文書と正本は別ファイルです。表示が古い場合は保存済み正本から再生成してください。", ""]
    return "\n".join(lines)


def _owner(root: Path, source: Path, plan: dict) -> dict:
    return {"source": str(source.relative_to(root.resolve())).replace("\\", "/"), "identity": [plan[key] for key in ("workspace_id", "plan_id", "plan_revision")]}


def publish_projection(root: Path, source: Path, plan: dict, *, base: str | None = None) -> dict:
    """Caller must hold the source directory writer lock."""
    target = source.with_suffix(".md")
    try:
        body = render_body(root, source, plan, base=base)
        owner = _owner(root, source, plan)
        if target.is_symlink() or target.resolve() == source.resolve() or target.resolve().parent != source.resolve().parent:
            raise ValueError("projection target alias or escape refused")
        if target.exists():
            with target.open("rb") as stream:
                prior = stream.read(MAX_PROJECTION_BYTES + 1)
            if len(prior) > MAX_PROJECTION_BYTES:
                raise ValueError("existing projection size exceeds read bound")
            header, separator, previous_body = prior.decode("utf-8").partition("\n")
            if not separator or not header.startswith(PREFIX) or not header.endswith(" -->"):
                raise ValueError("hand-authored Markdown conflict; retained unchanged")
            receipt = json.loads(base64.b64decode(header[len(PREFIX):-4], validate=True))
            if not isinstance(receipt, dict) or receipt.get("owner") != owner or receipt.get("body_sha256") != hashlib.sha256(previous_body.encode("utf-8")).hexdigest():
                raise ValueError("edited or different-owner Markdown conflict; retained unchanged")
        receipt = {"owner": owner, "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}
        header = PREFIX + base64.b64encode(json.dumps(receipt, ensure_ascii=True).encode()).decode() + " -->\n"
        payload = (header + body).encode("utf-8")
        if len(payload) > MAX_PROJECTION_BYTES:
            raise ValueError("8 MiB projection limit exceeded")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {"status": "generated", "output": str(target), "observation_revision": plan["observation_revision"]}
    except (OSError, ValueError, UnicodeError, RuntimeError, RecursionError) as exc:
        return {"status": "failed", "output": str(target), "issues": [str(exc)], "recovery": "render the stored JSON after resolving the cause; or retry the identical report"}


def regenerate(root: Path, source: Path, *, base: str | None = None) -> dict:
    root = root.resolve()
    source = source.absolute()
    plan = read_json(source)
    issues = validate_plan_v2(plan, stored=True)
    if issues:
        raise ValueError("; ".join(issues))
    workspace_for(root, source, plan)
    with writer_lock(source.parent / ".records.lock"):
        plan = read_json(source)
        issues = validate_plan_v2(plan, stored=True)
        if issues:
            raise ValueError("; ".join(issues))
        workspace_for(root, source, plan)
        matches = []
        candidates = list(source.parent.glob("*.json"))
        if len(candidates) > MAX_RECORDS:
            raise ValueError("plan file limit exceeded")
        for path in candidates:
            path.resolve().relative_to(source.parent.resolve())
            value = read_json(path)
            if isinstance(value, dict) and tuple(value.get(key) for key in ("workspace_id", "plan_id", "plan_revision")) == tuple(plan[key] for key in ("workspace_id", "plan_id", "plan_revision")):
                matches.append(path)
        if len(matches) != 1:
            raise ValueError("stored plan identity ambiguous")
        return {"saved": False, "output": str(source), "projection": publish_projection(root, source, plan, base=base)}
