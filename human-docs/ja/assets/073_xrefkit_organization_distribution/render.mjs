import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/073_xrefkit_organization_distribution");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const slides = [
  {
    name: "01_title",
    question: "管理された知識と手順を、組織のAI利用環境へどう届けるのですか。",
    title: "XRefKitは、検証済みの知識と手順を同じ契約で配布します。",
    copy: "リポジトリで管理した正本から、実行に必要な契約と資産をまとめ、利用環境によって内容が変わらない形で届けます。",
    cards: [
      ["配布元", "更新・検証されたリポジトリの正本を使います。"],
      ["配布単位", "契約、責務定義、必須知識、実行ツールをまとめます。"],
      ["利用先", "リポジトリ、導入済みパッケージ、MCPから利用します。"],
    ],
    takeaway: "<strong>管理</strong>と<strong>配布</strong>を分け、配布先で正本の意味を変えません。",
  },
  {
    name: "02_unit",
    question: "組織へ配布する単位には、何が含まれるのですか。",
    title: "文書一式ではなく、実行に必要な契約と資産を配布します。",
    copy: "AIが同じ境界で作業できるように、起動・進行契約、責務定義、必須知識、クライアント側ツールを分けてまとめます。",
    cards: [
      ["起動と進行", "起動契約、作業進行規約、終了条件を含めます。"],
      ["責務と知識", "選択した責務定義と必要なXID本文を含めます。"],
      ["実行ツール", "クライアント側で必要な決定的コマンドを含めます。"],
    ],
    takeaway: "配布物は<strong>読む情報</strong>だけでなく、<strong>同じ動作を保つ契約</strong>を持ちます。",
  },
  {
    name: "03_package",
    question: "これらの配布資産は、どこにまとめられるのですか。",
    title: "xrefkitパッケージに、実行、MCP、ツール、責務資産をまとめます。",
    copy: "Pythonパッケージを共通の配布単位とし、実行管理、参照解決、MCP接続、クライアント用ツールを同じ版として扱います。",
    cards: [
      ["実行管理", "目標、責務実行、記録、終了判定を扱います。"],
      ["MCP", "起動情報、責務定義、XID本文を配信します。"],
      ["ツールと責務", "決定的コマンドと配布対象の責務資産を持ちます。"],
    ],
    takeaway: "分割された機能を、<strong>一つの版を持つPythonパッケージ</strong>として配布します。",
  },
  {
    name: "04_generation",
    question: "更新途中の資産が混ざることはありませんか。",
    title: "実行時資産は世代単位で公開し、current.jsonが現在世代を示します。",
    copy: "新しい世代を完成させてから参照先を切り替えるため、利用側が複数世代の契約や知識を混ぜて読むことを防ぎます。",
    cards: [
      ["世代", "契約本文、必須XID、マニフェストを一つの世代にまとめます。"],
      ["原子的公開", "世代を完成させた後で現在世代の参照先を切り替えます。"],
      ["利用契約", "正式な利用側はcurrent.jsonが指す世代を必ず読みます。"],
    ],
    takeaway: "配布資産の一貫性は、<strong>世代単位の公開</strong>と<strong>正式な参照点</strong>で守ります。",
  },
  {
    name: "05_providers",
    question: "利用環境が違っても、同じXIDを参照できますか。",
    title: "同じXIDを、リポジトリ、導入済みパッケージ、MCPから解決します。",
    copy: "利用場所に応じて参照元を切り替えても、XIDを主キーとする契約は変えません。競合する本文を黙って優先することもありません。",
    cards: [
      ["リポジトリ", "開発時は管理中の正本を直接解決します。"],
      ["導入済みパッケージ", "組み込まれた世代の資産から解決します。"],
      ["MCP", "外部の利用環境へ必要な本文だけを返します。"],
    ],
    takeaway: "参照元が変わっても<strong>XIDの意味は同じ</strong>であり、競合は明示的に扱います。",
  },
  {
    name: "06_mcp",
    question: "MCPサーバーが、責務の作業まで実行するのですか。",
    title: "MCPは配布と参照解決を担い、作業実行はクライアント側が行います。",
    copy: "サーバーは起動契約、責務定義、XID本文、実行用資産を提供します。AIの作業とクライアント用コマンドの実行主体にはなりません。",
    cards: [
      ["起動", "起動情報と読込み順をクライアントへ返します。"],
      ["参照解決", "要求された責務定義とXID本文を返します。"],
      ["相関", "実行識別子を結び、配信したXIDを観測可能にします。"],
    ],
    takeaway: "MCPを<strong>薄い配布境界</strong>に保ち、実行責任をクライアントから奪いません。",
  },
  {
    name: "07_bootstrap",
    question: "クライアントは、受け取った配布物をそのまま信頼するのですか。",
    title: "取得後に、ハッシュ、版、互換性を確認してから利用します。",
    copy: "パッケージの導入または必要資産の配置後に、内容ハッシュと版の条件を確認します。ネットワーク経由の信頼は配置環境の責任として扱います。",
    cards: [
      ["導入", "Pythonパッケージとして導入するか、必要資産を配置します。"],
      ["整合性", "マニフェスト、ハッシュ、版、拡張条件を確認します。"],
      ["信頼境界", "通信、認証、配布元の信頼を配置環境で管理します。"],
    ],
    takeaway: "配布できることと信頼できることを分け、<strong>利用前の検証</strong>を要求します。",
  },
  {
    name: "08_conclusion",
    question: "管理と配布を分けると、組織では何が揃うのですか。",
    title: "一つの管理済み正本を、同じ契約で複数のAI利用環境へ届けられます。",
    copy: "正本の更新責任をリポジトリへ残したまま、利用側は環境に合う経路から同じ責務定義、必須知識、実行契約を取得できます。",
    cards: [
      ["一つの正本", "知識と手順の変更元をリポジトリへ集約します。"],
      ["複数の経路", "直接利用、パッケージ導入、MCP配信を選べます。"],
      ["同じ契約", "経路が変わっても実行境界とXIDの意味を保ちます。"],
    ],
    takeaway: "組織配布は正本を複製することではなく、<strong>同じ契約で利用可能にすること</strong>です。",
  },
];

