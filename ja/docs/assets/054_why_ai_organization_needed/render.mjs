import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("ja/docs/assets/054_why_ai_organization_needed");
const commonCss = await fs.readFile(path.resolve("ja/docs/assets/marketing_theme/common.css"), "utf8");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const renderers = {
  "00_intro": () => `
    <div class="canvas">
      <h1 class="title">はじめに</h1>
      <p class="subtitle">AI 活用は広がっているが、PoC から本番移行はまだ難しい</p>
      <div class="compare" style="margin-top:100px;">
        <div class="panel">
          <span class="badge b-blue" style="font-size:22px;">増えている情報</span>
          <div class="stack">
            <div class="box soft-blue">AI で効率化できる</div>
            <div class="box soft-blue">成功事例が多い</div>
            <div class="box soft-blue">PoC は始めやすい</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-red" style="font-size:22px;">現実の壁</span>
          <div class="stack">
            <div class="box soft-red">本番移行は難しい</div>
            <div class="box soft-red">品質担保が難しい</div>
            <div class="box soft-red">PoC の延長では止まりやすい</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>ここでは、その問題点と解決の方向を示す</strong>
        <span>論点は、導入のしやすさではなく、本番利用に必要な条件である。</span>
      </div>
    </div>`,
  "01_title": () => `
    <div class="canvas">
      <h1 class="title">AI を本番利用するための論点</h1>
      <p class="subtitle">PoC の先で、何を見ないと止まるのか</p>
      <div class="compare" style="margin-top:84px;">
        <div class="panel">
          <span class="badge b-blue" style="font-size:22px;">よくある理解</span>
          <div class="stack">
            <div class="box soft-blue">AI を入れれば速くなる</div>
            <div class="box soft-blue">良いプロンプトで解決する</div>
            <div class="box soft-blue">PoC 成功で次に進める</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-orange" style="font-size:22px;">実際の論点</span>
          <div class="stack">
            <div class="box soft-orange">品質がぶれないか</div>
            <div class="box soft-orange">複雑な本番に耐えるか</div>
            <div class="box soft-orange">組織で再現できるか</div>
          </div>
        </div>
      </div>
      <div class="hero-note">
        AI 活用の課題は、使えるかどうかではない。<br>
        品質を担保しながら、本番利用できるかである。
      </div>
    </div>`,
  "02_traits": () => `
    <div class="canvas">
      <h1 class="title">まず前提になる AI の特性</h1>
      <p class="subtitle">強力だが、従来システムとは異なる不安定さを持つ</p>
      <div class="grid-4" style="margin-top:120px;">
        <div class="card soft-orange"><h3>忘れる</h3><p>必要な手順や対象を落としやすい</p></div>
        <div class="card soft-orange"><h3>ぶれる</h3><p>同じ目的でも出力品質が揺れる</p></div>
        <div class="card soft-red"><h3>言い切る</h3><p>もっともらしく間違うことがある</p></div>
        <div class="card soft-blue"><h3>文脈依存</h3><p>業務知識がなければ外しやすい</p></div>
      </div>
      <div class="summary-band">
        <strong>AI は単体で放置して安定する対象ではない</strong>
        <span>だから使い方だけでなく、外側の設計が必要になる。</span>
      </div>
    </div>`,
  "03_success_gap": () => `
    <div class="canvas">
      <h1 class="title">成功事例を真似しても再現しない理由</h1>
      <p class="subtitle">見えている手法と、実際に効いている判断基準は別である</p>
      <div class="row" style="display:grid; grid-template-columns:1fr 160px 1fr; gap:24px; margin-top:112px; align-items:center;">
        <div class="panel">
          <h2>外から見えるもの</h2>
          <div class="stack">
            <div class="box soft-blue">プロンプト</div>
            <div class="box soft-blue">ツール選定</div>
            <div class="box soft-blue">成功した使い方</div>
          </div>
        </div>
        <div class="center" style="height:auto;">
          <div style="font-size:86px; color:#93a4bb; font-weight:800;">≠</div>
        </div>
        <div class="panel">
          <h2>裏で効いているもの</h2>
          <div class="stack">
            <div class="box soft-orange">対象の見極め</div>
            <div class="box soft-orange">品質の判断基準</div>
            <div class="box soft-orange">業務文脈の理解</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>成功事例は手法を見せるが、判断基準までは見せない</strong>
        <span>その差が、自社 PoC の再現性を崩す。</span>
      </div>
    </div>`,
  "04_poc_gap": () => `
    <div class="canvas">
      <h1 class="title">PoC と本番では、扱う複雑さが違う</h1>
      <p class="subtitle">PoC で成立しても、そのまま本番にはつながらない</p>
      <div class="compare" style="margin-top:92px;">
        <div class="panel">
          <span class="badge b-green" style="font-size:22px;">PoC</span>
          <div class="stack">
            <div class="box soft-green">単純で切り出しやすい仕事</div>
            <div class="box soft-green">例外が少ない</div>
            <div class="box soft-green">影響範囲が狭い</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-red" style="font-size:22px;">本番</span>
          <div class="stack">
            <div class="box soft-red">例外処理が増える</div>
            <div class="box soft-red">対象と手順が増える</div>
            <div class="box soft-red">部門連携と説明責任が入る</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>PoC は成立確認、本番は複雑さへの対処である</strong>
        <span>この差に耐えられないと、PoC 成功は本番移行につながらない。</span>
      </div>
    </div>`,
  "05_failures": () => `
    <div class="canvas">
      <h1 class="title">PoC で見え始める典型問題</h1>
      <p class="subtitle">複雑さが増えるほど、失敗は表面化しやすくなる</p>
      <div class="grid-3" style="margin-top:120px;">
        <div class="card soft-orange" style="padding:32px 24px;">
          <h3 style="font-size:30px;">作業忘れ</h3>
          <p style="font-size:23px;">必要な手順や確認工程が抜ける</p>
        </div>
        <div class="card soft-orange" style="padding:32px 24px;">
          <h3 style="font-size:30px;">作業対象忘れ</h3>
          <p style="font-size:23px;">見るべき対象や文脈を取りこぼす</p>
        </div>
        <div class="card soft-red" style="padding:32px 24px;">
          <h3 style="font-size:30px;">ハルシネーション</h3>
          <p style="font-size:23px;">もっともらしいが根拠のない出力を出す</p>
        </div>
      </div>
      <div class="big-arrow">↓</div>
      <div class="summary-band" style="margin-top:10px;">
        <strong>精度不足だけではなく、抜け漏れと暴走が問題になる</strong>
        <span>個人の注意力だけでは、複雑な本番を支えきれない。</span>
      </div>
    </div>`,
  "06_reproducibility": () => `
    <div class="canvas">
      <h1 class="title">AI でいう再現性とは何か</h1>
      <p class="subtitle">正解一致ではなく、期待品質を安定して満たせるかを見る</p>
      <div class="compare" style="margin-top:92px;">
        <div class="panel">
          <span class="badge b-blue" style="font-size:22px;">従来システム</span>
          <div class="stack">
            <div class="box soft-blue">同じ入力</div>
            <div class="box soft-blue">同じ出力</div>
            <div class="box soft-blue">仕様一致を確認</div>
          </div>
        </div>
        <div class="panel">
          <span class="badge b-orange" style="font-size:22px;">生成 AI</span>
          <div class="stack">
            <div class="box soft-orange">同じ目的</div>
            <div class="box soft-orange">十分な品質</div>
            <div class="box soft-orange">安定して業務に使える</div>
          </div>
        </div>
      </div>
      <div class="summary-band">
        <strong>AI の再現性は、出力品質の安定である</strong>
        <span>だから評価も運用も、固定解ではなく品質で設計する必要がある。</span>
      </div>
    </div>`,
  "07_beyond_prompt": () => `
    <div class="canvas">
      <h1 class="title">対処はプロンプト改善だけでは足りない</h1>
      <p class="subtitle">必要なのは、AI の使い方ではなく、仕事の設計全体の見直し</p>
      <div class="grid-3" style="margin-top:104px;">
        <div class="card"><h3>対象の明確化</h3><p>何に AI を使うかを絞る</p></div>
        <div class="card"><h3>手順の分解</h3><p>長い仕事を一回でやらせない</p></div>
        <div class="card"><h3>知識の供給</h3><p>業務文脈を先に与える</p></div>
      </div>
      <div class="grid-3" style="margin-top:18px;">
        <div class="card"><h3>確認の設計</h3><p>レビューと自己点検を入れる</p></div>
        <div class="card"><h3>役割分担</h3><p>実行と確認を分ける</p></div>
        <div class="card soft-blue"><h3>仕事の設計</h3><p>個人技でなく、再利用可能な型にする</p></div>
      </div>
      <div class="summary-band">
        <strong>プロンプトは一部でしかない</strong>
        <span>品質を担保するには、仕事の構造そのものを設計し直す必要がある。</span>
      </div>
    </div>`,
  "08_conclusion": () => `
    <div class="canvas">
      <h1 class="title">結論</h1>
      <p class="subtitle">PoC の延長では、本番利用には届かない</p>
      <div class="grid-3" style="margin-top:100px;">
        <div class="mini soft-orange">
          <h3>AI の特性</h3>
          <p>忘れる<br>ぶれる<br>言い切る</p>
        </div>
        <div class="mini soft-blue">
          <h3>本番の条件</h3>
          <p>複雑さが増える<br>品質を保つ必要がある<br>個人技では足りない</p>
        </div>
        <div class="mini soft-green">
          <h3>必要な方向</h3>
          <p>再現性を持たせる<br>品質を担保する<br>組織として広げる</p>
        </div>
      </div>
      <div class="summary-band" style="margin-top:34px;">
        <strong>AI 活用の課題は、導入ではなく本番利用である</strong>
        <span>だから、個人利用や PoC の延長ではなく、本番前提で品質と再現性を設計し直す必要がある。</span>
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
