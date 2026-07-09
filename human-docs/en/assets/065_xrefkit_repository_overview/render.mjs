import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/en/assets/065_xrefkit_repository_overview");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");
const slides = [
  ["01_title", "What is this repository for?", "XRefKit makes domain-guided AI work operable.", "It packages controlled procedures, selective knowledge loading, evidence, and handoff rules for organizational use.", [["Purpose", "Reproduce domain procedures and judgments."], ["Boundary", "Keep knowledge, execution, and evidence distinct."], ["Outcome", "Reduce omissions, guessing, and broken handoffs."]]],
  ["02_not_docs", "Why is an ordinary document repository not enough?", "Storage alone does not control what an AI reads or trusts.", "XRefKit adds stable identity, selection catalogs, execution contracts, and explicit closure on top of source material.", [["Problem", "Broad reading pollutes context."], ["Control", "Catalogs precede detailed bodies."], ["Result", "The same decision can be applied to another structure."]]],
  ["03_layers", "How is the repository divided?", "xrefkit, Skills, Knowledge, tools, sources, and work have separate roles.", "The Python package owns runtime behavior; XID-addressed content remains independently selectable and traceable.", [["Package", "Runtime, resolver, tool registry, and MCP adapter."], ["Selected content", "Skills and Knowledge expanded by XID."], ["Evidence", "Sources and work records preserve basis and history."]]],
  ["04_runtime", "Can an AI simply open and follow a Skill?", "A Skill runs inside the XRefKit runtime envelope.", "xrefkit skill run opens the log first; work items, artifacts, concerns, checks, and handoff must be complete before closure.", [["Start", "Validate metadata and assign roles."], ["Execute", "Record concrete work and evidence."], ["Close", "Reject incomplete or unsupported work."]]],
  ["05_guard", "How is context kept small in brownfield work?", "Select targets and findings before loading details.", "The target catalog identifies what can be analyzed. The finding catalog exposes compact metadata, freshness, and coverage before any body is expanded.", [["List", "Choose a source target."], ["Narrow", "Choose a relevant finding."], ["Expand", "Load only the selected XID body."]]],
  ["06_handoff", "How do repository, package, and MCP use the same knowledge?", "Provider-independent XID resolution preserves identity.", "Repository and installed-package providers implement the rules. MCP is a thin transport adapter and cannot introduce an independent catalog.", [["Repository", "Canonical authoring and local packs."], ["Package", "Compiled base runtime resources."], ["MCP", "Remote access to the shared resolver."]]],
  ["07_human", "Where do humans still decide?", "Humans retain trade-offs, risk acceptance, and approvals.", "Deterministic checks expose omissions and stale inputs. Semantic acceptance remains a documented human or independent-review boundary.", [["Automation", "Detect missing records and stale packs."], ["Review", "Assess output meaning and domain fit."], ["Approval", "Own risk and organizational trade-offs."]]],
  ["08_conclusion", "What is XRefKit now?", "A portable Python package for distributing domain-guided AI work.", "The same XID identities, catalog-first loading, Skill runtime, tools, and MCP surface work together without requiring the whole repository in context.", [["Read", "Lists first, selected details second."], ["Act", "Skills and tools run under explicit contracts."], ["Distribute", "Use repository, package, or MCP mode."]]],
];

function answer([name, question, title, copy, cards]) {
  const cardHtml = cards.map(([tag, text]) => `<article class="card"><div class="card-tag">${tag}</div><p>${text}</p></article>`).join("");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${title}</title><style>${css}</style></head><body><main class="slide"><header class="header"><div><div class="eyebrow">Repository Overview</div><h1 class="title">${title}</h1></div><div class="brand">XRefKit</div></header><section class="summary"><div class="summary-label">Question</div><div class="summary-copy">${question}</div><div class="summary-title">${copy}</div></section><section class="cards">${cardHtml}</section><div class="takeaway"><strong>Catalog first.</strong> Expand only the information needed for the current decision.</div></main></body></html>`;
}

function questionOnly([name, question]) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${question}</title><style>${css}</style></head><body><main class="slide"><header class="header"><div><div class="eyebrow">Repository Overview</div><h1 class="title">XRefKit in eight questions.</h1></div><div class="brand">XRefKit</div></header><section class="question-wrap"><div class="question-box"><div class="question-label">Question</div><div class="question-text">${question}</div></div></section><div class="takeaway">Start with the question, then load only the relevant explanation.</div></main></body></html>`;
}

for (const slide of slides) {
  await fs.writeFile(path.join(dir, `${slide[0]}_q.html`), questionOnly(slide), "utf8");
  await fs.writeFile(path.join(dir, `${slide[0]}.html`), answer(slide), "utf8");
}
