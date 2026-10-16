// BIO Cards: estructura i regles tal com al joc d'esports (Inici, Àlbum, Col·leccions, Missions, Taller, Perfil).
const CFG={startCoins:100,startPacks:3,cardsPerPack:5,maxPacks:3,msPerPack:10*60*1000,protoDailyCap:150,craftMult:5,
 weights:{comuna:60,poc_comuna:25,rara:10,epica:4,llegendaria:1},
 recycle:{comuna:5,poc_comuna:15,rara:50,epica:200,llegendaria:1000}};
const D=JSON.parse(document.getElementById('dades').textContent);
const CARDS=D.cartes, MIS=D.misions, BYID=Object.fromEntries(CARDS.map(c=>[c.id,c]));
const SETS=MIS.filter(m=>m.tipus!=='protocol'), PROTOS=MIS.filter(m=>m.tipus==='protocol');
const RARITIES=['comuna','poc_comuna','rara','epica','llegendaria'], RLABEL={comuna:'Common',poc_comuna:'Uncommon',rara:'Rare',epica:'Epic',llegendaria:'Legendary'};
const RARE_UP=new Set(['rara','epica','llegendaria']);
const CATS=[...new Set(CARDS.map(c=>c.cat))].sort();
const KEY='bio-cards-save-v2', today=()=>new Date().toISOString().slice(0,10);
let S, memSave=null;
const fresh=()=>({coins:CFG.startCoins,owned:{},claimed:{},proto:{},packs:CFG.startPacks,packTick:Date.now(),day:today(),dayCoins:0,
 opened:0,openedDay:today(),openedToday:0,recycled:0,crafted:0});
function load(){try{const r=localStorage.getItem(KEY);if(r)return Object.assign(fresh(),JSON.parse(r));}catch(e){}
 return memSave?Object.assign(fresh(),JSON.parse(memSave)):fresh();}
function save(){const j=JSON.stringify(S);memSave=j;try{localStorage.setItem(KEY,j);}catch(e){}}
function newDay(){const d=today(); if(S.day!==d){S.day=d;S.dayCoins=0;} if(S.openedDay!==d){S.openedDay=d;S.openedToday=0;}}
S=load(); newDay();
const $=s=>document.querySelector(s), esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let msgText='', view='home', opening=null, modalId=null, openCol=null, shopTab='destroy';
const F={q:'',cat:'',rar:''}, W={q:''};
const setMsg=t=>{msgText=t;const m=$('#msg');if(m)m.textContent=t;};
const own=id=>S.owned[id]||0, val=c=>CFG.recycle[c.raresa], craftCost=c=>val(c)*CFG.craftMult;
const have=m=>m.ids.filter(i=>own(i)>0).length;

// ---- sobres amb temps: +1 cada 10 min, màxim 3; plens, el rellotge no avança
function tickPacks(now=Date.now()){
 const before=S.packs;
 if(S.packs>=CFG.maxPacks){S.packs=CFG.maxPacks;S.packTick=now;return false;}
 const gen=Math.max(0,Math.floor((now-S.packTick)/CFG.msPerPack)); if(!gen) return false;
 const nous=S.packs+gen;
 if(nous>=CFG.maxPacks){S.packs=CFG.maxPacks;S.packTick=now;} else {S.packs=nous;S.packTick+=gen*CFG.msPerPack;}
 return S.packs!==before;
}
const msToNext=()=>S.packs>=CFG.maxPacks?0:CFG.msPerPack-Math.min(CFG.msPerPack,Math.max(0,Date.now()-S.packTick));
const fmt=ms=>{const t=Math.ceil(ms/1000);return `${String(Math.floor(t/60)).padStart(2,'0')}:${String(t%60).padStart(2,'0')}`;};
function rollRarity(){
 const have=new Set(CARDS.map(c=>c.raresa)); let tot=0;
 for(const r in CFG.weights) if(have.has(r)) tot+=CFG.weights[r];
 let x=Math.random()*tot;
 for(const r in CFG.weights){ if(!have.has(r)) continue; if((x-=CFG.weights[r])<0) return r; }
 return 'comuna';
}
function openPack(){
 newDay(); tickPacks(); if(S.packs<=0) return;
 if(S.packs>=CFG.maxPacks) S.packTick=Date.now(); S.packs--;
 const cards=[];
 for(let i=0;i<CFG.cardsPerPack;i++){
  const pool=CARDS.filter(c=>c.raresa===rollRarity());
  const c=pool[Math.floor(Math.random()*pool.length)];
  cards.push({id:c.id,nou:own(c.id)===0,flipped:false}); S.owned[c.id]=own(c.id)+1;
 }
 S.opened++; S.openedToday++; save(); opening={cards,leg:false}; render();
}

