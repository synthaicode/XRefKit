import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/en/assets/xrefkit_repository_snapshot");
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
        <h1>One portable package for XID-directed AI work.</h1>
        <p class="subtitle">XRefKit packages runtime contracts, Skills, tools, catalogs, and an MCP adapter while loading only the selected knowledge an AI needs.</p>
        <div class="snapshot">Repository snapshot: 2026-07-10</div>
      </div>
      <div class="brand">XRefKit</div>
    </header>

    <section class="main-grid">
      <section class="panel assets">
        <div class="panel-title">Unified xrefkit package</div>
        <div class="panel-body">
          <div class="asset-list">
            <div class="asset"><div class="ico">RT</div><strong>xrefkit runtime</strong></div>
            <div class="asset"><div class="ico">S</div><strong>xrefkit skills</strong></div>
            <div class="asset"><div class="ico">T</div><strong>xrefkit tools</strong></div>
            <div class="asset"><div class="ico">MCP</div><strong>xrefkit MCP adapter</strong></div>
            <div class="asset"><div class="ico">CAT</div><strong>Target + finding catalogs</strong></div>
            <div class="asset"><div class="ico">XID</div><strong>Stable references</strong></div>
          </div>
          <div class="memory-box">
            <div class="no-memory"></div>
            <h2>Load lists before bodies</h2>
            <p>Select a target, finding, Skill, or Knowledge XID before expanding detail. Unrelated context stays outside the prompt.</p>
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
            <div class="step"><div class="ico">RUN</div><div><h3>Load gate</h3><p><code>xrefkit skill run</code> validates the meta file and creates the runtime log before the Skill is opened.</p></div></div>
            <div class="step"><div class="ico">WI</div><div><h3>Concrete worklist</h3><p>Task-specific work items are added and must become done or escalated before closure.</p></div></div>
            <div class="step"><div class="ico">R</div><div><h3>Role separation</h3><p>Executor, checker, and handoff owner are assigned and enforced on phase updates.</p></div></div>
            <div class="step"><div class="ico">ART</div><div><h3>Artifacts and evidence</h3><p>Output and evidence links are required; checks, sources, judgments, and handoff links stay explicit.</p></div></div>
            <div class="step"><div class="ico">C</div><div><h3>Concern register</h3><p>Unknowns, risks, and non-trivial judgments are recorded instead of hidden in prose.</p></div></div>
            <div class="step"><div class="ico">QG</div><div><h3>Close and audit</h3><p><code>xrefkit skill close</code> and the XRefKit quality gate reject incomplete or non-envelope runs.</p></div></div>
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
        <div class="panel-title">Catalog-first context</div>
        <div class="panel-body">
          <div class="guard-stack">
            <div class="direction">
              <div class="guard-item">Target catalog</div>
              <div class="down">v</div>
              <div class="guard-item">Finding list</div>
              <div class="down">v</div>
              <div class="guard-item">Selected XID body</div>
              <div class="down">v</div>
              <div class="guard-item">Provider resolver</div>
              <div class="down">v</div>
              <div class="guard-item">Bounded AI context</div>
            </div>
            <div>
              <div class="shield">XID</div>
              <div class="guard-copy">Repository, package, or MCP; same identity</div>
            </div>
          </div>
          <div class="blocked">
            <p><strong>Blocked:</strong> stale packs, conflicting providers, missing coverage, and MCP provider cycles fail explicitly.</p>
            <p><strong>Expanded on demand:</strong> catalogs stay compact; only selected bodies enter the working context.</p>
          </div>
        </div>
      </section>

      <section class="panel human">
        <div class="panel-title">Distribution boundary</div>
        <div class="panel-body">
          <div class="human-flow">
            <div class="human-card"><div class="ico">R</div><div><h3>Repository mode</h3><p>Canonical Markdown and local packs resolve directly by XID.</p></div></div>
            <div class="human-card"><div class="ico">P</div><div><h3>Installed package</h3><p>Compiled base contracts start without repository-relative docs paths.</p></div></div>
            <div class="human-card"><div class="ico">M</div><div><h3>MCP mode</h3><p>A thin adapter exposes the same resolver and catalog operations.</p></div></div>
            <div class="human-card"><div class="ico">T</div><div><h3>Client-side tools</h3><p>Tool definitions cross MCP; execution remains on the trusted client.</p></div></div>
            <div class="bracket">Executable distribution requires pinned trust</div>
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
      <div class="principle"><div class="num">1</div><div><h3>Run the envelope first.</h3><p>Skill-backed work starts with <code>xrefkit skill run</code>, not direct procedure use.</p></div></div>
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
