import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("en/docs/assets/064_ai_team_operating_boundary");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const html = (body) => `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <style>${css}</style>
</head>
<body>${body}</body>
</html>`;

const wrap = ({ kicker, title, lead = "", body = "", summary = "" }) => `
  <main class="canvas">
    <div class="kicker">${kicker}</div>
    <h1>${title}</h1>
    ${lead ? `<p class="lead">${lead}</p>` : ""}
    <section class="stage">${body}</section>
    ${summary ? `<div class="summary">${summary}</div>` : ""}
  </main>`;

const dialogue = (questionTitle, questionText, answerTitle, answerText, mode = "both") => `
  <div class="dialogue-grid${mode === "question" ? " question-only" : ""}">
    <div class="bubble question">
      <div class="card-label">Q</div>
      <h2>${questionTitle}</h2>
      <p>${questionText}</p>
    </div>
    ${mode === "question" ? "" : `<div class="bubble answer">
      <div class="card-label">A</div>
      <h2>${answerTitle}</h2>
      <p>${answerText}</p>
    </div>`}
  </div>`;

const reviewVsBoundary = () => `
  <div class="two-col">
    <div class="card red">
      <h2>More human review</h2>
      <p>Humans keep watching everything, comparing everything, and deciding everything every time.</p>
    </div>
    <div class="card green">
      <h2>Explicit boundary</h2>
      <p>Humans review only the defined return points: unresolved risk, non-trivial judgment, failed checks, or release approval.</p>
    </div>
  </div>`;

const concernFlow = () => `
  <div class="stack">
    <div class="stack-row">
      <div class="pill blue">Unknown</div>
      <div class="arrow">do not guess<br/>keep it visible</div>
      <div class="pill red">Return or stop</div>
    </div>
    <div class="stack-row">
      <div class="pill amber">Risk</div>
      <div class="arrow">resolve or escalate<br/>before closure</div>
      <div class="pill teal">Human acceptance</div>
    </div>
    <div class="stack-row">
      <div class="pill teal">Judgment</div>
      <div class="arrow">record non-trivial<br/>trade-offs</div>
      <div class="pill green">Auditable handoff</div>
    </div>
  </div>`;

const roleSplit = () => `
  <div class="two-col">
    <div class="card blue">
      <h2>Execution role</h2>
      <p>Produce the work inside the fixed flow, capability, and context boundary. Execution should not certify itself.</p>
    </div>
    <div class="card teal">
      <h2>Check role</h2>
      <p>Verify evidence, assumptions, omissions, unknowns, and handoff readiness from a separate responsibility line.</p>
    </div>
  </div>`;

const closureCards = () => `
  <div class="two-col">
    <div class="card red">
      <h2>Without a closure gate</h2>
      <p>Open unknowns, weak evidence, and unfinished checks disappear into a “done” claim.</p>
    </div>
    <div class="card green">
      <h2>With a closure gate</h2>
      <p>The run cannot close until roles, work items, artifacts, and concerns satisfy the declared conditions.</p>
    </div>
  </div>`;

const handoffCards = () => `
  <div class="two-col">
    <div class="card blue">
      <h2>What gets handed over</h2>
      <p>Outputs, evidence, unresolved items, judgment references, and the next owner.</p>
    </div>
    <div class="card amber">
      <h2>Why it matters</h2>
      <p>Handoff is where responsibility changes. If that point is vague, humans re-explain and re-check the same work.</p>
    </div>
  </div>`;

const maturityLevels = () => `
  <div class="levels">
    <div class="level">
      <div class="tag">draft</div>
      <h2>Boundary is still a hypothesis</h2>
      <p>Purpose exists, but return conditions and human checkpoints are not yet reliable.</p>
    </div>
    <div class="level">
      <div class="tag">trial</div>
      <h2>Boundary is being observed</h2>
      <p>Real runs expose where unknowns, judgments, and handoffs still depend on human improvisation.</p>
    </div>
    <div class="level">
      <div class="tag">stable</div>
      <h2>Boundary is dependable</h2>
      <p>Runtime roles, evidence, concern handling, and closure conditions are explicit enough to reuse.</p>
    </div>
    <div class="level">
      <div class="tag">governed</div>
      <h2>Boundary is auditable</h2>
      <p>Governance and audit references explain why this responsibility split is acceptable for the organization.</p>
    </div>
  </div>`;

const closing = () => `
  <div class="closing-grid">
    <div class="big-card">
      <h2>An AI Team becomes trustworthy when the human boundary is fixed</h2>
      <p>The point is not to remove humans from the loop. The point is to stop making humans rediscover the loop every time.</p>
    </div>
    <div class="checklist">
      <div class="check-item">Separate execution and checking</div>
      <div class="check-item">Keep unknown and risk explicit</div>
      <div class="check-item">Record non-trivial judgment</div>
      <div class="check-item">Close only through declared conditions</div>
    </div>
  </div>`;

