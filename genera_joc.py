"""Genera web/joc.html: el joc (sobres, col·lecció, monedes, missions) en una sola pàgina estàtica.
L'estat del jugador es guarda al navegador (localStorage). Ús: python genera_joc.py"""
import json, sqlite3
from pathlib import Path

import genera_web as gw

ARREL = Path(__file__).parent

# Col·leccions: etiqueta de la BD -> nom que es mostra
NOMS_COLECCIO = {"cancer": "Cancer", "oncogenes": "Oncogenes", "suppressors": "Tumor suppressors",
                 "nobel": "Nobel laureates", "cell-lines": "Cell lines", "immunotherapy": "Immunotherapy targets"}

# Protocols: es completen tenint (no gastant) totes les cartes. Fets a mà; cal revisar-los amb criteri científic.
PROTOCOLS = [
    ("Run a gel", "Separate DNA fragments by size.", ["Gel electrophoresis", "Agarose", "Ethidium bromide", "Pipette"]),
    ("Build a PCR", "Amplify a DNA region.", ["PCR", "Thermal cycler", "Pipette", "Gel electrophoresis"]),
    ("Grow cells", "Keep a cell line alive in culture.", ["Cell culture", "Biosafety cabinet", "Trypsin", "Hemocytometer", "HeLa"]),
    ("Find a protein", "Detect one protein in a lysate.", ["Western blot", "SDS", "Gel electrophoresis", "PBS"]),
    ("Image the cell", "Look at stained cells.", ["Microscope", "Fluorescence microscopy", "Immunofluorescence", "Formaldehyde"]),
    ("Sort cells", "Count and sort cells by markers.", ["Flow cytometry", "Hemocytometer", "Cell culture"]),
]

# Mateixa economia que el joc d'esports (android/.../Motor.kt): destruir 5/15/50/200/1000, fabricar x5,
# premi de col·lecció = meitat de la suma dels valors + 10.
VALOR_RECICLAR = {"comuna": 5, "poc_comuna": 15, "rara": 50, "epica": 200, "llegendaria": 1000}

