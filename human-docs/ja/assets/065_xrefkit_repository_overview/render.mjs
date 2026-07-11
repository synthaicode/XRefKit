import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/065_xrefkit_repository_overview");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const slides = [
  {
    name: "01_title",
    question: "AIの特性に応じて分けた解決策は、XRefKitのどこに実装されているのですか。",
    title: "XRefKitは、問題ごとの解決策をリポジトリ構造として実装します。",
    copy:
      "通常のAI利用では、完了、責務、進行、判断材料、接続に別々の問題があります。問題ごとに異なる実装構造を対応させます。",
    cards: [
      ["完了と責務", "目標の状態管理と責務定義を別々に持ちます。"],
      ["進行と判断材料", "実行管理とXID参照知識を分離します。"],
      ["接続と証拠", "次作業選択と実行記録で、責務間を追跡可能につなぎます。"],
    ],
    takeaway: "ここからは<strong>なぜ必要か</strong>ではなく、<strong>どこに実装されるか</strong>を見ます。",
  },
  {
    name: "02_not_docs",
    question: "完了、責務、進行、判断材料、接続は、どの実装構造が担当するのですか。",
    title: "目標、限定責務、進行、判断材料、接続を別の構造で持ちます。",
    copy:
      "一つの万能機能にまとめず、問題ごとの責任境界をパッケージ、責務定義、組織固有知識、実行記録へ対応させます。",
    cards: [
      ["目標と限定責務", "目標状態は実行管理、担当範囲は責務定義が持ちます。"],
      ["進行と組織固有知識", "作業進行規約は実行記録、判断材料はXID本文が持ちます。"],
      ["次作業選択", "責務一覧と現在状態から、次に必要な責務を選びます。"],
    ],
    takeaway: "<strong>問題と解決策の対応</strong>を、そのまま<strong>実装境界</strong>として保ちます。",
  },
  {
    name: "03_layers",
    question: "では、このリポジトリは何をどう分けているのですか。",
    title: "パッケージ、責務定義、組織固有知識、実行記録、元資料を分けています。",
    copy:
      "人向け説明、実行手順、共有知識、実行記録、元資料を混ぜずに置くことで、読む相手と目的を分離します。",
    cards: [
      ["パッケージ", "xrefkitが実行管理、XID参照解決、ツール一覧、MCP接続を持ちます。"],
      ["責務と知識", "責務定義と組織固有知識をXIDで選択し、必要な本文だけを読みます。"],
      ["証拠と元資料", "元資料と実行記録を分け、根拠、判断、履歴を残します。"],
    ],
    takeaway: "層を分ける目的は整理整頓ではなく、<strong>AI が読むもの、従うもの、残すものを分離すること</strong>です。",
  },
  {
    name: "04_runtime",
    question: "責務定義があれば、そのまま実行すればいいのではないですか。",
    title: "作業進行規約を、記録と終了判定を持つ実行管理枠として実装します。",
    copy:
      "xrefkit skill runコマンドで責務実行を開始し、作業項目、成果物、懸念事項、役割分離を記録してから閉じます。これが作業途中の終了と作業漏れへの実装です。",
    cards: [
      ["開始", "定義情報を検証し、実行記録を開いてから作業を始めます。"],
      ["途中", "実行項目、成果物、証拠、未知やリスクを機械可読で残します。"],
      ["終了", "未完了、未記録、未解決の懸念事項があると終了が拒否されます。"],
    ],
    takeaway: "限定責務と作業進行規約を混ぜず、<strong>責務定義</strong>と<strong>実行管理</strong>に分けます。",
  },
  {
    name: "05_guard",
    question: "外部入力やコピーした文書で、方針が崩れる心配はありませんか。",
    title: "文脈方向保護が、下位入力による上位方針の書き換えを防ぎます。",
    copy:
      "外部タスク入力、ツール結果、生成物は事実や材料として使えても、意図、権限、手順、範囲、エスカレーション経路までは上書きできません。",
    cards: [
      ["守るもの", "起動方針、責務契約、作業進行規約などの上位制御です。"],
      ["許すもの", "外部入力は根拠、補足、局所事実として利用できます。"],
      ["防ぐもの", "もっともらしい入力が勝手に目的や責任境界を変えることを防ぎます。"],
    ],
    takeaway: "XRefKit は情報を読むだけでなく、<strong>情報がどこまで影響してよいか</strong>も制御します。",
  },
  {
    name: "06_handoff",
    question: "複数 AI や継続作業は、どうやって切れずにつなぐのですか。",
    title: "引継ぎは会話の雰囲気ではなく、実行履歴と引継ぎ元の終了状態でつなぎます。",
    copy:
      "次の起動側は前の実行の終了状態と引継ぎ元を確認してから続行します。だから、前の作業が何を終え、何を残したかを追えます。",
    cards: [
      ["残すもの", "実行単位、成果物、判断、振り返りに分けて記録を残します。"],
      ["受け取り条件", "前の実行の終了状態と引継ぎ元が確認できなければ継続しません。"],
      ["効く場面", "複数 AI、長い作業、途中再開、レビュー引き継ぎで効きます。"],
    ],
    takeaway: "継続性は記憶頼みではなく、<strong>確認可能な引継ぎ元</strong>で作ります。",
  },
  {
    name: "07_human",
    question: "実行後に、どの組織固有知識が使われたか確認できますか。",
    title: "責務実行とMCPを実行識別子で結び、XIDの利用を観測します。",
    copy:
      "選択、解決、読込み、適用を分けて記録し、使われなかった知識や不足した知識を改善材料にします。",
    cards: [
      ["相関", "クライアント実行とMCPアクセスを同じ識別子で結びます。"],
      ["区別", "XIDの選択、解決、読込み、適用を別の記録として残します。"],
      ["改善", "証拠から一覧、責務、組織固有知識の正本を見直します。"],
    ],
    takeaway: "観測は監査の終点ではなく、<strong>次の実行を改善する入力</strong>です。",
  },
  {
    name: "08_conclusion",
    question: "この実装構造を、組織の利用環境へどう届けるのですか。",
    title: "XRefKitは、同じ実装構造を組織へ配布するPythonパッケージです。",
    copy:
      "問題ごとに分けた解決策を、責務定義、組織固有知識、実行管理、証拠、参照解決として実装し、同じ構造を複数の利用環境へ届けます。",
    cards: [
      ["リポジトリ", "正本と開発時の実装構造を直接利用します。"],
      ["導入済みパッケージ", "圧縮された必須資産と実行機能を利用します。"],
      ["MCP", "同じ参照解決機構から必要なXID本文を配信します。"],
    ],
    takeaway: "問題ごとに分けた仕組みを、<strong>同じ契約のまま実装・配布する</strong>ことが、この資料の結論です。",
  },
];

