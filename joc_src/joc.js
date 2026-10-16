// BIO Cards: estructura i regles com al joc d'esports (Home, Album, All, Missions, Workshop, Profile).
const CFG={startCoins:100,startPacks:3,cardsPerPack:5,maxPacks:3,msPerPack:10*60*1000,protoDailyCap:150,craftMult:5,
 weights:{comuna:60,poc_comuna:25,rara:10,epica:4,llegendaria:1},
 recycle:{comuna:5,poc_comuna:15,rara:50,epica:200,llegendaria:1000}};
const D=JSON.parse(document.getElementById('dades').textContent);
const CARDS=D.cartes, MIS=D.misions, BYID=Object.fromEntries(CARDS.map(c=>[c.id,c]));
const SETS=MIS.filter(m=>m.tipus!=='protocol'), PROTOS=MIS.filter(m=>m.tipus==='protocol');
const RARITIES=['comuna','poc_comuna','rara','epica','llegendaria'], RLABEL={comuna:'Common',poc_comuna:'Uncommon',rara:'Rare',epica:'Epic',llegendaria:'Legendary'};
const RANK=Object.fromEntries(RARITIES.map((r,i)=>[r,i])), RCOLOR=D.colors;
const RARE_UP=new Set(['rara','epica','llegendaria']);
const CATS=[...new Set(CARDS.map(c=>c.cat))].sort();
const setName=m=>m.nom.replace('Collect all: ','');
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
let msgText='', view='home', opening=null, modalId=null, shopTab='destroy', shaking=false;
const F={album:{q:'',cat:'',rar:''},all:{q:'',cat:'',rar:'',miss:false,set:''}}, W={q:''}, SEL={on:false,ids:new Set()};
const setMsg=t=>{msgText=t;const m=$('#msg');if(m)m.textContent=t;};
const own=id=>S.owned[id]||0, val=c=>CFG.recycle[c.raresa], craftCost=c=>val(c)*CFG.craftMult;
const have=m=>m.ids.filter(i=>own(i)>0).length;
const IC={search:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>',
 check:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M5 12l5 5 9-10"/></svg>',
 left:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 5l-7 7 7 7"/></svg>',
 right:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5l7 7-7 7"/></svg>'};

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
// Una carta d'un sobre no es repeteix dins del mateix sobre; si la raresa tirada s'esgota, es prova la més propera.
function drawCards(n){
 const chosen=new Set(), avail=[...new Set(CARDS.map(c=>c.raresa))];
 for(let i=0;i<n;i++){
  let tot=0; avail.forEach(r=>tot+=CFG.weights[r]); let x=Math.random()*tot, roll=avail[0];
  for(const r of avail){ if((x-=CFG.weights[r])<0){roll=r;break;} }
  const order=[...avail].sort((a,b)=>Math.abs(RANK[a]-RANK[roll])-Math.abs(RANK[b]-RANK[roll]));
  for(const r of order){const pool=CARDS.filter(c=>c.raresa===r&&!chosen.has(c.id)); if(pool.length){chosen.add(pool[Math.floor(Math.random()*pool.length)].id);break;}}
 }
 return [...chosen];
}
function startOpen(){
 if(shaking) return; newDay(); tickPacks(); if(S.packs<=0) return;
 shaking=true; const pk=$('.packwrap'); pk&&pk.classList.add('shake');
 setTimeout(()=>{shaking=false; newDay(); tickPacks(); if(S.packs<=0) return render();
  if(S.packs>=CFG.maxPacks) S.packTick=Date.now(); S.packs--;
  const ids=drawCards(CFG.cardsPerPack), cards=ids.map(id=>({id,nou:own(id)===0}));
  ids.forEach(id=>S.owned[id]=own(id)+1); S.opened++; S.openedToday++; save();
  opening={cards,viewed:cards.map(()=>false),cur:0,leg:false}; render(); setTimeout(()=>viewCard(0),350);},400);
}

// ---- economia
function destroyOne(id){
 const c=BYID[id], v=val(c), last=own(id)===1;
 let t=`Destroy one copy of ${c.nom} for ${v} coins?`;
 if(last) t+=`\n\nIt is your last copy. You will lose the card (crafting it again costs ${craftCost(c)} coins).`;
 if(!confirm(t)) return; S.owned[id]--; if(!S.owned[id]) delete S.owned[id]; S.coins+=v; S.recycled++; save(); setMsg(`+${v} coins.`); render();
}
const selValue=()=>[...SEL.ids].reduce((a,id)=>a+val(BYID[id]),0);
function destroySel(){
 const ids=[...SEL.ids]; if(!ids.length) return; const v=selValue(), lost=ids.filter(i=>own(i)<=1).length;
 let t=`You will destroy one copy of each of the ${ids.length} selected cards and get ${v} coins.`;
 if(lost) t+=`\n\n${lost} will leave your album.`;
 if(!confirm(t)) return;
 ids.forEach(id=>{S.owned[id]--; if(!S.owned[id]) delete S.owned[id]; S.recycled++;}); S.coins+=v; save();
 SEL.on=false; SEL.ids=new Set(); setMsg(`+${v} coins.`); render();
}
const dupes=()=>CARDS.filter(c=>own(c.id)>1);
const dupesValue=()=>dupes().reduce((a,c)=>a+(own(c.id)-1)*val(c),0);
function destroyDupes(){
 const v=dupesValue(); if(!v) return;
 if(!confirm(`Destroy all duplicates for ${v} coins? You keep one copy of each card.`)) return;
 dupes().forEach(c=>{S.recycled+=own(c.id)-1; S.owned[c.id]=1;}); S.coins+=v; save(); setMsg(`+${v} coins.`); render();
}
function craft(id){
 const c=BYID[id], p=craftCost(c); if(S.coins<p) return setMsg("You don't have enough coins.");
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
function claimGen(id){const g=GEN.find(x=>x.id===id); if(!g||S.claimed[genKey(g)]||g.prog()<g.obj) return;
 S.claimed[genKey(g)]=true; S.coins+=g.premi; save(); setMsg(`+${g.premi} coins.`); render();}
function claimSet(id){const m=SETS.find(x=>x.id===id); if(!m||S.claimed[id]||have(m)<m.ids.length) return;
 S.claimed[id]=true; S.coins+=m.premi; save(); setMsg(`+${m.premi} coins: ${setName(m)}.`); render();}
function claimProto(id){const m=PROTOS.find(x=>x.id===id); if(!m||have(m)<m.ids.length) return;
 newDay(); if(S.dayCoins+m.premi>CFG.protoDailyCap) return setMsg(`Daily protocol limit reached (${CFG.protoDailyCap} coins/day).`);
 S.dayCoins+=m.premi; S.proto[id]=(S.proto[id]||0)+1; S.coins+=m.premi; save(); setMsg(`+${m.premi} coins: ${m.nom}.`); render();}

// ---- peces de pantalla
const coinSvg='<svg viewBox="0 0 24 24"><defs><linearGradient id="gc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFE082"/><stop offset="1" stop-color="#FFB300"/></linearGradient></defs><circle cx="12" cy="12" r="11" fill="url(#gc)"/><circle cx="12" cy="12" r="8" fill="none" stroke="#7A4A0088" stroke-width="1.4"/><circle cx="12" cy="12" r="2.3" fill="#7A4A0088"/></svg>';
function packSvg(){
 let d='M0 8',w=290,h=500,n=16,st=w/n; for(let i=0;i<n;i++) d+=` L${st*(i+.5)} 0 L${st*(i+1)} 8`;
 d+=` L${w} ${h-8}`; for(let i=n;i>0;i--) d+=` L${st*(i-.5)} ${h} L${st*(i-1)} ${h-8}`; d+=' Z';
 let rays=''; for(let i=0;i<18;i++){const a0=i*20*Math.PI/180,a1=a0+10*Math.PI/180;rays+=`<path d="M145 250 L${145+500*Math.cos(a0)} ${250+500*Math.sin(a0)} L${145+500*Math.cos(a1)} ${250+500*Math.sin(a1)}Z" fill="#FFD54A" opacity=".07"/>`;}
 const mini=(r,x)=>`<g transform="rotate(${r} ${x} 250)"><rect x="${x-38}" y="194" width="76" height="112" rx="9" fill="url(#pc)" stroke="#ffffffb3" stroke-width="2"/><rect x="${x-30}" y="202" width="60" height="58" rx="5" fill="#ffffff38"/><rect x="${x-30}" y="266" width="44" height="7" rx="3" fill="#00000040"/><rect x="${x-30}" y="278" width="30" height="5" rx="2" fill="#0000002e"/></g>`;
 return `<svg viewBox="0 0 290 500"><defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2A1166"/><stop offset=".45" stop-color="#6A35E8"/><stop offset="1" stop-color="#170845"/></linearGradient>
  <linearGradient id="pc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3DDC97"/><stop offset="1" stop-color="#1b6b49"/></linearGradient><clipPath id="pcl"><path d="${d}"/></clipPath></defs>
  <path d="${d}" fill="url(#pg)"/><g clip-path="url(#pcl)">${rays}<rect width="290" height="500" fill="#ffffff" opacity=".04"/>${mini(-14,105)}${mini(14,185)}${mini(0,145)}
  <circle cx="145" cy="400" r="34" fill="#FFD54A"/><circle cx="145" cy="400" r="28" fill="none" stroke="#7A4A00" stroke-width="3" opacity=".6"/>
  <path d="M133 382c0 12 24 12 24 18s-24 6-24 18M157 382c0 12-24 12-24 18s24 6 24 18" fill="none" stroke="#3a1d00" stroke-width="4" stroke-linecap="round"/></g></svg>`;
}
function ghostCard(c){return `<article class="carta ghost" style="--r:${c.color}"><header><h2>${esc(c.nom)}</h2><span>${c.rlabel}</span></header>
  <div class="img"><div class="sense-img"><svg viewBox="0 0 100 100">${c.icona}</svg><span>${c.cat}</span></div></div></article>`;}
function cell(c,o={}){const n=own(c.id), sel=SEL.on&&SEL.ids.has(c.id);
 return `<div class="cell ${o.dim&&!n?'dim':''} ${SEL.on&&!sel?'dimsel':''}" data-a="open" data-v="${c.id}">${SEL.on&&o.sel?`<span class="chk ${sel?'on':''}">${sel?IC.check:''}</span>`:''}${n>1?`<span class="qty">×${n}</span>`:''}${c.html}</div>`;}
const bar=(a,b)=>`<div class="bar"><i style="width:${100*a/b}%"></i></div>`;
const title=(t,sub,act='')=>`<div class="ttl"><div><h1>${esc(t)}</h1>${sub?`<p>${sub}</p>`:''}</div>${act}</div>`;
const chip=(txt,on,attrs,dot)=>`<button class="chip ${on?'on':''}" ${attrs}>${dot?`<i style="background:${dot}"></i>`:''}${esc(txt)}</button>`;
const searchBox=(id,v,ph)=>`<div class="search">${IC.search}<input type="search" id="${id}" placeholder="${ph}" value="${esc(v)}"></div>`;

function vHome(){
 tickPacks();
 return `<div class="home"><h1>Open a pack</h1><div class="sub">Discover ${CFG.cardsPerPack} new cards</div>
  <div class="packwrap" data-a="pack">${packSvg()}</div>
  <button class="openbtn" data-a="pack" ${S.packs<1?'disabled':''}>${S.packs>0?'Open':'Wait for the next pack'}</button>
  <div class="packinfo"><b id="pk">${S.packs} / ${CFG.maxPacks}</b><span id="cd">${S.packs>=CFG.maxPacks?'Packs full':`Next pack in ${fmt(msToNext())}`}</span></div></div>`;
}
const sortCards=l=>l.sort((a,b)=>RANK[b.raresa]-RANK[a.raresa]||b.pop-a.pop);
function albumGrid(){
 const f=F.album,q=f.q.trim().toLowerCase(), n=Object.keys(S.owned).length;
 if(!n) return '<p class="cnt">You do not have any card yet. Open a pack!</p>';
 const list=sortCards(CARDS.filter(c=>own(c.id)&&(!f.cat||c.cat===f.cat)&&(!f.rar||c.raresa===f.rar)&&(!q||c.nom.toLowerCase().includes(q))));
 return `<div class="grid compact">${list.map(c=>cell(c,{sel:true})).join('')||'<p class="cnt">No cards match.</p>'}</div>`;
}
function selBar(){return SEL.on&&SEL.ids.size?`<div class="selbar"><button class="btn red wide" data-a="destroySel">Destroy ${SEL.ids.size} cards (+${selValue()} coins)</button></div>`:'';}
function vAlbum(){
 const f=F.album, n=Object.keys(S.owned).length;
 const act=n?`<button class="btn sm" data-a="selMode">${SEL.on?'Cancel':'Select'}</button>`:'';
 return title('Album',SEL.on?`${SEL.ids.size} selected`:`${n} different cards`,act)+searchBox('q',f.q,'Search by name')+
  `<div class="chips">${chip('All',!f.cat,'data-a="f" data-s="album" data-k="cat" data-v=""')}${CATS.map(c=>chip(c,f.cat===c,`data-a="f" data-s="album" data-k="cat" data-v="${esc(c)}"`)).join('')}</div>`+
  `<div class="chips">${SEL.on?chip('Duplicates',false,'data-a="selDupes"'):''}${RARITIES.map(r=>chip(RLABEL[r],f.rar===r,`data-a="f" data-s="album" data-k="rar" data-v="${r}"`,RCOLOR[r])).join('')}</div>`+
  `<div id="albumGrid">${albumGrid()}</div><div id="selHost">${selBar()}</div>`;
}
function allGrid(){
 const f=F.all,q=f.q.trim().toLowerCase(), st=f.set&&SETS.find(m=>m.id===f.set);
 const list=sortCards(CARDS.filter(c=>(!f.cat||c.cat===f.cat)&&(!f.rar||c.raresa===f.rar)&&(!f.miss||!own(c.id))&&(!st||st.ids.includes(c.id))&&(!q||c.nom.toLowerCase().includes(q))));
 const info=st?`<div class="colinfo"><b>${esc(setName(st))}</b> <span class="cnt">· ${have(st)} of ${st.ids.length}</span>${bar(have(st),st.ids.length)}<span class="cnt">Reward for finishing: ${st.premi} coins (claim it in Missions)</span></div>`:'';
 return info+`<div class="grid compact">${list.map(c=>cell(c,{dim:true})).join('')||'<p class="cnt">No cards match.</p>'}</div>`;
}
function vAll(){
 const f=F.all;
 return title('All cards',`${CARDS.length} cards`)+searchBox('q2',f.q,'Search by name')+
  `<div class="chips">${chip('All',!f.cat,'data-a="f" data-s="all" data-k="cat" data-v=""')}${CATS.map(c=>chip(c,f.cat===c,`data-a="f" data-s="all" data-k="cat" data-v="${esc(c)}"`)).join('')}</div>`+
  `<div class="chips">${chip('Collections: all',!f.set,'data-a="f" data-s="all" data-k="set" data-v=""')}${SETS.map(m=>chip(setName(m),f.set===m.id,`data-a="f" data-s="all" data-k="set" data-v="${esc(m.id)}"`)).join('')}</div>`+
  `<div class="chips">${chip("I'm missing",f.miss,'data-a="miss"')}${RARITIES.map(r=>chip(RLABEL[r],f.rar===r,`data-a="f" data-s="all" data-k="rar" data-v="${r}"`,RCOLOR[r])).join('')}</div>`+
  `<div id="allGrid">${allGrid()}</div>`;
}
function vMis(){
 const row=g=>{const p=Math.min(g.prog(),g.obj),dn=S.claimed[genKey(g)];
  return `<div class="mis"><h3>${esc(g.nom)} ${g.daily?'<span class="cnt">· Daily</span>':''}</h3>${bar(p,g.obj)}<div class="cnt">${p} of ${g.obj}</div>
   ${dn?'<span class="done">Claimed</span>':`<button class="btn pri sm" data-a="claimGen" data-v="${g.id}" ${p>=g.obj?'':'disabled'}>Claim ${g.premi} coins</button>`}</div>`;};
 const colRow=m=>{const h=have(m),n=m.ids.length,dn=S.claimed[m.id];
  return `<div class="mis"><h3>${esc(setName(m))}</h3>${bar(h,n)}<div class="cnt">${h} of ${n}</div>
   ${dn?'<span class="done">Claimed</span>':`<button class="btn pri sm" data-a="claimSet" data-v="${esc(m.id)}" ${h===n?'':'disabled'}>Claim ${m.premi} coins</button>`}</div>`;};
 const pr=m=>{const h=have(m),n=m.ids.length;
  return `<div class="mis"><h3>${esc(m.nom)}</h3><p>${esc(m.desc)}</p><p>${m.ids.map(i=>`<span style="color:${own(i)?'#3DDC97':'#6b7471'}">${esc(BYID[i].nom)}</span>`).join(' + ')}</p>
   ${bar(h,n)}<div class="cnt">${h} of ${n}${S.proto[m.id]?` · done ×${S.proto[m.id]}`:''}</div>
   <button class="btn pri sm" data-a="claimProto" data-v="${esc(m.id)}" ${h===n?'':'disabled'}>Claim ${m.premi} coins (repeatable)</button></div>`;};
 return title('Missions')+GEN.map(row).join('')+`<h2 class="sec">Collections</h2>${SETS.map(colRow).join('')}
  <h2 class="sec">Protocols</h2><p class="cnt">Own all the cards of a protocol to complete it. Cards are not used up. Limit: ${CFG.protoDailyCap} coins per day (today: ${S.dayCoins}).</p>${PROTOS.map(pr).join('')}`;
}
function shopList(){
 if(shopTab==='destroy'){
  const d=sortCards(dupes()); if(!d.length) return '<p class="cnt">You have no duplicate cards.</p>';
  return d.map(c=>`<div class="item"><div class="nm" data-a="open" data-v="${c.id}"><b>${esc(c.nom)}</b><span style="color:${c.color}">${c.rlabel} · ×${own(c.id)}</span></div>
   <button class="btn pri sm" data-a="destroy" data-v="${c.id}">+${val(c)}</button></div>`).join('');
 }
 const q=W.q.trim().toLowerCase(), l=sortCards(CARDS.filter(c=>!own(c.id)&&(!q||c.nom.toLowerCase().includes(q))));
 return l.map(c=>`<div class="item"><div class="nm" data-a="open" data-v="${c.id}"><b>${esc(c.nom)}</b><span style="color:${c.color}">${c.rlabel} · ${c.cat}</span></div>
  <button class="btn pri sm" data-a="craft" data-v="${c.id}" ${S.coins<craftCost(c)?'disabled':''}>Craft (${craftCost(c)})</button></div>`).join('')||'<p class="cnt">Nothing to craft.</p>';
}
function vShop(){
 const seg=`<div class="seg">${chip('Destroy',shopTab==='destroy','data-a="shop" data-v="destroy"')}${chip('Craft',shopTab==='craft','data-a="shop" data-v="craft"')}</div>`;
 const top=shopTab==='destroy'?`<button class="btn pri wide" style="margin-bottom:10px" data-a="destroyAll" ${dupesValue()?'':'disabled'}>Destroy all duplicates (+${dupesValue()} coins)</button>`
  :`<div style="margin-bottom:10px">${searchBox('wq',W.q,'Search the card you want')}</div>`;
 return title('Workshop')+seg+top+`<div id="shopList">${shopList()}</div>`;
}
function vProfile(){
 return title('Profile')+`<h2 class="sec" style="font-size:16px">Statistics</h2><p>Packs opened: ${S.opened}</p><p>Different cards: ${Object.keys(S.owned).length} of ${CARDS.length}</p>
  <p>Cards destroyed: ${S.recycled}</p><p>Cards crafted: ${S.crafted}</p>
  <h2 class="sec" style="font-size:16px">Credits</h2><p class="cnt">Definitions: MeSH (NLM), UniProt (CC BY 4.0) and Wikipedia (CC BY-SA 4.0). Protein structures: RCSB PDB. Images: Wikimedia Commons, with author and licence shown on each card. Article counts: PubMed.</p>
  <h2 class="sec" style="font-size:16px">Save data</h2><p class="cnt">Your game is saved in this browser only. Copy the text to keep a backup, or paste one and press Import.</p>
  <textarea id="sv">${esc(JSON.stringify(S))}</textarea><div class="row" style="display:flex;gap:8px;margin-top:8px"><button class="btn" data-a="import">Import</button><button class="btn" data-a="reset">Reset game</button></div>`;
}
function detailHtml(){
 if(modalId===null) return ''; const c=BYID[modalId], n=own(c.id);
 return `<div class="modal" data-a="closeM"><div class="sheet">${n?c.html:ghostCard(c)}
  <div class="cnt">${n?`Copies: ${n}`:"You don't have this card yet"}</div>
  <div class="acts">${n?`<button class="btn wide" data-a="destroy" data-v="${c.id}">Destroy one copy (+${val(c)} coins)</button>`
   :`<button class="btn pri wide" data-a="craft" data-v="${c.id}" ${S.coins<craftCost(c)?'disabled':''}>Craft (${craftCost(c)} coins)</button>`}
  <button class="btn wide" data-a="closeM" data-v="x">Close</button></div></div></div>`;
}

// ---- obertura del sobre: una carta cada cop, es llisca; la carta es gira en veure-la
function overlayHtml(){
 const o=opening, N=o.cards.length;
 const slides=o.cards.map((p,i)=>{const c=BYID[p.id];
  return `<div class="slide"><div class="flipcard ${c.raresa==='llegendaria'?'leg':''} ${o.viewed[i]?'flipped':''}" data-i="${i}"><div class="fin"><div class="face back"><div>?</div></div>
   <div class="face front"><div class="cell" data-a="open" data-v="${c.id}">${c.html}</div></div></div></div>
   <span class="tag" style="background:${p.nou?'#69F0AE':'#CFCBEA'}">${p.nou?'New':'Repeated'}</span></div>`;}).join('');
 return `<div class="overlay"><div class="cn" id="cn">Card 1 / ${N}</div><div class="pager" id="pager">${slides}</div>
  <div class="nav2"><button class="iconbtn" data-a="pg" data-v="-1" id="pL" disabled>${IC.left}</button><div class="dots" id="dots" style="margin:0">${o.cards.map((_,i)=>`<i class="${i===0?'on':''}"></i>`).join('')}</div><button class="iconbtn" data-a="pg" data-v="1" id="pR">${IC.right}</button></div>
  <button class="btn pri" id="pBtn" data-a="pnext" style="min-width:220px;font-size:18px"></button></div>`;
}
function confetti(){
 const cols=['#FFB300','#7C4DFF','#69F0AE','#FF5252','#40C4FF'], el=document.createElement('div'); el.className='confetti';
 for(let i=0;i<70;i++){const s=4+Math.random()*7;el.insertAdjacentHTML('beforeend',`<i style="left:${Math.random()*100}%;width:${s}px;height:${s}px;background:${cols[i%5]};--dx:${(Math.random()-.5)*80}px;animation-delay:${Math.random()*.6}s"></i>`);}
 document.body.appendChild(el); setTimeout(()=>el.remove(),3800);
}
function updatePager(){
 const o=opening; if(!o) return; const N=o.cards.length, left=o.viewed.filter(v=>!v).length;
 $('#cn').textContent=`Card ${o.cur+1} / ${N}`;
 document.querySelectorAll('#dots i').forEach((d,i)=>d.classList.toggle('on',i===o.cur));
 $('#pL').disabled=o.cur<=0; $('#pR').disabled=o.cur>=N-1;
 $('#pBtn').textContent=left>0?`${left} card${left>1?'s':''} left`:'Continue';
}
function viewCard(i){
 const o=opening; if(!o) return; o.cur=i;
 if(!o.viewed[i]){o.viewed[i]=true; const fc=document.querySelector(`.flipcard[data-i="${i}"]`); fc&&fc.classList.add('flipped');
  if(BYID[o.cards[i].id].raresa==='llegendaria'){setTimeout(()=>{if(opening===o&&o.cur===i){confetti();const ov=$('.overlay');ov&&ov.insertAdjacentHTML('beforeend','<div class="legend">Legendary!</div>');setTimeout(()=>document.querySelectorAll('.legend').forEach(e=>e.remove()),3000);}},1800);}}
 updatePager();
}
function goPage(i){const p=$('#pager'),s=p&&p.children[i]; if(s) p.scrollTo({left:s.offsetLeft-(p.clientWidth-s.offsetWidth)/2,behavior:'smooth'});}
document.addEventListener('scroll',ev=>{const p=ev.target; if(!opening||!p||p.id!=='pager') return;
 const s=p.children[0], i=Math.max(0,Math.min(opening.cards.length-1,Math.round(p.scrollLeft/(s.offsetWidth+16)))); if(i!==opening.cur) viewCard(i);},true);

const TITLES={home:'Home',album:'Album',all:'All',mis:'Missions',shop:'Workshop',profile:'Profile'};
function render(){
 $('#coins').innerHTML=`${coinSvg}<span>${S.coins}</span>`;
 document.querySelectorAll('nav.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.v===view));
 $('#bProfile').classList.toggle('on',view==='profile');
 if(opening){ if(!$('.overlay')){$('#overlayHost').innerHTML=overlayHtml();updatePager();} } else $('#overlayHost').innerHTML='';
 $('#modalHost').innerHTML=detailHtml();
 $('#app').innerHTML=`<div class="msg" id="msg">${esc(msgText)}</div>`+({home:vHome,album:vAlbum,all:vAll,mis:vMis,shop:vShop,profile:vProfile}[view])();
 document.querySelectorAll('nav.tabs button').forEach(b=>{if(view==='profile')b.classList.remove('on');});
}
const ACT={
 pack:startOpen,
 pg:v=>goPage(Math.max(0,Math.min(opening.cards.length-1,opening.cur+ +v))),
 pnext:()=>{const o=opening,i=o.viewed.indexOf(false); if(i>=0) goPage(i); else {opening=null;render();}},
 open:(v,t)=>{ if(SEL.on&&view==='album'&&!opening){const id=+v; SEL.ids.has(id)?SEL.ids.delete(id):SEL.ids.add(id); $('#albumGrid').innerHTML=albumGrid(); $('#selHost').innerHTML=selBar(); document.querySelector('.ttl p').textContent=`${SEL.ids.size} selected`; return;}
  modalId=+v; $('#modalHost').innerHTML=detailHtml();},
 closeM:(v,t,ev)=>{if(v==='x'||ev.target===t){modalId=null;$('#modalHost').innerHTML='';}},
 destroy:v=>destroyOne(+v), destroyAll:destroyDupes, destroySel, craft:v=>craft(+v), shop:v=>{shopTab=v;render();},
 selMode:()=>{SEL.on=!SEL.on;SEL.ids=new Set();render();},
 selDupes:()=>{SEL.ids=new Set(dupes().map(c=>c.id));render();},
 f:(v,t)=>{F[t.dataset.s][t.dataset.k]=v;render();}, miss:()=>{F.all.miss=!F.all.miss;render();},
 claimSet, claimGen, claimProto,
 import:()=>{try{const o=JSON.parse($('#sv').value);if(typeof o.coins!=='number'||typeof o.owned!=='object')throw 0;S=Object.assign(fresh(),o);save();setMsg('Imported.');render();}catch(e){setMsg('That is not a valid backup.');}},
 reset:()=>{if(confirm('Delete all progress?')){S=fresh();save();opening=null;setMsg('Game reset.');render();}}
};
document.addEventListener('click',ev=>{let t=ev.target.closest('[data-a]'); if(!t) return;
 if(t.dataset.a==='closeM'&&t.dataset.v!=='x'&&ev.target!==t) return;
 if(opening&&t.dataset.a==='open'&&!t.closest('.modal')&&!t.closest('.flipcard.flipped')) return;
 const f=ACT[t.dataset.a]; if(f) f(t.dataset.v,t,ev);});
document.addEventListener('input',ev=>{
 if(ev.target.id==='q'){F.album.q=ev.target.value;$('#albumGrid').innerHTML=albumGrid();}
 if(ev.target.id==='q2'){F.all.q=ev.target.value;$('#allGrid').innerHTML=allGrid();}
 if(ev.target.id==='wq'){W.q=ev.target.value;$('#shopList').innerHTML=shopList();}});
document.querySelectorAll('nav.tabs button').forEach(b=>b.onclick=()=>{view=b.dataset.v;modalId=null;SEL.on=false;SEL.ids=new Set();setMsg('');window.scrollTo(0,0);render();});
$('#bProfile').onclick=()=>{view=view==='profile'?'home':'profile';modalId=null;SEL.on=false;SEL.ids=new Set();window.scrollTo(0,0);render();};
render();
setInterval(()=>{const was=S.packs; if(tickPacks()||S.packs!==was){save(); if(view==='home'&&!opening&&modalId===null&&!shaking) render(); return;}
 const e=$('#cd'); if(e&&S.packs<CFG.maxPacks) e.textContent=`Next pack in ${fmt(msToNext())}`;},1000);
