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
      <div class="card-label">Q</div>
      <h2>${questionTitle}</h2>
      <p>${questionText}</p>
    </div>
    ${mode === "question" ? "" : `<div class="bubble answer">
      <div class="card-label">A</div>
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
      <div class="card-label">DEF</div>
      <h2>AI Team とは</h2>
      <p>目的に対して、Skill、業務知識と判断ルール、役割、確認点、引き渡しを固定した運用体制です。</p>
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
        <li>業務知識と判断ルールが正しさを固定する</li>
        <li>確認点が漏れを拾う</li>
        <li>責任と引き渡しが固定される</li>
      </ul>
    </div>
  </div>`;

const burdenFlow = () => `
  <div class="burden-flow">
    <div class="burden-step">
      <div class="burden-label">Prompt</div>
      <h2>説明する負担</h2>
      <p>目的、前提、制約、出力形式を、人間が毎回説明する。</p>
      <div class="burden-arrow">Skill で減らす</div>
    </div>
    <div class="burden-step">
      <div class="burden-label">Skill</div>
      <h2>手順を選ぶ負担</h2>
      <p>手順は固定されるが、どれを使うかは人間が選ぶ。</p>
      <div class="burden-arrow">業務知識が必要</div>
    </div>
    <div class="burden-step">
      <div class="burden-label">Knowledge</div>
      <h2>更新・維持する負担</h2>
      <p>業務知識と判断ルールは共有されるが、古くならないよう更新・維持が必要。</p>
      <div class="burden-arrow">流れが必要</div>
    </div>
    <div class="burden-step">
      <div class="burden-label">AI Team</div>
      <h2>流れをつなぐ負担</h2>
      <p>役割、確認、順番、引き渡しを固定し、人間が確認できる形にする。</p>
      <div class="burden-arrow">管理可能な AI 作業へ</div>
    </div>
  </div>`;

const credit = () => `
  <div class="definition-grid">
    <div class="definition-main">
      <div class="card-label">DEF</div>
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
    kicker: "共通認識",
    title: "一般的には、AIで個人作業は速くなる",
    body: dialogue(
      "AIで個人作業は速くなる",
      "文章作成、要約、調査、コード生成では便利さを実感しやすい。",
      "",
      "",
      "question"
    ),
    summary: "まず、多くの人が共有している認識から始める"
  }),
  "01_title": wrap({
    kicker: "共通認識",
    title: "一般的には、AIで個人作業は速くなる",
    body: dialogue(
      "便利さは実感しやすい",
      "たたき台を出す、情報を集める、表現を整える作業は速くなる。",
      "ここまでは共通認識",
      "問題は、その速さが組織の品質・コスト・納期に変わるか。"
    ),
    summary: "個人の速度向上と組織のQCD改善を分けて見る"
  }),
  "02_team_definition_q": wrap({
    kicker: "事実確認",
    title: "でも、AIの後ろには人間の作業が残る",
    body: dialogue(
      "AI が出したら終わり?",
      "実際には、人間が検証し、統合し、監視し、判断している。",
      "",
      "",
      "question"
    ),
    summary: "AI利用後の人間作業を見落とさない"
  }),
  "02_team_definition": wrap({
    kicker: "事実確認",
    title: "でも、AIの後ろには人間の作業が残る",
    body: dialogue(
      "AI が出したら終わり?",
      "外部調査でも、生成AI利用時の人間の仕事は情報検証、回答統合、タスク管理へ移ると整理されている。",
      "ここがQCDに効く",
      "確認、比較、統合、判断が残るなら、速さだけでは改善を判断できない。"
    ),
    summary: "AIの便利さは、人間側に残る作業とセットで評価する"
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
    summary: "プロンプトの問題は、AI の挙動だけでなく、人間が毎回説明役になること"
  }),
  "03_prompt_skill_limit": wrap({
    kicker: "問題提起",
    title: "逐次利用のままでは、人間側に負荷が集まる",
    body: impact(
      "Prompt / Skill を増やす",
      "人間が選び、つなぎ、確認し、判断する前提が残る。",
      "使い方を変える",
      "AIをチームとして構造化し、役割と流れを固定する。"
    ),
    summary: "問題はAIの便利さではなく、人間が逐次管理する前提にある"
  }),
  "04_work_q": wrap({
    kicker: "次の対策",
    title: "Skill を増やすと、次は手順を選ぶ負担が生まれる",
    body: dialogue(
      "Skill にすれば安定するの?",
      "説明は減る。でも今度は、どの Skill を使うかが問題になる。",
      "",
      "",
      "question"
    ),
    summary: "Skill は解決策だが、新しい管理負荷も生む"
  }),
  "04_work": wrap({
    kicker: "次の対策",
    title: "Skill を増やすと、次は手順を選ぶ負担が生まれる",
    body: dialogue(
      "Skill にすれば安定するの?",
      "説明は減る。でも今度は、どの Skill を使うか、手順が目的に合うかを選ぶ負担が生まれる。",
      "業務知識と判断ルールを足す",
      "例: 説明動画なら、台本化や音声化は Skill。何を正しい説明と見るかは知識で決める。"
    ),
    summary: "Skill は説明疲れを減らすが、次は手順を選ぶ負担が人間に残る"
  }),
  "05_not_one_ai_q": wrap({
    kicker: "でも足りないもの",
    title: "業務知識がない Skill は、判断を人間に戻してしまう",
    body: dialogue(
      "手順があるのに、なぜ業務知識が必要?",
      "Skill は進め方。正しさは業務知識と判断ルールで決まります。",
      "",
      "",
      "question"
    ),
    summary: "Skill と業務知識の境界を見る",
    compact: true
  }),
  "05_not_one_ai": wrap({
    kicker: "でも足りないもの",
    title: "業務知識がない Skill は、判断を人間に戻してしまう",
    body: dialogue(
      "手順があるのに、なぜ業務知識が必要?",
      "Skill は進め方。何を正しいと見るかは、業務の用語・基準・制約で決まる。",
      "業務知識と判断ルールを共有する",
      "例: 初見向け、XRefkit は説明しない、実行とチェックを入れる。このルールが業務知識と判断ルールになる。"
    ),
    summary: "Skill は手順。正しさは業務知識と判断ルールで決まる",
    compact: true
  }),
  "06_repository_q": wrap({
    kicker: "組織で使う条件",
    title: "業務知識を共有すると、更新責任が生まれる",
    body: dialogue(
      "業務知識を共有すれば終わり?",
      "共有した業務知識と判断ルールは、変わったときに更新する必要があります。",
      "",
      "",
      "question"
    ),
    summary: "業務知識は共有するだけでなく、更新・維持する"
  }),
  "06_repository": wrap({
    kicker: "組織で使う条件",
    title: "業務知識を共有すると、更新責任が生まれる",
    body: dialogue(
      "業務知識を共有すれば終わり?",
      "終わりではない。ルールが変わったら、業務知識と判断ルールも更新しないと AI は古い業務知識で作業する。",
      "共有する場所を決める",
      "誰が見ても同じ前提を参照でき、変更時に直せる形で管理する。"
    ),
    summary: "組織では、業務知識と判断ルールを共有するだけでなく、更新・維持する責任が必要"
  }),
  "07_handoff_q": wrap({
    kicker: "それでも残る問題",
    title: "Skill と業務知識が増えるほど、仕事はバラバラになりやすい",
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
    title: "Skill と業務知識が増えるほど、仕事はバラバラになりやすい",
    body: dialogue(
      "部品が揃えば、仕事は回る?",
      "まだ回らない。調査、判断、制作、確認の順番や受け渡しを、人間が都度つなぐことになる。",
      "AI Team にする",
      "役割、順番、責任、引き渡しをチーム構成として先に決める。"
    ),
    summary: "部品が揃っても、仕事の流れを設計しないと人間の調整負担が残る"
  }),
  "08_burden_flow": wrap({
    kicker: "負担の移り変わり",
    title: "負担は減るが、次の負担が見える",
    body: burdenFlow(),
    summary: "AI Teamは、AIを賢くする仕組みではなく、AIの仕事を人間が管理できる形にする仕組み",
    compact: true
  }),
  "08_or_team_q": wrap({
    kicker: "解決策",
    title: "AI Teamは、人間の調整負荷を仕組みに変える",
    body: dialogue(
      "そこで AI Team が出てくるんですね?",
      "ここで、Skill と業務知識を仕事の流れにつなぎます。",
      "",
      "",
      "question"
    ),
    summary: "AI Teamは部品を仕事に変える"
  }),
  "08_or_team": wrap({
    kicker: "解決策",
    title: "AI Teamは、人間の調整負荷を仕組みに変える",
    body: dialogue(
      "AI Teamは何をしてくれるの?",
      "人間がAIを逐次使い分ける前提をやめ、AIをチームとして構造化する。",
      "仕事として固定する",
      "役割、順番、責任、確認、引き渡しをチーム構成として先に決める。"
    ),
    summary: "AI Teamは、手順・業務知識・責任・流れをまとめて仕事にする"
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
    summary: "チェック役は、人間が AI の忘れを追い続ける負担を減らす"
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
      "なくならない。ただし、全部を追いかける仕事から、確認点を見る仕事に変わる。",
      "確認点を固定する",
      "目的、実行、確認、記録、引き渡しをチーム内に置き、確認できる形にする。"
    ),
    summary: "人間の仕事は、全部を見ることから、確認点を見ることへ変わる"
  }),
  "11_before_after_q": wrap({
    kicker: "導入前後",
    title: "人間の仕事は、全部を見ることから、確認点を見ることへ",
    body: dialogue(
      "導入前後で、何が変わるの?",
      "Before / After で、管理負荷の置き場所を見ます。",
      "",
      "",
      "question"
    ),
    summary: "導入前後の違いを見る"
  }),
  "11_before_after": wrap({
    kicker: "導入前後",
    title: "人間の仕事は、全部を見ることから、確認点を見ることへ",
    body: compare(),
    summary: "AI Teamは、毎回の管理負荷を固定された運用体制に変える"
  }),
  "12_license_q": wrap({
    kicker: "まとめ",
    title: "AI Teamは、人間の負担を管理可能な作業に変える",
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
    title: "AI Teamは、人間の負担を管理可能な作業に変える",
    body: dialogue(
      "結局、AI Team が必要な理由は?",
      "PromptやSkillを人間が逐次使う前提では、説明、監視、比較、判断、調整が人間側に集まり続ける。",
      "使い方を変える",
      "AIをチームとして構造化し、負荷を役割、流れ、確認点、記録、引き渡しに変える。"
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