function layout({ eyebrow, title, question, copy, cards, takeaway }) {
  const cardHtml = cards
    .map(
      ([tag, text]) => `
      <article class="card">
        <div class="card-tag">${tag}</div>
        <p>${text}</p>
      </article>`
    )
    .join("");
  return `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
  <style>${css}</style>
</head>
<body>
  <main class="slide">
    <header class="header">
      <div>
        <div class="eyebrow">${eyebrow}</div>
        <h1 class="title">${title}</h1>
      </div>
      <div class="brand">XRefKit</div>
    </header>
    <section class="summary">
      <div class="summary-label">問い</div>
      <div class="summary-copy">${question}</div>
      <div class="summary-title">${copy}</div>
    </section>
    <section class="cards">${cardHtml}</section>
    <div class="takeaway">${takeaway}</div>
  </main>
</body>
</html>`;
}

function questionOnly({ title, question }) {
  return `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
  <style>${css}</style>
</head>
<body>
  <main class="slide">
    <header class="header">
      <div>
        <div class="eyebrow">リポジトリ概要</div>
        <h1 class="title">現在の XRefKit を短く説明します。</h1>
      </div>
      <div class="brand">XRefKit</div>
    </header>
    <section class="question-wrap">
      <div class="question-box">
        <div class="question-label">問い</div>
        <div class="question-text">${question}</div>
      </div>
    </section>
    <div class="takeaway"><strong>視聴者の疑問</strong>を先に置き、その次に一つずつ説明します。</div>
  </main>
</body>
</html>`;
}

for (const slide of slides) {
  const qPath = path.join(dir, `${slide.name}_q.html`);
  const aPath = path.join(dir, `${slide.name}.html`);
  await fs.writeFile(qPath, questionOnly(slide), "utf8");
  await fs.writeFile(aPath, layout({ ...slide, eyebrow: "リポジトリ概要" }), "utf8");
}
