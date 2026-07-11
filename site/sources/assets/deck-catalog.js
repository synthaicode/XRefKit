const XREFKIT_DECKS = [
  {
    id: "055",
    level: "Why",
    role: "AI characteristics and need",
    question: { en: "Why does ordinary AI use not become continuous business execution?", ja: "なぜ通常のAI利用だけでは、継続可能な業務実行にならないのか。" },
    title: { en: "Turning AI Use into Continuous Business Execution", ja: "AI活用を継続可能な業務実行に変える" },
    summary: { en: "Connects each AI characteristic to the distinct role of Goals, Skills, the workflow protocol, Knowledge, semantic routing, evidence, and human acceptance.", ja: "AIの局所作業と業務完了の差から、Goal、Skill、Workflow protocol、Knowledge、Semantic routing、Evidence、Human acceptanceが必要な理由を示します。" },
    links: { en: "why-ai-organization-needed", ja: "why-ai-organization-needed" },
  },
  {
    id: "063",
    level: "How",
    role: "Business execution loop",
    question: { en: "How do bounded responsibilities connect Goal to acceptance?", ja: "Goalから受入れまで、限定責務をどう接続するのか。" },
    title: { en: "XRefKit Business Execution Model", ja: "XRefKitの業務実行モデル" },
    summary: {
      en: "Shows how a Goal, bounded Skills, routing, Knowledge, and the workflow protocol make AI work resumable and reviewable.",
      ja: "Goal、限定責務、routing、Knowledge、workflow protocolにより、AI作業を再開・検証可能にする流れを説明します。",
    },
    links: { en: "063_ai_organization_explainer_clear", ja: "063_ai_organization_explainer_clear" },
  },
  {
    id: "064",
    level: "Boundary",
    levelJa: "責任境界",
    role: "Tool, AI, and human boundary",
    roleJa: "ツール・AI・人間の責任境界",
    question: { en: "What do tools, AI, and humans decide?", ja: "ツール・AI・人間は、それぞれ何を決めるのか。" },
    title: { en: "AI Work Operating Boundary", ja: "ツール・AI・人間の責任境界" },
    summary: { en: "Separates deterministic control, AI analysis, and accountable human decisions.", ja: "形式検証と進行管理、AIによる分析・推論、人間による受入れ・例外・リスク判断を分けます。" },
    links: { en: "064_ai_team_operating_boundary", ja: "064_ai_team_operating_boundary" },
  },
  {
    id: "065",
    level: "Implementation",
    levelJa: "実装",
    role: "Repository implementation",
    roleJa: "知識・手順の管理",
    question: { en: "Where is the operating model implemented?", ja: "業務実行モデルは、XRefKitのどこに実装されているのか。" },
    title: { en: "XRefKit Repository Overview", ja: "XRefKit リポジトリ概要" },
    summary: {
      en: "Explains XRefKit as the operating base that connects Goals, Skills, Knowledge, workflow evidence, and MCP distribution.",
      ja: "責務定義、組織固有知識、実行管理、証拠、元資料を分離し、更新・検証可能な正本として管理する構造を説明します。",
    },
    links: { en: "065_xrefkit_repository_overview", ja: "065_xrefkit_repository_overview" },
  },
  {
    id: "073",
    level: "Improvement and Distribution",
    levelJa: "改善と組織配布",
    role: "Evidence-led improvement and distribution",
    roleJa: "人間による改善と次版の配布",
    question: { en: "How do Dashboard observations become an improved, distributed version?", ja: "実行状況ダッシュボードの観測から、改善した次版をどう配布するのか。" },
    title: { en: "XRefKit Improvement and Distribution", ja: "XRefKit 改善と組織配布" },
    summary: { en: "Shows how people use run state, XID usage, and missing-information evidence to revise, validate, approve, distribute, and re-observe the next version.", ja: "実行状況ダッシュボードで実行状態、XID利用、不足情報を観測し、人間がKnowledge、Skill、routing、受入条件を改訂・検証して次版を配布する循環を説明します。" },
    links: { en: "073_xrefkit_organization_distribution", ja: "073_xrefkit_organization_distribution" },
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
    <div class="catalog-top"><span class="catalog-deck">${deck.level}</span><span class="catalog-lang">${languages.map((lang) => lang.toUpperCase()).join(" / ")}</span></div>
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
