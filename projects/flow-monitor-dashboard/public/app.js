const summaryGrid = document.getElementById("summaryGrid");
const projectSelector = document.getElementById("projectSelector");
const projectSummary = document.getElementById("projectSummary");
const projectFlowStates = document.getElementById("projectFlowStates");
const projectRunHistory = document.getElementById("projectRunHistory");
const projectFlowDesign = document.getElementById("projectFlowDesign");
const monitoringView = document.getElementById("monitoringView");
const designView = document.getElementById("designView");
const viewTabs = document.getElementById("viewTabs");
const generatedAt = document.getElementById("generatedAt");
const refreshButton = document.getElementById("refreshButton");
const metricCardTemplate = document.getElementById("metricCardTemplate");

let dashboardData = null;
let selectedProject = "";
let selectedView = "monitoring";
const expandedSequenceSkills = new Set();

function metricCard(label, value, note) {
  const fragment = metricCardTemplate.content.cloneNode(true);
  fragment.querySelector(".metric-label").textContent = label;
  fragment.querySelector(".metric-value").textContent = value;
  fragment.querySelector(".metric-note").textContent = note;
  return fragment;
}

function badge(text, tone = "default") {
  return `<span class="badge badge-${tone}">${escapeHtml(text)}</span>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatList(values, emptyText = "なし") {
  if (!values || values.length === 0) {
    return `<span class="muted">${emptyText}</span>`;
  }
  return values.map((value) => badge(value)).join("");
}

function preferredLoggingNames(flow, kind) {
  const observed = flow.observed_logging?.[kind] || [];
  if (observed.length > 0) {
    return observed;
  }
  return flow.logging_recommendation?.[kind] || [];
}

function percent(numerator, denominator) {
  if (!denominator) {
    return 0;
  }
  return Math.round((numerator / denominator) * 100);
}

function classifyRun(run) {
  if (run.missing_steps.length > 0) {
    return "warn";
  }
  if (run.decisions.length > 0 || run.checklist_usage.length > 0) {
    return "ok";
  }
  return "muted";
}

function runStateLabel(run) {
  if (run.missing_steps.length > 0) {
    return "incomplete";
  }
  if (run.decisions.length > 0 || run.checklist_usage.length > 0) {
    return "healthy";
  }
  return "flat";
}

function renderSummary(data) {
  summaryGrid.innerHTML = "";
  summaryGrid.appendChild(metricCard("Projects", String(data.project_count), "監視対象のプロジェクト数"));
  summaryGrid.appendChild(metricCard("Flows", String(data.flow_count), "定義済み Flow 数"));
  summaryGrid.appendChild(metricCard("Runs", String(data.run_count), "検出した実行単位"));

  const decisionRuns = data.flow_summaries.reduce((sum, flow) => sum + flow.decision_run_count, 0);
  const checklistRuns = data.flow_summaries.reduce((sum, flow) => sum + flow.checklist_run_count, 0);
  const incompleteRuns = data.flow_summaries.reduce((sum, flow) => sum + flow.incomplete_run_count, 0);
  summaryGrid.appendChild(metricCard("Decision Runs", String(decisionRuns), "判断イベントが記録された run"));
  summaryGrid.appendChild(metricCard("Checklist Runs", String(checklistRuns), "チェックリスト利用が記録された run"));
  summaryGrid.appendChild(metricCard("Incomplete Runs", String(incompleteRuns), "未観測ステップが残る run"));
}

function renderTabs() {
  for (const button of viewTabs.querySelectorAll("[data-view]")) {
    const isActive = button.getAttribute("data-view") === selectedView;
    button.classList.toggle("tab-button-active", isActive);
    button.setAttribute("aria-checked", isActive ? "true" : "false");
    if (button.dataset.bound === "true") {
      continue;
    }
    button.dataset.bound = "true";
    button.addEventListener("click", () => {
      selectedView = button.getAttribute("data-view") || "monitoring";
      renderViewVisibility();
    });
  }
}

function renderViewVisibility() {
  const workspace = document.querySelector(".workspace");
  const projectSummaryPanel = document.querySelector("#projectSummary")?.closest(".panel");
  const isMonitoring = selectedView === "monitoring";

  monitoringView.style.display = isMonitoring ? "" : "none";
  designView.style.display = isMonitoring ? "none" : "";
  workspace?.classList.toggle("design-mode", !isMonitoring);
  if (projectSummaryPanel) {
    projectSummaryPanel.style.display = isMonitoring ? "" : "none";
  }
  for (const button of viewTabs.querySelectorAll("[data-view]")) {
    const isActive = button.getAttribute("data-view") === selectedView;
    button.classList.toggle("tab-button-active", isActive);
    button.setAttribute("aria-checked", isActive ? "true" : "false");
  }
}

function deriveProjectFlowStates(data, projectName) {
  return data.flow_summaries
    .map((flow) => {
      const projectRuns = flow.recent_runs
        .filter((run) => run.project === projectName)
        .sort((left, right) => right.latest_at.localeCompare(left.latest_at));
      if (!projectRuns.length) {
        return null;
      }

      const latestRun = projectRuns[0];
      const incompleteCount = projectRuns.filter((run) => run.missing_steps.length > 0).length;
      const decisionCount = projectRuns.reduce((sum, run) => sum + run.decisions.length, 0);
      const checklistCount = projectRuns.reduce((sum, run) => sum + run.checklist_usage.length, 0);
      const pathCounts = new Map();
      for (const run of projectRuns) {
        for (const pathName of run.traversed_paths) {
          pathCounts.set(pathName, (pathCounts.get(pathName) || 0) + 1);
        }
      }

      const stepCoverage = flow.sequence.map((step) => ({
        step,
        run_count: projectRuns.filter((run) => run.visited_steps.includes(step)).length,
      }));

      return {
        ...flow,
        project_runs: projectRuns,
        project_run_count: projectRuns.length,
        project_incomplete_count: incompleteCount,
        project_decision_count: decisionCount,
        project_checklist_count: checklistCount,
        project_latest_run: latestRun,
        project_step_coverage: stepCoverage,
        project_paths: [...pathCounts.entries()].map(([name, count]) => ({ name, count })),
      };
    })
    .filter(Boolean)
    .sort((left, right) => {
      const leftLatest = left.project_latest_run?.latest_at || "";
      const rightLatest = right.project_latest_run?.latest_at || "";
      return rightLatest.localeCompare(leftLatest);
    });
}

function renderProjectSelector(data) {
  const projects = data.project_summaries;
  if (!projects.length) {
    projectSelector.innerHTML = `<option value="">project なし</option>`;
    projectSelector.disabled = true;
    return;
  }

  projectSelector.disabled = false;
  projectSelector.innerHTML = projects
    .map((project) => {
      return `
        <option value="${escapeHtml(project.project)}" ${project.project === selectedProject ? "selected" : ""}>
          ${escapeHtml(project.project)}
        </option>
      `;
    })
    .join("");
}

function renderProjectSummary(data, project, projectFlows, projectRuns) {
  if (!project) {
    projectSummary.innerHTML = `<p class="empty-state">project を選択してください。</p>`;
    return;
  }

  const incompleteFlowCount = projectFlows.filter((flow) => flow.project_incomplete_count > 0).length;
  const healthyFlowCount = projectFlows.filter((flow) => flow.project_latest_run && flow.project_latest_run.missing_steps.length === 0).length;

  projectSummary.innerHTML = `
    <div class="project-header">
      <div>
        <p class="flow-meta">Latest activity: ${escapeHtml(project.latest_at || "-")}</p>
      </div>
      <div class="project-badges">
        ${badge(`flows ${project.flow_count}`, "active")}
        ${badge(`runs ${project.run_count}`, "active")}
        ${badge(`healthy flows ${healthyFlowCount}`, healthyFlowCount ? "ok" : "muted")}
        ${badge(`attention ${incompleteFlowCount}`, incompleteFlowCount ? "warn" : "ok")}
      </div>
    </div>
    <div class="summary-grid project-summary-grid"></div>
  `;

  const target = projectSummary.querySelector(".project-summary-grid");
  target.appendChild(metricCard("Runs", String(project.run_count), "この project の全 run 数"));
  target.appendChild(metricCard("Flows", String(project.flow_count), "この project で動いた Flow 数"));
  target.appendChild(metricCard("Decisions", String(project.decision_count), "記録された判断イベント"));
  target.appendChild(metricCard("Checklists", String(project.checklist_count), "記録されたチェックリスト"));
  target.appendChild(metricCard("Latest Run", projectRuns[0]?.flow_name || "-", "直近に動いた Flow"));
  target.appendChild(metricCard("Monitoring Root", data.monitored_root, "監視ルート"));
}

function renderRunChips(runs) {
  if (!runs.length) {
    return '<p class="muted">まだ run がありません。</p>';
  }

  return `
    <div class="run-chip-list">
      ${runs
        .map((run) => {
          const tone = classifyRun(run);
          return `
            <div class="run-chip run-chip-${tone}">
              <div class="run-chip-head">
                <strong>${escapeHtml(run.run_key.split("::").slice(-1)[0])}</strong>
                <span>${escapeHtml(run.latest_at || "-")}</span>
              </div>
              <div class="run-chip-body">
                ${badge(runStateLabel(run), tone)}
                ${badge(`events ${run.event_count}`, "default")}
                ${badge(`decisions ${run.decisions.length}`, run.decisions.length ? "active" : "muted")}
                ${badge(`checklists ${run.checklist_usage.length}`, run.checklist_usage.length ? "active" : "muted")}
              </div>
              <div class="run-chip-foot">
                <span>paths</span>
                <span>${run.traversed_paths.length}</span>
                <span>missing</span>
                <span>${run.missing_steps.length}</span>
              </div>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderPathTable(pathItems) {
  if (!pathItems || pathItems.length === 0) {
    return '<p class="muted">未記録</p>';
  }

  const rows = pathItems
    .map(
      (item) => `
        <tr>
          <td>${escapeHtml(item.name)}</td>
          <td>${item.count}</td>
        </tr>
      `
    )
    .join("");

  return `
    <table>
      <thead>
        <tr>
          <th>Path</th>
          <th>Count</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function deriveStepRows(flow, latestRun) {
  const logging = {
    decisions: preferredLoggingNames(flow, "decisions"),
    checklists: preferredLoggingNames(flow, "checklists"),
    paths: preferredLoggingNames(flow, "paths"),
  };
  const latestChecklistMap = new Map(
    (latestRun?.checklist_usage || []).map((item) => [item.name, item])
  );

  return (flow.sequence || []).map((step) => {
    const visited = latestRun ? latestRun.visited_steps.includes(step) : false;
    const coverage = flow.project_step_coverage.find((item) => item.step === step)?.run_count || 0;
    const pathMatch = (flow.project_paths || []).filter((item) => item.name === step);
    const relatedPaths = pathMatch.length
      ? pathMatch
      : (flow.project_paths || []).filter((item) => item.name.includes(step) || step.includes(item.name));

    const checklist =
      latestChecklistMap.get(step)
      || logging.checklists
        .filter((name) => name === step || name.includes(step) || step.includes(name))
        .map((name) => latestChecklistMap.get(name) || { name, completed: null, total: null })[0]
      || null;

    return {
      step,
      visited,
      coverage,
      relatedPaths,
      checklist,
    };
  });
}

function renderChecklistCell(checklist) {
  if (!checklist) {
    return '<span class="muted">なし</span>';
  }

  const detail =
    checklist.completed === null || checklist.total === null
      ? `${checklist.name}`
      : `${checklist.name}: ${checklist.completed}/${checklist.total}`;

  return `
    <button
      type="button"
      class="mini-link"
      title="${escapeHtml(detail)}"
      aria-label="${escapeHtml(detail)}"
    >
      ${escapeHtml(checklist.name)}
    </button>
  `;
}

function renderDesignChecklistTable(names, latestRun) {
  if (!names || names.length === 0) {
    return '<p class="muted">定義なし</p>';
  }

  const checklistMap = new Map((latestRun?.checklist_usage || []).map((item) => [item.name, item]));
  const rows = names
    .map((name) => {
      const item = checklistMap.get(name);
      const status = item
        ? `${item.completed ?? "-"} / ${item.total ?? "-"}`
        : "未観測";
      return `
        <tr>
          <td>${escapeHtml(name)}</td>
          <td>${item ? badge("observed", "ok") : badge("missing", "warn")}</td>
          <td>${escapeHtml(status)}</td>
        </tr>
      `;
    })
    .join("");

  return `
    <table>
      <thead>
        <tr>
          <th>Checklist</th>
          <th>Status</th>
          <th>Latest</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderDesignDecisionTable(names, latestRun) {
  if (!names || names.length === 0) {
    return '<p class="muted">定義なし</p>';
  }

  const decisions = latestRun?.decisions || [];
  const rows = names
    .map((name) => {
      const item = decisions.find((decision) => decision.label === name);
      return `
        <tr>
          <td>${escapeHtml(name)}</td>
          <td>${item ? badge("observed", "ok") : badge("missing", "warn")}</td>
          <td>${escapeHtml(item?.result || "未観測")}</td>
        </tr>
      `;
    })
    .join("");

  return `
    <table>
      <thead>
        <tr>
          <th>Decision</th>
          <th>Status</th>
          <th>Latest Result</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderDesignIO(flow) {
  return `
    <div class="flow-columns">
      <section>
        <h4>Inputs</h4>
        <div class="tag-list">${formatList(flow.inputs, "定義なし")}</div>
      </section>
      <section>
        <h4>Outputs</h4>
        <div class="tag-list">${formatList(flow.outputs, "定義なし")}</div>
      </section>
    </div>
  `;
}

function skillRowId(flowName, skillId) {
  return `skill-${flowName}-${skillId}`.replace(/[^a-zA-Z0-9_-]+/g, "-");
}

function renderSkillDefinitionTable(flow) {
  const skills = flow.skill_definitions || [];
  if (!skills || skills.length === 0) {
    return '<p class="muted">この Flow に紐づく Skill 定義はありません。</p>';
  }

  const rows = skills
    .map(
      (skill) => `
        <tr id="${skillRowId(flow.name, skill.skill_id)}">
          <td><strong>${escapeHtml(skill.skill_id)}</strong></td>
          <td>${escapeHtml(skill.summary || "-")}</td>
          <td>${escapeHtml(skill.use_when || "-")}</td>
          <td>${escapeHtml(skill.input || "-")}</td>
          <td>${escapeHtml(skill.output || "-")}</td>
          <td>${escapeHtml(skill.constraints || "-")}</td>
          <td>
            ${skill.meta_path ? `<a class="table-doc-link" href="./repo/${escapeHtml(skill.meta_path)}" target="_blank" rel="noreferrer">meta.md</a>` : ""}
            ${skill.meta_path ? `<a class="table-doc-link" href="./repo/${escapeHtml(skill.meta_path.replace(/meta\.md$/i, "SKILL.md"))}" target="_blank" rel="noreferrer">SKILL.md</a>` : ""}
          </td>
        </tr>
      `
    )
    .join("");

  return `
    <table>
      <thead>
        <tr>
          <th>Skill</th>
          <th>Summary</th>
          <th>Use When</th>
          <th>Input</th>
          <th>Output</th>
          <th>Constraints</th>
          <th>Docs</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderInlineSkillDetail(flowName, skill) {
  const metaLink = skill.meta_path ? `./repo/${skill.meta_path}` : "";
  const skillDocPath = skill.meta_path
    ? skill.meta_path.replace(/meta\.md$/i, "SKILL.md")
    : "";
  const skillDocLink = skillDocPath ? `./repo/${skillDocPath}` : "";
  return `
    <div class="inline-skill-detail">
      <div class="skill-card-head">
        <div>
          <p class="eyebrow">Skill</p>
          <h4>${escapeHtml(skill.skill_id)}</h4>
        </div>
        <div class="skill-card-tags">
          ${skill.tags ? badge(skill.tags, "active") : ""}
          ${skillDocLink ? `<a class="skill-doc-link" href="${escapeHtml(skillDocLink)}" target="_blank" rel="noreferrer">SKILL.md</a>` : ""}
          ${metaLink ? `<a class="skill-doc-link" href="${escapeHtml(metaLink)}" target="_blank" rel="noreferrer">meta.md</a>` : ""}
        </div>
      </div>
      <p class="skill-card-summary">${escapeHtml(skill.summary || "-")}</p>
      <div class="flow-columns">
        <section>
          <h4>Use When</h4>
          <p class="skill-card-text">${escapeHtml(skill.use_when || "-")}</p>
          <h4>Constraints</h4>
          <p class="skill-card-text">${escapeHtml(skill.constraints || "-")}</p>
        </section>
        <section>
          <h4>Input</h4>
          <p class="skill-card-text">${escapeHtml(skill.input || "-")}</p>
          <h4>Output</h4>
          <p class="skill-card-text">${escapeHtml(skill.output || "-")}</p>
        </section>
      </div>
    </div>
  `;
}

function sequenceRowKey(flowName, step) {
  return `${flowName}::${step}`;
}

function renderSequenceTable(flow) {
  if (!flow.sequence || flow.sequence.length === 0) {
    return '<p class="muted">sequence 定義なし</p>';
  }

  const skillMap = new Map((flow.skill_definitions || []).map((skill) => [skill.skill_id, skill]));
  const rows = flow.sequence.map((step, index) => {
    const mappedSkillId = flow.step_skill_map?.[step] || "";
    const mappedSkill = mappedSkillId ? skillMap.get(mappedSkillId) : null;
    const rowKey = sequenceRowKey(flow.name, step);
    const expanded = expandedSequenceSkills.has(rowKey);

    const mainRow = `
      <tr class="${mappedSkill ? "sequence-clickable-row" : ""}" ${mappedSkill ? `data-sequence-row="${escapeHtml(rowKey)}"` : ""}>
        <td>${index + 1}</td>
        <td>${escapeHtml(step)}</td>
        <td>${
          mappedSkill
            ? `<button type="button" class="sequence-skill-button" data-sequence-row="${escapeHtml(rowKey)}">${escapeHtml(mappedSkill.skill_id)}</button>`
            : '<span class="muted">なし</span>'
        }</td>
        <td>${mappedSkill ? badge(expanded ? "open" : "show", expanded ? "ok" : "default") : '<span class="muted">-</span>'}</td>
      </tr>
    `;

    if (!mappedSkill || !expanded) {
      return mainRow;
    }

    return `
      ${mainRow}
      <tr class="sequence-detail-row">
        <td colspan="4">
          ${renderInlineSkillDetail(flow.name, mappedSkill)}
        </td>
      </tr>
    `;
  }).join("");

  return `
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Step</th>
          <th>Skill</th>
          <th>Detail</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderStepStateTable(flow, latestRun) {
  const rows = deriveStepRows(flow, latestRun)
    .map(
      (row) => `
        <tr>
          <td>${escapeHtml(row.step)}</td>
          <td>${badge(row.visited ? "passed" : "missing", row.visited ? "ok" : "warn")}</td>
          <td>${row.coverage}/${flow.project_run_count}</td>
          <td>${formatList(row.relatedPaths.map((item) => `${item.name} x${item.count}`), "なし")}</td>
          <td>${renderChecklistCell(row.checklist)}</td>
        </tr>
      `
    )
    .join("");

  return `
    <table>
      <thead>
        <tr>
          <th>Step</th>
          <th>Latest Run</th>
          <th>Coverage</th>
          <th>Path</th>
          <th>Checklist</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderProjectFlowStates(projectFlows) {
  if (!projectFlows.length) {
    projectFlowStates.innerHTML = `<p class="empty-state">選択中 project の Flow 実行はありません。</p>`;
    return;
  }

  projectFlowStates.innerHTML = "";
  for (const flow of projectFlows) {
    const latestRun = flow.project_latest_run;
    const completionRate = percent(flow.project_run_count - flow.project_incomplete_count, flow.project_run_count);
    const decisionRate = percent(
      flow.project_runs.filter((run) => run.decisions.length > 0).length,
      flow.project_run_count
    );
    const checklistRate = percent(
      flow.project_runs.filter((run) => run.checklist_usage.length > 0).length,
      flow.project_run_count
    );

    const coverageBars = flow.project_step_coverage
      .map((item) => {
        const ratio = percent(item.run_count, flow.project_run_count);
        return `
          <div class="coverage-row">
            <div class="coverage-meta">
              <span>${escapeHtml(item.step)}</span>
              <span>${item.run_count}/${flow.project_run_count}</span>
            </div>
            <div class="coverage-bar"><span style="width:${ratio}%"></span></div>
          </div>
        `;
      })
      .join("");

    const logging = {
      decisions: preferredLoggingNames(flow, "decisions"),
      checklists: preferredLoggingNames(flow, "checklists"),
      paths: preferredLoggingNames(flow, "paths"),
    };
    const article = document.createElement("article");
    article.className = "flow-card";
    article.innerHTML = `
      <div class="flow-card-head">
        <div>
          <p class="flow-phase">${escapeHtml(flow.phase || "unknown")}</p>
          <h3>${escapeHtml(flow.name)}</h3>
          <p class="flow-meta">${escapeHtml(flow.flow_id)} / latest ${escapeHtml(latestRun?.latest_at || "-")}</p>
        </div>
        <div class="flow-metrics">
          ${badge(`state ${runStateLabel(latestRun)}`, classifyRun(latestRun))}
          ${badge(`runs ${flow.project_run_count}`, "active")}
          ${badge(`completion ${completionRate}%`, completionRate === 100 ? "ok" : "warn")}
          ${badge(`decision ${decisionRate}%`, decisionRate > 0 ? "active" : "muted")}
          ${badge(`checklist ${checklistRate}%`, checklistRate > 0 ? "active" : "muted")}
        </div>
      </div>
      <div class="flow-columns">
        <section>
          <h4>Flow State</h4>
          <div class="tag-list">
            ${badge(`latest run ${latestRun?.run_key.split("::").slice(-1)[0] || "-"}`, "default")}
            ${badge(`missing ${latestRun?.missing_steps.length || 0}`, latestRun?.missing_steps.length ? "warn" : "ok")}
            ${badge(`paths ${latestRun?.traversed_paths.length || 0}`, latestRun?.traversed_paths.length ? "active" : "muted")}
          </div>
          <h4>Latest Missing Steps</h4>
          <div class="tag-list">${formatList(latestRun?.missing_steps || [], "なし")}</div>
          <h4>Latest Paths</h4>
          <div class="tag-list">${formatList(latestRun?.traversed_paths || [], "未記録")}</div>
        </section>
        <section>
          <h4>Step Coverage In This Project</h4>
          ${coverageBars || '<p class="muted">sequence 定義なし</p>'}
        </section>
      </div>
      <div class="flow-runs">
        <h4>Step Table</h4>
        ${renderStepStateTable(flow, latestRun)}
      </div>
      <div class="flow-columns">
        <section>
          <h4>Decision Logs</h4>
          <div class="tag-list">${formatList(logging.decisions, "追加不要")}</div>
          <h4>Checklist Logs</h4>
          <div class="tag-list">${formatList(logging.checklists, "追加不要")}</div>
        </section>
        <section>
          <h4>Path Logs</h4>
          <div class="tag-list">${formatList(logging.paths, "追加不要")}</div>
          <h4>Observed Paths</h4>
          ${renderPathTable(flow.project_paths)}
        </section>
      </div>
      <div class="flow-runs">
        <h4>Run Snapshot</h4>
        ${renderRunChips(flow.project_runs)}
      </div>
    `;
    projectFlowStates.appendChild(article);
  }
}

function renderProjectFlowDesign(projectFlows) {
  if (!projectFlows.length) {
    projectFlowDesign.innerHTML = `<p class="empty-state">選択中 project の Flow 設計対象はありません。</p>`;
    return;
  }

  projectFlowDesign.innerHTML = "";
  for (const flow of projectFlows) {
    const latestRun = flow.project_latest_run;
    const logging = {
      decisions: preferredLoggingNames(flow, "decisions"),
      checklists: preferredLoggingNames(flow, "checklists"),
      paths: preferredLoggingNames(flow, "paths"),
    };
    const article = document.createElement("article");
    article.className = "flow-card";
    article.innerHTML = `
      <div class="flow-card-head">
        <div>
          <p class="flow-phase">${escapeHtml(flow.phase || "unknown")}</p>
          <h3>${escapeHtml(flow.name)}</h3>
          <p class="flow-meta">${escapeHtml(flow.flow_id)} / AI 単体責務の定義確認</p>
        </div>
        <div class="flow-metrics">
          ${badge(`inputs ${flow.inputs.length}`, flow.inputs.length ? "active" : "muted")}
          ${badge(`outputs ${flow.outputs.length}`, flow.outputs.length ? "active" : "muted")}
          ${badge(`decisions ${logging.decisions.length}`, logging.decisions.length ? "active" : "muted")}
          ${badge(`checklists ${logging.checklists.length}`, logging.checklists.length ? "active" : "muted")}
        </div>
      </div>
      ${renderDesignIO(flow)}
      <div class="flow-runs">
        <h4>Sequence</h4>
        ${renderSequenceTable(flow)}
      </div>
      <div class="flow-runs">
        <h4>Skill Definition Table</h4>
        ${renderSkillDefinitionTable(flow)}
      </div>
      <div class="flow-columns">
        <section>
          <h4>Decision Responsibility</h4>
          ${renderDesignDecisionTable(logging.decisions, latestRun)}
        </section>
        <section>
          <h4>Checklist Responsibility</h4>
          ${renderDesignChecklistTable(logging.checklists, latestRun)}
        </section>
      </div>
      <div class="flow-columns">
        <section>
          <h4>Path Responsibility</h4>
          ${renderPathTable((flow.project_paths || []).length ? flow.project_paths : logging.paths.map((name) => ({ name, count: 0 })))}
        </section>
        <section>
          <h4>Control Rules</h4>
          <div class="tag-list">${formatList(flow.control_rules, "定義なし")}</div>
        </section>
      </div>
    `;
    projectFlowDesign.appendChild(article);
  }

  for (const row of projectFlowDesign.querySelectorAll("[data-sequence-row]")) {
    row.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-sequence-row]");
      const rowKey = trigger?.getAttribute("data-sequence-row") || row.getAttribute("data-sequence-row");
      if (!rowKey) {
        return;
      }
      if (expandedSequenceSkills.has(rowKey)) {
        expandedSequenceSkills.delete(rowKey);
      } else {
        expandedSequenceSkills.add(rowKey);
      }
      renderProjectFlowDesign(projectFlows);
    });
  }

}

function renderProjectRunHistory(projectRuns) {
  if (!projectRuns.length) {
    projectRunHistory.innerHTML = `<p class="empty-state">run 履歴はありません。</p>`;
    return;
  }

  const rows = projectRuns
    .map(
      (run) => `
        <tr>
          <td>${escapeHtml(run.latest_at || "-")}</td>
          <td>${escapeHtml(run.flow_name)}</td>
          <td>${escapeHtml(run.run_key.split("::").slice(-1)[0])}</td>
          <td>${badge(runStateLabel(run), classifyRun(run))}</td>
          <td>${run.event_count}</td>
          <td>${run.decisions.length}</td>
          <td>${run.checklist_usage.length}</td>
          <td>${formatList(run.traversed_paths, "未記録")}</td>
          <td>${formatList(run.missing_steps, "なし")}</td>
        </tr>
      `
    )
    .join("");

  projectRunHistory.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Latest</th>
          <th>Flow</th>
          <th>Run</th>
          <th>State</th>
          <th>Events</th>
          <th>Decisions</th>
          <th>Checklists</th>
          <th>Paths</th>
          <th>Missing Steps</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderProjectWorkspace() {
  if (!dashboardData) {
    return;
  }

  const project = dashboardData.project_summaries.find((item) => item.project === selectedProject)
    || dashboardData.project_summaries[0]
    || null;

  selectedProject = project?.project || "";
  renderProjectSelector(dashboardData);

  const projectRuns = dashboardData.runs
    .filter((run) => run.project === selectedProject)
    .sort((left, right) => right.latest_at.localeCompare(left.latest_at));
  const projectFlows = deriveProjectFlowStates(dashboardData, selectedProject);

  renderProjectSummary(dashboardData, project, projectFlows, projectRuns);
  renderProjectFlowStates(projectFlows);
  renderProjectRunHistory(projectRuns);
  renderProjectFlowDesign(projectFlows);
  renderViewVisibility();
}

async function loadDashboard() {
  generatedAt.textContent = "読み込み中...";
  const response = await fetch("./api/dashboard");
  dashboardData = await response.json();
  if (!selectedProject) {
    selectedProject = dashboardData.project_summaries[0]?.project || "";
  }
  renderSummary(dashboardData);
  renderTabs();
  renderProjectWorkspace();
  generatedAt.textContent = `Last update: ${dashboardData.generated_at}`;
}

refreshButton.addEventListener("click", () => {
  loadDashboard().catch((error) => {
    generatedAt.textContent = `読込失敗: ${error.message}`;
  });
});

projectSelector?.addEventListener("change", (event) => {
  selectedProject = event.target.value || "";
  renderProjectWorkspace();
});

loadDashboard().catch((error) => {
  generatedAt.textContent = `読込失敗: ${error.message}`;
});
