import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("ja/docs/assets/056_structure_for_ai_organization");
const commonCss = await fs.readFile(path.resolve("ja/docs/assets/marketing_theme/common.css"), "utf8");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const renderers = {
  "00_intro": () => `
    <div class="canvas">
      <h1 class="title">はじめに</h1>
      <p class="subtitle">AI に必要な構造を、具体的に何で持たせるのか</p>
      <div class="compare" style="margin-top:88px;">
        <div class="panel">
          <span class="badge b-blue" style="font-size:22px;">前の資料で見たこと</span>
          <div class="stack">
            <div class="box soft-blue">責務</div>
            <div class="box soft-blue">判断・知識</div>
            <div class="box soft-blue">牽制</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-orange" style="font-size:22px;">今の問い</span>
          <div class="stack">
            <div class="box soft-orange">何で持たせるのか</div>
            <div class="box soft-orange">どう分けるのか</div>
            <div class="box soft-orange">どう組み合わせるのか</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>ここでは、AI の構造を支える具体要素を見ていく</strong>
        <span>Skill、ドメイン知識、Flow、Group の4つで整理する。</span>
      </div>
    </div>`,
  "01_title": () => `
    <div class="canvas">
      <h1 class="title">AI にこの構造をどう持たせるか</h1>
      <p class="subtitle">Skill、ドメイン知識、Flow、Group で具体化する</p>
      <div class="summary-band" style="margin-top:92px;">
        <strong>AI に必要なのは、単なる機能追加ではない</strong>
        <span>責務、判断、知識、牽制が働くように、構造を具体要素へ落とす必要がある。</span>
      </div>
    </div>`,
  "02_four_elements": () => `
    <div class="canvas">
      <h1 class="title">4つの構成要素で考える</h1>
      <p class="subtitle">役割の違う要素を分けて持つことで、構造として扱いやすくなる</p>
      <div class="grid-4" style="margin-top:104px; gap:16px;">
        <div class="card soft-blue"><h3>Skill</h3><p>何をさせるかを定義した能力</p></div>
        <div class="card soft-blue"><h3>ドメイン知識</h3><p>判断に必要な前提とルール</p></div>
        <div class="card soft-blue"><h3>Flow</h3><p>判断と実行の順序</p></div>
        <div class="card soft-blue"><h3>Group</h3><p>責務分離と牽制の単位</p></div>
      </div>
      <div class="summary-band">
        <strong>4つは並列ではなく、構造を持たせるための分担になる</strong>
        <span>次に、それぞれが何を担うかを見ていく。</span>
      </div>
    </div>`,
  "03_skill": () => `
    <div class="canvas">
      <h1 class="title">Skill とは何か</h1>
      <p class="subtitle">AI に何をさせるかを、再利用できる能力として切り出す</p>
      <div class="compare" style="margin-top:88px;">
        <div class="panel">
          <span class="badge" style="font-size:20px; background:#eef2f6; color:#6b7a8c;">ない状態</span>
          <div class="stack">
            <div class="box soft-gray">毎回ゼロから指示する</div>
            <div class="box soft-gray">役割がぶれる</div>
            <div class="box soft-gray">再利用しにくい</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-blue" style="font-size:20px;">ある状態</span>
          <div class="stack">
            <div class="box soft-blue">責務に応じた能力を持てる</div>
            <div class="box soft-blue">何をさせるかが明確になる</div>
            <div class="box soft-blue">再利用しやすい</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>Skill は、責務を実行するための専門能力になる</strong>
        <span>責務を具体的な行動へ落とす役割を持つ。</span>
      </div>
    </div>`,
  "04_domain_knowledge": () => `
    <div class="canvas">
      <h1 class="title">ドメイン知識とは何か</h1>
      <p class="subtitle">AI の判断を支える、業務文脈とルールを持つ</p>
      <div class="grid-3" style="margin-top:104px;">
        <div class="card soft-blue"><h3>業務知識</h3><p>何が重要で、何が例外かを知る</p></div>
        <div class="card soft-blue"><h3>ルール</h3><p>判断に必要な基準や制約を持つ</p></div>
        <div class="card soft-blue"><h3>文脈</h3><p>その場の背景や前提を理解する</p></div>
      </div>
      <div class="summary-band">
        <strong>ドメイン知識がないと、AI の判断は安定しにくい</strong>
        <span>知識は、判断を成り立たせるための土台になる。</span>
      </div>
    </div>`,
  "05_flow": () => `
    <div class="canvas">
      <h1 class="title">Flow とは何か</h1>
      <p class="subtitle">判断と実行を、どの順で進めるかを固定する</p>
      <div class="h-flow" style="margin-top:190px; justify-content:center;">
        <div class="step soft-blue">前提を読む</div>
        <div class="chev">›</div>
        <div class="step soft-blue">判断する</div>
        <div class="chev">›</div>
        <div class="step soft-blue">実行する</div>
        <div class="chev">›</div>
        <div class="step soft-blue">確認する</div>
      </div>
      <div class="summary-band" style="margin-top:110px;">
        <strong>Flow は、判断と実行の順序を再利用可能にする</strong>
        <span>個人依存の進め方を、運用として持てる形にする。</span>
      </div>
    </div>`,
  "06_group": () => `
    <div class="canvas">
      <h1 class="title">Group とは何か</h1>
      <p class="subtitle">責務分離と牽制を成り立たせる単位として持つ</p>
      <div class="grid-3" style="margin-top:104px;">
        <div class="card soft-blue"><h3>責務を分ける</h3><p>誰が何を担うかを明確にする</p></div>
        <div class="card soft-blue"><h3>判断を分ける</h3><p>見る観点を分離する</p></div>
        <div class="card soft-blue"><h3>牽制を効かせる</h3><p>別の責務から見直せるようにする</p></div>
      </div>
      <div class="summary-band">
        <strong>Group があることで、責務分離と牽制を運用に乗せやすくなる</strong>
        <span>ここで初めて、AI を組織として扱えるようになる。</span>
      </div>
    </div>`,
  "07_mapping": () => `
    <div class="canvas">
      <h1 class="title">4つは、何に対応しているのか</h1>
      <p class="subtitle">責務、判断、知識、牽制の関係に対応している</p>
      <div style="margin-top:74px;">
        <div class="grid-4" style="gap:14px;">
          <div class="card soft-blue"><h3>責務</h3><p>Group</p></div>
          <div class="card soft-blue"><h3>判断</h3><p>Skill / Flow</p></div>
          <div class="card soft-blue"><h3>知識</h3><p>ドメイン知識</p></div>
          <div class="card soft-blue"><h3>牽制</h3><p>Group / Flow</p></div>
        </div>
        <div class="big-arrow">↓</div>
        <div style="display:flex; justify-content:center;">
          <div class="card" style="width:980px; padding:22px; border:1px solid #d8e1eb; background:linear-gradient(135deg, #f7fbff 0%, #edf4ff 100%); box-shadow:0 16px 34px rgba(21,34,53,0.09);">
            <div style="border:2px solid #9fb9e8; border-radius:24px; background:rgba(255,255,255,0.9); padding:24px 28px;">
              <h3 style="font-size:40px; text-align:center; color:#234e95; margin:0;">4つを組み合わせることで、AI に必要な構造を持たせやすくなる</h3>
              <p style="font-size:24px; text-align:center; color:#526985; margin-top:12px;">単独ではなく、対応関係の中で使うことが重要になる</p>
            </div>
          </div>
        </div>
      </div>
    </div>`,
  "08_conclusion": () => `
    <div class="canvas">
      <h1 class="title">結論</h1>
      <p class="subtitle">Skill、ドメイン知識、Flow、Group を組み合わせて、AI に構造を持たせる</p>
      <div class="compare" style="margin-top:88px;">
        <div class="panel">
          <span class="badge" style="font-size:20px; background:#eef2f6; color:#6b7a8c;">ばらばらに持つ</span>
          <div class="stack">
            <div class="box soft-gray">能力だけある</div>
            <div class="box soft-gray">知識だけある</div>
            <div class="box soft-gray">統制が効きにくい</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-blue" style="font-size:20px;">組み合わせて持つ</span>
          <div class="stack">
            <div class="box soft-blue">責務に応じて動ける</div>
            <div class="box soft-blue">判断が安定する</div>
            <div class="box soft-blue">牽制が効く</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>AI に構造を持たせるとは、4つを分けて置くことではなく、責務、判断、知識、牽制が機能するように組み合わせて持たせることである</strong>
        <span>次は、この構成をどう実際の組織に落とすかを見る。</span>
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