const slides = {
  "01_title_q": wrap({
    kicker: "The next level after AI Team basics",
    title: "If an AI Team exists, what exactly still belongs to humans?",
    body: dialogue(
      "Once an AI Team is defined, what should humans still decide?",
      "The next question is not whether AI helps. It is where human responsibility must remain visible.",
      "",
      "",
      "question"
    ),
    summary: "Move from “why AI Team” to “where the human boundary lives”"
  }),
  "01_title": wrap({
    kicker: "The next level after AI Team basics",
    title: "An AI Team is useful only when its human boundary is explicit",
    body: dialogue(
      "Once an AI Team is defined, what should humans still decide?",
      "The next question is not whether AI helps. It is where human responsibility must remain visible.",
      "Define the return points",
      "An AI Team becomes governable when it fixes what AI may handle, what must stay explicit as uncertainty or risk, and what must be handed back to a human with evidence."
    ),
    summary: "This is a responsibility design problem, not only a tooling problem"
  }),
  "02_review_q": wrap({
    kicker: "Common misunderstanding",
    title: "More human review is not the same as a better operating boundary",
    body: dialogue(
      "Can't humans simply review more carefully?",
      "That only increases human monitoring work unless the return points are fixed.",
      "",
      "",
      "question"
    ),
    summary: "Review load is not a substitute for design"
  }),
  "02_review": wrap({
    kicker: "Common misunderstanding",
    title: "More human review is not the same as a better operating boundary",
    body: reviewVsBoundary(),
    summary: "A boundary reduces what humans must inspect, instead of asking them to inspect everything"
  }),
  "03_concern_q": wrap({
    kicker: "Keep uncertainty visible",
    title: "Unknown, risk, and judgment mark the points that must not disappear",
    body: dialogue(
      "What should force work back to humans?",
      "Unknowns, unresolved risks, and non-trivial judgments are the first signals that the boundary has been reached.",
      "",
      "",
      "question"
    ),
    summary: "These are operating signals, not optional notes"
  }),
  "03_concern": wrap({
    kicker: "Keep uncertainty visible",
    title: "Unknown, risk, and judgment mark the points that must not disappear",
    body: concernFlow(),
    summary: "The team must stop guessing and show where human responsibility resumes"
  }),
  "04_roles_q": wrap({
    kicker: "Role structure",
    title: "Execution and checking should not collapse into one role",
    body: dialogue(
      "If the same AI produces and checks the work, is that enough?",
      "Not if you want a reliable boundary. Self-certification hides omissions and weak evidence.",
      "",
      "",
      "question"
    ),
    summary: "Separation is part of control, not ceremony"
  }),
  "04_roles": wrap({
    kicker: "Role structure",
    title: "Execution and checking should not collapse into one role",
    body: roleSplit(),
    summary: "Humans can then inspect the check result instead of replaying the entire execution"
  }),
  "05_closure_q": wrap({
    kicker: "Closure discipline",
    title: "Closure gate means the run cannot declare success by optimism",
    body: dialogue(
      "Why do we need an explicit closure gate?",
      "Because incomplete evidence, unresolved concerns, and skipped checks otherwise vanish into a casual “done.”",
      "",
      "",
      "question"
    ),
    summary: "Closure is a control point, not a formatting step"
  }),
  "05_closure": wrap({
    kicker: "Closure discipline",
    title: "Closure gate means the run cannot declare success by optimism",
    body: closureCards(),
    summary: "The gate holds the line between unfinished work and releasable work"
  }),
  "06_handoff_q": wrap({
    kicker: "Where responsibility moves",
    title: "Handoff is the moment the next responsibility line begins",
    body: dialogue(
      "If the work is checked, isn't that enough?",
      "No. Someone still needs the result, the evidence, and the unresolved edges in a form they can accept.",
      "",
      "",
      "question"
    ),
    summary: "A result without handoff still creates human rediscovery work"
  }),
  "06_handoff": wrap({
    kicker: "Where responsibility moves",
    title: "Handoff is the moment the next responsibility line begins",
    body: handoffCards(),
    summary: "A good handoff prevents the next person from reconstructing the missing context"
  }),
  "07_maturity_q": wrap({
    kicker: "Why Skill maturity exists",
    title: "A Skill is not complete when it is written. It matures as its human boundary becomes clear",
    body: dialogue(
      "Why do Skills need maturity levels at all?",
      "Because the procedure text may exist early, while the practical boundary with humans is still uncertain.",
      "",
      "",
      "question"
    ),
    summary: "Maturity tracks boundary clarity, not cosmetic progress"
  }),
  "07_maturity": wrap({
    kicker: "Why Skill maturity exists",
    title: "Skill maturity shows how clear the human boundary has become",
    body: maturityLevels(),
    summary: "The real question is whether the team knows what AI may do and when humans must take over"
  }),
  "08_conclusion_q": wrap({
    kicker: "The operating conclusion",
    title: "So what makes an AI Team trustworthy?",
    body: dialogue(
      "What should an organization design first?",
      "Not more prompts, and not more review load. First design the human boundary and the conditions that govern return, closure, and handoff.",
      "",
      "",
      "question"
    ),
    summary: "Trust comes from boundary discipline"
  }),
  "08_conclusion": wrap({
    kicker: "The operating conclusion",
    title: "A trustworthy AI Team fixes where humans must return, decide, and accept",
    body: closing(),
    summary: "AI convenience becomes organizational control only when the responsibility boundary is explicit"
  })
};

await fs.mkdir(dir, { recursive: true });
for (const [name, body] of Object.entries(slides)) {
  await fs.writeFile(path.join(dir, `${name}.html`), html(body), "utf8");
}
