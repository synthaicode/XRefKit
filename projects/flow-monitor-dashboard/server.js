const fs = require("fs");
const path = require("path");
const http = require("http");
const { URL } = require("url");

const HOST = process.env.HOST || "127.0.0.1";
const PORT = Number(process.env.PORT || "3087");
const APP_DIR = __dirname;
const REPO_ROOT = path.resolve(APP_DIR, "..", "..");
const PROJECTS_DIR = path.join(REPO_ROOT, "projects");
const FLOWS_DIR = path.join(REPO_ROOT, "flows");
const PUBLIC_DIR = path.join(APP_DIR, "public");
const LOG_PRESETS_FILE = path.join(APP_DIR, "flow-log-presets.json");
const FLOW_SKILL_MAP_FILE = path.join(APP_DIR, "flow-skill-map.json");
const FLOW_STEP_SKILL_MAP_FILE = path.join(APP_DIR, "flow-step-skill-map.json");
const SKILLS_DIR = path.join(REPO_ROOT, "skills");
const TRACE_FILE_PATTERN = /(?:flow-events|flow-monitor|flow-monitoring|trace|events)\.(?:jsonl|json)$/i;
const SKIP_DIRS = new Set(["node_modules", ".git", ".next", "dist", "build"]);

const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/plain; charset=utf-8",
  ".svg": "image/svg+xml",
};

function readDirSafe(targetDir) {
  try {
    return fs.readdirSync(targetDir, { withFileTypes: true });
  } catch {
    return [];
  }
}

function readFileSafe(filePath) {
  try {
    return fs.readFileSync(filePath, "utf8");
  } catch {
    return "";
  }
}

function extractScalar(lines, key) {
  const prefix = `${key}:`;
  for (const line of lines) {
    if (line.startsWith(prefix)) {
      return line.slice(prefix.length).trim();
    }
  }
  return "";
}

function extractList(lines, key) {
  const values = [];
  const startPrefix = `${key}:`;
  let inSection = false;
  let sectionIndent = 0;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const indent = line.length - line.trimStart().length;

    if (!inSection) {
      if (line.startsWith(startPrefix)) {
        inSection = true;
        sectionIndent = indent;
      }
      continue;
    }

    if (indent <= sectionIndent) {
      break;
    }

    if (trimmed.startsWith("- ")) {
      values.push(trimmed.slice(2).trim());
    }
  }

  return values;
}

function normalizeKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function loadFlowDefinitions() {
  const logPresets = loadLogPresets();
  const flowSkillMap = loadFlowSkillMap();
  const flowStepSkillMap = loadFlowStepSkillMap();
  const skillCatalog = loadSkillCatalog();
  return readDirSafe(FLOWS_DIR)
    .filter((entry) => entry.isFile() && entry.name.endsWith(".yaml"))
    .map((entry) => {
      const filePath = path.join(FLOWS_DIR, entry.name);
      const content = readFileSafe(filePath);
      const lines = content.split(/\r?\n/);
      const flow = {
        file_name: entry.name,
        flow_id: extractScalar(lines, "flow_id"),
        name: extractScalar(lines, "name"),
        phase: extractScalar(lines, "phase"),
        doc_xid: extractScalar(lines, "doc_xid"),
        sequence: extractList(lines, "sequence"),
        control_rules: extractList(lines, "control_rules"),
        inputs: extractList(lines, "inputs"),
        outputs: extractList(lines, "outputs"),
      };
      flow.slug = normalizeKey(flow.name || flow.flow_id || entry.name.replace(/\.yaml$/i, ""));
      flow.logging_recommendation = logPresets[flow.name] || {
        decisions: [],
        checklists: [],
        paths: [],
      };
      flow.skill_definitions = (flowSkillMap[flow.name] || [])
        .map((skillId) => skillCatalog[skillId])
        .filter(Boolean);
      flow.step_skill_map = flowStepSkillMap[flow.name] || {};
      return flow;
    })
    .sort((left, right) => left.name.localeCompare(right.name));
}

function loadLogPresets() {
  try {
    return JSON.parse(readFileSafe(LOG_PRESETS_FILE));
  } catch {
    return {};
  }
}

function loadFlowSkillMap() {
  try {
    return JSON.parse(readFileSafe(FLOW_SKILL_MAP_FILE));
  } catch {
    return {};
  }
}

function loadFlowStepSkillMap() {
  try {
    return JSON.parse(readFileSafe(FLOW_STEP_SKILL_MAP_FILE));
  } catch {
    return {};
  }
}

function parseMetaField(lines, key) {
  const prefix = `- ${key}:`;
  for (const line of lines) {
    if (line.startsWith(prefix)) {
      return line.slice(prefix.length).trim().replace(/^`|`$/g, "");
    }
  }
  return "";
}

