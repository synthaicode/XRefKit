// Small DOM boundary harness exercising the real browser script and failed fetch.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const sample = JSON.parse(fs.readFileSync(0, 'utf8'));
const html = fs.readFileSync('xrefkit/resources/attention_pet/pet.html', 'utf8');
assert.doesNotMatch(html, /id="workspace"/);
assert.doesNotMatch(html, /id="close"/);
assert.doesNotMatch(html, /id="import-section"/);
assert.doesNotMatch(html, /id="recovery-section"/);
assert.match(html, /<section id="panel" class="panel" aria-label=/);
function element() {
  return {textContent:'',value:'',checked:true,hidden:true,dataset:{},children:[],
    setAttribute(name,value){this[name]=value;},
    replaceChildren(...children){this.children=children;this.textContent='';},
    append(child){this.children.push(child);}};
}
const nodes = new Map();
const node = id => {if(!nodes.has(id)) nodes.set(id,element());return nodes.get(id);};
const storage = {getItem:()=>null,setItem:()=>{}};
let failure = false;
let hold = false, releaseFetch;
const context = vm.createContext({
  document:{getElementById:node,body:element(),createElement:element,querySelectorAll:()=>[],addEventListener:()=>{}},
  window:{addEventListener:()=>{},matchMedia:()=>({matches:false,addEventListener:()=>{}})},
  localStorage:storage,sessionStorage:storage,location:{hash:'',pathname:'/'},history:{replaceState:()=>{}},
  URLSearchParams,AbortSignal,setInterval:()=>{},setTimeout,clearTimeout,
  fetch:async()=>{if(failure) throw Error('simulated connection failure');if(hold) await new Promise(resolve=>releaseFetch=resolve);return {ok:true,json:async()=>sample};},
  sample,
});
(async()=>{
  vm.runInContext(fs.readFileSync('xrefkit/resources/attention_pet/pet.js','utf8'),context);
  await new Promise(setImmediate);
  assert.match(node('model-fit').textContent,/Sufficient/);
  assert.equal(node('dock').dataset.expression,sample.fit.presentation.petState.toLowerCase());
  assert.notEqual(node('effective').textContent,'—');
  assert.equal(node('state-title').textContent,sample.fit.presentation.headline);
  assert.equal(node('pet-caption').textContent,sample.fit.presentation.shortMessage);
  assert.equal(node('panel-model-guide').textContent,sample.fit.presentation.modelGuide);
  hold=true;
  node('model-profile').value='astra';
  vm.runInContext('storeProfile()',context);
  assert.equal(node('state-title').textContent,'評価を更新中');
  assert.equal(node('dock').dataset.expression,'unknown');
  hold=false;releaseFetch();
  await new Promise(setImmediate);
  assert.equal(node('state-title').textContent,sample.fit.presentation.headline);
  failure=true;
  await vm.runInContext('refresh()',context);
  for(const id of ['ral','expansion','effective','model-fit','cost-fit','fit-coverage','fit-confidence']) assert.equal(node(id).textContent,'—',id);
  for(const id of ['fit-reasons','capability-rows','candidate-rows','lower-cost-candidates','causes']) assert.equal(node(id).children.length,0,id);
  assert.equal(node('dock').dataset.expression,'unknown');
  assert.equal(node('state-title').textContent,'評価を取得できません');
  assert.equal(node('panel-model-guide').textContent,'');
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
  sample.source={mode:'codex-chat',observedUserTurns:2,model:'gpt-6-sol',effort:'medium',profile:'sol',reasoning:'standard'};
  vm.runInContext('comparisonInitialized=false; comparisonOverridden=false; document.getElementById("model-profile").value=""',context);
  vm.runInContext('renderedSignature=""; render(sample)',context);
  assert.equal(node('model-profile').value,'sol');
  assert.equal(node('reasoning-effort').value,'standard');
  assert.equal(node('model-profile').disabled,false);
  assert.equal(node('reasoning-effort').disabled,false);
  assert.match(node('source-detail').textContent,/会話中の発言数/);
  assert.match(node('source-model').textContent,/Codex model: gpt-6-sol/);
  assert.match(node('source-model').textContent,/Default evaluation profile: Sol \/ standard/);
  assert.notEqual(node('dock').dataset.chatUpdate,'on');
  sample.source.observedUserTurns=3;
  vm.runInContext('render(sample)',context);
  assert.equal(node('dock').dataset.chatUpdate,'on');
})().catch(error=>{console.error(error);process.exitCode=1;});
