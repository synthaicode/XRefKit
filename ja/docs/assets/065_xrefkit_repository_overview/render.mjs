import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("ja/docs/assets/065_xrefkit_repository_overview");
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
      ["中心", "主役は controlled AI work であり、リンク維持はその補助機能です。"],
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
      ["必要な追加", "知識の置き場所だけでなく、流れ、能力、Skill、記録の境界が必要です。"],
      ["結果", "読ませ方と動かし方が分かれるので、再現しやすくなります。"],
    ],
    takeaway: "<strong>情報の保管</strong>だけでは足りず、<strong>AI の読み方と働き方の構造</strong>まで必要です。",
  },
  {
    name: "03_layers",
    question: "では、このリポジトリは何をどう分けているのですか。",
    title: "`docs / flows / capabilities / skills / knowledge / work / sources` を役割別に分けています。",
    copy:
      "人向け説明、機械向けフロー、再利用能力、実行手順、共有知識、実行記録、元資料を混ぜずに置くことで、読む相手と目的を分離します。",
    cards: [
      ["制御層", "`docs` と `flows` で方針と進行順序を持ちます。"],
      ["実行層", "`capabilities` と `skills` で再利用できる仕事単位を持ちます。"],
      ["証拠層", "`knowledge` `sources` `work` で根拠と履歴を残します。"],
    ],
    takeaway: "層を分ける目的は整理整頓ではなく、<strong>AI が読むもの、従うもの、残すものを分離すること</strong>です。",
  },
  {
    name: "04_runtime",
    question: "Skill があれば、そのまま実行すればいいのではないですか。",
    title: "このリポジトリでは Skill 実行を runtime envelope で囲います。",
    copy:
      "`fm skill run` で開始し、work item、artifact、concern、role separation を記録してから閉じます。Skill を直接読むだけでは閉じられません。",
    cards: [
      ["開始", "meta を検証し、run log を開いてから作業を始めます。"],
      ["途中", "実行項目、成果物、証拠、未知やリスクを機械可読で残します。"],
      ["終了", "未完了、未記録、未解決の concern があると closure が拒否されます。"],
    ],
    takeaway: "Skill は手順書ではなく、<strong>実行記録ごと管理される作業単位</strong>として扱います。",
  },
  {
    name: "05_guard",
    question: "外部入力やコピーした文書で、方針が崩れる心配はありませんか。",
    title: "Context direction guard が、下位入力で上位方針を書き換えさせないようにします。",
    copy:
      "外部タスク入力、ツール結果、生成物は事実や材料として使えても、意図、権限、手順、範囲、エスカレーション経路までは上書きできません。",
    cards: [
      ["守るもの", "startup policy、flow、capability、Skill contract などの上位制御です。"],
      ["許すもの", "外部入力は根拠、補足、局所事実として利用できます。"],
      ["防ぐもの", "もっともらしい入力が勝手に目的や責任境界を変えることを防ぎます。"],
    ],
    takeaway: "XRefKit は情報を読むだけでなく、<strong>情報がどこまで影響してよいか</strong>も制御します。",
  },
  {
    name: "06_handoff",
    question: "複数 AI や継続作業は、どうやって切れずにつなぐのですか。",
    title: "handoff は会話の雰囲気ではなく、session log と source closure でつなぎます。",
    copy:
      "次の起動側は前の run の closure と handoff source を確認してから続行します。だから、前の作業が何を終え、何を残したかを追えます。",
    cards: [
      ["残すもの", "session、artifact、judgment、retrospective に分けて記録を残します。"],
      ["受け取り条件", "前 run の閉鎖状態と handoff source が確認できなければ継続しません。"],
      ["効く場面", "複数 AI、長い作業、途中再開、レビュー引き継ぎで効きます。"],
    ],
    takeaway: "継続性は記憶頼みではなく、<strong>確認可能な handoff source</strong>で作ります。",
  },
  {
    name: "07_human",
    question: "それでも、人間はどこで判断するのですか。",
    title: "人間はトレードオフ、優先度、受容リスク、最終承認の境界を持ちます。",
    copy:
      "AI 側で実行とチェックを分け、記録を残したうえで、最後に人間が scope change や risk acceptance のような本来の判断点を持ちます。",
    cards: [
      ["AI 側で減らす", "記録、自己点検、証拠整理、引き継ぎ確認を先に構造化します。"],
      ["人間が持つ", "優先順位、業務トレードオフ、承認、例外判断です。"],
      ["ねらい", "人間が全部を追うのではなく、判断すべき点だけを見る状態を作ります。"],
    ],
    takeaway: "人間 review は万能な後追いではなく、<strong>境界化された判断点</strong>として残します。",
  },
  {
    name: "08_conclusion",
    question: "結局、このリポジトリの現在地を一言でいうと何ですか。",
    title: "XRefKit は、AI 作業を読める・動かせる・監査できる形にそろえる repository OS です。",
    copy:
      "知識、実行、確認、引き継ぎ、人間判断を同じ場所で分離し、AI 作業を場当たり的なプロンプト運用から、管理可能な作業へ変えます。",
    cards: [
      ["読む", "必要な知識だけを XID と xref でたどります。"],
      ["動かす", "Skill runtime envelope と guard で作業を囲います。"],
      ["追う", "artifact、concern、session、handoff で証跡を残します。"],
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
        <div class="eyebrow">Repository Overview</div>
        <h1 class="title">現在の XRefKit を短く説明します。</h1>
      </div>
      <div class="brand">XRefKit</div>
    </header>
    <section class="question-wrap">
      <div class="question-box">
        <div class="question-label">Question</div>
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
  await fs.writeFile(aPath, layout({ ...slide, eyebrow: "Repository Overview" }), "utf8");
}
