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
 // Sobre de laboratori: làmina fosca blau-verdosa amb segellat dentat, graella de molècules, doble hèlix d'ADN i, al centre,
 // la vista d'un microscopi amb cèl·lules tenyides (una d'elles en divisió). A baix, material de laboratori.
 const w=290,h=500,n=16,st=w/n; let d='M0 8';
 for(let i=0;i<n;i++) d+=` L${st*(i+.5)} 0 L${st*(i+1)} 8`;
 d+=` L${w} ${h-8}`; for(let i=n;i>0;i--) d+=` L${st*(i-.5)} ${h} L${st*(i-1)} ${h-8}`; d+=' Z';
 let hex=''; const R=15;
 for(let r=-1;r<24;r++) for(let c=-1;c<11;c++){const x=c*R*1.732+(r%2?R*.866:0), y=r*R*1.5; let q='';
  for(let k=0;k<6;k++){const a=Math.PI/3*k+Math.PI/6; q+=(k?'L':'M')+(x+R*Math.cos(a)).toFixed(1)+' '+(y+R*Math.sin(a)).toFixed(1);} hex+=q+'Z';}
 const helix=(cx,amp,ph)=>{let a='',b='',rg='';for(let y=34;y<=466;y+=4){const t=y/20+ph,x1=cx+amp*Math.sin(t),x2=cx-amp*Math.sin(t);a+=(y===34?'M':'L')+x1.toFixed(1)+' '+y;b+=(y===34?'M':'L')+x2.toFixed(1)+' '+y;
  if(Math.abs(Math.cos(t))<.12&&y%8===0) rg+=`M${x1.toFixed(1)} ${y}L${x2.toFixed(1)} ${y}`;}
  return `<path d="${a}" stroke="#7ff3d0" stroke-width="3" fill="none" opacity=".35"/><path d="${b}" stroke="#7fc8ff" stroke-width="3" fill="none" opacity=".35"/><path d="${rg}" stroke="#ffffff" stroke-width="1.6" opacity=".22"/>`;};
 const cell=(x,y,r,nr=.5)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="#f7a8d0" opacity=".85" stroke="#d9579a" stroke-width="1.5"/><ellipse cx="${x+r*.08}" cy="${y-r*.05}" rx="${r*nr}" ry="${r*nr*.9}" fill="#5a2a8c"/><circle cx="${x-r*.1}" cy="${y-r*.1}" r="${r*.12}" fill="#c9a2ff"/>`;
 const cells=[[108,196,19],[160,186,23],[205,215,17],[98,248,16],[188,262,20],[126,288,21],[170,300,15],[222,268,12],[132,236,9]].map(c=>cell(...c)).join('');
 const dividing=`<g><ellipse cx="150" cy="248" rx="35" ry="21" fill="#f7a8d0" opacity=".9" stroke="#d9579a" stroke-width="1.6" transform="rotate(-20 150 248)"/>
  <path d="M138 242c-6-4-5-14 2-14 6 0 8 8 3 13zM162 254c6 4 5 14-2 14-6 0-8-8-3-13z" fill="#5a2a8c"/><path d="M142 236l-7-9M146 232l-3-8M158 262l7 9M154 266l3 8" stroke="#3b1a66" stroke-width="2" stroke-linecap="round"/></g>`;
 const tube=(x,col)=>`<g transform="translate(${x} 0)"><rect x="-7" y="402" width="14" height="46" rx="6" fill="#ffffff22" stroke="#bff8ff" stroke-width="2"/><rect x="-5" y="422" width="10" height="24" rx="4" fill="${col}" opacity=".85"/><rect x="-9" y="398" width="18" height="6" rx="3" fill="#bff8ff"/></g>`;
 const flask=`<g transform="translate(145 0)"><path d="M-8 394h16v22l22 36a6 6 0 0 1-5 9h-50a6 6 0 0 1-5-9l22-36z" fill="#ffffff1c" stroke="#ffd54a" stroke-width="2.4" stroke-linejoin="round"/><path d="M-22 438h44l12 20h-68z" fill="#3DDC97" opacity=".8"/><circle cx="-6" cy="448" r="2.4" fill="#fff" opacity=".8"/><circle cx="8" cy="443" r="1.8" fill="#fff" opacity=".8"/></g>`;
 return `<svg viewBox="0 0 290 500"><defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#082a3a"/><stop offset=".5" stop-color="#0e6b6b"/><stop offset="1" stop-color="#051a26"/></linearGradient>
  <radialGradient id="sg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffe6f2"/><stop offset=".75" stop-color="#f3b4d6"/><stop offset="1" stop-color="#b4579a"/></radialGradient>
  <linearGradient id="sh" x1="0" y1="0" x2="1" y2="1"><stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset=".65" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="pcl"><path d="${d}"/></clipPath><clipPath id="vw"><circle cx="145" cy="228" r="82"/></clipPath></defs>
  <path d="${d}" fill="url(#pg)"/><g clip-path="url(#pcl)">
  <path d="${hex}" fill="none" stroke="#9ff7e6" stroke-width=".8" opacity=".10"/>
  ${helix(40,14,0)}${helix(250,14,3.1)}
  <path d="M0 22H290M0 30H290M0 470H290M0 478H290" stroke="#ffffff" stroke-opacity=".12" stroke-width="2"/>
  <text x="145" y="74" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="800" font-size="34" letter-spacing="5" fill="#fff">BIO</text>
  <text x="145" y="98" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700" font-size="13" letter-spacing="6" fill="#3DDC97">CARDS</text>
  <circle cx="145" cy="228" r="94" fill="#031017" opacity=".55"/><circle cx="145" cy="228" r="88" fill="url(#sg)"/>
  <g clip-path="url(#vw)">${cells}${dividing}
   <g fill="#7a3ca8" opacity=".5"><circle cx="85" cy="215" r="3"/><circle cx="214" cy="190" r="2.5"/><circle cx="196" cy="300" r="3"/><circle cx="108" cy="318" r="2.5"/><circle cx="228" cy="240" r="2"/></g>
   <circle cx="145" cy="228" r="82" fill="none" stroke="#6b1f5e" stroke-opacity=".45" stroke-width="14"/></g>
  <circle cx="145" cy="228" r="88" fill="none" stroke="#cffcff" stroke-width="5"/><circle cx="145" cy="228" r="94" fill="none" stroke="#ffd54a" stroke-width="2.5"/>
  <path d="M60 228h12M218 228h12M145 143v12M145 301v12" stroke="#fff" stroke-width="2" opacity=".6"/>
  <path d="M110 330h40" stroke="#fff" stroke-width="3"/><text x="130" y="344" text-anchor="middle" font-family="system-ui,sans-serif" font-size="9" fill="#fff" opacity=".85">50 µm</text>
  ${tube(85,'#ff7ab8')}${flask}${tube(205,'#ffd54a')}
  <text x="145" y="488" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700" font-size="9" letter-spacing="3" fill="#bff8ff" opacity=".8">RESEARCH PACK</text>
  <rect width="290" height="500" fill="url(#sh)"/></g></svg>`;
}
function ghostCard(c){return `<article class="carta ghost" data-r="${c.raresa}" style="--r:${c.color}"><header><h2>${esc(c.nom)}</h2><span class="rb">${c.rlabel}</span></header>
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
