import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("en/docs/assets/063_ai_organization_explainer_clear");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const html = (body) => `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <style>${css}</style>
</head>
<body>${body}</body>
</html>`;

const wrap = ({ kicker, title, lead = "", body = "", summary = "", compact = false }) => `
  <main class="canvas">
    <div class="kicker">${kicker}</div>
    <h1>${title}</h1>
    ${lead ? `<p class="lead">${lead}</p>` : ""}
    <section class="stage${compact ? " compact" : ""}">${body}</section>
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

const definition = () => `
  <div class="definition-grid">
    <div class="definition-main">
      <div class="card-label">DEF</div>
      <h2>What is an AI Team?</h2>
      <p>An operating structure that fixes the Skill, domain knowledge, roles, checkpoints, and handoffs around a purpose.</p>
    </div>
    <div class="management-list">
      <div class="management-item">Explaining the work</div>
      <div class="management-item">Making decisions</div>
      <div class="management-item">Checking the output</div>
      <div class="management-item">Handing work over</div>
    </div>
  </div>`;

const compare = () => `
  <div class="compare-grid">
    <div class="compare-box before">
      <h2>Before</h2>
      <ul>
        <li>Humans explain every time</li>
        <li>Humans decide every time</li>
        <li>Humans check every time</li>
        <li>Humans hand work over every time</li>
      </ul>
    </div>
    <div class="compare-box after">
      <h2>After</h2>
      <ul>
        <li>Skills fix the procedure</li>
        <li>Knowledge fixes the criteria</li>
        <li>Checkpoints catch omissions</li>
        <li>Responsibility and handoffs are fixed</li>
      </ul>
    </div>
  </div>`;

const burdenFlow = () => `
  <div class="burden-flow">
    <div class="burden-step">
      <div class="burden-label">Prompt</div>
      <h2>Explaining</h2>
      <p>Humans still explain the goal, assumptions, constraints, and output format every time.</p>
      <div class="burden-arrow">reduces into Skill</div>
    </div>
    <div class="burden-step">
      <div class="burden-label">Skill</div>
      <h2>Procedure choice</h2>
      <p>The procedure is fixed, but humans still choose which Skill fits the purpose.</p>
      <div class="burden-arrow">needs criteria</div>
    </div>
    <div class="burden-step">
      <div class="burden-label">Knowledge</div>
      <h2>Ownership</h2>
      <p>Decision criteria are shared, but someone must keep the knowledge current.</p>
      <div class="burden-arrow">needs flow</div>
    </div>
    <div class="burden-step">
      <div class="burden-label">AI Team</div>
      <h2>Coordination</h2>
      <p>Roles, checks, sequence, and handoffs make AI work inspectable by humans.</p>
      <div class="burden-arrow">becomes governable AI work</div>
    </div>
  </div>`;

const slides = {
  "01_title_q": wrap({
    kicker: "Why AI organizations become necessary",
    title: "The more you use AI, the more management work humans inherit",
    body: dialogue(
      "If we add AI, doesn't work simply get easier?",
      "It can. But used the wrong way, AI increases the management work on the human side.",
      "",
      "",
      "question"
    ),
    summary: "Start with the common expectation"
  }),
  "01_title": wrap({
    kicker: "Why AI organizations become necessary",
    title: "The more you use AI, the more management work humans inherit",
    body: dialogue(
      "If we add AI, doesn't work simply get easier?",
      "It can. But used the wrong way, AI increases the management work on the human side.",
      "Today, we trace the pattern",
      "Prompt, Skill, domain knowledge, and AI Team. We will separate the burden each step creates from the structure that solves it."
    ),
    summary: "Key idea: an AI Team makes AI work manageable for an organization"
  }),
  "02_team_definition_q": wrap({
    kicker: "Define it early",
    title: "An AI Team is an operating structure for assigning work to AI",
    body: dialogue(
      "So what exactly is an AI Team?",
      "Before we go further, let's set the meaning of the term.",
      "",
      "",
      "question"
    ),
    summary: "Align on the meaning first"
  }),
  "02_team_definition": wrap({
    kicker: "Define it early",
    title: "An AI Team is an operating structure for assigning work to AI",
    body: definition(),
    summary: "An AI Team packages AI work into a unit humans can manage"
  }),
  "03_problem_q": wrap({
    kicker: "The starting point",
    title: "With prompts alone, humans must explain everything every time",
    body: dialogue(
      "Isn't a careful prompt enough?",
      "Every run still asks a human to explain the goal, assumptions, constraints, and output format.",
      "",
      "",
      "question"
    ),
    summary: "First, look at the burden of prompt-based work"
  }),
  "03_problem": wrap({
    kicker: "The starting point",
    title: "With prompts alone, humans must explain everything every time",
    body: dialogue(
      "Isn't a careful prompt enough?",
      "Every run still asks a human to explain the goal, assumptions, constraints, and output format.",
      "Turn repeat work into a Skill",
      "For repeated tasks, stop rewriting instructions every time. Fix the procedure as a reusable Skill and reduce explanation fatigue."
    ),
    summary: "The prompt problem is not only AI behavior. It is the human becoming the explainer every time"
  }),
  "04_work_q": wrap({
    kicker: "The next countermeasure",
    title: "As Skills grow, humans must manage the procedures",
    body: dialogue(
      "If we use Skills, does it become stable?",
      "The repeated explanation decreases. But now the question becomes which Skill to use.",
      "",
      "",
      "question"
    ),
    summary: "A Skill solves one burden and creates another"
  }),
  "04_work": wrap({
    kicker: "The next countermeasure",
    title: "As Skills grow, humans must manage the procedures",
    body: dialogue(
      "If we use Skills, does it become stable?",
      "The repeated explanation decreases. But humans must manage which Skill to use and whether the procedure fits the purpose.",
      "Add domain knowledge",
      "Example: for an explainer video, scripting and voice production are Skills. What counts as a correct explanation must be decided separately."
    ),
    summary: "Skills reduce explanation fatigue, but procedure selection becomes human work"
  }),
  "05_not_one_ai_q": wrap({
    kicker: "What is still missing",
    title: "A Skill without domain knowledge sends judgment back to humans",
    body: dialogue(
      "If the procedure exists, why do we need knowledge?",
      "A Skill is the way to proceed. The criteria for correctness are separate.",
      "",
      "",
      "question"
    ),
    summary: "Separate Skill from domain knowledge",
    compact: true
  }),
  "05_not_one_ai": wrap({
    kicker: "What is still missing",
    title: "A Skill without domain knowledge sends judgment back to humans",
    body: dialogue(
      "If the procedure exists, why do we need knowledge?",
      "A Skill is the way to proceed. Correctness depends on business terms, criteria, and constraints.",
      "Share the decision criteria",
      "Example: make it beginner-friendly, exclude certain explanations, include execution and checking. Those criteria become domain knowledge."
    ),
    summary: "Skill is procedure. Judgment needs domain knowledge",
    compact: true
  }),
  "06_repository_q": wrap({
    kicker: "Conditions for organizational use",
    title: "Shared knowledge needs ownership",
    body: dialogue(
      "If we share the knowledge, are we done?",
      "Shared knowledge still has to be updated when the rules or assumptions change.",
      "",
      "",
      "question"
    ),
    summary: "Knowledge is not only stored. It must be maintained"
  }),
  "06_repository": wrap({
    kicker: "Conditions for organizational use",
    title: "Shared knowledge needs ownership",
    body: dialogue(
      "If we share the knowledge, are we done?",
      "No. If the rules change and the knowledge is not updated, AI keeps working from an old version of correctness.",
      "Define where knowledge lives",
      "Manage it where everyone can refer to the same assumptions and update them when they change."
    ),
    summary: "Organizations need not only explicit knowledge, but ownership for maintaining it"
  }),
  "07_handoff_q": wrap({
    kicker: "The remaining problem",
    title: "As Skills and knowledge grow, work tends to fragment",
    body: dialogue(
      "If we have all the parts, does the work run?",
      "Parts alone do not decide sequence, responsibility, or handoff.",
      "",
      "",
      "question"
    ),
    summary: "Now the problem shifts to workflow"
  }),
  "07_handoff": wrap({
    kicker: "The remaining problem",
    title: "As Skills and knowledge grow, work tends to fragment",
    body: dialogue(
      "If we have all the parts, does the work run?",
      "Not yet. Humans still have to connect research, decisions, production, and review each time.",
      "Make it an AI Team",
      "Fix roles, sequence, responsibility, and handoffs as the team structure before the work starts."
    ),
    summary: "Even with the parts in place, humans still carry the coordination burden unless the flow is designed"
  }),
  "08_burden_flow": wrap({
    kicker: "How the burden moves",
    title: "Each step replaces one human burden and exposes the next",
    body: burdenFlow(),
    summary: "AI Team is not added to make AI magical. It is added to make AI work governable",
    compact: true
  }),
  "08_or_team_q": wrap({
    kicker: "The solution",
    title: "An AI Team turns human coordination into structure",
    body: dialogue(
      "This is where the AI Team comes in, right?",
      "Yes. This connects Skills and knowledge into a working flow.",
      "",
      "",
      "question"
    ),
    summary: "An AI Team turns parts into work"
  }),
  "08_or_team": wrap({
    kicker: "The solution",
    title: "An AI Team turns human coordination into structure",
    body: dialogue(
      "What does an AI Team actually do?",
      "It fixes the sequence, responsibility, checks, and handoffs that humans otherwise rethink every time.",
      "Connect the parts into real work",
      "Example: a producer creates, a checker catches omissions, records remain, and the work is handed to the next step. That is the Team."
    ),
    summary: "An AI Team combines procedure, knowledge, responsibility, and flow into work"
  }),
  "09_value_q": wrap({
    kicker: "What the AI Team decides",
    title: "AI forgets. So do not design the work around human memory",
    body: dialogue(
      "If AI forgets, can't humans just check?",
      "If humans must remember everything, misses become likely.",
      "",
      "",
      "question"
    ),
    summary: "Reduce checking burden through structure"
  }),
  "09_value": wrap({
    kicker: "What the AI Team decides",
    title: "AI forgets. So do not design the work around human memory",
    body: dialogue(
      "If AI forgets, can't humans just check?",
      "Tracking everything by human memory is exhausting. Work omissions, review omissions, and missing rationale become easy to miss.",
      "Separate execution from checking",
      "One role creates. Another checks for missed work, missed review points, and missing rationale."
    ),
    summary: "A checker reduces the burden of humans continuously tracking what AI might forget"
  }),
  "10_conclusion_q": wrap({
    kicker: "The role of the AI Team",
    title: "Define where humans inspect the work",
    body: dialogue(
      "Does this remove human work?",
      "No. It changes how humans look at the work.",
      "",
      "",
      "question"
    ),
    summary: "Clarify how human work changes"
  }),
  "10_conclusion": wrap({
    kicker: "The role of the AI Team",
    title: "Define where humans inspect the work",
    body: dialogue(
      "Does this remove human work?",
      "No. But it changes the job from chasing everything to checking the points that matter.",
      "Fix the human review points",
      "Place purpose, execution, checking, records, and handoffs inside the team so humans can inspect them."
    ),
    summary: "Human work shifts from watching everything to checking the right points"
  }),
  "11_before_after_q": wrap({
    kicker: "Before and after",
    title: "Human work shifts from watching everything to checking the right points",
    body: dialogue(
      "What changes before and after adoption?",
      "Use Before / After to see where the management work moves.",
      "",
      "",
      "question"
    ),
    summary: "Compare the operating model"
  }),
  "11_before_after": wrap({
    kicker: "Before and after",
    title: "Human work shifts from watching everything to checking the right points",
    body: compare(),
    summary: "An AI Team turns repeated management work into a fixed operating structure"
  }),
  "12_license_q": wrap({
    kicker: "Summary",
    title: "An AI Team turns human burden into visible work",
    body: dialogue(
      "So why is an AI Team necessary?",
      "Let's summarize the growing burden and the solution.",
      "",
      "",
      "question"
    ),
    summary: "Close with the core message"
  }),
  "12_license": wrap({
    kicker: "Summary",
    title: "An AI Team turns human burden into visible work",
    body: dialogue(
      "So why is an AI Team necessary?",
      "Because the more AI is used, the more humans must explain, manage procedures, update knowledge, coordinate flow, and check work.",
      "Make it manageable",
      "An AI Team turns those burdens into roles, flow, and checkpoints, so the organization can handle AI work."
    ),
    summary: "AI Team makes AI work governable, not magical"
  })
};

await fs.mkdir(dir, { recursive: true });

for (const [name, body] of Object.entries(slides)) {
  await fs.writeFile(path.join(dir, `${name}.html`), html(body), "utf8");
}

console.log(`rendered ${Object.keys(slides).length} html files`);