// ---- economia
function destroyOne(id){
 const c=BYID[id], v=val(c), last=own(id)===1;
 const openSets=last?SETS.filter(m=>m.ids.includes(id)&&!S.claimed[m.id]):[];
 let t=`Destroy one copy of ${c.nom} for ${v} coins?`;
 if(last) t+=`\n\nIt is your last copy. You will lose the card (crafting it again costs ${craftCost(c)} coins).`;
 if(openSets.length) t+=`\n\nIt is part of collections you have started: ${openSets.map(m=>m.nom.replace('Collect all: ','')).join(', ')}.`;
 if(!confirm(t)) return; S.owned[id]--; if(!S.owned[id]) delete S.owned[id]; S.coins+=v; S.recycled++; save(); setMsg(`+${v} coins.`); render();
}
const dupes=()=>CARDS.filter(c=>own(c.id)>1);
const dupesValue=()=>dupes().reduce((a,c)=>a+(own(c.id)-1)*val(c),0);
function destroyDupes(){
 const v=dupesValue(); if(!v) return;
 if(!confirm(`Destroy all duplicates for ${v} coins? You keep one copy of each card.`)) return;
 dupes().forEach(c=>{S.recycled+=own(c.id)-1; S.owned[c.id]=1;}); S.coins+=v; save(); setMsg(`+${v} coins.`); render();
}
function craft(id){
 const c=BYID[id], p=craftCost(c); if(S.coins<p) return setMsg('You do not have enough coins.');
 if(!confirm(`Craft ${c.nom} for ${p} coins?`)) return; S.coins-=p; S.owned[id]=1; S.crafted++; save(); setMsg(`Crafted ${c.nom}.`); render();
}

// ---- missions
const setsDone=()=>SETS.filter(m=>have(m)===m.ids.length).length;
const rareOwned=()=>CARDS.filter(c=>own(c.id)&&RARE_UP.has(c.raresa)).length;
const GEN=[
 {id:'d_packs3',nom:'Open 3 packs today',obj:3,premi:40,daily:true,prog:()=>S.openedToday},
 {id:'packs10',nom:'Open 10 packs',obj:10,premi:60,prog:()=>S.opened},
 {id:'packs50',nom:'Open 50 packs',obj:50,premi:250,prog:()=>S.opened},
 {id:'diff10',nom:'Get 10 different cards',obj:10,premi:50,prog:()=>Object.keys(S.owned).length},
 {id:'diff50',nom:'Get 50 different cards',obj:50,premi:300,prog:()=>Object.keys(S.owned).length},
 {id:'rare1',nom:'Get 1 rare or better card',obj:1,premi:60,prog:rareOwned},
 {id:'rare5',nom:'Get 5 rare or better cards',obj:5,premi:250,prog:rareOwned},
 {id:'rec5',nom:'Destroy 5 cards',obj:5,premi:30,prog:()=>S.recycled},
 {id:'craft1',nom:'Craft 1 card',obj:1,premi:40,prog:()=>S.crafted},
 {id:'sets1',nom:'Finish 1 collection',obj:1,premi:100,prog:setsDone},
 {id:'sets5',nom:'Finish 5 collections',obj:5,premi:500,prog:setsDone}];
