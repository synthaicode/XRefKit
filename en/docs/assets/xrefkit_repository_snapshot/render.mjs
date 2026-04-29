import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("en/docs/assets/xrefkit_repository_snapshot");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>XRefKit Repository Snapshot</title>
  <style>${css}</style>
</head>
<body>
  <main class="canvas">
    <header class="header">
      <div>
        <h1>An operating foundation that keeps AI work controlled, traceable, and reviewable.</h1>
        <p class="subtitle">Current repository snapshot: control assets define the work, AI roles execute and check it, guardrails stop boundary drift, and humans decide trade-offs.</p>
        <div class="snapshot">Repository snapshot: 2026-04-29</div>
      </div>
      <div class="brand">XRefKit</div>
    </header>

    <section class="main-grid">
      <section class="panel assets">
        <div class="panel-title">Control assets</div>
        <div class="panel-body">
          <div class="asset-list">
            <div class="asset"><div class="ico">F</div><strong>Flow</strong></div>
            <div class="asset"><div class="ico">C</div><strong>Capability</strong></div>
            <div class="asset"><div class="ico">S</div><strong>Skill</strong></div>
            <div class="asset"><div class="ico">K</div><strong>Knowledge</strong></div>
            <div class="asset"><div class="ico">SRC</div><strong>Sources</strong></div>
            <div class="asset"><div class="ico">XID</div><strong>Stable references</strong></div>
          </div>
          <div class="memory-box">
            <div class="no-memory"></div>
            <h2>Do not rely on memory</h2>
            <p>AI loads required knowledge, rules, skills, and workflow definitions on demand.</p>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-title">Controlled AI work pipeline</div>
        <div class="panel-body pipeline">
          <div class="left-numbers">
            <div class="num">1</div>
            <div class="num">2</div>
            <div class="num">3</div>
            <div class="num">4</div>
            <div class="num">5</div>
            <div class="num">6</div>
          </div>
          <div class="steps">
            <div class="step"><div class="ico">CTX</div><div><h3>Load required context</h3><p>Retrieve exact assets, rules, and evidence needed for the task.</p></div></div>
            <div class="step"><div class="ico">AI</div><div><h3>AI Executor</h3><p>Execute under defined flow, capability, skill, and procedure.</p></div></div>
            <div class="step"><div class="ico">QA</div><div><h3>AI Reviewer / Checker</h3><p>Verify evidence, boundaries, assumptions, output quality, and handoff readiness.</p></div></div>
            <div class="step"><div class="ico">G</div><div><h3>Quality Gate</h3><p>Apply policy and quality rules. Determine pass, fail, or escalate.</p></div></div>
            <div class="step"><div class="ico">LOG</div><div><h3>Record assumptions</h3><p>Log constraints, unknowns, decisions, and dependencies.</p></div></div>
            <div class="step"><div class="ico">OUT</div><div><h3>Produce output</h3><p>Generate artifacts with links to sources, evidence, and records.</p></div></div>
          </div>
          <aside class="side-rule">
            <h3>No unsupported guessing</h3>
            <div class="rule-card">Unknowns stay explicit</div>
            <div class="rule-card">Missing evidence is blocked</div>
            <div class="stop">STOP</div>
            <p class="small">Unsupported assumptions are stopped and made visible instead of guessed.</p>
          </aside>
          <div class="ai-first">
            <p><strong>AI-to-AI verification first</strong><br><span class="small">Execution and checking are separate AI roles before humans are involved.</span></p>
            <p><strong>Human review only where needed</strong><br><span class="small">Escalations, approvals, and trade-off decisions return to humans.</span></p>
          </div>
        </div>
      </section>

      <section class="panel guard">
        <div class="panel-title">Context Direction Security Guard</div>
        <div class="panel-body">
          <div class="guard-stack">
            <div class="direction">
              <div class="guard-item">Flow</div>
              <div class="down">↓</div>
              <div class="guard-item">Capability</div>
              <div class="down">↓</div>
              <div class="guard-item">Skill</div>
              <div class="down">↓</div>
              <div class="guard-item">External input</div>
              <div class="down">↓</div>
              <div class="guard-item">Output</div>
            </div>
            <div>
              <div class="shield">✓</div>
              <div class="guard-copy">Guard protects direction</div>
            </div>
          </div>
          <div class="blocked">
            <p><strong>Blocked:</strong> lower-layer input cannot rewrite higher-layer intent, authority, scope, capability, skill procedure, or escalation path.</p>
          </div>
        </div>
      </section>

      <section class="panel human">
        <div class="panel-title">Human decision layer</div>
        <div class="panel-body">
          <div class="human-flow">
            <div class="human-card"><div class="ico">!</div><div><h3>Escalations</h3><p>AI escalates with reasons, evidence, and options.</p></div></div>
            <div class="human-card"><div class="ico">?</div><div><h3>Unknowns / risks</h3><p>Risks, missing evidence, and impact remain visible.</p></div></div>
            <div class="bracket">Trade-offs return to humans</div>
            <div class="human-card"><div class="ico">BAL</div><div><h3>Trade-off decision</h3><p>AI prepares options, evidence, risks, and recommendations.</p></div></div>
            <div class="human-card"><div class="ico">OK</div><div><h3>Human approval</h3><p>Humans decide risk, scope, priority, and business trade-offs.</p></div></div>
            <div class="bracket">Human approval</div>
            <div class="human-card"><div class="ico">GO</div><div><h3>Approved handoff</h3><p>Release the output for the next action or recipient.</p></div></div>
            <div class="human-card"><div class="ico">AUD</div><div><h3>Audit trail</h3><p>Record decisions, evidence, checks, and approvals.</p></div></div>
          </div>
        </div>
      </section>
    </section>

    <section class="xid-band">
      <div class="band-cell"><div class="ico">ID</div><p class="small"><strong>Persistent identifiers</strong><br>for control assets, sources, and outputs.</p></div>
      <div class="band-cell"><div class="ico">MAP</div><p class="small"><strong>Traceability</strong><br>across flows, capabilities, skills, evidence, and outputs.</p></div>
      <div class="band-center"><h2>Stable XID references</h2><p>Durable reference layer that supports controlled AI work</p></div>
      <div class="band-cell"><div class="ico">EVD</div><p class="small"><strong>Evidence links</strong><br>from assumptions to sources, checks, and decisions.</p></div>
      <div class="band-cell"><div class="ico">AUD</div><p class="small"><strong>Auditability</strong><br>for reproducibility and handoff continuity.</p></div>
    </section>

    <section class="principles">
      <div class="principle"><div class="num">1</div><div><h3>AI does not rely on memory.</h3><p>Tasks load required context from control assets.</p></div></div>
      <div class="principle"><div class="num">2</div><div><h3>Execution and checking are separated.</h3><p>Different AI roles reduce responsibility mixing.</p></div></div>
      <div class="principle"><div class="num">3</div><div><h3>AI verifies before human review.</h3><p>Humans review only escalations and decisions.</p></div></div>
      <div class="principle"><div class="num">4</div><div><h3>AI does not guess.</h3><p>Unknowns and missing evidence are stopped or surfaced.</p></div></div>
      <div class="principle"><div class="num">5</div><div><h3>Guard prevents redirection.</h3><p>External input cannot override higher-layer control.</p></div></div>
      <div class="principle"><div class="num">6</div><div><h3>Trade-offs return to humans.</h3><p>Humans approve actions and accept responsibility.</p></div></div>
    </section>
  </main>
</body>
</html>`;

await fs.writeFile(path.join(dir, "xrefkit_repository_snapshot.html"), html, "utf8");
