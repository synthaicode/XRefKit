const XREFKIT_DECKS = [
  {
    id: "065",
    role: "Repository overview",
    title: { en: "XRefKit Repository Overview", ja: "XRefKit リポジトリ概要" },
    summary: {
      en: "Explains XRefKit as the operating base that connects Goals, Skills, Knowledge, workflow evidence, and MCP distribution.",
      ja: "Goal、Skill、Knowledge、workflowの証拠、MCP配布を接続する運用基盤としてXRefKitを説明します。",
    },
    links: { en: "065_xrefkit_repository_overview", ja: "065_xrefkit_repository_overview" },
  },
  {
    id: "063",
    role: "Execution model",
    title: { en: "AI Work Execution", ja: "AI 作業実行の説明資料" },
    summary: {
      en: "Shows how a Goal, bounded Skills, routing, Knowledge, and the workflow protocol make AI work resumable and reviewable.",
      ja: "Goal、限定責務、routing、Knowledge、workflow protocolにより、AI作業を再開・検証可能にする流れを説明します。",
    },
    links: { en: "063_ai_organization_explainer_clear", ja: "063_ai_organization_explainer_clear" },
  },
  {
    id: "064",
    role: "Operating boundary",
    title: { en: "AI Work Operating Boundary" },
    summary: { en: "Explains quality review, closure, handoff, and the decisions that remain with humans." },
    links: { en: "064_ai_team_operating_boundary" },
  },
  {
    id: "054",
    role: "Production background",
    title: { ja: "AI を本番利用するための論点" },
    summary: { ja: "AIを単発の出力評価から継続可能な業務実行へ進める際の論点を整理します。" },
    links: { ja: "ai-production-topics" },
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
  const status = deck.links[other] ? (lang === "ja" ? "英語版あり" : "Japanese version available") : `${lang === "ja" ? "日本語" : "English"} only`;
  return `<a class="deck-card" href="${languageLink(lang, deck.links[lang])}">
    <span class="deck-tag">Deck ${deck.id} · ${deck.role}</span>
    <h2>${deck.title[lang]}</h2>
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
