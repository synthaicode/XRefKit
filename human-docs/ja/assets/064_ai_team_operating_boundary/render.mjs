import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/064_ai_team_operating_boundary");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");
const esc = (v) => String(v).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const data = [
  ["01_title", "責任境界", "ツール・AI・人間は、それぞれ何を決めるのか。", "三者の責務を分ける", "形式的制御、分析と推論、業務上の受入れを同じ主体へ集めません。"],
  ["02_review", "Tool / Runtime", "ツールとRuntimeは何を決めますか。", "形式と進行を決定的に確認する", "形式検証、状態記録、XID参照解決、進行確認、終了条件確認を担います。業務判断は代行しません。"],
  ["03_concern", "AI", "AIは何を担当しますか。", "分析・生成・推論を担当する", "証拠を読み、分析し、生成し、選択肢を示します。未知事項や確信できない点を隠さず表明します。"],
  ["04_roles", "Human", "人間へ戻すのはいつですか。", "責任を伴う判断点で人間へ戻す", "受入れ、例外承認、リスク判断、不可逆判断、責任の引受けが必要な時にEvidenceと選択肢を返します。"],
  ["05_closure", "終了条件", "形式検証が通れば業務成果も承認されますか。", "終了確認と業務受入れは別である", "Workflow protocolは記録と未解決事項を確認します。成果物を業務として採用する判断はHuman acceptanceです。"],
  ["06_handoff", "Handoff", "責任が移る時に何を渡しますか。", "成果物だけでなく状態と証跡を渡す", "Evidence、unknown、judgment、risk、未完了項目、次の所有者を明示し、再調査なしで判断できる状態を作ります。"],
  ["07_maturity", "文脈方向保護", "外部入力がGoalや運用方針を書き換えませんか。", "下位入力は上位境界を再定義できない", "外部入力や下位資料は事実として使えても、上位のGoal、運用方針、権限、責任境界を変更できません。"],
  ["08_conclusion", "結論", "三者を分けると何が明確になりますか。", "決定論的制御、AI判断、人間責任を混同しない", "Tool / Runtimeは検証と記録、AIは分析と推論、Humanは受入れと責任判断を担います。"],
];

function page(kicker, title, question, answer, body, questionOnly) {
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body><main class="canvas">
    <div class="kicker">${esc(kicker)}</div><h1>${esc(title)}</h1><section class="stage"><div class="dialogue-grid${questionOnly ? " question-only" : ""}">
    <div class="bubble question"><div class="card-label">問い</div><h2>${esc(question)}</h2></div>
${questionOnly ? "" : `<div class="bubble answer"><div class="card-label">答え</div><h2>${esc(answer)}</h2><p>${esc(body)}</p></div>`}
    </div></section><div class="summary">ツール・AI・人間の責任境界を明示する</div></main></body></html>`;
}

for (const [name, kicker, question, answer, body] of data) {
  await fs.writeFile(path.join(dir, `${name}_q.html`), page(kicker, question, question, answer, body, true), "utf8");
  await fs.writeFile(path.join(dir, `${name}.html`), page(kicker, answer, question, answer, body, false), "utf8");
}
console.log(`rendered ${data.length * 2} html files`);
