import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("ja/docs/assets/063_ai_organization_explainer_clear");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const html = (body) => `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <style>${css}</style>
</head>
<body>${body}</body>
</html>`;

const wrap = ({ kicker, title, lead = "", body = "", summary = "", compact = false }) => `
  <main class="canvas">
    <div class="kicker">${kicker}</div>
    <h1>${title}</h1>
    ${lead ? `<p class="lead">${lead}</p>` : ""}
    <section class="stage${compact ? " compact" : ""}">${body}</section>
    ${summary ? `<div class="summary">${summary}</div>` : ""}
  </main>`;

const card = (tone, title, text, extraClass = "") => `
  <div class="card ${tone} ${extraClass}">
    <h2>${title}</h2>
    <p>${text}</p>
  </div>`;

const impact = (problemTitle, problemText, solutionTitle, solutionText) => `
  <div class="impact-grid">
    <div class="impact-box problem">
      <div class="impact-label">人間側に増えた問題</div>
      <h2>${problemTitle}</h2>
      <p>${problemText}</p>
    </div>
    <div class="impact-box solution">
      <div class="impact-label">次の解決策</div>
      <h2>${solutionTitle}</h2>
      <p>${solutionText}</p>
    </div>
  </div>`;

const dialogue = (questionTitle, questionText, answerTitle, answerText, mode = "both") => `
  <div class="dialogue-grid${mode === "question" ? " question-only" : ""}">
    <div class="bubble question">
      <h2>${questionTitle}</h2>
      <p>${questionText}</p>
    </div>
    ${mode === "question" ? "" : `<div class="bubble answer">
      <h2>${answerTitle}</h2>
      <p>${answerText}</p>
    </div>`}
  </div>`;

const list = (items) => `
  <div class="list">
    ${items.map((item) => `<div class="list-item"><div class="check">✓</div><div>${item}</div></div>`).join("")}
  </div>`;

const definition = () => `
  <div class="definition-grid">
    <div class="definition-main">
      <h2>AI Team とは</h2>
      <p>目的に対して、Skill、ドメイン知識、役割、チェック点、引き渡しを固定した AI の作業体制です。</p>
    </div>
    <div class="management-list">
      <div class="management-item">説明すること</div>
      <div class="management-item">判断すること</div>
      <div class="management-item">確認すること</div>
      <div class="management-item">引き渡すこと</div>
    </div>
  </div>`;

const compare = () => `
  <div class="compare-grid">
    <div class="compare-box before">
      <h2>Before</h2>
      <ul>
        <li>人間が毎回説明する</li>
        <li>人間が毎回判断する</li>
        <li>人間が毎回確認する</li>
        <li>人間が毎回引き渡す</li>
      </ul>
    </div>
    <div class="compare-box after">
      <h2>After</h2>
      <ul>
        <li>Skill が手順を固定する</li>
        <li>知識が判断基準を固定する</li>
        <li>チェック点が漏れを拾う</li>
        <li>責任と引き渡しが固定される</li>
      </ul>
    </div>
  </div>`;

const credit = () => `
  <div class="definition-grid">
    <div class="definition-main">
      <h2>音声クレジット</h2>
      <p>この動画の音声には、VOICEVOX を使用しています。</p>
    </div>
    <div class="management-list">
      <div class="management-item">VOICEVOX:ずんだもん</div>
      <div class="management-item">VOICEVOX:四国めたん</div>
      <div class="management-item">動画: AI Team Explainer</div>
      <div class="management-item">用途: AI 組織の説明</div>
    </div>
  </div>`;

