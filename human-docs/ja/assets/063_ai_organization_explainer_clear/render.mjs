import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/063_ai_organization_explainer_clear");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const escape = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;");

const page = ({ kicker, title, question, answer, summary }) => `<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>
  <main class="canvas">
    <div class="kicker">${escape(kicker)}</div>
    <h1>${escape(title)}</h1>
    <section class="stage">
      <div class="dialogue-grid${answer ? "" : " question-only"}">
        <div class="bubble question"><div class="card-label">問い</div><h2>${escape(question)}</h2></div>
        ${answer ? `<div class="bubble answer"><div class="card-label">答え</div><p>${escape(answer)}</p></div>` : "<!-- question only -->"}
      </div>
    </section>
    <div class="summary">${escape(summary)}</div>
  </main>
</body></html>`;

const slides = {
  "01_title_q": ["出発点", "AI は個人作業を速くする。では、仕事全体は?", "AI を入れれば、仕事は楽になりますか?", "", "速さと業務の完了は別に考える"],
  "01_title": ["出発点", "AI は個人作業を速くする。では、仕事全体は?", "何が変わる?", "文章作成、要約、調査、コード生成は速くなる。しかし、確認、判断、引き継ぎまで終わったとは限らない。", "AI の便利さを、組織の成果へつなげる必要がある"],
  "02_team_definition_q": ["問題", "AI が途中で止まると、何が残ったか分からない", "出力があれば、仕事は終わりですか?", "", "未完了が完了に見えることが、業務上のリスクになる"],
  "02_team_definition": ["問題", "AI が途中で止まると、何が残ったか分からない", "何が失われる?", "途中で止まると、未了の作業、確認していない点、根拠、次の担当が会話の中に埋もれる。", "中断をなくすのではなく、中断しても仕事を失わない"],
  "03_problem_q": ["限界", "プロンプトだけでは、毎回の説明と完了判定が人に戻る", "丁寧なプロンプトで十分ですか?", "", "目的、前提、制約、確認点を毎回書くだけでは再現できない"],
  "03_problem": ["限界", "プロンプトだけでは、毎回の説明と完了判定が人に戻る", "何が残る?", "人が毎回説明し、出力を読み、何が残ったかを判断する。書き漏れと確認漏れが積み上がる。", "必要なのは、回答を増やすことではなく、仕事を構造化すること"],
  "03_prompt_skill_limit": ["全体像", "Goal が到達点を固定し、Skill が責務を限定する", "何を先に決める?", "Goal は最終状態と受入条件を持つ。Skill は、その途中で担う判断方法と成果物の境界を持つ。", "最終目的と個別作業を、同じものとして扱わない"],
  "04_work_q": ["Skill", "Skill は、AI に任せる責務を限定する", "Skill があれば、何が変わる?", "", "一つの判断方法と一つの成果物に集中できる"],
  "04_work": ["Skill", "Skill は、AI に任せる責務を限定する", "何を持つ?", "Skill は capability、tuning、responsibility、入出力、判断方法、必要な Knowledge、handoff 境界を定義する。", "大きな依頼を、責任を持てる仕事の単位に分ける"],
  "05_not_one_ai_q": ["Routing", "次に必要な Skill は、Goal と現在状態から選ぶ", "誰が Skill を選ぶ?", "", "人が毎回一覧から手作業で選ぶ運用にしない"],
  "05_not_one_ai": ["Routing", "次に必要な Skill は、Goal と現在状態から選ぶ", "どう選ぶ?", "semantic routing が Skill の capability、tuning、responsibility と precondition を照合し、次の責務を選ぶ。", "Skill の完了後は、新しい状態から次の Skill を選ぶ"],
  "06_repository_q": ["Knowledge", "Skill は方法を持ち、Knowledge は判断材料を持つ", "なぜ知識を分ける?", "", "手順とドメイン事実を一つの長いプロンプトに混ぜない"],
  "06_repository": ["Knowledge", "Skill は方法を持ち、Knowledge は判断材料を持つ", "どう読む?", "Skill の knowledge slot から候補を一覧で選び、必要な XID の本文だけを読み込む。", "不要な文脈を減らし、古い知識は更新可能にする"],
  "07_handoff_q": ["Protocol", "Skill が閉じても、Goal が完了したとは限らない", "途中の仕事はどう管理する?", "", "個別作業の完了性と、最終目標の達成は別に確認する"],
  "07_handoff": ["Protocol", "workflow protocol が、各 Skill Run の作業漏れを検査する", "何を記録する?", "work item、成果物、根拠、unknown、risk、judgment、進行状態、handoff を run log に残す。", "AI の自己申告ではなく、記録から未了を見つける"],
  "08_burden_flow": ["流れ", "Goal -> routing -> Skill Run -> verify -> handoff -> Goal", "どこで止める?", "Skill Run は work item と evidence を記録し、verify が進行漏れを検査する。不足は修復または明示的な handoff に戻る。", "未完了を成功扱いにせず、次の AI または人が再開できる"],
  "08_or_team_q": ["検査", "verify は、成果物の内容を自動承認する機能ではない", "verify が通れば品質も保証されますか?", "", "進行の完全性と、成果物の受入れは別の軸である"],
  "08_or_team": ["検査", "verify は、成果物の内容を自動承認する機能ではない", "何を確認する?", "verify は作業項目、根拠、未解決事項、役割、進行記録を検査する。成果物の受入れは必要に応じて quality review と人が担う。", "検査の対象を分けることで、確認漏れを減らす"],
  "09_value_q": ["中断", "AI が途中で止まっても、仕事を失わない", "中断したらどうする?", "", "止まったことを隠さず、状態を残して再開または引き継ぐ"],
  "09_value": ["中断", "AI が途中で止まっても、仕事を失わない", "何が残る?", "run log に完了済み、未了、根拠、未解決事項、次の担当を残す。Goal は受入条件が満たされるまで継続する。", "会話履歴や担当者の記憶を再構築する時間を減らす"],
  "10_conclusion_q": ["人の役割", "人間の仕事は、すべてを監視することではない", "人間は何を担う?", "", "Goal、受入条件、承認、例外判断を明確に持つ"],
  "10_conclusion": ["人の役割", "人間の仕事は、すべてを監視することではない", "どこを見る?", "人は Goal の達成、品質受入れ、承認、例外を判断する。AI の各作業状態は protocol の記録から確認する。", "人の注意力を、判断が必要な場所へ使う"],
  "11_before_after_q": ["導入前後", "個人の会話から、継続可能な業務実行へ", "何が変わる?", "", "Before と After の違いは、AI の数ではなく仕事の管理方法"],
  "11_before_after": ["導入前後", "個人の会話から、継続可能な業務実行へ", "After はどう違う?", "Goal が最終状態を管理し、routing が次の責務を選び、Skill が仕事を行い、protocol が漏れを検査し、Knowledge が判断を支える。", "AI の速さを、手戻り削減と継続性へ変える"],
  "12_license_q": ["結論", "AI 活用の効率は、出力速度だけでは決まらない", "なぜこの構造が必要?", "", "再説明、再調査、確認漏れ、引き継ぎ漏れを減らすため"],
  "12_license": ["結論", "AI 活用を、管理できる業務実行へ変える", "何を実現する?", "Goal、semantic routing、Skill、Knowledge、workflow protocol を分けることで、AI の責務を限定し、途中終了を管理し、成果を受け入れられる状態にする。", "AI を止めないためではなく、止まっても仕事を失わないための仕組み"],
  "13_voicevox_credit": ["クレジット", "音声ライセンス", "VOICEVOX", "VOICEVOX:ずんだもん / VOICEVOX:四国めたん", "音声クレジット"],
  "13_irodori_credit": ["クレジット", "音声クレジット", "Irodori-TTS", "Irodori-TTS VoiceDesign", "音声クレジット"]
};

await fs.mkdir(dir, { recursive: true });
for (const [name, [kicker, title, question, answer, summary]] of Object.entries(slides)) {
  await fs.writeFile(path.join(dir, `${name}.html`), page({ kicker, title, question, answer, summary }), "utf8");
}
console.log(`rendered ${Object.keys(slides).length} html files`);
