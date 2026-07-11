import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/065_xrefkit_repository_overview");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const slides = [
  {
    name: "01_title",
    question: "このリポジトリは、結局何のためにあるのですか。",
    title: "XRefKit は AI 作業を管理可能にするための運用基盤です。",
    copy:
      "単なる文書置き場ではなく、AI が必要な知識だけを読み、決められた境界で動き、後から追跡できる形で作業するためのリポジトリです。",
    cards: [
      ["役割", "AI のふるまい、知識読み込み、作業構造、記録を一つの場所で扱います。"],
      ["中心", "主役は管理可能なAI作業であり、リンク維持はその補助機能です。"],
      ["狙い", "忘却、責務混在、判断漏れ、引き継ぎ断絶を減らします。"],
    ],
    takeaway: "XRefKit は <strong>AI が作業できること</strong>ではなく、<strong>AI 作業を運用できること</strong>を狙います。",
  },
  {
    name: "02_not_docs",
    question: "文書を置くだけなら、普通のリポジトリで十分ではないですか。",
    title: "普通の保管だけでは、AI が何を読むか、どこまで信じるか、どう動くかが固定されません。",
    copy:
      "ファイルがあるだけでは、知識の場所、手順の境界、判断の責任、確認のしかたが毎回ゆらぎます。XRefKit はその揺れを構造で減らします。",
    cards: [
      ["保管だけの問題", "AI が毎回広く読んで迷い、古い文脈や余計な断片も拾いやすくなります。"],
      ["必要な追加", "知識の置き場所だけでなく、責務、記録、境界の定義が必要です。"],
      ["結果", "読ませ方と動かし方が分かれるので、再現しやすくなります。"],
    ],
    takeaway: "<strong>情報の保管</strong>だけでは足りず、<strong>AI の読み方と働き方の構造</strong>まで必要です。",
  },
  {
    name: "03_layers",
    question: "では、このリポジトリは何をどう分けているのですか。",
    title: "パッケージ、責務、知識、道具、実行記録、元資料を役割別に分けています。",
    copy:
      "人向け説明、実行手順、共有知識、実行記録、元資料を混ぜずに置くことで、読む相手と目的を分離します。",
    cards: [
      ["パッケージ", "xrefkitが実行管理、XID参照解決、ツール一覧、MCP接続を持ちます。"],
      ["実行と知識", "責務と組織固有知識をXIDで選択し、必要な本文だけを読みます。"],
      ["証拠と元資料", "元資料と実行記録を分け、根拠、判断、履歴を残します。"],
    ],
    takeaway: "層を分ける目的は整理整頓ではなく、<strong>AI が読むもの、従うもの、残すものを分離すること</strong>です。",
  },
  {
    name: "04_runtime",
    question: "責務定義があれば、そのまま実行すればいいのではないですか。",
    title: "責務の実行を、記録と終了判定を持つ実行管理枠で囲います。",
    copy:
      "xrefkit skill runコマンドで開始し、作業項目、成果物、懸念事項、役割分離を記録してから閉じます。責務定義を読むだけでは完了しません。",
    cards: [
      ["開始", "定義情報を検証し、実行記録を開いてから作業を始めます。"],
      ["途中", "実行項目、成果物、証拠、未知やリスクを機械可読で残します。"],
      ["終了", "未完了、未記録、未解決の懸念事項があると終了が拒否されます。"],
    ],
    takeaway: "責務定義は手順書ではなく、<strong>実行記録ごと管理される作業単位</strong>として扱います。",
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
    question: "結局、このリポジトリの現在地を一言でいうと何ですか。",
    title: "XRefKitは、ドメイン手順と判断を組織へ配布するPythonパッケージです。",
    copy:
      "知識、実行、確認、引き継ぎ、人間判断を同じ場所で分離し、AI 作業を場当たり的なプロンプト運用から、管理可能な作業へ変えます。",
    cards: [
      ["読む", "対象と検出事項の一覧から選び、必要なXID本文だけを展開します。"],
      ["動かす", "統合パッケージの責務実行機能とツールで作業を囲います。"],
      ["配る", "同じ参照解決機構をリポジトリ、導入済みパッケージ、MCPから利用します。"],
    ],
    takeaway: "<strong>AI が便利</strong>で終わらせず、<strong>AI 作業を運用可能にする</strong>ところまでを、このリポジトリが担います。",
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