const slides = {
  "01_title_q": wrap({
    kicker: "AI 組織が必要になる流れ",
    title: "AI を使うほど、人間の管理仕事が増えていく",
    body: dialogue(
      "AI を入れれば、楽になるんじゃないの?",
      "でも実際は、使い方を間違えると人間の管理仕事が増える。",
      "",
      "",
      "question"
    ),
    summary: "まず、よくある期待から確認する"
  }),
  "01_title": wrap({
    kicker: "AI 組織が必要になる流れ",
    title: "AI を使うほど、人間の管理仕事が増えていく",
    body: dialogue(
      "AI を入れれば、楽になるんじゃないの?",
      "でも実際は、使い方を間違えると人間の管理仕事が増える。",
      "今日はそこを順番に見る",
      "プロンプト、Skill、ドメイン知識、AI Team の順に、増える負担と解決策を整理する。"
    ),
    summary: "結論: AI Team は、人間が AI の仕事を管理できる形にする仕組み"
  }),
  "02_team_definition_q": wrap({
    kicker: "先に定義",
    title: "AI Team は、AI に仕事を任せるための作業体制",
    body: dialogue(
      "AI Team って、最初に言うと何?",
      "ここで一度、定義を置いておきます。",
      "",
      "",
      "question"
    ),
    summary: "先に言葉の意味を揃える"
  }),
  "02_team_definition": wrap({
    kicker: "先に定義",
    title: "AI Team は、AI に仕事を任せるための作業体制",
    body: definition(),
    summary: "AI Team は、AI の作業を人間が管理できる単位にまとめる"
  }),
  "03_problem_q": wrap({
    kicker: "出発点",
    title: "プロンプトだけだと、人間が毎回すべてを説明する",
    body: dialogue(
      "丁寧にプロンプトを書けば十分では?",
      "毎回、目的・前提・制約・出力形式を人間が説明することになる。",
      "",
      "",
      "question"
    ),
    summary: "まず、プロンプト運用の負担を見る"
  }),
  "03_problem": wrap({
    kicker: "出発点",
    title: "プロンプトだけだと、人間が毎回すべてを説明する",
    body: dialogue(
      "丁寧にプロンプトを書けば十分では?",
      "毎回、目的・前提・制約・出力形式を人間が説明することになる。",
      "Skill にする",
      "よく使う作業は、毎回の文章ではなく、再利用できる手順として固定する。説明疲れを減らす。"
    ),
    summary: "プロンプトの問題は AI だけでなく、人間が毎回説明役になること"
  }),
  "04_work_q": wrap({
    kicker: "次の対策",
    title: "Skill が増えると、人間は手順を管理する必要が出る",
    body: dialogue(
      "Skill にすれば安定するの?",
      "説明は減る。でも今度は、どの Skill を使うかが問題になる。",
      "",
      "",
      "question"
    ),
    summary: "Skill は解決策だが、新しい管理仕事も生む"
  }),
  "04_work": wrap({
    kicker: "次の対策",
    title: "Skill が増えると、人間は手順を管理する必要が出る",
    body: dialogue(
      "Skill にすれば安定するの?",
      "説明は減る。でも今度は、どの Skill を使うか、手順が目的に合うかを管理する必要が出る。",
      "ドメイン知識を足す",
      "例: 説明動画なら、台本化や音声化は Skill。何を正しい説明と見るかは知識で決める。"
    ),
    summary: "Skill は説明疲れを減らすが、今度は手順選択と手順管理が人間の仕事になる"
  }),
  "05_not_one_ai_q": wrap({
    kicker: "でも足りないもの",
    title: "ドメイン知識がない Skill は、判断を人間に戻してしまう",
    body: dialogue(
      "手順があるのに、なぜ知識が必要?",
      "Skill は進め方。正しさの基準は別に必要です。",
      "",
      "",
      "question"
    ),
    summary: "Skill とドメイン知識の境界を見る",
    compact: true
  }),
  "05_not_one_ai": wrap({
    kicker: "でも足りないもの",
    title: "ドメイン知識がない Skill は、判断を人間に戻してしまう",
    body: dialogue(
      "手順があるのに、なぜ知識が必要?",
      "Skill は進め方。何を正しいと見るかは、業務の用語・基準・制約で決まる。",
      "判断基準を共有する",
      "例: 初見向け、XRefkit は説明しない、実行とチェックを入れる。この基準が知識になる。"
    ),
    summary: "Skill は手順。判断にはドメイン知識がいる",
    compact: true
  }),
  "06_repository_q": wrap({
    kicker: "組織で使う条件",
    title: "知識を外に出すと、人間には更新責任が生まれる",
    body: dialogue(
      "知識を共有すれば終わり?",
      "共有した知識は、変わったときに更新する必要があります。",
      "",
      "",
      "question"
    ),
    summary: "知識は置くだけでなく保守する"
  }),
  "06_repository": wrap({
    kicker: "組織で使う条件",
    title: "知識を外に出すと、人間には更新責任が生まれる",
    body: dialogue(
      "知識を共有すれば終わり?",
      "終わりではない。ルールが変わったら、知識も更新しないと AI は古い正解で作業する。",
      "知識の置き場を決める",
      "誰が見ても同じ前提を参照でき、変更時に直せる形で管理する。"
    ),
    summary: "組織では、暗黙知を出すだけでなく、知識を保守する責任が必要"
  }),
  "07_handoff_q": wrap({
    kicker: "それでも残る問題",
    title: "Skill と知識が増えるほど、仕事はバラバラになりやすい",
    body: dialogue(
      "部品が揃えば、仕事は回る?",
      "部品だけでは、順番や責任までは決まりません。",
      "",
      "",
      "question"
    ),
    summary: "ここから仕事の流れの問題に移る"
  }),
  "07_handoff": wrap({
    kicker: "それでも残る問題",
    title: "Skill と知識が増えるほど、仕事はバラバラになりやすい",
    body: dialogue(
      "部品が揃えば、仕事は回る?",
      "まだ回らない。調査、判断、制作、確認の順番や受け渡しを、人間が都度つなぐことになる。",
      "AI Team にする",
      "役割、順番、責任、引き渡しをチーム構成として先に決める。"
    ),
    summary: "部品が揃っても、仕事の流れを設計しないと人間の調整負担が残る"
  }),
  "08_or_team_q": wrap({
    kicker: "解決策",
    title: "AI Team は、人間の交通整理を仕組みに変える",
    body: dialogue(
      "そこで AI Team が出てくるんですね?",
      "ここで、Skill と知識を仕事の流れにつなぎます。",
      "",
      "",
      "question"
    ),
    summary: "AI Team は部品を仕事に変える"
  }),
  "08_or_team": wrap({
    kicker: "解決策",
    title: "AI Team は、人間の交通整理を仕組みに変える",
    body: dialogue(
      "AI Team は何をしてくれるの?",
      "人間が毎回考えていた順番、責任、確認、引き渡しを、チームの構成として固定する。",
      "仕事としてつなぐ",
      "例: 制作役が作り、チェック役が漏れを見て、記録を残して次へ渡す。ここまでが Team。"
    ),
    summary: "AI Team は、手順・知識・責任・流れをまとめて仕事にする"
  }),
  "09_value_q": wrap({
    kicker: "AI Team が決めること",
    title: "AI は忘れる。だから人間が全部覚える設計にしない",
    body: dialogue(
      "AI が忘れるなら、人間が確認すればいい?",
      "全部を人間の記憶で追うと、見落としが起きます。",
      "",
      "",
      "question"
    ),
    summary: "確認の負担を構造で減らす"
  }),
  "09_value": wrap({
    kicker: "AI Team が決めること",
    title: "AI は忘れる。だから人間が全部覚える設計にしない",
    body: dialogue(
      "AI が忘れるなら、人間が確認すればいい?",
      "全部を人間の記憶で追うと疲弊する。作業漏れ、確認漏れ、根拠漏れを見落としやすい。",
      "実行とチェックを分ける",
      "作る役と見る役を分け、作業漏れ、確認漏れ、根拠漏れを別の目で拾う。"
    ),
    summary: "チェック役は、AI の忘れを人間が追い続ける負担を減らす"
  }),
  "10_conclusion_q": wrap({
    kicker: "AI Team の役割",
    title: "人間が見るべき場所を、チーム内に固定する",
    body: dialogue(
      "人間の仕事はなくなるの?",
      "なくなりません。人間の仕事の見方が変わります。",
      "",
      "",
      "question"
    ),
    summary: "人間の仕事がどう変わるかを見る"
  }),
  "10_conclusion": wrap({
    kicker: "AI Team の役割",
    title: "人間が見るべき場所を、チーム内に固定する",
    body: dialogue(
      "人間の仕事はなくなるの?",
      "なくならない。ただし、全部を追いかける仕事から、見るべき点を確認する仕事に変わる。",
      "確認点を固定する",
      "目的、実行、チェック、記録、引き渡しをチーム内に置き、確認できる形にする。"
    ),
    summary: "人間の仕事は、全部を見ることから、見るべき点を確認することへ変わる"
  }),
  "11_before_after_q": wrap({
    kicker: "導入前後",
    title: "人間の仕事は、全部を見ることから、見るべき点の確認へ",
    body: dialogue(
      "導入前後で、何が変わるの?",
      "Before / After で、管理仕事の置き場所を見ます。",
      "",
      "",
      "question"
    ),
    summary: "導入前後の違いを見る"
  }),
  "11_before_after": wrap({
    kicker: "導入前後",
    title: "人間の仕事は、全部を見ることから、見るべき点の確認へ",
    body: compare(),
    summary: "AI Team は、毎回の管理仕事を固定された作業体制に変える"
  }),
  "12_license_q": wrap({
    kicker: "まとめ",
    title: "AI Team は、人間の負担を見える仕事に変える",
    body: dialogue(
      "結局、AI Team が必要な理由は?",
      "最後に、増える負担と解決策をまとめます。",
      "",
      "",
      "question"
    ),
    summary: "最後に要点をまとめる"
  }),
  "12_license": wrap({
    kicker: "まとめ",
    title: "AI Team は、人間の負担を見える仕事に変える",
    body: dialogue(
      "結局、AI Team が必要な理由は?",
      "AI を使うほど、人間には説明、手順管理、知識更新、交通整理、確認の負担が増えるから。",
      "管理できる形にする",
      "AI Team は、それらの負担を役割、流れ、チェックに変え、組織で扱える仕事にする。"
    ),
    summary: "AI を組織で使うとは、人間が管理できる形に設計すること"
  }),
  "13_voicevox_credit": wrap({
    kicker: "クレジット",
    title: "音声ライセンス",
    body: credit(),
    summary: "音声: VOICEVOX:ずんだもん / VOICEVOX:四国めたん"
  })
};

await fs.mkdir(dir, { recursive: true });

for (const [name, body] of Object.entries(slides)) {
  await fs.writeFile(path.join(dir, `${name}.html`), html(body), "utf8");
}

console.log(`rendered ${Object.keys(slides).length} html files`);