const genKey=g=>g.daily?`${g.id}:${today()}`:g.id;
function claimGen(id){
 const g=GEN.find(x=>x.id===id); if(!g||S.claimed[genKey(g)]||g.prog()<g.obj) return;
 S.claimed[genKey(g)]=true; S.coins+=g.premi; save(); setMsg(`+${g.premi} coins.`); render();
}
function claimSet(id){
 const m=SETS.find(x=>x.id===id); if(!m||S.claimed[id]||have(m)<m.ids.length) return;
 S.claimed[id]=true; S.coins+=m.premi; save(); setMsg(`+${m.premi} coins: ${m.nom}.`); render();
}
function claimProto(id){
 const m=PROTOS.find(x=>x.id===id); if(!m||have(m)<m.ids.length) return;
 newDay(); if(S.dayCoins+m.premi>CFG.protoDailyCap) return setMsg(`Daily protocol limit reached (${CFG.protoDailyCap} coins/day).`);
 S.dayCoins+=m.premi; S.proto[id]=(S.proto[id]||0)+1; S.coins+=m.premi; save(); setMsg(`+${m.premi} coins: ${m.nom}.`); render();
}

// ---- peces de pantalla
function ghostCard(c){return `<article class="carta ghost" style="--r:${c.color}"><header><h2>${esc(c.nom)}</h2><span>${c.rlabel}</span></header>
  <div class="img"><div class="sense-img"><svg viewBox="0 0 100 100">${c.icona}</svg><span>${c.cat}</span></div></div></article>`;}
function cell(c,withQty=true){const n=own(c.id);
 return `<div class="cell" data-a="open" data-v="${c.id}">${withQty&&n>1?`<span class="qty">×${n}</span>`:''}${n?c.html:ghostCard(c)}</div>`;}
const bar=(a,b)=>`<div class="bar"><i style="width:${100*a/b}%"></i></div>`;