function loadSkillCatalog() {
  const catalog = {};
  for (const entry of readDirSafe(SKILLS_DIR)) {
    if (!entry.isDirectory()) {
      continue;
    }
    const metaPath = path.join(SKILLS_DIR, entry.name, "meta.md");
    if (!fs.existsSync(metaPath)) {
      continue;
    }
    const lines = readFileSafe(metaPath).split(/\r?\n/);
    const skill = {
      skill_id: parseMetaField(lines, "skill_id"),
      summary: parseMetaField(lines, "summary"),
      use_when: parseMetaField(lines, "use_when"),
      input: parseMetaField(lines, "input"),
      output: parseMetaField(lines, "output"),
      constraints: parseMetaField(lines, "constraints"),
      tags: parseMetaField(lines, "tags"),
      skill_doc: parseMetaField(lines, "skill_doc"),
      meta_path: path.relative(REPO_ROOT, metaPath).replace(/\\/g, "/"),
    };
    if (skill.skill_id) {
      catalog[skill.skill_id] = skill;
    }
  }
  return catalog;
}

function walkForTraceFiles(currentDir, traceFiles) {
  for (const entry of readDirSafe(currentDir)) {
    const absolutePath = path.join(currentDir, entry.name);
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name) || absolutePath === APP_DIR) {
        continue;
      }
      walkForTraceFiles(absolutePath, traceFiles);
      continue;
    }

    if (!TRACE_FILE_PATTERN.test(entry.name)) {
      continue;
    }

    traceFiles.push(absolutePath);
  }
}

function loadTraceFiles() {
  const traceFiles = [];
  walkForTraceFiles(PROJECTS_DIR, traceFiles);
  return traceFiles.filter((filePath) => !filePath.startsWith(APP_DIR));
}

function parseJsonl(content, filePath) {
  const events = [];
  for (const [index, line] of content.split(/\r?\n/).entries()) {
    const trimmed = line.trim();
    if (!trimmed) {
      continue;
    }
    try {
      events.push(JSON.parse(trimmed));
    } catch {
      events.push({
        type: "parse_error",
        file_path: filePath,
        line_number: index + 1,
        message: trimmed,
      });
    }
  }
  return events;
}

function extractEvents(document, inherited = {}) {
  if (Array.isArray(document)) {
    return document.flatMap((item) => extractEvents(item, inherited));
  }

  if (!document || typeof document !== "object") {
    return [];
  }

  if (Array.isArray(document.runs)) {
    return document.runs.flatMap((run) =>
      extractEvents(run.events || run, {
        ...inherited,
        project: run.project || inherited.project,
        flow_id: run.flow_id || inherited.flow_id,
        flow_name: run.flow_name || run.flow || inherited.flow_name,
        run_id: run.run_id || inherited.run_id,
      })
    );
  }

  if (Array.isArray(document.events)) {
    return document.events.flatMap((event) =>
      extractEvents(event, {
        ...inherited,
        project: document.project || inherited.project,
        flow_id: document.flow_id || inherited.flow_id,
        flow_name: document.flow_name || document.flow || inherited.flow_name,
        run_id: document.run_id || inherited.run_id,
      })
    );
  }

  return [{ ...inherited, ...document }];
}

function parseTraceFile(filePath) {
  const content = readFileSafe(filePath);
  if (!content.trim()) {
    return [];
  }

  const relativePath = path.relative(PROJECTS_DIR, filePath);
  const [projectFolder] = relativePath.split(path.sep);
  const inherited = {
    project: projectFolder || "unknown-project",
    source_file: relativePath.replace(/\\/g, "/"),
  };

  if (filePath.endsWith(".jsonl")) {
    return parseJsonl(content, filePath).map((event) => ({ ...inherited, ...event }));
  }

  try {
    return extractEvents(JSON.parse(content), inherited);
  } catch {
    return [
      {
        ...inherited,
        type: "parse_error",
        message: "Invalid JSON",
      },
    ];
  }
}

function inferFlow(event, flowDefinitions) {
  const eventKeys = [
    event.flow_id,
    event.flow_name,
    event.flow,
    event.workflow,
    event.name,
  ]
    .filter(Boolean)
    .map(normalizeKey);

  for (const flow of flowDefinitions) {
    const flowKeys = [flow.flow_id, flow.name, flow.slug].filter(Boolean).map(normalizeKey);
    if (eventKeys.some((key) => flowKeys.includes(key))) {
      return flow;
    }
  }

  const pathKey = normalizeKey(event.source_file || "");
  return flowDefinitions.find((flow) => pathKey.includes(flow.slug)) || null;
}

