import fs from "node:fs/promises";
import path from "node:path";
const dir=path.resolve("human-docs/ja/assets/056_structure_for_ai_organization");
const css=await fs.readFile(path.join(dir,"diagram.css"),"utf8");
const cards=(items)=>`<div class="grid">${items.map(([h,p,t="blue"])=>`<section class="card ${t}"><h2>${h}</h2><p>${p}</p></section>`).join("")}</div>`;
const slide=(h,l,i,s)=>`<div class="canvas"><h1>${h}</h1><p class="lead">${l}</p>${cards(i)}<div class="summary">${s}</div></div>`;
const renderers={
 "00_intro":()=>slide("Goalを達成するには、限定責務を複数つなぐ","AIの業務実行構造は、AIを並べる組織図ではない",[["Goal","最終状態と受入れ条件を定義する"],["複数の責務","Goal達成に必要な仕事を分ける"],["接続する構造","個別完了を全体完了と混同しない","green"]],"Goalが、分割した仕事の終点を持つ。"),
 "01_title":()=>slide("Skillが、限定された責務を担う","各責務の判断とhandoffの境界を明確にする",[["判断方法","何を見て、どう決めるか"],["入出力","何を受け取り、何を返すか"],["Knowledgeとhandoff","何を参照し、どこへ渡すか","green"]],"一つのAIに業務全体を任せず、必要な判断へ集中させる。"),
 "02_four_elements":()=>slide("semantic routing が、責務間をGoalへつなぐ","Goalと現在状態から、次に必要なSkillを選ぶ",[["現在状態","何が終わり、何が未了か"],["routing","次に必要な責務を選ぶ"],["次のSkill Run","Goal達成まで進行を続ける","green"]],"作業の分割は、全体の目的を失うことを意味しない。"),
 "03_skill":()=>slide("workflow protocol が、各責務の進行を残す","未完了、根拠、次の責任地点を記録する",[["work and artifact","何を行い、何を出したか"],["evidence and concern","根拠、unknown、risk、judgmentを残す"],["handoff and close","次の責任地点と閉鎖条件を固定する","green"]],"未確認や作業漏れを完了扱いにしない。"),
 "04_domain_knowledge":()=>slide("組織固有Knowledgeが、実務判断を支える","AIの一般化された知識だけでは組織の判断を支えられない",[["一般知識","概念、方法、一般的な事例"],["組織固有Knowledge","ルール、対象、例外、過去の判断"],["XID選択","必要な本文だけを段階的に参照する","green"]],"Knowledgeは、AIの一般知識を業務判断へ接続する。"),
 "05_flow":()=>slide("検証と受入れは別の軸","作業記録の完全性と、成果物を採用するかを混同しない",[["verify","work item、artifact、concern、roleを検査する"],["quality review","必要なとき成果物を確認する"],["human decision","Goal、承認、例外を判断する","green"]],"決定的な検証は、成果物内容の自動承認を主張しない。"),
 "06_group":()=>slide("観測を、次の業務実行の改善へ戻す","ログは監査の終点ではなく、正本を直す入力である",[["observe","Skill RunとMCPを相関する"],["distinguish","XIDの選択、解決、ロード、適用を分ける"],["improve","routing、Skill、Knowledgeを更新する","green"]],"実行の記録から、次のGoal実行を良くする。"),
 "07_mapping":()=>slide("構造は、分離と接続を両立させる","各要素を混ぜず、Goalへ向けて接続する",[["Goal","業務完了を定義する"],["Skill and routing","限定責務と責務間の接続"],["workflow and Knowledge","進行記録と判断材料","green"]],"人間の受入れを含めて、業務実行の構造になる。"),
 "08_conclusion":()=>slide("結論","AIの業務実行構造を、継続・検証・改善できる形にする",[["Goal","終点を持つ"],["限定責務","AIを必要な判断へ集中させる"],["運用構造","接続、記録、Knowledge、受入れを持つ","green"]],"AI活用を、単発の会話から継続可能な業務実行へ変える。")};
const html=(b)=>`<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>${b}</body></html>`;
for(const [n,r]of Object.entries(renderers))await fs.writeFile(path.join(dir,`${n}.html`),html(r()),"utf8");