def construeix_dades():
    con = sqlite3.connect(ARREL / "db" / "cartes.sqlite")
    con.row_factory = sqlite3.Row
    cartes, per_nom = [], {}
    for c in con.execute("SELECT * FROM carta ORDER BY categoria, nom"):
        raresa = c["raresa"] or "comuna"
        meta = {"id": c["id"], "nom": c["nom"], "cat": gw.ETIQ_CAT[c["categoria"]], "raresa": raresa,
                "rlabel": gw.ETIQ_RARESA[raresa], "color": gw.COLORS[raresa],
                "sets": [x for x in (c["coleccions"] or "").split(",") if x],
                "html": gw.carta_html(c), "icona": gw.ICONES[c["categoria"]]}
        cartes.append(meta)
        per_nom[c["nom"]] = c["id"]
    by_id = {m["id"]: m["raresa"] for m in cartes}
    sets = {}
    for m in cartes:
        for s in m["sets"]:
            sets.setdefault(s, []).append(m["id"])
    misions = []
    for clau, ids in sets.items():
        if len(ids) >= 2:
            misions.append({"id": f"set:{clau}", "tipus": "col·lecció", "nom": f"Collect all: {NOMS_COLECCIO.get(clau, clau)}",
                            "desc": f"Own every card in this collection ({len(ids)} cards). One-time badge.",
                            "ids": ids, "premi": sum(VALOR_RECICLAR[by_id[i]] for i in ids) // 2 + 10})
    for nom, desc, noms in PROTOCOLS:
        faltes = [n for n in noms if n not in per_nom]
        assert not faltes, f"Protocol «{nom}»: no existeixen les cartes {faltes}"
        misions.append({"id": f"proto:{nom}", "tipus": "protocol", "nom": nom, "desc": desc,
                        "ids": [per_nom[n] for n in noms], "premi": 25})
    return cartes, misions

CSS_JOC = """
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html{touch-action:manipulation}
body{padding-bottom:calc(70px + env(safe-area-inset-bottom))}
header.top{position:sticky;top:0;z-index:5;background:#10141bf2;display:flex;align-items:center;padding:10px 16px;
padding-top:calc(10px + env(safe-area-inset-top));border-bottom:1px solid #263041}
header.top h1{padding:0;font-size:18px}.coins{margin-left:auto;font-weight:700;color:#f0c34a;font-size:16px}
nav.tabs{position:fixed;bottom:0;left:0;right:0;z-index:6;display:flex;background:#10141b;border-top:1px solid #263041;
padding-bottom:env(safe-area-inset-bottom)}
nav.tabs button{flex:1;background:none;border:0;color:#9aa6b6;font:inherit;font-size:12px;padding:8px 0;min-height:56px;
display:flex;flex-direction:column;align-items:center;gap:2px;cursor:pointer}
nav.tabs button svg{width:24px;height:24px}nav.tabs button.on{color:#4a9bf0}
.btn{background:#1f2a3a;color:#e8ecf2;border:1px solid #33425a;border-radius:10px;padding:12px 14px;min-height:46px;
cursor:pointer;font:inherit;font-size:15px}.btn.pri{background:#2f7fd1;border-color:#2f7fd1}.btn:disabled{opacity:.4;cursor:not-allowed}
.btn.wide{width:100%}
main{padding:12px;max-width:1100px;margin:auto}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0 14px}
.row.col .btn,.row.col select{flex:1 1 100%}
select{background:#1f2a3a;color:#e8ecf2;border:1px solid #33425a;border-radius:10px;padding:12px;font:inherit;min-height:46px;flex:1 1 45%}
.grid.compact{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;padding:0}
.cell{position:relative;cursor:pointer;min-width:0}.cell .carta{height:100%;padding:6px;gap:4px;border-width:2px;border-radius:12px}
.compact h2{font-size:14px;overflow-wrap:anywhere}.compact header span{font-size:10px}.compact .img{height:96px}
.compact .def{font-size:12px;-webkit-line-clamp:3}.compact .font,.compact .stats,.compact .cat{display:none}
.compact .cred{font-size:8px}.compact .sense-img svg{width:56px;height:56px}
.qty{position:absolute;top:-6px;right:-4px;background:#2f7fd1;color:#fff;border-radius:11px;font-size:12px;font-weight:700;padding:1px 7px;z-index:2}
.nou{position:absolute;top:-6px;left:-4px;background:#e0a21a;color:#111;border-radius:6px;font-size:11px;font-weight:700;padding:1px 6px;z-index:2}
.cell.glow .carta{box-shadow:0 0 16px var(--r)}.ghost{opacity:.45;filter:grayscale(.8)}
.reveal .cell{animation:in .45s both}@keyframes in{from{opacity:0;transform:translateY(14px) scale(.96)}}
.cnt{font-size:12px;color:#9aa6b6}
.mis{background:#1a212c;border:1px solid #263041;border-radius:12px;padding:12px;margin-bottom:10px;display:flex;flex-direction:column;gap:10px}
.mis h3{margin:0;font-size:16px}.mis p{margin:2px 0;color:#9aa6b6;font-size:13px;line-height:1.5}
.bar{height:6px;background:#0c1016;border-radius:3px;overflow:hidden;margin-top:6px}.bar i{display:block;height:100%;background:#3f9b5c}
.done{color:#3f9b5c;font-weight:700}textarea{width:100%;height:110px;background:#0c1016;color:#e8ecf2;border:1px solid #33425a;border-radius:10px;font-size:12px}
.msg{min-height:20px;color:#f0c34a;margin:4px 0 8px;font-size:14px}h2.sec{margin:18px 0 6px;font-size:18px}
.modal{position:fixed;inset:0;z-index:20;background:#000c;display:flex;align-items:flex-end;justify-content:center}
.sheet{background:#10141b;width:100%;max-width:460px;max-height:92vh;overflow:auto;border-radius:16px 16px 0 0;padding:14px;
padding-bottom:calc(14px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:10px}
.sheet .img{height:200px}.sheet .def{display:block;-webkit-line-clamp:unset;font-size:14px;max-height:170px;overflow:auto}
.acts{position:sticky;bottom:-14px;background:#10141b;padding:8px 0;display:flex;flex-direction:column;gap:8px}.sheet .carta{border-width:3px}
@media(min-width:640px){.grid.compact{grid-template-columns:repeat(auto-fill,minmax(190px,1fr))}.modal{align-items:center}.sheet{border-radius:16px}
.mis{flex-direction:row;align-items:center}.mis .info{flex:1}.btn.wide{width:auto}}
"""

JS = r"""
const CFG={startCoins:100,startPacks:3,cardsPerPack:5,maxPacks:3,msPerPack:10*60*1000,protoDailyCap:150,craftMult:5,
 weights:{comuna:60,poc_comuna:25,rara:10,epica:4,llegendaria:1},
 recycle:{comuna:5,poc_comuna:15,rara:50,epica:200,llegendaria:1000}};
const D=JSON.parse(document.getElementById('dades').textContent);
const CARDS=D.cartes, MIS=D.misions, BYID=Object.fromEntries(CARDS.map(c=>[c.id,c]));
const RARE_UP=new Set(['rara','epica','llegendaria']);
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
let msgText='', view='packs', lastPack=[];
const setMsg=t=>{msgText=t;const m=$('#msg');if(m)m.textContent=t;};
const own=id=>S.owned[id]||0, craftCost=c=>CFG.recycle[c.raresa]*CFG.craftMult;

// Sobres amb temps (com al joc d'esports): +1 cada 10 min, màxim 3 guardats; plens, el rellotge no avança.
function tickPacks(now=Date.now()){
 const before=S.packs;
 if(S.packs>=CFG.maxPacks){S.packs=CFG.maxPacks;S.packTick=now;return false;}
 const gen=Math.max(0,Math.floor((now-S.packTick)/CFG.msPerPack)); if(!gen) return false;
 const nous=S.packs+gen;
 if(nous>=CFG.maxPacks){S.packs=CFG.maxPacks;S.packTick=now;} else {S.packs=nous;S.packTick+=gen*CFG.msPerPack;}
 return S.packs!==before;
}
const msToNext=()=>S.packs>=CFG.maxPacks?0:CFG.msPerPack-Math.min(CFG.msPerPack,Math.max(0,Date.now()-S.packTick));
const fmt=ms=>{const t=Math.ceil(ms/1000);return `${Math.floor(t/60)}:${String(t%60).padStart(2,'0')}`;};

function rollRarity(){
 const have=new Set(CARDS.map(c=>c.raresa)); let tot=0;
 for(const r in CFG.weights) if(have.has(r)) tot+=CFG.weights[r];
 let x=Math.random()*tot;
 for(const r in CFG.weights){ if(!have.has(r)) continue; if((x-=CFG.weights[r])<0) return r; }
 return 'comuna';
}
function openPack(){
 newDay(); tickPacks(); if(S.packs<=0) return setMsg('No packs ready. The next one arrives soon.');
 if(S.packs>=CFG.maxPacks) S.packTick=Date.now(); S.packs--;
 lastPack=[];
 for(let i=0;i<CFG.cardsPerPack;i++){
  const pool=CARDS.filter(c=>c.raresa===rollRarity());
  const c=pool[Math.floor(Math.random()*pool.length)];
  lastPack.push({id:c.id,nou:own(c.id)===0 && !lastPack.some(p=>p.id===c.id)}); S.owned[c.id]=own(c.id)+1;
 }
 S.opened++; S.openedToday++; save(); setMsg(''); render();
}
function recycle(id){
 const c=BYID[id], v=CFG.recycle[c.raresa], last=own(id)===1;
 const openSets=last?MIS.filter(m=>m.tipus!=='protocol'&&m.ids.includes(id)&&!S.claimed[m.id]):[];
 let t=`Recycle one copy of ${c.nom} for ${v} coins?`;
 if(last) t+=`\n\nIt is your LAST copy. Crafting it again costs ${craftCost(c)} coins.`;
 if(openSets.length) t+=`\n\nIt is part of a collection you have not finished: ${openSets.map(m=>m.nom.replace('Collect all: ','')).join(', ')}.`;
 if(!confirm(t)) return; S.owned[id]--; if(!S.owned[id]) delete S.owned[id]; S.coins+=v; S.recycled++; save(); setMsg(`+${v} coins.`); render();
}
function craft(id){
 const c=BYID[id], p=craftCost(c); if(S.coins<p) return setMsg('Not enough coins.');
 if(!confirm(`Craft ${c.nom} for ${p} coins?`)) return; S.coins-=p; S.owned[id]=1; S.crafted++; save(); setMsg(`Crafted ${c.nom}.`); render();
}
const have=m=>m.ids.filter(i=>own(i)>0).length;
const setsDone=()=>MIS.filter(m=>m.tipus!=='protocol'&&have(m)===m.ids.length).length;
const rareOwned=()=>CARDS.filter(c=>own(c.id)&&RARE_UP.has(c.raresa)).length;
const GEN=[
 {id:'d_packs3',nom:'Open 3 packs today',obj:3,premi:40,daily:true,prog:()=>S.openedToday},
 {id:'packs10',nom:'Open 10 packs',obj:10,premi:60,prog:()=>S.opened},
 {id:'packs50',nom:'Open 50 packs',obj:50,premi:250,prog:()=>S.opened},
 {id:'diff10',nom:'Own 10 different cards',obj:10,premi:50,prog:()=>Object.keys(S.owned).length},
 {id:'diff50',nom:'Own 50 different cards',obj:50,premi:300,prog:()=>Object.keys(S.owned).length},
 {id:'rare1',nom:'Own 1 rare or better card',obj:1,premi:60,prog:rareOwned},
 {id:'rare5',nom:'Own 5 rare or better cards',obj:5,premi:250,prog:rareOwned},
 {id:'rec5',nom:'Recycle 5 cards',obj:5,premi:30,prog:()=>S.recycled},
 {id:'craft1',nom:'Craft a card',obj:1,premi:40,prog:()=>S.crafted},
 {id:'sets1',nom:'Complete 1 collection',obj:1,premi:100,prog:setsDone},
 {id:'sets5',nom:'Complete 5 collections',obj:5,premi:500,prog:setsDone}];
const genKey=g=>g.daily?`${g.id}:${today()}`:g.id;
function claimGen(id){
 const g=GEN.find(x=>x.id===id); if(!g||S.claimed[genKey(g)]||g.prog()<g.obj) return;
 S.claimed[genKey(g)]=true; S.coins+=g.premi; save(); setMsg(`+${g.premi} coins: ${g.nom}.`); render();
}
function claim(mid){
 const m=MIS.find(x=>x.id===mid); if(have(m)<m.ids.length) return;
 if(m.tipus==='protocol'){
  newDay(); if(S.dayCoins+m.premi>CFG.protoDailyCap) return setMsg(`Daily protocol limit reached (${CFG.protoDailyCap} coins/day).`);
  S.dayCoins+=m.premi; S.proto[mid]=(S.proto[mid]||0)+1;
 } else { if(S.claimed[mid]) return; S.claimed[mid]=true; }
 S.coins+=m.premi; save(); setMsg(`+${m.premi} coins: ${m.nom}.`); render();
}
function ghostCard(c){return `<article class="carta ghost" style="--r:${c.color}"><header><h2>${esc(c.nom)}</h2><span>${c.rlabel}</span></header>
  <div class="img"><div class="sense-img"><svg viewBox="0 0 100 100">${c.icona}</svg><span>${c.cat}</span></div></div></article>`;}
function cell(c,nou){
 const n=own(c.id);
 return `<div class="cell ${nou?'glow':''}" data-open="${c.id}">${nou?'<span class="nou">NEW</span>':''}${n>1?`<span class="qty">×${n}</span>`:''}${n?c.html:ghostCard(c)}</div>`;
}
let modalId=null;
function modalHtml(){
 if(modalId===null) return ''; const c=BYID[modalId], n=own(c.id);
 return `<div class="modal" id="mod"><div class="sheet">${n?c.html:ghostCard(c)}
  <div class="cnt">${n?`You own ×${n}`:'You do not own this card'}</div>
  <div class="acts">${n?`<button class="btn wide" data-rec="${c.id}">Recycle one · +${CFG.recycle[c.raresa]} coins</button>`:''}
  ${n?'':`<button class="btn pri wide" data-craft="${c.id}" ${S.coins<craftCost(c)?'disabled':''}>Craft · ${craftCost(c)} coins</button>`}
  <button class="btn wide" id="bClose">Close</button></div></div></div>`;
}
function vPacks(){
 tickPacks();
 let h=`<div class="row col"><button class="btn pri" id="bPack" ${S.packs<1?'disabled':''}>Open a pack (${S.packs} / ${CFG.maxPacks} ready)</button>
  <span class="cnt" id="cd">${S.packs>=CFG.maxPacks?'Packs full: open one so the timer restarts.':`Next pack in ${fmt(msToNext())}`}</span>
  <span class="cnt">${CFG.cardsPerPack} cards per pack · packs opened: ${S.opened}</span></div>`;
 if(lastPack.length) h+=`<div class="grid compact reveal">${lastPack.map((p,i)=>`<div style="animation-delay:${i*.25}s">${cell(BYID[p.id],p.nou)}</div>`).join('')}</div>`;
 else h+=`<p class="cnt">Open a pack to get cards. Tap a card to see it in full or to recycle it for coins.</p>`;
 return h;
}
function vColl(){
 const f=window.F||(window.F={cat:'',st:'all',set:''});
 const cats=[...new Set(CARDS.map(c=>c.cat))].sort(), sets=[...new Set(CARDS.flatMap(c=>c.sets))].sort();
 let list=CARDS.filter(c=>(!f.cat||c.cat===f.cat)&&(!f.set||c.sets.includes(f.set))&&(f.st==='all'||(f.st==='owned')===(own(c.id)>0)));
 const total=Object.keys(S.owned).length;
 return `<div class="row"><b style="flex:1 1 100%">${total} / ${CARDS.length} cards</b>
  <select id="fCat"><option value="">All categories</option>${cats.map(x=>`<option ${f.cat===x?'selected':''}>${esc(x)}</option>`).join('')}</select>
  <select id="fSet"><option value="">All collections</option>${sets.map(x=>`<option value="${esc(x)}" ${f.set===x?'selected':''}>${esc(D.nomsSet[x]||x)}</option>`).join('')}</select>
  <select id="fSt">${[['all','All'],['owned','Owned'],['missing','Missing']].map(([v,l])=>`<option value="${v}" ${f.st===v?'selected':''}>${l}</option>`).join('')}</select></div>
  <div class="grid compact">${list.map(c=>cell(c,false)).join('')||'<p class="cnt">No cards match.</p>'}</div>`;
}
function vMis(){
 const row=m=>{const h=have(m),n=m.ids.length,ok=h===n,once=m.tipus!=='protocol',dn=once&&S.claimed[m.id];
  return `<div class="mis"><div class="info"><h3>${esc(m.nom)} <span class="cnt">· ${m.tipus}</span></h3><p>${esc(m.desc)}</p>
   <p>${m.ids.map(i=>`<span style="color:${own(i)?'#3f9b5c':'#6b7686'}">${esc(BYID[i].nom)}</span>`).join(' + ')}</p>
   <div class="bar"><i style="width:${100*h/n}%"></i></div></div>
   ${dn?'<span class="done">★ Badge earned</span>':`<button class="btn pri" data-claim="${esc(m.id)}" ${ok?'':'disabled'}>Claim +${m.premi}${once?'':' (repeatable)'}</button>`}
   ${!once&&S.proto[m.id]?`<span class="cnt">done ×${S.proto[m.id]}</span>`:''}</div>`;};
 const genRow=g=>{const p=Math.min(g.prog(),g.obj),dn=S.claimed[genKey(g)];
  return `<div class="mis"><div class="info"><h3>${esc(g.nom)} <span class="cnt">· ${g.daily?'daily':'goal'}</span></h3><div class="bar"><i style="width:${100*p/g.obj}%"></i></div><p>${p} / ${g.obj}</p></div>
   ${dn?'<span class="done">✓ Claimed</span>':`<button class="btn pri" data-gen="${g.id}" ${p>=g.obj?'':'disabled'}>Claim +${g.premi}</button>`}</div>`;};
 return `<h2 class="sec">Goals</h2>${GEN.map(genRow).join('')}<h2 class="sec">Protocols</h2><p class="cnt">Own all the cards to complete a protocol. Cards are not consumed. Daily limit: ${CFG.protoDailyCap} coins (used today: ${S.dayCoins}).</p>
  ${MIS.filter(m=>m.tipus==='protocol').map(row).join('')}<h2 class="sec">Collections</h2>${MIS.filter(m=>m.tipus!=='protocol').map(row).join('')}`;
}
function vSave(){
 return `<h2 class="sec">Save data</h2><p class="cnt">Your progress lives in this browser only. Copy the text below to back it up, or paste a backup and press Import.</p>
  <textarea id="sv">${esc(JSON.stringify(S))}</textarea><div class="row"><button class="btn" id="bImp">Import</button><button class="btn" id="bRes">Reset game</button></div>`;
}
function render(){
 $('#coins').textContent=`● ${S.coins} coins`;
 document.querySelectorAll('nav.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.v===view));
 document.querySelector('#modalHost').innerHTML=modalHtml();
 $('#app').innerHTML=`<div class="msg" id="msg">${esc(msgText)}</div>`+({packs:vPacks,coll:vColl,mis:vMis,save:vSave}[view])();
 const on=(s,f)=>{const e=$(s);if(e)e.onclick=f;};
 on('#bPack',openPack);
 document.querySelectorAll('[data-open]').forEach(e=>e.onclick=()=>{modalId=+e.dataset.open;render();});
 on('#bClose',()=>{modalId=null;render();}); const mo=$('#mod'); if(mo) mo.onclick=ev=>{if(ev.target===mo){modalId=null;render();}};
 document.querySelectorAll('[data-rec]').forEach(b=>b.onclick=()=>recycle(+b.dataset.rec));
 document.querySelectorAll('[data-craft]').forEach(b=>b.onclick=()=>craft(+b.dataset.craft));
 document.querySelectorAll('[data-gen]').forEach(b=>b.onclick=()=>claimGen(b.dataset.gen));
 document.querySelectorAll('[data-claim]').forEach(b=>b.onclick=()=>claim(b.dataset.claim));
 [['#fCat','cat'],['#fSet','set'],['#fSt','st']].forEach(([s,k])=>{const e=$(s);if(e)e.onchange=()=>{window.F[k]=e.value;render();};});
 on('#bImp',()=>{try{const o=JSON.parse($('#sv').value);if(typeof o.coins!=='number'||typeof o.owned!=='object')throw 0;S=Object.assign(fresh(),o);save();setMsg('Imported.');render();}catch(e){setMsg('That is not a valid backup.');}});
 on('#bRes',()=>{if(confirm('Delete all progress?')){S=fresh();save();lastPack=[];setMsg('Game reset.');render();}});
}
document.querySelectorAll('nav.tabs button').forEach(b=>b.onclick=()=>{view=b.dataset.v;modalId=null;setMsg('');window.scrollTo(0,0);render();});
render();
setInterval(()=>{const was=S.packs; if(tickPacks()||S.packs!==was){save(); if(view==='packs'&&modalId===null) render(); return;}
 const e=$('#cd'); if(e&&S.packs<CFG.maxPacks) e.textContent=`Next pack in ${fmt(msToNext())}`;},1000);
"""

IC = {'packs': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16"/></svg>', 'coll': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/></svg>', 'mis': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l2.6 5.6 6 .8-4.4 4.2 1.1 6L12 16.8 6.7 19.6l1.1-6L3.4 9.4l6-.8z"/></svg>', 'save': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3h11l3 3v15H5z"/><path d="M8 3v6h7V3M8 21v-7h8v7"/></svg>'}

def main():
    cartes, misions = construeix_dades()
    dades = json.dumps({"cartes": cartes, "misions": misions, "nomsSet": NOMS_COLECCIO}, ensure_ascii=False).replace("</", "<\\/")
    pagina = (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#10141b"><meta name="apple-mobile-web-app-capable" content="yes">'
              f'<title>BIO Cards</title><style>{gw.CSS}{CSS_JOC}</style>'
              f'<header class="top"><h1>BIO Cards</h1><span class="coins" id="coins"></span></header>'
              f'<nav class="tabs"><button data-v="packs">{IC["packs"]}Packs</button><button data-v="coll">{IC["coll"]}Cards</button>'
              f'<button data-v="mis">{IC["mis"]}Missions</button><button data-v="save">{IC["save"]}Save</button></nav><div id="modalHost"></div>'
              f'<main id="app"></main><script id="dades" type="application/json">{dades}</script><script>{JS}</script></html>')
    (ARREL / "web").mkdir(exist_ok=True)
    (ARREL / "web" / "joc.html").write_text(pagina, encoding="utf-8")
    (ARREL / "docs").mkdir(exist_ok=True)
    (ARREL / "docs" / "index.html").write_text(pagina, encoding="utf-8")  # per publicar-ho amb GitHub Pages
    print(f"web/joc.html generat: {len(cartes)} cartes, {len(misions)} missions")

if __name__ == "__main__":
    main()