function layout({ eyebrow, title, question, copy, cards, takeaway }) {
  const cardHtml = cards.map(([tag, text]) => `
    <article class="card"><div class="card-tag">${tag}</div><p>${text}</p></article>`).join("");
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8" /><title>${title}</title><style>${css}</style></head>
  <body><main class="slide"><header class="header"><div><div class="eyebrow">${eyebrow}</div><h1 class="title">${title}</h1></div><div class="brand">XRefKit</div></header>
  <section class="summary"><div class="summary-label">問い</div><div class="summary-copy">${question}</div><div class="summary-title">${copy}</div></section>
  <section class="cards">${cardHtml}</section><div class="takeaway">${takeaway}</div></main></body></html>`;
}

function questionOnly({ question }) {
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8" /><title>${question}</title><style>${css}</style></head>
  <body><main class="slide"><header class="header"><div><div class="eyebrow">組織配布</div><h1 class="title">管理された知識と手順を組織へ届けます。</h1></div><div class="brand">XRefKit</div></header>
  <section class="question-wrap"><div class="question-box"><div class="question-label">問い</div><div class="question-text">${question}</div></div></section>
  <div class="takeaway"><strong>配布の疑問</strong>を先に置き、その仕組みを一つずつ確認します。</div></main></body></html>`;
}

for (const slide of slides) {
  await fs.writeFile(path.join(dir, `${slide.name}_q.html`), questionOnly(slide), "utf8");
  await fs.writeFile(path.join(dir, `${slide.name}.html`), layout({ ...slide, eyebrow: "組織配布" }), "utf8");
}
console.log(`rendered ${slides.length * 2} html files`);
