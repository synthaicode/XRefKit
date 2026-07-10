import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/055_why_ai_organization_needed");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const threeCards = (items, tone = "soft-blue") => `
  <div class="grid-3" style="margin-top:92px;">
    ${items.map(([title, body]) => `<div class="card ${tone}"><h3>${title}</h3><p>${body}</p></div>`).join("\n")}
  </div>`;

const renderers = {
  "00_intro": () => `
    <div class="canvas">
      <h1 class="title">はじめに</h1>
      <p class="subtitle">AI の回答を、組織の完了した仕事へ変えるには何が必要か</p>
      ${threeCards([["AI は速く答える", "生成と調査をすばやく進められる"], ["しかし仕事は残る", "確認、根拠、次の担当、受入れが会話に埋もれる"], ["運用が必要になる", "途中で止まっても、仕事を失わずに続ける"]])}
      <div class="summary-band"><strong>回答が出たことと、仕事が完了したことは同じではない</strong><span>継続、検証、改善できる運用を持つことが必要になる。</span></div>
    </div>`,
  "01_title": () => `
    <div class="canvas">
      <h1 class="title">AI活用を継続可能な業務実行に変える</h1>
      <p class="subtitle">Goalから完了までを、継続・検証・改善できる形にする</p>
      <div class="hero-note">AI が途中で止まっても、未確認の仕事を完了扱いにしない。<br>誰が再開しても、同じ記録と境界から仕事を続けられるようにする。</div>
      <div class="summary-band" style="margin-top:42px;"><strong>AI活用を継続可能な業務実行に変える</strong><span>そのために、役割、知識、記録、受入れを分けて管理する。</span></div>
    </div>`,
  "02_individual_limit": () => `
    <div class="canvas">
      <h1 class="title">個人利用だけでは、仕事の状態が残らない</h1>
      <p class="subtitle">プロンプトと会話だけでは、次の人が同じ仕事を続けにくい</p>
      <div class="compare" style="margin-top:84px;"><div class="panel"><span class="badge" style="font-size:20px; background:#eef2f6; color:#6b7a8c;">個人の会話</span><div class="stack"><div class="box soft-gray">判断材料が会話に散る</div><div class="box soft-gray">未確認点が残る</div><div class="box soft-gray">停止時の次作業が曖昧</div></div></div><div class="panel"><span class="badge b-red" style="font-size:20px;">組織で起きる問題</span><div class="stack"><div class="box soft-red">再説明と再調査が増える</div><div class="box soft-red">作業漏れを検出しにくい</div><div class="box soft-red">担当変更で品質が揺れる</div></div></div></div>
      <div class="summary-band"><strong>個人の成功を、組織が再現できる仕事の状態へ変える必要がある</strong><span>その出発点が Goal と記録である。</span></div>
    </div>`,
  "03_input_organization": () => `
    <div class="canvas"><h1 class="title">Goal が、作業の終点を持つ</h1><p class="subtitle">タスク消化やAIの停止ではなく、達成後の状態と受入れ条件を固定する</p>
      ${threeCards([["Desired state", "何が実現されている状態か"], ["Acceptance conditions", "何を満たせば受け入れられるか"], ["Continuation", "複数の Skill をまたいで完了まで続ける"]])}
      <div class="summary-band"><strong>Goal は、未完了を完了扱いにしないための基準になる</strong><span>Skill は Goal を達成する途中の限定された責務を担う。</span></div></div>`,
  "04_scattered_controls": () => `
    <div class="canvas"><h1 class="title">semantic routing が、次の責務を選ぶ</h1><p class="subtitle">Goal と現在状態から、次に必要な Skill を選択する</p>
      <div class="grid-3" style="margin-top:98px;"><div class="card soft-blue"><h3>Goal と現在状態</h3><p>何を達成し、何が未了かを確認する</p></div><div class="card soft-blue"><h3>semantic routing</h3><p>候補の Skill から適用可能な責務を選ぶ</p></div><div class="card soft-blue"><h3>次の Skill Run</h3><p>選んだ責務を実行し、結果を Goal へ戻す</p></div></div>
      <div class="summary-band"><strong>人が毎回一覧から手選びするのではなく、状態に応じて責務を選ぶ</strong><span>選択理由も記録し、後で見直せるようにする。</span></div></div>`,
  "05_organization_role": () => `
    <div class="canvas"><h1 class="title">Skill は、AI の責務を限定する</h1><p class="subtitle">一つのAIに全てを任せず、必要な判断と成果物へ集中させる</p>
      ${threeCards([["責務と判断", "何を担当し、どの方法で判断するか"], ["入出力と Knowledge", "何を受け取り、何を返し、何を参照するか"], ["handoff 境界", "どこで次の責務や人間へ渡すか"]])}
      <div class="summary-band"><strong>責務が限定されるほど、AI は必要な判断に集中できる</strong><span>Skill は方法を持ち、Knowledge は判断材料を持つ。</span></div></div>`,
  "06_organization_value": () => `
    <div class="canvas"><h1 class="title">Knowledge は、必要な XID だけを読む</h1><p class="subtitle">対象一覧と詳細を分け、必要な判断材料だけを段階的に取り込む</p>
      <div class="grid-3" style="margin-top:98px;"><div class="card soft-blue"><h3>catalog</h3><p>候補の領域と XID を一覧で見つける</p></div><div class="card soft-blue"><h3>select and resolve</h3><p>必要な XID の本文だけを取得する</p></div><div class="card soft-blue"><h3>apply</h3><p>判断・成果物との関係を記録する</p></div></div>
      <div class="summary-band"><strong>全体を毎回読み込まないことで、コンテキスト汚染を抑える</strong><span>使用状況はログから確認し、不要・不足の Knowledge を改善する。</span></div></div>`,
  "07_human_control_unit": () => `
    <div class="canvas"><h1 class="title">workflow protocol が、作業漏れを検査する</h1><p class="subtitle">各 Skill Run に、実行に必要な状態と根拠を残す</p>
      <div class="grid-4" style="margin-top:88px; gap:16px;"><div class="card soft-blue"><h3>work item</h3><p>何を行うか</p></div><div class="card soft-blue"><h3>artifact / evidence</h3><p>何を出し、何に基づくか</p></div><div class="card soft-blue"><h3>unknown / risk</h3><p>何が未確定か</p></div><div class="card soft-blue"><h3>handoff</h3><p>次に誰が何をするか</p></div></div>
      <div class="summary-band"><strong><code>xrefkit skill verify</code> は、記録された workflow progression を決定的に検査する</strong><span>AI の自己申告ではなく、work item、artifact、concern、役割、phase を確認する。</span></div></div>`,
  "08_ai_control_unit": () => `
    <div class="canvas"><h1 class="title">検証と品質受入れを分ける</h1><p class="subtitle">作業記録の完全性と、成果物を受け入れるかは別の判断である</p>
      <div class="compare" style="margin-top:88px;"><div class="panel"><span class="badge b-blue" style="font-size:20px;">deterministic verification</span><div class="stack"><div class="box soft-blue">workflow の記録に漏れがないか</div><div class="box soft-blue">役割と progression が正しいか</div><div class="box soft-blue">成果物の内容は判定しない</div></div></div><div class="panel"><span class="badge b-green" style="font-size:20px;">quality and human acceptance</span><div class="stack"><div class="box soft-green">成果物が受入れ可能か</div><div class="box soft-green">品質レビューが必要か</div><div class="box soft-green">Goal、例外、承認を人間が担う</div></div></div></div>
      <div class="summary-band"><strong>検証を通っても、内容の受入れを自動で主張しない</strong><span>人間の意思決定とAIの実行責務を混ぜない。</span></div></div>`,
  "09_conclusion": () => `
    <div class="canvas"><h1 class="title">継続と改善の仕組みを持つ</h1><p class="subtitle">速度だけでなく、再開、handoff、検証、改善までを仕事として扱う</p>
      <div class="grid-3" style="margin-top:96px;"><div class="card soft-blue"><h3>継続できる</h3><p>Goal とログから、途中で止まっても再開できる</p></div><div class="card soft-green"><h3>検証できる</h3><p>作業漏れと品質受入れを別々に確認できる</p></div><div class="card soft-orange"><h3>改善できる</h3><p>routing、Skill、Knowledge、XID利用を観測して直せる</p></div></div>
      <div class="summary-band"><strong>AI の速さを、手戻り削減と継続可能な業務実行へ変える</strong><span>Goal、Skill、Knowledge、workflow protocol を接続して実現する。</span></div></div>`
};

const html = (body) => `<!doctype html><html lang="ja"><head><meta charset="utf-8" /><style>${css}</style></head><body>${body.replace(/[ \t]+(?=\n)/g, "")}</body></html>`;

for (const [name, render] of Object.entries(renderers)) {
  await fs.writeFile(path.join(dir, `${name}.html`), html(render()), "utf8");
}

console.log(`rendered ${Object.keys(renderers).length} html diagrams to ${dir}`);
