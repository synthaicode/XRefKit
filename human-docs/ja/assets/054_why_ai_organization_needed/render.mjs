import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/054_why_ai_organization_needed");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");
const cards = (items) => `<div class="grid">${items.map(([title, body, tone = "blue"]) => `<section class="card ${tone}"><h2>${title}</h2><p>${body}</p></section>`).join("")}</div>`;
const slide = (title, lead, items, summary) => `<div class="canvas"><h1>${title}</h1><p class="lead">${lead}</p>${cards(items)}<div class="summary">${summary}</div></div>`;
const renderers = {
  "00_intro": () => slide("はじめに", "AI の回答を、完了した業務へ変えるには何が必要か", [["AI は速く答える", "生成、調査、要約を速く進められる"], ["しかし仕事は残る", "確認、根拠、次の担当、受入れが必要になる", "amber"], ["本番は運用する", "途中で止まっても仕事を失わずに続ける", "green"]], "回答が出たことと、組織の仕事が完了したことは同じではない。"),
  "01_title": () => slide("AI を本番利用するための論点", "本番利用の課題を、モデル精度だけに還元しない", [["Goal", "どの状態を達成し、何を受け入れるか"], ["実行構造", "責務を限定し、根拠と進行を残す"], ["改善", "利用状況から Skill と Knowledge を直す", "green"]], "AI の速さを、継続可能な業務実行へ変える。"),
  "02_traits": () => slide("PoC と本番で、管理するものが変わる", "一回の出力評価から、長い仕事の状態管理へ", [["PoC", "限定した入力で、出力が使えるかを見る"], ["本番", "例外、担当変更、根拠、未確認点を扱う", "amber"], ["必要なこと", "再開、handoff、受入れまでを運用する", "green"]], "本番では、会話履歴だけに仕事の状態を置かない。"),
  "03_success_gap": () => slide("Goal と受入れ条件を固定する", "AI が停止しても、未完了を完了扱いにしない", [["desired state", "達成後に何が実現されているか"], ["acceptance conditions", "何を満たせば受け入れるか"], ["continuation", "複数 Skill をまたいで完了まで続ける", "green"]], "Goal は、作業消化ではなく達成状態を管理する。"),
  "04_poc_gap": () => slide("責務を限定して実行する", "Goal と現在状態から、semantic routing が次の Skill を選ぶ", [["routing", "候補から、現在必要な責務を選ぶ"], ["Skill", "判断、入出力、Knowledge、handoff を持つ"], ["bounded work", "一つのAIに全てを任せず、責務へ集中する", "green"]], "責務の境界が、品質と引き継ぎの境界になる。"),
  "05_failures": () => slide("Knowledge は、必要な XID だけを使う", "対象一覧と詳細を分け、判断材料を段階的に与える", [["catalog", "候補の領域と XID を見つける"], ["resolve and load", "必要な本文だけを文脈へ入れる"], ["apply", "判断や成果物との関係を残す", "green"]], "全体を毎回読み込まず、コンテキスト汚染を抑える。"),
  "06_reproducibility": () => slide("作業漏れの検証と品質受入れを分ける", "同じ言葉で混ぜると、どちらも弱くなる", [["workflow protocol", "work item、根拠、unknown、handoff を残す"], ["deterministic verify", "作業記録の完全性を検査する"], ["quality and acceptance", "成果物の内容は品質レビューと人間が判断する", "green"]], "verify の通過は、成果物内容の自動承認を意味しない。"),
  "07_beyond_prompt": () => slide("観測して、Skill と Knowledge を改善する", "運用ログは監査の終点ではなく、次の改善の入力である", [["correlate", "Skill Run と MCP を run_id で相関する"], ["distinguish", "selected、resolved、loaded、applied を分ける"], ["improve", "不要・不足の原因を証拠から修正する", "green"]], "XID 利用状況は、Knowledge を増やす前に見るべき改善材料である。"),
  "08_conclusion": () => slide("結論", "AI の速さを、継続可能な業務実行へ変える", [["終点を持つ", "Goal と受入れ条件で完了を定義する"], ["責務を分ける", "routing、Skill、Knowledge、workflow を分ける"], ["改善を回す", "ログと人間の判断から正本を改善する", "green"]], "本番利用とは、回答を作ることではなく、仕事を継続・検証・改善できるようにすること。")
};
const html = (body) => `<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`;
for (const [name, render] of Object.entries(renderers)) await fs.writeFile(path.join(dir, `${name}.html`), html(render()), "utf8");
console.log(`rendered ${Object.keys(renderers).length} slides`);