function toArray(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (value === undefined || value === null || value === "") {
    return [];
  }
  return [value];
}

function normalizeEvent(rawEvent, flowDefinitions) {
  const flow = inferFlow(rawEvent, flowDefinitions);
  const step = rawEvent.step || rawEvent.step_name || rawEvent.sequence_step || "";
  const pathNames = [
    ...toArray(rawEvent.path),
    ...toArray(rawEvent.route),
    ...toArray(rawEvent.branch),
  ].filter(Boolean);
  const checklist = rawEvent.checklist || rawEvent.checklist_name;
  const checklistCompleted =
    rawEvent.completed_items ??
    rawEvent.checked_items ??
    rawEvent.completed ??
    rawEvent.checklist_completed ??
    null;
  const checklistTotal =
    rawEvent.total_items ??
    rawEvent.total ??
    rawEvent.checklist_total ??
    null;
  const decisionResult =
    rawEvent.decision_result ??
    rawEvent.result ??
    rawEvent.outcome ??
    rawEvent.judgment_result ??
    null;

  return {
    timestamp: rawEvent.timestamp || rawEvent.time || rawEvent.occurred_at || "",
    project: rawEvent.project || "unknown-project",
    source_file: rawEvent.source_file || "",
    flow_id: flow ? flow.flow_id : rawEvent.flow_id || "",
    flow_name: flow ? flow.name : rawEvent.flow_name || rawEvent.flow || rawEvent.workflow || "unknown_flow",
    run_id: rawEvent.run_id || rawEvent.execution_id || path.basename(rawEvent.source_file || "run"),
    type: rawEvent.type || "event",
    status: rawEvent.status || rawEvent.outcome || "",
    step,
    paths: pathNames,
    checklist_name: checklist || "",
    checklist_used: Boolean(checklist || rawEvent.checklist_used),
    checklist_completed: Number.isFinite(checklistCompleted) ? Number(checklistCompleted) : null,
    checklist_total: Number.isFinite(checklistTotal) ? Number(checklistTotal) : null,
    decision_label: rawEvent.decision || rawEvent.judgment || rawEvent.label || "",
    decision_result: decisionResult,
    notes: rawEvent.notes || rawEvent.message || "",
    raw: rawEvent,
    flow_definition: flow,
  };
}

function getRunSummary(runKey, events, flowDefinition) {
  const visitedSteps = new Set();
  const traversedPaths = new Set();
  const decisionResults = [];
  const checklistUsage = [];
  const statuses = new Set();
  const timestamps = [];
  const expectedSteps = new Set(flowDefinition ? flowDefinition.sequence : []);

  for (const event of events) {
    if (event.step) {
      visitedSteps.add(event.step);
    }
    for (const pathName of event.paths) {
      traversedPaths.add(pathName);
      if (expectedSteps.has(pathName)) {
        visitedSteps.add(pathName);
      }
    }
    if (event.decision_result || event.type === "decision") {
      decisionResults.push({
        label: event.decision_label || event.step || "decision",
        result: event.decision_result || event.status || "recorded",
        timestamp: event.timestamp,
      });
    }
    if (event.checklist_used) {
      if (event.checklist_name && expectedSteps.has(event.checklist_name)) {
        visitedSteps.add(event.checklist_name);
      }
      checklistUsage.push({
        name: event.checklist_name || "checklist",
        completed: event.checklist_completed,
        total: event.checklist_total,
      });
    }
    if (event.status) {
      statuses.add(event.status);
    }
    if (event.timestamp) {
      timestamps.push(event.timestamp);
    }
  }

  const missingSteps = [...expectedSteps].filter((step) => !visitedSteps.has(step));

  return {
    run_key: runKey,
    project: events[0]?.project || "",
    flow_id: flowDefinition?.flow_id || events[0]?.flow_id || "",
    flow_name: flowDefinition?.name || events[0]?.flow_name || "",
    started_at: timestamps.length ? [...timestamps].sort()[0] : "",
    latest_at: timestamps.length ? [...timestamps].sort().slice(-1)[0] : "",
    statuses: [...statuses],
    visited_steps: [...visitedSteps],
    missing_steps: missingSteps,
    traversed_paths: [...traversedPaths],
    decisions: decisionResults,
    checklist_usage: checklistUsage,
    event_count: events.length,
  };
}

