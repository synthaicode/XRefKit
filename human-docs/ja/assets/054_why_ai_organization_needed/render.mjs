import fs from "node:fs/promises";
import path from "node:path";
const dir = path.resolve("human-docs/ja/assets/054_why_ai_organization_needed");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");
const cards = (items) => `<div class="grid">${items.map(([h,p,t="blue"])=>`<section class="card ${t}"><h2>${h}</h2><p>${p}</p></section>`).join("")}</div>`;
const slide = (h,l,items,s) => `<div class="canvas"><h1>${h}</h1><p class="lead">${l}</p>${cards(items)}<div class="summary">${s}</div></div>`;
const renderers = {
 "00_intro":()=>slide("AI を本番利用するための論点","単発の出力評価から、継続可能な業務実行へ",[["PoC","限定した出力が使えるかを見る"],["本番","未完了、例外、受入れ、担当変更を扱う","amber"],["運用","Goalまで仕事を続けられる状態を持つ","green"]],"本番では、会話ではなく業務の状態を管理する。"),
 "01_title":()=>slide("PoC と本番では、管理する対象が違う","本番では出力だけでなく、仕事の進行と完了を扱う",[["出力","その時点の要求への応答"],["業務状態","根拠、未確認点、次作業、受入れ"],["継続","中断後も次の実行者が続けられる","green"]],"出力終了と業務完了を同じものとして扱わない。"),
 "02_traits":()=>slide("AIは、途中で作業を終えても完了として扱いやすい","AIの応答終了だけでは、業務の未了を判断できない",[["未了項目","まだ実行していない作業"],["未確認点","確認待ち、例外、判断不足"],["受入れ","誰が何を満たせば完了か","amber"]],"本番利用には、業務全体の完了を別に定義する必要がある。"),
 "03_success_gap":()=>slide("Goal が、完了を定義し、作業分割を導く","Goalは最終状態と受入れ条件を持つ",[["desired state","何が実現されれば完了か"],["acceptance conditions","何を満たせば受け入れるか"],["task decomposition","Goal達成のため責務単位へ分ける","green"]],"一つの作業やAIの停止を、業務完了にはしない。"),
 "04_poc_gap":()=>slide("AIには、限定した責務を担当させる","分割した責務をSkillとして定義する",[["判断","何を見て、どう決めるか"],["入出力","何を受け取り、何を返すか"],["handoff","どこで次の責務へ渡すか","green"]],"限定責務により、AIは必要な判断へ集中できる。"),
 "05_failures":()=>slide("semantic routing が、複数の責務をGoalへつなぐ","Goalと現在状態から、次に必要なSkillを選ぶ",[["Goal","全体の終点を保持する"],["routing","現在必要な責務を選ぶ"],["Skill Run","個別完了をGoal達成と混同しない","green"]],"分割された作業を、全体の目的から切り離さない。"),
 "06_reproducibility":()=>slide("workflow protocol が、各責務の進行を残す","未完了を残し、次の責任地点へ渡す",[["work and evidence","何を行い、何を根拠にするか"],["unknown and risk","何が未確定かを明示する"],["handoff and close","次の責任地点と閉鎖条件を固定する","green"]],"未確認や作業漏れを、完了扱いにしない。"),
 "07_beyond_prompt":()=>slide("AI活用には、組織固有のKnowledgeが必要","一般化された学習知識だけでは実務判断を支えられない",[["一般知識","概念、方法、一般的な事例"],["組織固有Knowledge","ルール、対象、例外、過去の判断"],["XID選択","必要な本文だけを段階的に参照する","green"]],"Knowledgeが、AIの一般知識を組織の業務判断へ接続する。"),
 "08_conclusion":()=>slide("検証、受入れ、改善を分けて回す","本番利用は、実行記録から次の業務実行を良くする",[["verify","作業記録の完全性を検査する"],["human acceptance","成果物とGoalの受入れを判断する"],["improve","ログからrouting、Skill、Knowledgeを改善する","green"]],"AIの速さを、継続・検証・改善できる業務実行へ変える。")
};
const html=(body)=>`<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`;
for(const [name,render] of Object.entries(renderers)) await fs.writeFile(path.join(dir,`${name}.html`),html(render()),"utf8");
