const XREFKIT_DECKS = [
  {
    id: "055",
    level: "Problem",
    role: "Problem framing",
    question: { ja: "なぜ通常のAI利用だけでは、継続可能な業務実行にならないのか。" },
    title: { ja: "AI活用を継続可能な業務実行に変える" },
    summary: { ja: "AIの特性から業務実行上の問題を分け、目標、限定責務、作業進行規約、組織固有知識、次作業選択が解く内容を示します。" },
    links: { ja: "why-ai-organization-needed" },
  },
  {
    id: "063",
    level: "Model",
    role: "Execution model",
    question: { en: "How is AI work kept resumable and reviewable?", ja: "AI作業を、どう再開・検証可能にするのか。" },
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
    levelJa: "実装",
    role: "Repository implementation",
    roleJa: "知識・手順の管理",
    question: { en: "How does the repository implement controlled AI work?", ja: "組織固有知識とAIに任せる手順を、どう管理・実行・改善するのか。" },
    title: { en: "XRefKit Repository Overview", ja: "XRefKit リポジトリ概要" },
    summary: {
      en: "Explains XRefKit as the operating base that connects Goals, Skills, Knowledge, workflow evidence, and MCP distribution.",
      ja: "責務定義、組織固有知識、実行管理、証拠、元資料を分離し、更新・検証可能な正本として管理する構造を説明します。",
    },
    links: { en: "065_xrefkit_repository_overview", ja: "065_xrefkit_repository_overview" },
  },
  {
    id: "073",
    level: "Distribution",
    levelJa: "組織配布",
    role: "Organization distribution",
    roleJa: "管理済み資産の配布",
    question: { ja: "管理された知識と手順を、組織のAI利用環境へどう届けるのか。" },
    title: { ja: "XRefKit 組織配布" },
    summary: { ja: "検証済みの責務定義、必須知識、実行契約を、PythonパッケージとMCPを通じて同じ契約のまま届ける仕組みを説明します。" },
    links: { ja: "073_xrefkit_organization_distribution" },
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
    <span class="deck-tag">${lang === "ja" ? (deck.levelJa || deck.level) : deck.level} · ${lang === "ja" ? (deck.roleJa || deck.role) : deck.role}</span>
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
