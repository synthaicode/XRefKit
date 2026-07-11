import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/en/assets/063_ai_organization_explainer_clear");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");
const escape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const page = ({ kicker, title, question, answer, summary }) => `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><style>${css}</style></head><body>
  <main class="canvas"><div class="kicker">${escape(kicker)}</div><h1>${escape(title)}</h1>
  <section class="stage"><div class="dialogue-grid${answer ? "" : " question-only"}">
  <div class="bubble question"><div class="card-label">Question</div><h2>${escape(question)}</h2></div>
  ${answer ? `<div class="bubble answer"><div class="card-label">Answer</div><p>${escape(answer)}</p></div>` : "<!-- question only -->"}
  </div></section><div class="summary">${escape(summary)}</div></main></body></html>`;

const slides = {
  "01_title_q": ["Execution model", "How are bounded AI tasks connected from Goal to acceptance?", "What does the execution model connect?", "", "This deck explains the relationships between the operating parts."],
  "01_title": ["Execution model", "How are bounded AI tasks connected from Goal to acceptance?", "What is the whole flow?", "A Goal holds the endpoint, routing selects the next responsibility, a Skill Run performs work, the protocol preserves state, and acceptance returns to the Goal.", "Keep individual work connected to the business endpoint."],
  "02_team_definition_q": ["Goal", "A Goal holds the desired state, not a task count", "What does a Goal define?", "", "Fix the desired state and acceptance conditions."],
  "02_team_definition": ["Goal", "A Goal holds the desired state, not a task count", "What is checked?", "The Goal retains desired state and acceptance conditions. Finishing one Skill does not complete the Goal.", "Separate business completion from the moment an AI stops."],
  "03_problem_q": ["Decomposition", "Reaching a Goal requires multiple bounded responsibilities", "Why decompose the work?", "", "Give AI one judgment method and output boundary at a time."],
  "03_problem": ["Decomposition", "Reaching a Goal requires multiple bounded responsibilities", "What is separated?", "Each responsibility groups its method, input, output, required Knowledge, and handoff boundary.", "Decomposition clarifies responsibility without shrinking the Goal."],
  "04_work_q": ["Skill", "A Skill narrows the responsibility delegated to AI", "What changes with a Skill?", "", "Focus one judgment method and one output boundary."],
  "04_work": ["Skill", "A Skill narrows the responsibility delegated to AI", "What does it contain?", "A Skill declares capability, tuning, responsibility, I/O, method, needed Knowledge, and its handoff boundary.", "Split large requests at accountable responsibility boundaries."],
  "05_not_one_ai_q": ["Routing", "The next Skill is selected from the Goal and current state", "Who selects the Skill?", "", "Do not make people manually choose from a long list every time."],
  "05_not_one_ai": ["Routing", "The next Skill is selected from the Goal and current state", "How is it selected?", "Semantic routing matches the Skill triad and preconditions to the goal and current state.", "After each Skill, select the next responsibility from the new state."],
  "06_repository_q": ["Knowledge", "Skills hold methods; Knowledge holds judgment material", "Why separate knowledge?", "", "Do not mix domain facts into one long procedure prompt."],
  "06_repository": ["Knowledge", "Skills hold methods; Knowledge holds judgment material", "How is it loaded?", "Knowledge slots list candidates first. Only the required XID bodies are loaded.", "Reduce irrelevant context and keep knowledge maintainable."],
  "07_handoff_q": ["Protocol", "Closing a Skill does not complete the Goal", "How is intermediate work controlled?", "", "Individual completeness and goal achievement are separate checks."],
  "07_handoff": ["Protocol", "The workflow protocol checks each Skill Run for omissions", "What is recorded?", "The run log records work items, artifacts, evidence, unknowns, risks, judgments, progress, and handoffs.", "Find unfinished work from records, not an AI self-report."],
  "08_burden_flow": ["Flow", "Goal -> routing -> Skill Run -> verify -> handoff -> Goal", "Where does work stop?", "A run records work and evidence. Verify checks progression. Gaps return for repair or explicit handoff.", "Never mark incomplete work as successful."],
  "08_or_team_q": ["Verification", "Verify does not automatically accept output quality", "Does passing verify guarantee quality?", "", "Process completeness and output acceptance are separate."],
  "08_or_team": ["Verification", "Verify does not automatically accept output quality", "What does it check?", "Verify checks work, evidence, concerns, roles, and progression. Quality review and people accept output content when needed.", "Separate checks to reduce missed work."],
  "09_value_q": ["Interruption", "AI can stop without losing the work", "What happens after interruption?", "", "Keep the state explicit, then resume or hand off."],
  "09_value": ["Interruption", "AI can stop without losing the work", "What remains?", "The log preserves completed work, remaining work, evidence, unresolved items, and the next owner. The Goal stays active until acceptance conditions are met.", "Avoid rebuilding context from memory."],
  "10_conclusion_q": ["Human role", "Human work is not to watch everything", "What do people own?", "", "Own goals, acceptance, approvals, and exceptions."],
  "10_conclusion": ["Human role", "Human work is not to watch everything", "Where should people look?", "People judge goal completion, output acceptance, approvals, and exceptions. The protocol exposes the execution state.", "Use human attention where judgment is required."],
  "11_before_after_q": ["Before and after", "From individual chat to continuous work execution", "What changes?", "", "The difference is how work is managed, not the number of AIs."],
  "11_before_after": ["Before and after", "From individual chat to continuous work execution", "What does the new model do?", "Goals manage destination. Routing selects responsibility. Skills work. The protocol checks gaps. Knowledge supports judgment.", "Turn AI speed into less rework and better continuity."],
  "12_license_q": ["Conclusion", "AI efficiency is not only output speed", "Why is this structure necessary?", "", "Reduce re-explanation, rediscovery, missed checks, and lost handoffs."],
  "12_license": ["Conclusion", "Turn AI use into manageable work execution", "What does it achieve?", "Goals, routing, Skills, Knowledge, and the workflow protocol narrow responsibility, manage interruption, and support acceptance.", "Do not prevent AI from stopping; prevent work from being lost when it stops."]
};

await fs.mkdir(dir, { recursive: true });
for (const [name, [kicker, title, question, answer, summary]] of Object.entries(slides)) {
  await fs.writeFile(path.join(dir, `${name}.html`), page({ kicker, title, question, answer, summary }), "utf8");
}
console.log(`rendered ${Object.keys(slides).length} html files`);
