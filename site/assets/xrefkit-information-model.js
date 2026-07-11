const XREFKIT_TOUR = [
  { id: "055", phase: "Why", ja: "なぜ通常のAI利用だけでは業務実行にならないのか", en: "Why ordinary AI use is not business execution", jaPath: "why-ai-organization-needed" },
  { id: "063", phase: "How", ja: "Goalから受入れまで、限定責務をどう接続するか", en: "How bounded responsibilities connect Goal to acceptance", jaPath: "063_ai_organization_explainer_clear", enPath: "063_ai_organization_explainer_clear" },
  { id: "064", phase: "Boundary", ja: "ツール・AI・人間はそれぞれ何を決めるのか", en: "What tools, AI, and humans decide", jaPath: "064_ai_team_operating_boundary", enPath: "064_ai_team_operating_boundary" },
  { id: "065", phase: "Implementation", ja: "業務実行モデルはXRefKitのどこに実装されるのか", en: "Where the operating model is implemented", jaPath: "065_xrefkit_repository_overview", enPath: "065_xrefkit_repository_overview" },
  { id: "073", phase: "Improvement and Distribution", ja: "実行証跡から改善し、次の版をどう配布するのか", en: "How evidence becomes an improved, distributed version", jaPath: "073_xrefkit_organization_distribution" },
];

const XREFKIT_TERMS = {
  Goal: "目標と受入条件",
  Skill: "限定責務",
  "Workflow protocol": "作業進行規約",
  Knowledge: "組織固有知識",
  "Semantic routing": "意味による次作業選択",
  Evidence: "証跡",
  "Human acceptance": "人間による受入れ",
  Handoff: "引継ぎ",
};

function deckHref(lang, path) {
  return `/XRefKit/${lang}/slides/${path}/`;
}

for (const host of document.querySelectorAll("[data-xrefkit-navigation]")) {
  const id = host.dataset.xrefkitNavigation;
  const lang = document.documentElement.lang === "ja" ? "ja" : "en";
  const index = XREFKIT_TOUR.findIndex((item) => item.id === id);
  const current = XREFKIT_TOUR[index];
  const previous = XREFKIT_TOUR[index - 1];
  const next = XREFKIT_TOUR[index + 1];
  const label = (item) => lang === "ja" ? item.ja : item.en;
  const pathFor = (item, targetLang) => item && item[`${targetLang}Path`];
  const links = [];
  if (previous && pathFor(previous, lang)) links.push(`<a href="${deckHref(lang, pathFor(previous, lang))}">${lang === "ja" ? "前の資料" : "Previous"}: ${label(previous)}</a>`);
  links.push(`<a href="/XRefKit/">${lang === "ja" ? "全体像へ戻る" : "Back to overview"}</a>`);
  links.push(`<a href="/XRefKit/${lang}/">${lang === "ja" ? "全資料カタログ" : "All decks"}</a>`);
  const other = lang === "ja" ? "en" : "ja";
  if (pathFor(current, other)) links.push(`<a href="${deckHref(other, pathFor(current, other))}">${other === "ja" ? "日本語" : "English"}</a>`);
  if (next && pathFor(next, lang)) links.push(`<a href="${deckHref(lang, pathFor(next, lang))}">${lang === "ja" ? "次の資料" : "Next"}: ${label(next)}</a>`);
  host.className = "xrefkit-deck-navigation";
  host.innerHTML = links.join("");
}

globalThis.XREFKIT_INFORMATION_MODEL = { tour: XREFKIT_TOUR, terms: XREFKIT_TERMS };