function vHome(){
 tickPacks();
 return `<div class="home"><div class="packart"><div id="pk">${S.packs}</div></div>
  <div class="big">Packs: ${S.packs} of ${CFG.maxPacks}</div>
  <div class="cnt" id="cd">${S.packs>=CFG.maxPacks?'Packs full':`Next pack in ${fmt(msToNext())}`}</div>
  <button class="btn pri" id="bPack" data-a="pack" ${S.packs<1?'disabled':''} style="min-width:200px">${S.packs>0?'Open a pack':'Wait for the next pack'}</button>
  <div class="cnt">${CFG.cardsPerPack} cards per pack</div></div>`;
}
function albumGrid(){
 const q=F.q.trim().toLowerCase();
 const list=CARDS.filter(c=>own(c.id)&&(!F.cat||c.cat===F.cat)&&(!F.rar||c.raresa===F.rar)&&(!q||c.nom.toLowerCase().includes(q)));
 return `<p class="cnt">${Object.keys(S.owned).length} different cards</p>`+
  (Object.keys(S.owned).length?`<div class="grid compact">${list.map(c=>cell(c)).join('')||'<p class="cnt">No cards match.</p>'}</div>`
   :'<p class="cnt">You do not have any card yet. Open a pack!</p>');
}
function vAlbum(){
 const chip=(k,v,l)=>`<button class="chip ${F[k]===v?'on':''}" data-a="f" data-k="${k}" data-v="${esc(v)}">${esc(l)}</button>`;
 return `<input type="search" id="q" placeholder="Search by name" value="${esc(F.q)}">
  <div class="chips" style="margin-top:10px">${chip('cat','','All')}${CATS.map(c=>chip('cat',c,c)).join('')}</div>
  <div class="chips">${chip('rar','','Any rarity')}${RARITIES.map(r=>chip('rar',r,RLABEL[r])).join('')}</div><div id="albumGrid">${albumGrid()}</div>`;
}
function vCols(){
 return SETS.map(m=>{const h=have(m),n=m.ids.length,ok=h===n,dn=S.claimed[m.id],op=openCol===m.id;
  return `<div class="col"><div class="top" data-a="col" data-v="${esc(m.id)}"><h3>${esc(m.nom.replace('Collect all: ',''))}</h3><span class="cnt">${h} of ${n}</span></div>${bar(h,n)}
   ${ok?(dn?'<span class="done">Claimed</span>':`<button class="btn pri wide" data-a="claimSet" data-v="${esc(m.id)}">Claim ${m.premi} coins</button>`):`<span class="cnt">Reward: ${m.premi} coins</span>`}
   ${op?`<div class="grid compact">${m.ids.map(i=>cell(BYID[i],false)).join('')}</div>`:''}</div>`;}).join('')||'<p class="cnt">There are no collections yet.</p>';
}
function vMis(){
 const row=g=>{const p=Math.min(g.prog(),g.obj),dn=S.claimed[genKey(g)];
  return `<div class="mis"><h3>${esc(g.nom)} ${g.daily?'<span class="cnt">· Daily</span>':''}</h3>${bar(p,g.obj)}<div class="cnt">${p} of ${g.obj}</div>
   ${dn?'<span class="done">Claimed</span>':`<button class="btn pri" data-a="claimGen" data-v="${g.id}" ${p>=g.obj?'':'disabled'}>Claim ${g.premi} coins</button>`}</div>`;};
 const pr=m=>{const h=have(m),n=m.ids.length;
  return `<div class="mis"><h3>${esc(m.nom)}</h3><p>${esc(m.desc)}</p><p>${m.ids.map(i=>`<span style="color:${own(i)?'#69F0AE':'#8d8aa8'}">${esc(BYID[i].nom)}</span>`).join(' + ')}</p>
   ${bar(h,n)}<div class="cnt">${h} of ${n}${S.proto[m.id]?` · done ×${S.proto[m.id]}`:''}</div>
   <button class="btn pri" data-a="claimProto" data-v="${esc(m.id)}" ${h===n?'':'disabled'}>Claim ${m.premi} coins (repeatable)</button></div>`;};
 return `<h2 class="sec" style="margin-top:0">Missions</h2>${GEN.map(row).join('')}
  <h2 class="sec">Protocols</h2><p class="cnt">Own all the cards of a protocol to complete it. Cards are not used up. Limit: ${CFG.protoDailyCap} coins per day (today: ${S.dayCoins}).</p>${PROTOS.map(pr).join('')}`;
}
function shopList(){
 if(shopTab==='destroy'){
  const d=dupes(); if(!d.length) return '<p class="cnt">You have no duplicate cards.</p>';
  return d.map(c=>`<div class="item"><span class="dot" style="background:${c.color}"></span><div class="nm" data-a="open" data-v="${c.id}"><b>${esc(c.nom)}</b><span class="cnt">${c.rlabel} · ×${own(c.id)}</span></div>
   <button class="btn" data-a="destroy" data-v="${c.id}">+${val(c)}</button></div>`).join('');
 }
 const q=W.q.trim().toLowerCase(), l=CARDS.filter(c=>!own(c.id)&&(!q||c.nom.toLowerCase().includes(q)));
 return l.map(c=>`<div class="item"><span class="dot" style="background:${c.color}"></span><div class="nm" data-a="open" data-v="${c.id}"><b>${esc(c.nom)}</b><span class="cnt">${c.rlabel} · ${c.cat}</span></div>
  <button class="btn pri" data-a="craft" data-v="${c.id}" ${S.coins<craftCost(c)?'disabled':''}>${craftCost(c)}</button></div>`).join('')||'<p class="cnt">Nothing to craft.</p>';
}
function vShop(){
 const seg=`<div class="seg"><button class="chip ${shopTab==='destroy'?'on':''}" data-a="shop" data-v="destroy">Destroy</button><button class="chip ${shopTab==='craft'?'on':''}" data-a="shop" data-v="craft">Craft</button></div>`;
 const top=shopTab==='destroy'?`<button class="btn pri wide" style="margin-bottom:12px" data-a="destroyAll" ${dupesValue()?'':'disabled'}>Destroy all duplicates (+${dupesValue()} coins)</button>`
  :`<input type="search" id="wq" placeholder="Search the card you want" value="${esc(W.q)}" style="margin-bottom:12px">`;
 return seg+top+`<div id="shopList">${shopList()}</div>`;
}
function vProfile(){
 return `<button class="btn" data-a="back">‹ Back</button><h2 class="sec">Profile</h2>
  <h2 class="sec" style="font-size:16px">Statistics</h2><p>Packs opened: ${S.opened}</p><p>Different cards: ${Object.keys(S.owned).length} of ${CARDS.length}</p>
  <p>Cards destroyed: ${S.recycled}</p><p>Cards crafted: ${S.crafted}</p>
  <h2 class="sec" style="font-size:16px">Credits</h2><p class="cnt">Definitions: MeSH (NLM), UniProt (CC BY 4.0) and Wikipedia (CC BY-SA 4.0). Protein structures: RCSB PDB. Images: Wikimedia Commons, with author and licence shown on each card. Article counts: PubMed.</p>
  <h2 class="sec" style="font-size:16px">Save data</h2><p class="cnt">Your game is saved in this browser only. Copy the text to keep a backup, or paste one and press Import.</p>
  <textarea id="sv">${esc(JSON.stringify(S))}</textarea><div class="row"><button class="btn" data-a="import">Import</button><button class="btn" data-a="reset">Reset game</button></div>`;
}
function detailHtml(){
 if(modalId===null) return ''; const c=BYID[modalId], n=own(c.id);
 return `<div class="modal" id="mod" data-a="closeM"><div class="sheet">${n?c.html:ghostCard(c)}
  <div class="cnt">${n?`Copies: ${n}`:'You do not have this card yet'}</div>
  <div class="acts">${n?`<button class="btn wide" data-a="destroy" data-v="${c.id}">Destroy one copy (+${val(c)} coins)</button>`
   :`<button class="btn pri wide" data-a="craft" data-v="${c.id}" ${S.coins<craftCost(c)?'disabled':''}>Craft (${craftCost(c)} coins)</button>`}
  <button class="btn wide" data-a="closeM" data-v="x">Close</button></div></div></div>`;
}
function overlayHtml(){
 if(!opening) return '';
 const tiles=opening.cards.map((p,i)=>{const c=BYID[p.id];
  return `<div class="tile ${p.flipped?'flipped':''}" data-a="flip" data-v="${i}"><div class="in"><div class="face back"><div>?</div></div>
   <div class="face front"><div class="cell">${c.html}</div><span class="tag" style="background:${p.nou?'#69F0AE':'#CFCBEA'}">${p.nou?'New':'Repeated'}</span></div></div></div>`;}).join('');
 return `<div class="overlay"><div class="hint">Tap the cards to flip them</div><div class="tiles">${tiles}</div>
  <div class="btns"><button class="btn" data-a="flipAll">Flip all</button><button class="btn pri" data-a="done">Continue</button></div>
  ${opening.leg?'<div class="legend">Legendary!</div>':''}</div>`;
}
function confetti(){
 const cols=['#FFB300','#7C4DFF','#69F0AE','#FF5252','#40C4FF'], el=document.createElement('div'); el.className='confetti';
 for(let i=0;i<70;i++){const s=4+Math.random()*7;el.insertAdjacentHTML('beforeend',`<i style="left:${Math.random()*100}%;width:${s}px;height:${s}px;background:${cols[i%5]};--dx:${(Math.random()-.5)*80}px;animation-delay:${Math.random()*.6}s"></i>`);}
 document.body.appendChild(el); setTimeout(()=>el.remove(),3800);
}
function flipTile(i){
 const p=opening.cards[i]; if(p.flipped) return setModal(p.id);
 p.flipped=true; const t=document.querySelector(`.tile[data-v="${i}"]`); t&&t.classList.add('flipped');
 if(BYID[p.id].raresa==='llegendaria'&&!opening.leg){opening.leg=true;confetti();const o=$('.overlay');o&&o.insertAdjacentHTML('beforeend','<div class="legend">Legendary!</div>');}
}
function setModal(id){modalId=id;$('#modalHost').innerHTML=detailHtml();}

