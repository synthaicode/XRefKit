"""Read-only projection of explicitly structured plan artifacts.

The module CLI serializes a producer-supplied plan; it never extracts steps
from prose or creates execution records.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from urllib.parse import urlencode

MAX_PLAN_BYTES = 1024 * 1024
MAX_PLAN_FILES = 200
MAX_PLAN_STEPS = 500
MAX_STEP_RUNS = 200


def artifact_path(root: Path, value: object) -> Path | None:
    """Resolve only repository-relative regular files, including symlink targets."""
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        return None
    try:
        resolved = (root.resolve() / path).resolve()
        resolved.relative_to(root.resolve())
        return resolved if resolved.is_file() else None
    except (OSError, ValueError, RuntimeError):
        return None


def _string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_plan(plan: object) -> list[str]:
    """Validate a v1 producer payload without coercion or invented values."""
    if not isinstance(plan, dict):
        return ["計画はJSONオブジェクトである必要があります"]
    if type(plan.get("schema_version")) is int and plan["schema_version"] == 2:
        from xrefkit.work_management import validate_plan_v2
        return validate_plan_v2(plan)
    issues: list[str] = []
    unknown = set(plan) - {"schema_version", "plan_id", "plan_revision", "repository_root", "title", "source", "approval_status", "approval_evidence", "steps"}
    if unknown:
        issues.append(f"未対応の計画フィールド: {', '.join(sorted(unknown))}")
    if type(plan.get("schema_version")) is not int or plan.get("schema_version") != 1:
        issues.append("未対応のschema_version（対応: 1）")
    for key in ("plan_id", "plan_revision", "repository_root", "title", "source"):
        if not _string(plan.get(key)):
            issues.append(f"{key}: 空でない文字列が必要です")
    for key in ("approval_status", "approval_evidence"):
        if plan.get(key) is not None and not _string(plan[key]):
            issues.append(f"{key}: 文字列またはnullが必要です")
    steps = plan.get("steps")
    if not isinstance(steps, list):
        return issues + ["steps: 配列が必要です"]
    if len(steps) > MAX_PLAN_STEPS:
        return issues + [f"steps: 表示上限{MAX_PLAN_STEPS}工程を超えています"]
    identifiers: set[str] = set()
    graph: dict[str, list[str]] = {}
    for index, step in enumerate(steps):
        prefix = f"steps[{index}]"
        if not isinstance(step, dict):
            issues.append(f"{prefix}: オブジェクトが必要です")
            continue
        unknown = set(step) - {"step_id", "title", "depends_on", "status", "status_evidence", "planned_skill", "agent", "completion_criterion", "outputs", "runs"}
        if unknown:
            issues.append(f"{prefix}: 未対応の工程フィールド: {', '.join(sorted(unknown))}")
        for key in ("step_id", "title"):
            if not _string(step.get(key)):
                issues.append(f"{prefix}.{key}: 空でない文字列が必要です")
        step_id = step.get("step_id")
        if _string(step_id):
            if step_id in identifiers:
                issues.append(f"工程IDが重複しています: {step_id}")
            identifiers.add(step_id)
        for key in ("status", "status_evidence", "planned_skill", "agent", "completion_criterion"):
            if step.get(key) is not None and not _string(step[key]):
                issues.append(f"{prefix}.{key}: 文字列またはnullが必要です")
        for key in ("depends_on", "outputs"):
            values = step.get(key)
            if not isinstance(values, list) or not all(_string(value) for value in values):
                issues.append(f"{prefix}.{key}: 文字列の配列が必要です")
            elif key == "depends_on" and _string(step_id):
                graph[step_id] = values
        mappings = step.get("runs")
        if not isinstance(mappings, list):
            issues.append(f"{prefix}.runs: 配列が必要です")
            continue
        if len(mappings) > MAX_STEP_RUNS:
            issues.append(f"{prefix}.runs: 表示上限{MAX_STEP_RUNS}件を超えています")
            continue
        for number, mapping in enumerate(mappings):
            if not isinstance(mapping, dict):
                issues.append(f"{prefix}.runs[{number}]: オブジェクトが必要です")
                continue
            unknown = set(mapping) - {"run_id", "flow_id", "work_item_id", "node_id", "recorded_at"}
            if unknown:
                issues.append(f"{prefix}.runs[{number}]: 未対応の対応フィールド: {', '.join(sorted(unknown))}")
            for key in ("run_id", "flow_id", "work_item_id", "node_id", "recorded_at"):
                if mapping.get(key) is not None and not _string(mapping[key]):
                    issues.append(f"{prefix}.runs[{number}].{key}: 文字列またはnullが必要です")
            stamp = mapping.get("recorded_at")
            if _string(stamp):
                try:
                    parsed = datetime.fromisoformat(stamp)
                    if parsed.tzinfo is None or parsed.utcoffset() is None:
                        raise ValueError("timezone missing")
                except ValueError:
                    issues.append(f"{prefix}.runs[{number}].recorded_at: タイムゾーン付きISO日時が必要です")
    for step_id, dependencies in graph.items():
        for dependency in dependencies:
            if dependency not in identifiers:
                issues.append(f"{step_id}: 依存先工程がありません: {dependency}")
    # Iterative traversal keeps a legal long dependency chain off Python's stack.
    visiting: set[str] = set()
    visited: set[str] = set()
    for start in graph:
        stack = [(start, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                visiting.discard(node)
                visited.add(node)
            elif node in visiting:
                issues.append("依存関係に循環があります")
                return issues
            elif node not in visited:
                visiting.add(node)
                stack.append((node, True))
                stack.extend((child, False) for child in graph.get(node, []) if child in graph)
    return issues


def _repository_matches(root: Path, plan: dict) -> bool:
    try:
        repository = Path(plan["repository_root"])
        return repository.is_absolute() and repository.resolve() == root.resolve()
    except (OSError, ValueError, RuntimeError):
        return False


def resolve_mapping(root: Path, plan: dict, mapping: dict, runs_by_id: dict) -> dict:
    result = {**mapping, "available": False, "reason": "", "monitor_url": None}
    if not _repository_matches(root, plan):
        result["reason"] = "別リポジトリの計画です"
        return result
    run_id = mapping.get("run_id")
    if not _string(run_id):
        result["reason"] = "Run対応が未記録です（対応確認待ち）"
        return result
    matches = runs_by_id.get(run_id, [])
    if not matches:
        result["reason"] = "対応Runが見つかりません（未生成・削除・対象外）"
        return result
    if len(matches) != 1:
        result["reason"] = "Run IDが重複しています（対応確認待ち）"
        return result
    run = matches[0]
    for key in ("flow_id", "work_item_id", "node_id"):
        if mapping.get(key) is not None and mapping[key] != run.get(key):
            result["reason"] = f"{key}がRunの記録と一致しません"
            return result
    result.update(available=True, reason="対応確認済み", run_path=run["path"],
                  process_status=run.get("status"), closure_status=run.get("closure_status"),
                  quality_status=run.get("quality_status"))
    return result


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSONキーが重複しています: {key}")
        result[key] = value
    return result


def _read_plan(path: Path) -> object:
    with path.open("rb") as stream:
        data = stream.read(MAX_PLAN_BYTES + 1)
    if len(data) > MAX_PLAN_BYTES:
        raise ValueError("計画ファイルが1 MiBの読み込み上限を超えています")
    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=_unique_object)


def load_plans(root: Path, runs: list[dict], *, plans_dir: Path | None = None, workspace_id: str | None = None) -> list[dict]:
    """Keep independent malformed intake visible without crashing the dashboard."""
    directory = plans_dir if plans_dir is not None else root.resolve() / "work" / "plans"
    if not directory.exists():
        return []
    rows: list[dict] = []
    by_run: dict[str, list[dict]] = {}
    for run in runs:
        if run.get("run_id"):
            by_run.setdefault(run["run_id"], []).append(run)
    try:
        paths = sorted(directory.glob("*.json"))
    except OSError as exc:
        return [{"file": "work/plans", "issues": [f"計画一覧を読めません: {exc}"], "plan": None}]
    for path in paths[:MAX_PLAN_FILES]:
        row: dict = {"file": str(path.relative_to(root.resolve())), "issues": [], "plan": None}
        try:
            if artifact_path(root, row["file"]) is None:
                raise ValueError("計画ファイルがリポジトリ内の通常ファイルではありません")
            plan = _read_plan(path)
            row["issues"] = validate_plan(plan)
            if isinstance(plan, dict) and plan.get("schema_version") == 2:
                from xrefkit.work_management import validate_plan_v2
                row["issues"] = validate_plan_v2(plan, stored=True)
            if not row["issues"]:
                row["plan"] = plan
        except (OSError, ValueError, UnicodeError, RecursionError) as exc:
            row["issues"] = [f"計画を読み込めません: {exc}"]
        rows.append(row)
    if len(paths) > MAX_PLAN_FILES:
        rows.append({"file": "work/plans", "plan": None,
                     "issues": [f"計画ファイルが表示上限{MAX_PLAN_FILES}件を超えています（超過分未読）"]})
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        if row["plan"]:
            plan = row["plan"]
            identity = (plan["plan_id"], plan["plan_revision"])
            counts[identity] = counts.get(identity, 0) + 1
    for row in rows:
        plan = row["plan"]
        if plan is None:
            continue
        if plan["schema_version"] == 2 and (workspace_id is None or plan["workspace_id"] != workspace_id):
            row["issues"].append("作業領域の対応が未記録・不一致です。リンク利用不可。")
        if plan["schema_version"] == 1 and directory.resolve() != root.resolve() / "work/plans":
            row["issues"].append("v1はリポジトリ直下の計画のみ対応しています。")
        if counts[(plan["plan_id"], plan["plan_revision"])] > 1:
            row["issues"].append("計画IDと版が重複しています（対応確認待ち）")
        for step in plan["steps"]:
            mappings = [resolve_mapping(root, plan, mapping, by_run) for mapping in step["runs"]]
            mappings.sort(key=lambda mapping: (
                mapping.get("recorded_at") is None,
                datetime.fromisoformat(mapping["recorded_at"]) if mapping.get("recorded_at") else datetime.max.replace(tzinfo=timezone.utc),
            ))
            for mapping in mappings:
                if row["issues"]:
                    mapping.update(available=False, reason=row["issues"][0])
                if mapping["available"]:
                    mapping["monitor_url"] = "/?" + urlencode({
                        "panel": "closure", "run_id": mapping["run_id"],
                        "plan_id": plan["plan_id"], "plan_revision": plan["plan_revision"],
                        "step_id": step["step_id"],
                    })
                    if plan["schema_version"] == 2:
                        mapping["monitor_url"] += "&" + urlencode({"workspace_id": plan["workspace_id"]})
            step["run_observations"] = mappings
    return rows


def _display(value: object) -> str:
    if isinstance(value, list):
        return "、".join(_display(item) for item in value) or "記録なし"
    if isinstance(value, dict):
        return " / ".join(f"{_display(key)}: {_display(item)}" for key, item in value.items()) or "記録なし"
    return html.escape(str(value)) if value is not None else "未記録"


def _status_label(value: object) -> str:
    labels = {"pending": "未着手", "in_progress": "進行中", "done": "完了", "blocked": "停止中", "unknown": "未確認"}
    return labels.get(value, _display(value))


def _artifact_link(root: Path, value: object) -> str:
    if value is None:
        return "未記録"
    label = _display(value)
    if artifact_path(root, value) is None:
        return f"{label} <span>（ローカルリンク利用不可）</span>"
    url = html.escape("/artifact?" + urlencode({"path": value}), quote=True)
    return f'<a href="{url}">{label}</a>'


def _dependency_graph(steps: list[dict]) -> str:
    if not steps:
        return ""
    levels: dict[str, int] = {}
    pending = {step["step_id"]: step for step in steps}
    while pending:
        ready = [step for step in pending.values() if all(dep in levels for dep in step["depends_on"])]
        if not ready:
            return "<p>依存図を表示できません（対応確認待ち）</p>"
        for step in ready:
            levels[step["step_id"]] = max((levels[dep] + 1 for dep in step["depends_on"]), default=0)
            del pending[step["step_id"]]
    positions: dict[str, tuple[int, int]] = {}
    row_counts: dict[int, int] = {}
    for step in steps:
        level = levels[step["step_id"]]
        row = row_counts.get(level, 0)
        row_counts[level] = row + 1
        positions[step["step_id"]] = (level * 270 + 15, row * 95 + 15)
    width = (max(levels.values()) + 1) * 270
    height = max(row_counts.values()) * 95
    edges = []
    nodes = []
    for step in steps:
        x, y = positions[step["step_id"]]
        for dependency in step["depends_on"]:
            before_x, before_y = positions[dependency]
            edges.append(f'<path d="M {before_x + 220} {before_y + 32} L {x} {y + 32}" fill="none" stroke="currentColor"/><text x="{x - 12}" y="{y + 36}" fill="currentColor">›</text>')
        title = _display(step["title"])
        label = _display(step["title"][:15] + ("…" if len(step["title"]) > 15 else ""))
        identifier = _display(step["step_id"][:16] + ("…" if len(step["step_id"]) > 16 else ""))
        nodes.append(f'<g><title>{title}</title><rect x="{x}" y="{y}" width="220" height="64" rx="8" fill="none" stroke="currentColor"/><text x="{x + 10}" y="{y + 24}" fill="currentColor">{label}</text><text x="{x + 10}" y="{y + 46}" fill="currentColor">{identifier}</text></g>')
    return f'<div style="overflow:auto;max-height:360px"><svg role="img" font-size="12" aria-label="計画工程の依存図。矢印の先は依存する工程。詳細は下の工程一覧を参照" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">{"".join(edges)}{"".join(nodes)}</svg></div>'


def plan_panel(root: Path, rows: list[dict]) -> str:
    if not rows:
        return '<section class="empty">計画がありません。計画Skillの成果物と構造化sidecarを work/plans/*.json に記録すると、未実行の工程から表示できます。自由文から工程を推測しません。</section>'
    cards: list[str] = []
    for row in rows:
        errors = "".join(f"<li>{_display(issue)}</li>" for issue in row["issues"])
        plan = row["plan"]
        if plan is None:
            cards.append(f'<article class="box"><h3>{_display(row["file"])}</h3><p>計画表示不可</p><ul>{errors}</ul></article>')
            continue
        if plan["schema_version"] == 2:
            from xrefkit.work_management_view import plan_v2_card
            cards.append(plan_v2_card(root, row))
            continue
        attributes = ' '.join(f'data-{key.replace("_", "-")}="{html.escape(plan[key], quote=True)}"'
                              for key in ("plan_id", "plan_revision"))
        matches_root = _repository_matches(root, plan)
        def artifact(value: object) -> str:
            return _artifact_link(root, value) if matches_root else f"{_display(value)} （別リポジトリ・リンク利用不可）"
        repository_issue = "" if matches_root else "<p>別リポジトリの計画です。モニタと成果物へのリンクは利用できません。</p>"
        dependencies = []
        details = []
        for step in plan["steps"]:
            step_id = html.escape(step["step_id"], quote=True)
            before = "、".join(_display(item) for item in step["depends_on"]) or "依存なし"
            dependencies.append(f'<li><button type="button" class="plan-step" {attributes} data-step-id="{step_id}"><strong>{_display(step["title"])}</strong><span>工程状態: {_status_label(step.get("status"))}</span><small><code>{step_id}</code> ← {before}</small></button></li>')
            history = []
            for mapping in step["run_observations"]:
                link = (f'<a class="monitor-link" {attributes} data-step-id="{step_id}" data-run-id="{html.escape(mapping["run_id"], quote=True)}" href="{html.escape(mapping["monitor_url"], quote=True)}">モニタを開く</a>'
                        if mapping["available"] else f'<span aria-disabled="true">モニタ利用不可: {_display(mapping["reason"])}</span>')
                states = (f' | プロセス: {_display(mapping.get("process_status"))} / Closure: {_display(mapping.get("closure_status"))} / 品質: {_display(mapping.get("quality_status"))}'
                          if mapping["available"] else "")
                correlations = " / ".join(f'{key}: {_display(mapping.get(key))}' for key in ("flow_id", "work_item_id", "node_id"))
                history.append(f'<li><code>{_display(mapping.get("run_id"))}</code> | 記録日時: {_display(mapping.get("recorded_at"))}{states}<br>{correlations}<br>{link}</li>')
            outputs = "".join(f"<li>{artifact(output)}</li>" for output in step["outputs"]) or "<li>未記録</li>"
            history_html = "".join(history) or "<li>未実行（Run対応なし）</li>"
            details.append(f'''<section class="plan-step-detail box" {attributes} data-step-id="{step_id}" hidden>
              <h4>{_display(step["title"])} <code>{step_id}</code></h4>
              <p>依存工程: {before}</p><p>工程状態（記録値）: {_display(step.get("status"))} | 根拠: {artifact(step.get("status_evidence"))}</p>
              <p>担当Skill: {_display(step.get("planned_skill"))} | Agent担当: {_display(step.get("agent"))}</p>
              <p>完了条件: {_display(step.get("completion_criterion"))}</p><h5>成果物</h5><ul>{outputs}</ul>
              <h5>実行履歴</h5><p>日時未記録のRunは末尾に元の順序で表示します。再試行の前後関係は推測しません。</p><ul>{history_html}</ul>
            </section>''')
        cards.append(f'''<article class="plan-card box" {attributes}><h3>{_display(plan["title"])}</h3>
          <p>計画ID: <code>{_display(plan["plan_id"])}</code> | 版: {_display(plan["plan_revision"])}</p>
          {repository_issue}<details><summary>計画の出典と対象リポジトリ</summary><p>リポジトリ: {_display(plan["repository_root"])}</p><p>計画成果物: {artifact(plan["source"])}</p></details>
          <p>承認状態（記録値）: {_display(plan.get("approval_status"))} | 承認根拠: {artifact(plan.get("approval_evidence"))}</p>
          <ul>{errors}</ul><h4>工程と依存関係</h4><p>「工程 ← 依存先」を表示します。工程を選ぶと詳細とモニタリンクが開きます。</p>
          {_dependency_graph(plan["steps"])}<ul class="plan-dependencies">{"".join(dependencies) or "<li>工程がありません</li>"}</ul>{"".join(details)}</article>''')
    return "".join(cards)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and atomically serialize an explicit plan sidecar")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--name", required=True, help="Output filename under work/plans (must end in .json)")
    args = parser.parse_args(argv)
    if Path(args.name).name != args.name or PureWindowsPath(args.name).name != args.name or not args.name.endswith(".json"):
        parser.error("--name must be a plain .json filename")
    try:
        plan = _read_plan(args.input)
        if isinstance(plan, dict) and plan.get("schema_version") == 2:
            raise ValueError("v2 requires python -m xrefkit.work_management record with workspace and CAS")
        issues = validate_plan(plan)
        if issues:
            print(json.dumps({"valid": False, "issues": issues}, ensure_ascii=False))
            return 1
        directory = args.root.resolve() / "work" / "plans"
        directory.resolve().relative_to(args.root.resolve())
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / args.name
        text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
        if len(text.encode("utf-8")) > MAX_PLAN_BYTES:
            raise ValueError("serialized plan exceeds 1 MiB")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(text)
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        print(json.dumps({"valid": True, "output": str(target)}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        print(json.dumps({"valid": False, "issues": [str(exc)]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
