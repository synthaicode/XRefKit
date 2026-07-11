const XREFKIT_DECKS = [
  {
    id: "055",
    level: "Problem",
    role: "Problem framing",
    question: { ja: "なぜ通常のAI利用だけでは、継続可能な業務実行にならないのか。" },
    title: { ja: "AI活用を継続可能な業務実行に変える" },
    summary: { ja: "AIの応答終了と業務完了の違いから、Goalと限定責務が必要になる理由を説明します。" },
    links: { ja: "why-ai-organization-needed" },
  },
  {
    id: "063",
    level: "Model",
    role: "Execution model",
    question: { en: "How do Goal, Skills, routing, Knowledge, and workflow connect?", ja: "Goal、Skill、routing、Knowledge、workflowはどう接続するのか。" },
    title: { en: "AI Work Execution", ja: "AI 作業実行の説明資料" },
    summary: {
      en: "Shows how a Goal, bounded Skills, routing, Knowledge, and the workflow protocol make AI work resumable and reviewable.",
      ja: "Goal、限定責務、routing、Knowledge、workflow protocolにより、AI作業を再開・検証可能にする流れを説明します。",
    },
    links: { en: "063_ai_organization_explainer_clear", ja: "063_ai_organization_explainer_clear" },
  },
  {
    id: "065",
    level: "Implementation",
    role: "Repository implementation",
    question: { en: "How does the repository implement controlled AI work?", ja: "リポジトリは管理可能なAI作業をどう実現するのか。" },
    title: { en: "XRefKit Repository Overview", ja: "XRefKit リポジトリ概要" },
    summary: {
      en: "Explains XRefKit as the operating base that connects Goals, Skills, Knowledge, workflow evidence, and MCP distribution.",
      ja: "Goal、Skill、Knowledge、workflowの証拠、MCP配布を接続する運用基盤としてXRefKitを説明します。",
    },
    links: { en: "065_xrefkit_repository_overview", ja: "065_xrefkit_repository_overview" },
  },
  {
    id: "064",
    level: "Boundary",
    role: "Human and AI boundary",
    question: { en: "What does AI decide, and what remains with humans?" },
    title: { en: "AI Work Operating Boundary" },
    summary: { en: "Explains quality review, closure, handoff, and the decisions that remain with humans." },
    links: { en: "064_ai_team_operating_boundary" },
  },
];

function rootLink(lang, slug) {
  return `./${lang}/slides/${slug}/`;
}

function languageLink(lang, slug) {
  return `./slides/${slug}/`;
}

function renderRootCard(deck) {
  const languages = Object.keys(deck.links);
  const actions = languages.map((lang) => `<a class="open-deck-button" href="${rootLink(lang, deck.links[lang])}">${lang === "ja" ? "Japanese" : "English"} →</a>`).join("");
  return `<article class="catalog-card" data-lang="${languages.join(",")}">
    <div class="catalog-top"><span class="catalog-deck">Deck ${deck.id}</span><span class="catalog-lang">${languages.map((lang) => lang.toUpperCase()).join(" / ")}</span></div>
    <h3>${deck.title.en || deck.title.ja}</h3>
    <p class="catalog-summary">${deck.summary.en || deck.summary.ja}</p>
    <p class="catalog-meta-line">${deck.role}</p>
    <div class="catalog-actions">${actions}</div>
  </article>`;
}

function renderLanguageCard(deck, lang) {
  const other = lang === "ja" ? "en" : "ja";
  const status = deck.links[other] ? (lang === "ja" ? "英語版あり" : "Japanese version available") : (lang === "ja" ? "日本語のみ" : "English only");
  return `<a class="deck-card" href="${languageLink(lang, deck.links[lang])}">
    <span class="deck-tag">${deck.level} · ${deck.role}</span>
    <h2>${deck.title[lang]}</h2>
    <p class="deck-question">${deck.question[lang]}</p>
    <p>${deck.summary[lang]}</p>
    <div class="status-row"><span class="status-chip ${deck.links[other] ? "dual" : "single"}">${status}</span></div>
  </a>`;
}

for (const catalog of document.querySelectorAll("[data-deck-catalog]")) {
  const scope = catalog.dataset.deckCatalog;
  if (scope === "root") catalog.innerHTML = XREFKIT_DECKS.map(renderRootCard).join("");
  if (scope === "ja" || scope === "en") {
    catalog.innerHTML = XREFKIT_DECKS.filter((deck) => deck.links[scope]).map((deck) => renderLanguageCard(deck, scope)).join("");
  }
}