const TITLES={home:'BIO Cards',album:'Album',cols:'Collections',mis:'Missions',shop:'Workshop',profile:'Profile'};
function render(){
 $('#coins').textContent=`● ${S.coins} coins`; $('#title').textContent=TITLES[view];
 document.querySelectorAll('nav.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.v===view));
 $('#overlayHost').innerHTML=overlayHtml(); $('#modalHost').innerHTML=detailHtml();
 $('#app').innerHTML=`<div class="msg" id="msg">${esc(msgText)}</div>`+({home:vHome,album:vAlbum,cols:vCols,mis:vMis,shop:vShop,profile:vProfile}[view])();
}
const ACT={
 pack:openPack, flip:v=>flipTile(+v),
 flipAll:()=>{opening.cards.forEach((_,i)=>setTimeout(()=>flipTile2(i),i*120));},
 done:()=>{opening=null;render();},
 open:v=>setModal(+v), closeM:(v,t,ev)=>{if(v==='x'||ev.target===t){modalId=null;$('#modalHost').innerHTML='';}},
 destroy:v=>destroyOne(+v), destroyAll:destroyDupes, craft:v=>craft(+v), shop:v=>{shopTab=v;render();},
 f:(v,t)=>{F[t.dataset.k]=v;render();}, col:v=>{openCol=openCol===v?null:v;render();},
 claimSet:claimSet, claimGen:claimGen, claimProto:claimProto, back:()=>{view='home';render();},
 import:()=>{try{const o=JSON.parse($('#sv').value);if(typeof o.coins!=='number'||typeof o.owned!=='object')throw 0;S=Object.assign(fresh(),o);save();setMsg('Imported.');render();}catch(e){setMsg('That is not a valid backup.');}},
 reset:()=>{if(confirm('Delete all progress?')){S=fresh();save();setMsg('Game reset.');render();}}
};
function flipTile2(i){if(opening&&!opening.cards[i].flipped) flipTile(i);}
document.addEventListener('click',ev=>{const t=ev.target.closest('[data-a]'); if(!t) return;
 if(t.dataset.a==='closeM'&&t.dataset.v!=='x'&&ev.target!==t) return;
 const f=ACT[t.dataset.a]; if(f) f(t.dataset.v,t,ev);});
document.addEventListener('input',ev=>{
 if(ev.target.id==='q'){F.q=ev.target.value;$('#albumGrid').innerHTML=albumGrid();}
 if(ev.target.id==='wq'){W.q=ev.target.value;$('#shopList').innerHTML=shopList();}});
document.querySelectorAll('nav.tabs button').forEach(b=>b.onclick=()=>{view=b.dataset.v;modalId=null;setMsg('');window.scrollTo(0,0);render();});
$('#bProfile').onclick=()=>{view='profile';modalId=null;window.scrollTo(0,0);render();};
render();
setInterval(()=>{const was=S.packs; if(tickPacks()||S.packs!==was){save(); if(view==='home'&&!opening&&modalId===null) render(); return;}
 const e=$('#cd'); if(e&&S.packs<CFG.maxPacks) e.textContent=`Next pack in ${fmt(msToNext())}`;},1000);