function buildDashboardData() {
  const flowDefinitions = loadFlowDefinitions();
  const rawEvents = loadTraceFiles()
    .flatMap((filePath) => parseTraceFile(filePath))
    .map((event) => normalizeEvent(event, flowDefinitions));

  const groupedRuns = new Map();
  for (const event of rawEvents) {
    const runKey = [event.project, event.flow_name, event.run_id].join("::");
    const bucket = groupedRuns.get(runKey) || [];
    bucket.push(event);
    groupedRuns.set(runKey, bucket);
  }

  const runs = [...groupedRuns.entries()]
    .map(([runKey, events]) => {
      const flowDefinition = events[0]?.flow_definition || null;
      return getRunSummary(runKey, events, flowDefinition);
    })
    .sort((left, right) => right.latest_at.localeCompare(left.latest_at));

  const flowSummaries = flowDefinitions.map((flow) => {
    const flowRuns = runs.filter((run) => run.flow_name === flow.name || run.flow_id === flow.flow_id);
    const stepCoverage = flow.sequence.map((step) => ({
      step,
      run_count: flowRuns.filter((run) => run.visited_steps.includes(step)).length,
    }));
    const pathCounts = new Map();
    for (const run of flowRuns) {
      for (const pathName of run.traversed_paths) {
        pathCounts.set(pathName, (pathCounts.get(pathName) || 0) + 1);
      }
    }

    return {
      ...flow,
      run_count: flowRuns.length,
      decision_run_count: flowRuns.filter((run) => run.decisions.length > 0).length,
      checklist_run_count: flowRuns.filter((run) => run.checklist_usage.length > 0).length,
      incomplete_run_count: flowRuns.filter((run) => run.missing_steps.length > 0).length,
      step_coverage: stepCoverage,
      traversed_paths: [...pathCounts.entries()]
        .map(([name, count]) => ({ name, count }))
        .sort((left, right) => right.count - left.count),
      recent_runs: flowRuns.slice(0, 6),
    };
  });

  const projectSummaries = [...new Set(runs.map((run) => run.project))]
    .filter(Boolean)
    .map((projectName) => {
      const projectRuns = runs.filter((run) => run.project === projectName);
      return {
        project: projectName,
        run_count: projectRuns.length,
        flow_count: new Set(projectRuns.map((run) => run.flow_name)).size,
        decision_count: projectRuns.reduce((sum, run) => sum + run.decisions.length, 0),
        checklist_count: projectRuns.reduce((sum, run) => sum + run.checklist_usage.length, 0),
        latest_at: projectRuns.map((run) => run.latest_at).sort().slice(-1)[0] || "",
      };
    })
    .sort((left, right) => right.latest_at.localeCompare(left.latest_at));

  return {
    generated_at: new Date().toISOString(),
    monitored_root: path.relative(REPO_ROOT, PROJECTS_DIR).replace(/\\/g, "/"),
    trace_file_pattern: TRACE_FILE_PATTERN.source,
    flow_count: flowDefinitions.length,
    run_count: runs.length,
    project_count: projectSummaries.length,
    flow_summaries: flowSummaries,
    project_summaries: projectSummaries,
    runs: runs.slice(0, 50),
  };
}

function sendJson(response, payload, statusCode = 200) {
  response.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload, null, 2));
}

function sendFile(response, filePath) {
  const extension = path.extname(filePath);
  const contentType = MIME_TYPES[extension] || "application/octet-stream";
  try {
    const content = fs.readFileSync(filePath);
    response.writeHead(200, { "Content-Type": contentType });
    response.end(content);
  } catch {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
}

function sendRepoFile(response, relativePath) {
  const safeRelativePath = relativePath.split("/").join(path.sep);
  const resolved = path.resolve(REPO_ROOT, safeRelativePath);
  if (!resolved.startsWith(REPO_ROOT)) {
    response.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Bad request");
    return;
  }
  sendFile(response, resolved);
}

function resolvePublicPath(urlPath) {
  const cleanPath = urlPath === "/" ? "/index.html" : urlPath;
  const resolved = path.normalize(path.join(PUBLIC_DIR, cleanPath));
  if (!resolved.startsWith(PUBLIC_DIR)) {
    return null;
  }
  return resolved;
}

const server = http.createServer((request, response) => {
  const requestUrl = new URL(request.url, `http://${request.headers.host || "localhost"}`);

  if (requestUrl.pathname === "/api/dashboard") {
    return sendJson(response, buildDashboardData());
  }

  if (requestUrl.pathname.startsWith("/repo/")) {
    const relativePath = decodeURIComponent(requestUrl.pathname.slice("/repo/".length));
    return sendRepoFile(response, relativePath);
  }

  const filePath = resolvePublicPath(requestUrl.pathname);
  if (!filePath) {
    response.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Bad request");
    return;
  }

  sendFile(response, filePath);
});

server.listen(PORT, HOST, () => {
  process.stdout.write(`Flow monitor dashboard is running at http://${HOST}:${PORT}\n`);
});
