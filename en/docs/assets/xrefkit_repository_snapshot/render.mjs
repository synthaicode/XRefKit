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
        <h1>A repository OS for controlled Skill-backed AI work.</h1>
        <p class="subtitle">Current repository snapshot: Skills now open through a runtime envelope, create work items and evidence, separate execution from checking, and close only after machine-readable gates pass.</p>
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
            <div class="asset"><div class="ico">LOG</div><strong>Sessions</strong></div>
            <div class="asset"><div class="ico">XID</div><strong>Stable references</strong></div>
          </div>
          <div class="memory-box">
            <div class="no-memory"></div>
            <h2>Do not rely on memory</h2>
            <p>Startup routing loads the current policy, Skill metadata, knowledge, evidence, and handoff source before work continues.</p>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-title">Skill runtime OS pipeline</div>
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
            <div class="step"><div class="ico">RUN</div><div><h3>Load gate</h3><p><code>fm skill run</code> validates the meta file and creates the runtime log before the Skill is opened.</p></div></div>
            <div class="step"><div class="ico">WI</div><div><h3>Concrete worklist</h3><p>Task-specific work items are added and must become done or escalated before closure.</p></div></div>
            <div class="step"><div class="ico">R</div><div><h3>Role separation</h3><p>Executor, checker, and handoff owner are assigned and enforced on phase updates.</p></div></div>
            <div class="step"><div class="ico">ART</div><div><h3>Artifacts and evidence</h3><p>Output and evidence links are required; checks, sources, judgments, and handoff links stay explicit.</p></div></div>
            <div class="step"><div class="ico">C</div><div><h3>Concern register</h3><p>Unknowns, risks, and non-trivial judgments are recorded instead of hidden in prose.</p></div></div>
            <div class="step"><div class="ico">QG</div><div><h3>Close and audit</h3><p><code>fm skill close</code> and the FM quality gate reject incomplete or non-envelope runs.</p></div></div>
          </div>
          <aside class="side-rule">
            <h3>Closure is refused when</h3>
            <div class="rule-card">Execution, check, or handoff is incomplete</div>
            <div class="rule-card">Work items or artifacts are missing</div>
            <div class="rule-card">Unknowns or non-escalated risks remain</div>
            <div class="stop">STOP</div>
            <p class="small">Non-trivial judgments must link to evidence before the run can close.</p>
          </aside>
          <div class="ai-first">
            <p><strong>AI-to-AI verification first</strong><br><span class="small">Execution and checking are separate runtime responsibilities before human review.</span></p>
            <p><strong>Machine-readable handoff</strong><br><span class="small">The next startup must verify source closure before continuing from a handoff.</span></p>
          </div>
        </div>
      </section>

      <section class="panel guard">
        <div class="panel-title">Startup and direction guard</div>
        <div class="panel-body">
          <div class="guard-stack">
            <div class="direction">
              <div class="guard-item">Startup policy</div>
              <div class="down">v</div>
              <div class="guard-item">Skill meta + OS contract</div>
              <div class="down">v</div>
              <div class="guard-item">Runtime envelope</div>
              <div class="down">v</div>
              <div class="guard-item">External task input</div>
              <div class="down">v</div>
              <div class="guard-item">Auditable output</div>
            </div>
            <div>
              <div class="shield">OK</div>
              <div class="guard-copy">Higher layers control lower layers</div>
            </div>
          </div>
          <div class="blocked">
            <p><strong>Blocked:</strong> external input cannot rewrite the active flow, capability, Skill procedure, scope, authority, or escalation path.</p>
            <p><strong>Handoff source:</strong> receiving startup must confirm the prior run's closure and handoff before using it as context.</p>
          </div>
        </div>
      </section>

      <section class="panel human">
        <div class="panel-title">Human boundary and maturity</div>
        <div class="panel-body">
          <div class="human-flow">
            <div class="human-card"><div class="ico">DR</div><div><h3>Draft</h3><p>Hypothesis record. Not load-ready until the operating boundary is tested.</p></div></div>
            <div class="human-card"><div class="ico">TR</div><div><h3>Trial</h3><p>Runnable with observation links; weak or ambiguous boundaries are discovered through use.</p></div></div>
            <div class="human-card"><div class="ico">ST</div><div><h3>Stable</h3><p>Runtime envelope, guard policy, references, and handoff boundary are explicit.</p></div></div>
            <div class="human-card"><div class="ico">GV</div><div><h3>Governed</h3><p>Stable Skill plus governance evidence and auditable responsibility linkage.</p></div></div>
            <div class="bracket">Trade-offs return to humans</div>
            <div class="human-card"><div class="ico">H</div><div><h3>Human decisions</h3><p>Humans decide risk acceptance, scope changes, priority, and business trade-offs.</p></div></div>
            <div class="human-card"><div class="ico">A</div><div><h3>Audit trail</h3><p>Logs preserve decisions, evidence, checks, concerns, approvals, and handoffs.</p></div></div>
          </div>
        </div>
      </section>
    </section>

    <section class="xid-band">
      <div class="band-cell"><div class="ico">XID</div><p class="small"><strong>Stable anchors</strong><br>for docs, policies, skills, sources, and outputs.</p></div>
      <div class="band-cell"><div class="ico">LOG</div><p class="small"><strong>Session records</strong><br>for runtime state, role actions, and closure events.</p></div>
      <div class="band-center"><h2>Runtime evidence layer</h2><p>Traceable work foundation across Skills, artifacts, checks, concerns, and handoffs</p></div>
      <div class="band-cell"><div class="ico">JDG</div><p class="small"><strong>Judgment records</strong><br>for non-trivial reasoning and human-facing decisions.</p></div>
      <div class="band-cell"><div class="ico">CI</div><p class="small"><strong>Quality audit</strong><br>detects non-envelope logs and unfinished Skill runs.</p></div>
    </section>

    <section class="principles">
      <div class="principle"><div class="num">1</div><div><h3>Run the envelope first.</h3><p>Skill-backed work starts with <code>fm skill run</code>, not direct procedure use.</p></div></div>
      <div class="principle"><div class="num">2</div><div><h3>Work items are real.</h3><p>Generic phases are not enough to close a run.</p></div></div>
      <div class="principle"><div class="num">3</div><div><h3>Execution and checking split.</h3><p>Assigned roles enforce separate responsibility.</p></div></div>
      <div class="principle"><div class="num">4</div><div><h3>Concerns must resolve.</h3><p>Unknowns, risks, and judgments are closure inputs.</p></div></div>
      <div class="principle"><div class="num">5</div><div><h3>Handoff source is checked.</h3><p>Receivers verify prior closure before continuing.</p></div></div>
      <div class="principle"><div class="num">6</div><div><h3>Maturity means boundary clarity.</h3><p>Skills mature as the human/Skill boundary becomes explicit.</p></div></div>
    </section>
  </main>
</body>
</html>`;

await fs.writeFile(path.join(dir, "xrefkit_repository_snapshot.html"), html, "utf8");
