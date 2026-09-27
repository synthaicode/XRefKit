// Small DOM boundary harness exercising the real browser script and failed fetch.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const testLang = process.env.ATTENTION_PET_TEST_LANG || 'ja-JP';
const english = testLang.startsWith('en');
const sample = JSON.parse(fs.readFileSync(0, 'utf8'));
const html = fs.readFileSync('xrefkit/resources/attention_pet/pet.html', 'utf8');
assert.doesNotMatch(html, /id="workspace"/);
assert.doesNotMatch(html, /id="close"/);
assert.doesNotMatch(html, /id="import-section"/);
assert.doesNotMatch(html, /id="recovery-section"/);
assert.match(html, /<section id="panel" class="panel" aria-label=/);
assert.match(html, /id="pet-model-guide" hidden/);
assert.doesNotMatch(html, /Model Fit/);
const localizedTextNodes = [...html.matchAll(/data-i18n="([^"]+)"/g)].map(match => ({dataset:{i18n:match[1]},innerHTML:null}));
const localizedAriaNodes = [...html.matchAll(/data-i18n-aria="([^"]+)"/g)].map(match => ({dataset:{i18nAria:match[1]},setAttribute(_name,value){this.ariaLabel=value;}}));
function element() {
  return {textContent:'',value:'',checked:true,hidden:true,dataset:{},children:[],options:[],
    setAttribute(name,value){this[name]=value;},
    replaceChildren(...children){this.children=children;this.options=children;this.textContent='';},
    append(child){this.children.push(child);}};
}
const nodes = new Map();
const node = id => {if(!nodes.has(id)) nodes.set(id,element());return nodes.get(id);};
const storage = {getItem:()=>null,setItem:()=>{}};
let failure = false;
let hold = false, releaseFetch;
let lastFetchOptions = null;
let lastFetchPath = null;
const context = vm.createContext({
  document:{getElementById:node,body:element(),documentElement:element(),title:'',createElement:element,querySelectorAll:selector=>selector==='[data-i18n]' ? localizedTextNodes : selector==='[data-i18n-aria]' ? localizedAriaNodes : [],addEventListener:()=>{}},
  window:{addEventListener:()=>{},matchMedia:()=>({matches:false,addEventListener:()=>{}})},
  navigator:{languages:[testLang],language:testLang},
  localStorage:storage,sessionStorage:storage,location:{hash:'',pathname:'/'},history:{replaceState:()=>{}},
  URLSearchParams,AbortSignal,setInterval:()=>{},setTimeout,clearTimeout,
  fetch:async(path,options)=>{lastFetchPath=path;lastFetchOptions=options;if(failure) throw Error('simulated connection failure');if(hold) await new Promise(resolve=>releaseFetch=resolve);return {ok:true,json:async()=>path==='/api/profiles' ? {models:[{id:'luna',label:'Luna',reasoning:['low','medium','high','xhigh']},{id:'terra',label:'Terra',reasoning:['low','medium','high']},{id:'sol',label:'Sol',reasoning:['low','medium','high','xhigh','max']},{id:'astra',label:'Astra',reasoning:['low','medium','high','xhigh','max']}]} : sample};},
  sample,
});
(async()=>{
  vm.runInContext(fs.readFileSync('xrefkit/resources/attention_pet/pet.js','utf8'),context);
  await new Promise(setImmediate);
  assert.match(lastFetchPath, new RegExp(`lang=${english ? 'en' : 'ja'}`));
  if (english) {
    assert.ok(localizedTextNodes.every(item => typeof item.innerHTML === 'string' && item.innerHTML.length));
    assert.ok(localizedAriaNodes.every(item => typeof item.ariaLabel === 'string' && item.ariaLabel.length));
    assert.equal(context.document.documentElement.lang,'en');
  }
  assert.equal(lastFetchOptions.method,'GET');
  assert.equal(lastFetchOptions.headers.Authorization,undefined);
  assert.match(node('model-fit').textContent,/Sufficient/);
  assert.equal(node('dock').dataset.expression,sample.fit.presentation.petState.toLowerCase());
  assert.notEqual(node('effective').textContent,'—');
  assert.equal(node('state-title').textContent,sample.fit.presentation.headline);
  assert.equal(node('pet-caption').textContent,sample.fit.presentation.shortMessage);
  assert.equal(node('panel-model-guide').textContent,sample.fit.presentation.modelGuide);
  assert.equal(node('pet-model-guide').textContent,sample.fit.presentation.modelGuideShort);
  assert.equal(node('pet-model-guide').hidden,!sample.fit.presentation.modelGuideShort);
  const profileFitLabel = localizedTextNodes.find(item => item.dataset.i18n === 'modelFit');
  if (english) assert.match(profileFitLabel.innerHTML,/Profile Fit/);
  assert.equal(node('model-profile').options.length,5);
  assert.equal(node('reasoning-effort').options.length,5);
  node('model-profile').value='terra';node('reasoning-effort').value='max';
  vm.runInContext('syncReasoningOptions(true)',context);
  assert.equal(node('reasoning-effort').value,'low');
  assert.equal(node('reasoning-effort').options.find(option=>option.value==='max').disabled,true);
  hold=true;
  node('model-profile').value='astra';
  vm.runInContext('storeProfile()',context);
  assert.equal(node('state-title').textContent,english ? 'Updating evaluation' : '評価を更新中');
  assert.equal(node('dock').dataset.expression,'unknown');
  hold=false;releaseFetch();
  await new Promise(setImmediate);
  assert.equal(node('state-title').textContent,sample.fit.presentation.headline);
  failure=true;
  await vm.runInContext('refresh()',context);
  for(const id of ['ral','expansion','effective','model-fit','cost-fit','fit-coverage','fit-confidence']) assert.equal(node(id).textContent,'—',id);
  for(const id of ['fit-reasons','capability-rows','candidate-rows','lower-cost-candidates','causes']) assert.equal(node(id).children.length,0,id);
  assert.equal(node('dock').dataset.expression,'unknown');
  assert.equal(node('state-title').textContent,english ? 'Could not retrieve the evaluation' : '評価を取得できません');
  assert.equal(node('panel-model-guide').textContent,'');
  assert.equal(node('pet-model-guide').textContent,'');
  assert.equal(node('pet-model-guide').hidden,true);
  assert.equal(node('pet-caption').textContent,node('state-title').textContent);
  assert.equal(vm.runInContext('current',context),null);
  failure=false;
  await vm.runInContext('refresh()',context);
  assert.equal(node('dock').dataset.expression,sample.fit.presentation.petState.toLowerCase());
  assert.match(node('model-fit').textContent,/Sufficient/);
  sample.fit.costFit='ReviewNeeded';
  sample.fit.presentation.petState='Review';
  vm.runInContext('renderedSignature=""; render(sample)',context);
  assert.equal(node('dock').dataset.expression,'review');
  // The browser consumes API-provided text; it must not derive its own headline.
  sample.fit.presentation.headline='API supplied headline';
  vm.runInContext('render(sample)',context);
  assert.equal(node('state-title').textContent,'API supplied headline');
  sample.fit.presentation.modelGuide='API supplied downgrade guide';
  sample.fit.presentation.modelGuideShort='低コスト比較候補: Terra';
  sample.fit.presentation.modelGuideStatus='Available';
  vm.runInContext('render(sample)',context);
  assert.equal(node('panel-model-guide').textContent,'API supplied downgrade guide');
  assert.equal(node('pet-model-guide').textContent,'低コスト比較候補: Terra');
  assert.equal(node('pet-model-guide').hidden,false);
  sample.source={mode:'codex-chat',observedUserTurns:2,model:'gpt-6-sol',effort:'medium',profile:'sol',reasoning:'medium'};
  vm.runInContext('comparisonOverridden=false; document.getElementById("model-profile").value=""',context);
  vm.runInContext('renderedSignature=""; render(sample)',context);
  assert.equal(node('model-profile').value,'sol');
  assert.equal(node('reasoning-effort').value,'medium');
  assert.equal(node('model-profile').disabled,false);
  assert.equal(node('reasoning-effort').disabled,false);
  assert.match(node('source-detail').textContent,english ? /message counts/ : /会話中の発言数/);
  assert.match(node('source-model').textContent,/Codex model: gpt-6-sol/);
  assert.match(node('source-model').textContent,/Default evaluation profile: Sol \/ medium/);
  assert.notEqual(node('dock').dataset.chatUpdate,'on');
  sample.source.observedUserTurns=3;
  vm.runInContext('render(sample)',context);
  assert.equal(node('dock').dataset.chatUpdate,'on');
  sample.source={mode:'client-state',connected:true,provider:'github-copilot-vscode',activationRevision:3,model:'gpt-6-sol',effort:'medium',profile:'sol',reasoning:'medium'};
  vm.runInContext('renderedSignature=""; render(sample)',context);
  assert.match(node('source-model').textContent,/Client: github-copilot-vscode/);
  assert.match(node('source-detail').textContent,english ? /structured information/ : /構造化情報/);
  sample.source={...sample.source,activationRevision:4,model:'gpt-6-astra',effort:'high',profile:'astra',reasoning:'high'};
  vm.runInContext('renderedSignature=""; render(sample)',context);
  assert.equal(node('model-profile').value,'astra');
  assert.equal(node('reasoning-effort').value,'high');
  await vm.runInContext('refresh()',context);
  assert.equal(new URLSearchParams(lastFetchPath.split('?')[1]).get('model'),'');
  node('model-profile').value='terra';
  node('reasoning-effort').value='high';
  vm.runInContext('storeProfile()',context);
  await new Promise(setImmediate);
  sample.source={...sample.source,activationRevision:5,model:'gpt-6-sol',effort:'medium',profile:'sol',reasoning:'medium'};
  vm.runInContext('renderedSignature=""; render(sample)',context);
  assert.equal(node('model-profile').value,'terra');
  assert.equal(node('reasoning-effort').value,'high');
  await vm.runInContext('refresh()',context);
  assert.equal(new URLSearchParams(lastFetchPath.split('?')[1]).get('model'),'terra');
  node('model-profile').value='';
  vm.runInContext('storeProfile()',context);
  await new Promise(setImmediate);
  assert.equal(node('model-profile').value,'sol');
  assert.equal(node('reasoning-effort').value,'medium');
  assert.equal(new URLSearchParams(lastFetchPath.split('?')[1]).get('model'),'');
  assert.match(node('cost-note').textContent,english ? /waiting time/ : /待ち時間/);
  const disclaimer = localizedTextNodes.find(item => item.dataset.i18n === 'costDisclaimer');
  if (english) assert.match(disclaimer.innerHTML,/waiting time/);
  else assert.match(html,/総コスト ＝ 推論 ＋ 再試行 ＋ 修正 ＋ 待ち時間/);
})().catch(error=>{console.error(error);process.exitCode=1;});
