import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("ja/docs/assets/055_why_ai_organization_needed");
const commonCss = await fs.readFile(path.resolve("ja/docs/assets/marketing_theme/common.css"), "utf8");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const renderers = {
  "00_intro": () => `
    <div class="canvas">
      <h1 class="title">はじめに</h1>
      <p class="subtitle">統制された運用を、誰が持ち、どう維持するのか</p>
      <div class="compare" style="margin-top:88px;">
        <div class="panel">
          <span class="badge b-blue" style="font-size:22px;">前の資料で見たこと</span>
          <div class="stack">
            <div class="box soft-blue">対象を決める</div>
            <div class="box soft-blue">手順を分解する</div>
            <div class="box soft-blue">知識・確認・役割を置く</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-orange" style="font-size:22px;">次に出る問い</span>
          <div class="stack">
            <div class="box soft-orange">誰が持つのか</div>
            <div class="box soft-orange">どう維持するのか</div>
            <div class="box soft-orange">どう改善するのか</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>統制された運用を一度作るだけでは足りない</strong>
        <span>継続して持ち、共有し、改善する単位が必要になる。</span>
      </div>
    </div>`,
  "01_title": () => `
    <div class="canvas">
      <h1 class="title">なぜ AI を組織化する必要があるのか</h1>
      <p class="subtitle">統制された運用を、継続して回すための単位が必要になる</p>
      <div class="hero-note">
        AI 活用では、要素を揃えることと、<br>
        それを回し続けられることは別の課題になる。
      </div>
      <div class="summary-band" style="margin-top:42px;">
        <strong>ここで問いたいのは、統制を持続できる形があるかどうか</strong>
        <span>それが、組織化を考える理由になる。</span>
      </div>
    </div>`,
  "02_individual_limit": () => `
    <div class="canvas">
      <h1 class="title">個人運用のままでは広がりにくい</h1>
      <p class="subtitle">うまくいっている人がいても、そのままでは組織成果になりにくい</p>
      <div class="compare" style="margin-top:90px;">
        <div class="panel">
          <span class="badge" style="font-size:20px; background:#eef2f6; color:#6b7a8c;">個人で回っている状態</span>
          <div class="stack">
            <div class="box soft-gray">担当者が工夫している</div>
            <div class="box soft-gray">判断基準が頭の中にある</div>
            <div class="box soft-gray">改善方法も個人依存</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-red" style="font-size:20px;">起きやすいこと</span>
          <div class="stack">
            <div class="box soft-red">担当者が変わると品質が落ちる</div>
            <div class="box soft-red">他部門へ広げにくい</div>
            <div class="box soft-red">改善が資産になりにくい</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>個人の成功は、そのまま組織の成功にはなりにくい</strong>
        <span>継続性と共有性を持たせるには、別の持ち方が必要になる。</span>
      </div>
    </div>`,
  "03_input_organization": () => `
    <div class="canvas">
      <h1 class="title">まず、AI に渡す情報を整理する</h1>
      <p class="subtitle">統制された運用は、AI への入力を構造化して持つところから始まる</p>
      <div class="grid-4" style="margin-top:92px; gap:16px;">
        <div class="card soft-blue"><h3>対象</h3><p>何に AI を使うか</p></div>
        <div class="card soft-blue"><h3>手順</h3><p>どの順で仕事を進めるか</p></div>
        <div class="card soft-blue"><h3>知識</h3><p>何を前提として渡すか</p></div>
        <div class="card soft-blue"><h3>確認・役割</h3><p>誰がどう確かめるか</p></div>
      </div>
      <div class="big-arrow">↓</div>
      <div class="summary-band" style="margin-top:8px;">
        <strong>この4つが揃ってはじめて、AI の運用を構造として扱いやすくなる</strong>
        <span>次に見るのは、これらが別々に管理されると何が起きるかです。</span>
      </div>
    </div>`,
  "04_scattered_controls": () => `
    <div class="canvas">
      <h1 class="title">要素が別管理だと、運用はずれやすい</h1>
      <p class="subtitle">対象、手順、知識、確認、役割が分かれたままだと統制しにくい</p>
      <div class="grid-4" style="margin-top:92px; gap:16px;">
        <div class="card soft-blue"><h3>対象</h3><p>ユースケース選定が人ごとに変わる</p></div>
        <div class="card soft-blue"><h3>手順</h3><p>やり方が担当者ごとにずれる</p></div>
        <div class="card soft-blue"><h3>知識</h3><p>必要な前提が散らばる</p></div>
        <div class="card soft-blue"><h3>確認・役割</h3><p>レビュー観点が揃いにくい</p></div>
      </div>
      <div class="big-arrow">↓</div>
      <div class="summary-band" style="margin-top:8px;">
        <strong>要素を持つだけでは、統制にはならない</strong>
        <span>ひとつの運用として束ねて持つ必要がある。</span>
      </div>
    </div>`,
  "05_organization_role": () => `
    <div class="canvas">
      <h1 class="title">組織化が担うのは、人を増やすことではない</h1>
      <p class="subtitle">成功条件を持ち、品質の見方をそろえ、改善を続ける単位を持つこと</p>
      <div class="grid-3" style="margin-top:104px;">
        <div class="card soft-blue"><h3 style="display:flex; align-items:center; gap:10px;"><span style="display:inline-block; width:22px; height:24px; border:2px solid #6e8fbd; border-radius:4px; position:relative;"><span style="position:absolute; left:4px; top:5px; width:10px; height:2px; background:#6e8fbd;"></span><span style="position:absolute; left:4px; top:11px; width:12px; height:2px; background:#6e8fbd;"></span></span>成功条件を持つ</h3><p>何をもって前進とするかを組織で共有する</p></div>
        <div class="card soft-blue"><h3 style="display:flex; align-items:center; gap:10px;"><span style="display:inline-grid; place-items:center; width:26px; height:26px; border:2px solid #6e8fbd; border-radius:8px; color:#6e8fbd; font-size:16px; font-weight:800;">✓</span>品質の見方をそろえる</h3><p>出力をどう評価するかを揃える</p></div>
        <div class="card soft-blue"><h3 style="display:flex; align-items:center; gap:10px;"><span style="display:inline-flex; gap:4px; align-items:flex-end;"><span style="display:block; width:8px; height:8px; background:#6e8fbd; border-radius:999px;"></span><span style="display:block; width:8px; height:15px; background:#6e8fbd; border-radius:999px;"></span><span style="display:block; width:8px; height:22px; background:#6e8fbd; border-radius:999px;"></span></span>改善を続ける</h3><p>問題が出たときに戻せる運用を持つ</p></div>
      </div>
      <div class="summary-band">
        <strong>組織化とは、統制を継続できる単位を持つこと</strong>
        <span>大きい組織図を作ること自体が目的ではない。</span>
      </div>
    </div>`,
  "06_organization_value": () => `
    <div class="canvas">
      <h1 class="title">組織化で変わること</h1>
      <p class="subtitle">個人依存の成功が、継続・共有・改善できる状態へ変わっていく</p>
      <div class="compare" style="margin-top:88px;">
        <div class="panel">
          <span class="badge" style="font-size:20px; background:#eef2f6; color:#6b7a8c;">組織化前</span>
          <div class="stack">
            <div class="box soft-gray">担当者依存</div>
            <div class="box soft-gray">属人的な品質判断</div>
            <div class="box soft-gray">改善が蓄積されにくい</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-green" style="font-size:20px;">組織化後</span>
          <div class="stack">
            <div class="box soft-green">継続できる</div>
            <div class="box soft-green">共有できる</div>
            <div class="box soft-green">改善が資産になる</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>組織化によって、AI 活用は個人技から運用資産へ変わる</strong>
        <span>ここではじめて、本番利用を広げやすくなる。</span>
      </div>
    </div>`,
  "07_human_control_unit": () => `
    <div class="canvas">
      <h1 class="title">組織化とは、何を持つことか</h1>
      <p class="subtitle">まず人の組織で考えると、責務があり、その責務を達成するために判断・知識・牽制がある</p>
      <div style="margin-top:78px;">
        <div style="display:flex; justify-content:center;">
          <div class="card soft-blue" style="width:1040px; padding:22px; border-width:2px;">
            <h3 style="font-size:34px; text-align:center; color:#234e95; margin-bottom:10px;">責務</h3>
            <p style="font-size:22px; text-align:center; color:#526985; margin-bottom:20px;">何を担い、どこまで責任を持つか</p>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:18px;">
              <div class="card" style="background:rgba(255,255,255,0.82); border:1px solid #cfdcff; box-shadow:none;">
                <h3>判断</h3>
                <p>責務を達成するために、何を選び、どう決めるか</p>
              </div>
              <div class="card" style="background:rgba(255,255,255,0.82); border:1px solid #cfdcff; box-shadow:none;">
                <h3>知識</h3>
                <p>その判断を支える前提、経験、ルールを持つ</p>
              </div>
              <div class="card" style="background:rgba(255,255,255,0.82); border:1px solid #cfdcff; box-shadow:none;">
                <h3>牽制</h3>
                <p>別の視点から確認し、責務が適切に果たされているかを見る</p>
              </div>
            </div>
          </div>
        </div>
        <div class="big-arrow">↓</div>
        <div style="display:flex; justify-content:center;">
          <div class="card" style="width:940px; padding:22px; border:1px solid #d8e1eb; background:linear-gradient(135deg, #f7fbff 0%, #edf4ff 100%); box-shadow:0 16px 34px rgba(21,34,53,0.09);">
            <div style="border:2px solid #9fb9e8; border-radius:24px; background:rgba(255,255,255,0.9); padding:24px 28px;">
              <h3 style="font-size:40px; text-align:center; color:#234e95; margin:0;">人の組織は、責務を中心に判断・知識・牽制を持つことで仕事を成り立たせている</h3>
              <p style="font-size:24px; text-align:center; color:#526985; margin-top:12px;">組織化とは、責務を果たすための判断、知識、牽制を持てる単位を持つことでもある</p>
            </div>
          </div>
        </div>
      </div>
      <div class="summary-band" style="margin-top:18px;">
        <strong>ここでは、責務を中心に判断・知識・牽制が構成されることを確認したい</strong>
        <span>次に、なぜ責務を分けるのかを見る。</span>
      </div>
    </div>`,
  "08_ai_control_unit": () => `
    <div class="canvas">
      <h1 class="title">この構図を AI に当てるとどうなるか</h1>
      <p class="subtitle">AI にも責務があり、その責務を達成するための判断・知識・牽制が必要になる</p>
      <div style="margin-top:78px;">
        <div style="display:flex; justify-content:center;">
          <div class="card soft-blue" style="width:1040px; padding:22px; border-width:2px;">
            <h3 style="font-size:34px; text-align:center; color:#234e95; margin-bottom:10px;">AI の責務</h3>
            <p style="font-size:22px; text-align:center; color:#526985; margin-bottom:20px;">どの AI が、何を担い、どこまで責任を持つか</p>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:18px;">
              <div class="card" style="background:rgba(255,255,255,0.82); border:1px solid #cfdcff; box-shadow:none;">
                <h3>判断</h3>
                <p>その責務を達成するために、何を見て、どう決めるか</p>
              </div>
              <div class="card" style="background:rgba(255,255,255,0.82); border:1px solid #cfdcff; box-shadow:none;">
                <h3>知識</h3>
                <p>判断に必要な文脈、ルール、前提を渡す</p>
              </div>
              <div class="card" style="background:rgba(255,255,255,0.82); border:1px solid #cfdcff; box-shadow:none;">
                <h3>牽制</h3>
                <p>別の責務や確認工程から見直せるようにする</p>
              </div>
            </div>
          </div>
        </div>
        <div class="big-arrow">↓</div>
        <div style="display:flex; justify-content:center;">
          <div class="card" style="width:1020px; padding:22px; border:1px solid #d8e1eb; background:linear-gradient(135deg, #f7fbff 0%, #edf4ff 100%); box-shadow:0 16px 34px rgba(21,34,53,0.09);">
            <div style="border:2px solid #9fb9e8; border-radius:24px; background:rgba(255,255,255,0.9); padding:24px 28px;">
              <h3 style="font-size:40px; text-align:center; color:#234e95; margin:0;">AI にも、責務を中心に判断・知識・牽制を持たせる必要がある</h3>
              <p style="font-size:24px; text-align:center; color:#526985; margin-top:12px;">07 で見た人の組織の持ち方を、そのまま AI の運用単位に当てて考える</p>
            </div>
          </div>
        </div>
      </div>
      <div class="summary-band" style="margin-top:18px;">
        <strong>AI でも、責務だけでは足りず、その責務を達成するための判断・知識・牽制が必要になる</strong>
        <span>次は、この構造をどう持ち続けるかを見る。</span>
      </div>
    </div>`,
  "09_conclusion": () => `
    <div class="canvas">
      <h1 class="title">AI にこの構造をどう持たせるか</h1>
      <p class="subtitle">都度与えるだけでは不安定になるため、継続して持てる単位として扱う必要がある</p>
      <div class="compare" style="margin-top:88px;">
        <div class="panel">
          <span class="badge" style="font-size:20px; background:#eef2f6; color:#6b7a8c;">都度与えるだけ</span>
          <div class="stack">
            <div class="box soft-gray">その場ごとの運用になる</div>
            <div class="box soft-gray">判断・知識・牽制が散らばる</div>
            <div class="box soft-gray">継続も改善もしにくい</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-blue" style="font-size:20px;">単位として持つ</span>
          <div class="stack">
            <div class="box soft-blue">継続して持てる</div>
            <div class="box soft-blue">揃えて運用できる</div>
            <div class="box soft-blue">改善を回せる</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>AI に必要な構造は、都度与えるだけでなく、継続して持ち、揃え、改善できる単位として扱うことが求められる</strong>
        <span>その持ち方が、AI を組織的に扱うことにつながっていく。</span>
      </div>
    </div>`
};

const html = (body) => `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <style>${commonCss}\n${css}</style>
</head>
<body>${body}</body>
</html>`;

for (const [name, render] of Object.entries(renderers)) {
  await fs.writeFile(path.join(dir, `${name}.html`), html(render()), "utf8");
}

console.log(`rendered ${Object.keys(renderers).length} html diagrams to ${dir}`);
