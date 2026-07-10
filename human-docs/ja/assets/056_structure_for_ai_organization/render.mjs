import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/056_structure_for_ai_organization");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");
const cards = (items) => `<div class="grid">${items.map(([title, body, tone = "blue"]) => `<section class="card ${tone}"><h2>${title}</h2><p>${body}</p></section>`).join("")}</div>`;
const slide = (title, lead, items, summary) => `<div class="canvas"><h1>${title}</h1><p class="lead">${lead}</p>${cards(items)}<div class="summary">${summary}</div></div>`;
const renderers = {
  "00_intro": () => slide("はじめに", "AI の業務実行構造は、AI を並べる組織図ではない", [["終点", "何を達成し、何を受け入れるか"], ["責務", "どの Skill が何を担うか"], ["記録", "途中で止まっても続けられるか", "green"]], "目標から完了までの責務、情報、記録の接続を設計する。"),
  "01_title": () => slide("AI の業務実行構造をどう持たせるか", "Goal、routing、Skill、Knowledge、workflow、受入れを混ぜずに接続する", [["Goal", "最終状態と受入れ条件"], ["Skill Run", "限定された責務の実行単位"], ["Human acceptance", "内容と例外を受け入れる判断", "green"]], "構造を分けることで、それぞれの責任と改善点を明確にする。"),
  "02_four_elements": () => slide("Goal が、全体の終点を持つ", "複数の Skill Run をまたいでも、同じ達成状態を目指す", [["desired state", "達成後に何が存在するか"], ["acceptance conditions", "受入れに必要な条件は何か"], ["continue until accepted", "中断やhandoff後も未完了を残す", "green"]], "Goal はタスクのリストではなく、業務の完了状態を管理する。"),
  "03_skill": () => slide("semantic routing が、次の責務を選ぶ", "Goal と現在状態から、候補 Skill の適用可能性を判断する", [["current state", "何が終わり、何が未了か"], ["routing", "次に必要な責務を選ぶ"], ["selection record", "選択理由を残して後で見直す", "green"]], "routing は Skill の手順を実行せず、次の実行単位を選ぶ。"),
  "04_domain_knowledge": () => slide("Skill が、責務を限定して実行する", "一つのAIに全てを任せず、必要な判断と成果物へ集中する", [["procedure", "その責務で何をどの順に行うか"], ["inputs and outputs", "何を受け取り、何を返すか"], ["handoff boundary", "どこで次の Skill や人間へ渡すか", "green"]], "責務の境界が、AI の能力を有効に使うための境界になる。"),
  "05_flow": () => slide("Knowledge は、判断材料を段階的に渡す", "一覧から選び、必要な XID の本文だけを読む", [["catalog", "対象領域と候補を見つける"], ["resolve and load", "必要な本文だけを文脈へ入れる"], ["apply", "判断・成果物との関係を記録する", "green"]], "XID により、巨大な文脈を毎回読み込まずに判断材料を扱う。"),
  "06_group": () => slide("workflow protocol が、作業漏れを検査可能にする", "Skill Run の状態を決定的に記録し、進行を検証する", [["work and artifacts", "何を行い、何を出したか"], ["evidence and concerns", "根拠、unknown、risk、judgment を残す"], ["handoff and close", "次の責任地点と閉鎖条件を固定する", "green"]], "ログは会話の要約ではなく、再開と検証のための実行記録である。"),
  "07_mapping": () => slide("検証と品質受入れは別の軸", "workflow の完全性と、成果物を採用するかを混同しない", [["xrefkit skill verify", "work item、artifact、concern、role、phase を検査する"], ["quality review", "必要なとき、成果物の受入れ可能性を確認する"], ["human decision", "Goal、承認、例外を判断する", "green"]], "決定的な検証は、成果物内容の自動承認を主張しない。"),
  "08_conclusion": () => slide("結論", "AI の業務実行構造は、分離と接続を両立させる", [["分ける", "Goal、routing、Skill、Knowledge、workflow、受入れ"], ["つなぐ", "run log、XID、handoffで状態と根拠をつなぐ"], ["改善する", "運用ログから正本を更新し、次の実行へ戻す", "green"]], "AI を組織化するとは、回答を増やすことではなく、業務実行を継続・検証・改善できるようにすること。")
};
const html = (body) => `<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`;
for (const [name, render] of Object.entries(renderers)) await fs.writeFile(path.join(dir, `${name}.html`), html(render()), "utf8");
console.log(`rendered ${Object.keys(renderers).length} slides`);
