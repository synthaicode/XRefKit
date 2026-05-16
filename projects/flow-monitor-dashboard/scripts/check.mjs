import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectDir = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(projectDir, "..", "..");
const require = createRequire(import.meta.url);

const files = [
  "server.js",
  "flow-log-presets.json",
  "flow-skill-map.json",
  "flow-step-skill-map.json",
];

for (const relativePath of files) {
  const fullPath = path.join(projectDir, relativePath);
  const content = fs.readFileSync(fullPath, "utf8");
  if (relativePath.endsWith(".json")) {
    JSON.parse(content);
  }
}

const { buildDashboardData } = require(path.join(projectDir, "server.js"));
const data = buildDashboardData();

assert.equal(typeof data, "object", "dashboard data must be an object");
assert.ok(Array.isArray(data.flow_summaries), "flow_summaries must be an array");
assert.ok(Array.isArray(data.project_summaries), "project_summaries must be an array");
assert.ok(Array.isArray(data.skill_summaries), "skill_summaries must be an array");
assert.ok(Array.isArray(data.runs), "runs must be an array");

// This dashboard exists so humans can inspect real AI/Flow activity from repo data.
assert.ok(data.flow_count > 0, "dashboard must detect at least one flow definition");
assert.ok(data.run_count > 0, "dashboard must detect at least one monitored flow run from projects/");
assert.ok(data.skill_run_count > 0, "dashboard must detect at least one skill runtime log from work/sessions/");
assert.ok(data.project_count > 0, "dashboard must detect at least one monitored project");

const flowWithRuns = data.flow_summaries.find((flow) => (flow.recent_runs || []).length > 0);
assert.ok(flowWithRuns, "at least one flow summary must include recent monitored runs");
assert.ok(Array.isArray(flowWithRuns.step_coverage), "flow summary with runs must include step coverage");

const flowWithSkillRuntime = data.flow_summaries.find((flow) => (flow.skill_runtime_summaries || []).length > 0);
assert.ok(flowWithSkillRuntime, "at least one flow summary must include skill runtime summaries");

const skillWithRecentRun = data.skill_summaries.find((skill) => (skill.recent_runs || []).length > 0);
assert.ok(skillWithRecentRun, "at least one skill summary must include recent runs");
assert.ok(
  skillWithRecentRun.recent_runs.some((run) => run.log_path && run.task !== undefined),
  "skill summary must retain linkable runtime run details for human review"
);
const runtimeRuns = data.skill_summaries.flatMap((skill) => skill.recent_runs || []);
assert.ok(
  runtimeRuns.some((run) => (run.counts?.output_artifacts || 0) > 0),
  "dashboard must expose at least one runtime run with output artifacts"
);
assert.ok(
  runtimeRuns.some((run) => (run.counts?.evidence_artifacts || 0) > 0),
  "dashboard must expose at least one runtime run with evidence artifacts"
);
assert.ok(
  runtimeRuns.some((run) => (run.counts?.handoff_artifacts || 0) > 0),
  "dashboard must expose at least one runtime run with handoff artifacts"
);
assert.ok(
  runtimeRuns.some((run) => (run.counts?.judgments || 0) >= 0 && run.concerns !== undefined),
  "dashboard must retain concern parsing for judgments and unknowns"
);

assert.equal(
  data.monitored_root,
  path.relative(repoRoot, path.join(repoRoot, "projects")).replace(/\\/g, "/"),
  "dashboard must report projects/ as monitored root"
);
