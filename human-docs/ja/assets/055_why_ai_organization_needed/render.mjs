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
  "03_input_organization": () => slide("目標が、業務の完了を定義する", "個々の作業ではなく、達成後の状態と受入条件を持つ", [["達成状態", "何が実現されていれば業務が完了か"], ["受入条件", "何を満たせば受け入れられるか"], ["作業分割", "目標達成のため、AIが扱える責務単位へ作業を分ける", "soft-green"]], "AIの停止や個別作業の終了を、業務完了にはしない。"),
  "04_scattered_controls": () => slide("AIには、限定した責務を担当させる", "分割した作業を、判断と引継ぎの境界を持つ責務単位として扱う", [["担当範囲", "何を行い、どこまで責任を持つか"], ["判断と入出力", "何を見て、何を返すか"], ["組織固有知識と引継ぎ", "何を参照し、どこで次へ渡すか", "soft-green"]], "責務を限定することで、AIは必要な判断と成果物に集中できる。"),
  "05_organization_role": () => slide("分割した責務には、接続する仕組みが必要", "個別作業を速くしても、業務の終点へつながらなければ完了しない", [["現在状態", "何が終わり、何が未了か"], ["次の責務", "いま必要な判断と作業は何か"], ["目標への接続", "個別完了を全体完了と混同しない", "soft-green"]], "XRefKitでは、この接続を実行モデルとして分けて扱う。"),
  "06_organization_value": () => slide("途中終了を前提に、仕事の状態を残す", "AIを止めないのではなく、止まっても次が続けられるようにする", [["完了済み", "何を行い、何ができたか"], ["未完了", "何が残り、何が不明か"], ["次の責任地点", "誰または何が続けるか", "soft-green"]], "継続可能性は、会話履歴ではなく明示された業務状態から生まれる。"),
  "07_human_control_unit": () => slide("AI活用には、組織固有の知識が必要", "一般化された学習知識だけでは、組織の業務判断を支えられない", [["AIが持つ一般知識", "概念、方法、一般的な事例"], ["組織固有知識", "ルール、対象情報、例外、過去の判断、責任境界"], ["段階的な参照", "XIDを選び、必要な本文だけを判断へ使う", "soft-green"]], "組織固有知識は、AIの一般知識を組織の業務判断へ接続する。"),
  "08_ai_control_unit": () => slide("検証と受入れは、業務状態に対して行う", "AIの自己申告ではなく、残された状態から未了と判断点を確認する", [["作業の完全性", "必要な作業が残っていないか"], ["成果物の受入れ", "業務目的に使える内容か"], ["人間の判断", "承認、例外、トレードオフを担う", "soft-green"]], "検証できる状態を残すことが、信頼の前提になる。"),
  "09_conclusion": () => slide("必要なのは、AIの回答ではなく業務実行の構造", "目標、限定責務、組織固有知識、状態記録、受入れを分けて接続する", [["終点", "目標と受入条件を持つ"], ["実行", "限定した責務へ集中させる"], ["継続", "未了を残し、次へ渡す", "soft-green"]], "具体的な接続方法は、実行モデル資料で説明する。")
};
const html = (body) => `<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`;
for (const [name, render] of Object.entries(renderers)) await fs.writeFile(path.join(dir, `${name}.html`), html(render()), "utf8");
console.log(`rendered ${Object.keys(renderers).length} slides`);
