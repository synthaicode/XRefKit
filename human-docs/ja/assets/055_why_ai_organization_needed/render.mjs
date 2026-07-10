import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/055_why_ai_organization_needed");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");
const cards = (items) => `<div class="grid-3" style="margin-top:88px;">${items.map(([title, body, tone = "soft-blue"]) => `<div class="card ${tone}"><h3>${title}</h3><p>${body}</p></div>`).join("")}</div>`;
const slide = (title, subtitle, items, summary) => `<div class="canvas"><h1 class="title">${title}</h1><p class="subtitle">${subtitle}</p>${cards(items)}<div class="summary-band"><strong>${summary}</strong></div></div>`;
const renderers = {
  "00_intro": () => slide("AI活用を継続可能な業務実行に変える", "途中で止まっても、再開・検証・受入れ・改善できる仕事にする", [["継続", "中断しても、未完了を残して再開できる"], ["検証", "作業漏れと根拠を確認できる"], ["改善", "実行ログから次の運用を良くする", "soft-green"]], "AI活用を、単発の会話から継続可能な業務実行へ変える。"),
  "01_title": () => slide("毎回のプロンプト主体の利用方法では、業務の状態が残らない", "会話を終えるたびに、次の仕事に必要な状態が失われる", [["判断材料", "何を根拠に判断したか"], ["未確認点", "何がまだ分からないか"], ["次作業と受入れ", "誰が何をし、何を満たせば完了か", "soft-orange"]], "次の実行者は、会話から業務の状態を再構成しなければならない。"),
  "02_individual_limit": () => slide("AIは、途中で作業を終えても完了として扱いやすい", "出力終了と業務完了は、同じではない", [["AIの応答", "その時点の要求に対して出力を返す"], ["残りやすい問題", "未了項目、確認待ち、例外、根拠"], ["起きる誤認", "出力が終わったので業務も終わったと扱う", "soft-red"]], "業務全体の未了事項と受入れ条件は、別の仕組みで残す必要がある。"),
  "03_input_organization": () => slide("Goal が、業務の完了を定義する", "個々の作業ではなく、達成後の状態と受入れ条件を持つ", [["desired state", "何が実現されていれば業務が完了か"], ["acceptance conditions", "何を満たせば受け入れられるか"], ["task decomposition", "Goal達成のため、AIが扱える責務単位へ作業を分ける", "soft-green"]], "AIの停止や個別作業の終了を、業務完了にはしない。"),
  "04_scattered_controls": () => slide("AIには、限定した責務を担当させる", "分割した作業を、判断とhandoffの境界を持つSkillとして扱う", [["担当範囲", "何を行い、どこまで責任を持つか"], ["判断と入出力", "何を見て、何を返すか"], ["Knowledgeとhandoff", "何を参照し、どこで次へ渡すか", "soft-green"]], "責務を限定することで、AIは必要な判断と成果物に集中できる。"),
  "05_organization_role": () => slide("semantic routing が、分割した作業をGoalへつなぐ", "Goalと現在状態から、次に必要なSkillを選ぶ", [["Goalと現在状態", "何が達成済みで、何が未了か"], ["semantic routing", "候補から次に必要な責務を選ぶ"], ["次のSkill Run", "個別完了をGoal達成と混同せず、終点へ進める", "soft-green"]], "分割された作業を、全体の目的から切り離さない。"),
  "06_organization_value": () => slide("workflow protocol が、未完了の仕事を残す", "Skill Runごとに状態と根拠を記録し、次の責任地点へ渡す", [["実行記録", "work item、artifact、evidenceを残す"], ["未確定の記録", "unknown、risk、judgmentを明示する"], ["次へ渡す", "handoffとcloseで、次の責任地点を固定する", "soft-green"]], "AIが途中で止まっても、次のSkillまたは人間が状態から続けられる。"),
  "07_human_control_unit": () => slide("AI活用には、組織固有のKnowledgeが必要", "一般化された学習知識だけでは、組織の業務判断を支えられない", [["AIが持つ一般知識", "概念、方法、一般的な事例"], ["組織固有Knowledge", "ルール、対象情報、例外、過去の判断、責任境界"], ["段階的な参照", "XIDを選び、必要な本文だけを判断へ使う", "soft-green"]], "Knowledgeは、AIの一般知識を組織固有の業務判断へ接続する。"),
  "08_ai_control_unit": () => slide("作業漏れの検証と、成果物の受入れを分ける", "作業記録の完全性と、成果物を採用するかは別の判断である", [["xrefkit skill verify", "work item、artifact、concern、role、phaseを検査する"], ["quality review", "必要なとき、成果物の受入れ可能性を確認する"], ["human decision", "Goal、承認、例外を判断する", "soft-green"]], "決定的な検証は、成果物内容の自動承認を主張しない。"),
  "09_conclusion": () => slide("ログから、次の業務実行を改善する", "観測は監査の終点ではなく、次の実行を良くする入力である", [["相関する", "Skill RunとMCPをrun_idで結び付ける"], ["区別して見る", "XIDの選択、解決、ロード、適用を分ける"], ["正本を改善する", "routing、Skill、Knowledgeを証拠から更新する", "soft-green"]], "継続・検証・改善できることが、AI活用を業務実行に変える。")
};
const html = (body) => `<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`;
for (const [name, render] of Object.entries(renderers)) await fs.writeFile(path.join(dir, `${name}.html`), html(render()), "utf8");
console.log(`rendered ${Object.keys(renderers).length} slides`);
