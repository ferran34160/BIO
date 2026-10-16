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
    sets = {}
    for m in cartes:
        for s in m["sets"]:
            sets.setdefault(s, []).append(m["id"])
    misions = []
    for clau, ids in sets.items():
        if len(ids) >= 2:
            misions.append({"id": f"set:{clau}", "tipus": "col·lecció", "nom": f"Collect all: {NOMS_COLECCIO.get(clau, clau)}",
                            "desc": f"Own every card in this collection ({len(ids)} cards). One-time badge.",
                            "ids": ids, "premi": 15 * len(ids)})
    for nom, desc, noms in PROTOCOLS:
        faltes = [n for n in noms if n not in per_nom]
        assert not faltes, f"Protocol «{nom}»: no existeixen les cartes {faltes}"
        misions.append({"id": f"proto:{nom}", "tipus": "protocol", "nom": nom, "desc": desc,
                        "ids": [per_nom[n] for n in noms], "premi": 25})
    return cartes, misions

CSS_JOC = """
header.top{position:sticky;top:0;z-index:5;background:#10141bee;backdrop-filter:blur(6px);display:flex;gap:12px;
align-items:center;flex-wrap:wrap;padding:10px 16px;border-bottom:1px solid #263041}
header.top h1{padding:0;font-size:20px}.coins{margin-left:auto;font-weight:700;color:#f0c34a}
nav button,.btn{background:#1f2a3a;color:#e8ecf2;border:1px solid #33425a;border-radius:8px;padding:8px 12px;cursor:pointer;font:inherit}
nav button.on,.btn.pri{background:#2f7fd1;border-color:#2f7fd1}.btn:disabled{opacity:.4;cursor:not-allowed}
main{padding:16px;max-width:1200px;margin:auto}.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:8px 0 16px}
select{background:#1f2a3a;color:#e8ecf2;border:1px solid #33425a;border-radius:8px;padding:8px}
.slot{display:flex;flex-direction:column;gap:6px}.slot .carta{height:100%}.slot.new .carta{box-shadow:0 0 18px var(--r)}
.badge{align-self:flex-start;font-size:11px;font-weight:700;background:#e0a21a;color:#111;border-radius:6px;padding:1px 6px}
.cnt{font-size:12px;color:#9aa6b6}.ghost{opacity:.45;filter:grayscale(.8)}.ghost .sense-img span{font-size:12px}
.pack{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}.reveal .slot{animation:in .5s both}
@keyframes in{from{opacity:0;transform:translateY(14px) scale(.96)}}
.mis{background:#1a212c;border:1px solid #263041;border-radius:12px;padding:12px;margin-bottom:10px;display:flex;gap:12px;
align-items:center;flex-wrap:wrap}.mis h3{margin:0;font-size:16px}.mis p{margin:2px 0;color:#9aa6b6;font-size:13px}.mis .info{flex:1;min-width:220px}
.bar{height:6px;background:#0c1016;border-radius:3px;overflow:hidden}.bar i{display:block;height:100%;background:#3f9b5c}
.done{color:#3f9b5c;font-weight:700}textarea{width:100%;height:90px;background:#0c1016;color:#e8ecf2;border:1px solid #33425a;border-radius:8px}
.msg{min-height:22px;color:#f0c34a;margin:8px 0}h2.sec{margin:20px 0 8px;font-size:18px}
"""

JS = r"""
const CFG={packCost:50,cardsPerPack:5,startCoins:150,dailyFree:1,protoDailyCap:150,craftMult:4,
 weights:{comuna:55,poc_comuna:25,rara:12,epica:6,llegendaria:2},
 recycle:{comuna:5,poc_comuna:10,rara:25,epica:60,llegendaria:150}};
const D=JSON.parse(document.getElementById('dades').textContent);
const CARDS=D.cartes, MIS=D.misions, BYID=Object.fromEntries(CARDS.map(c=>[c.id,c]));
const KEY='bio-cards-save-v1', today=()=>new Date().toISOString().slice(0,10);
let S, memSave=null;
const fresh=()=>({coins:CFG.startCoins,owned:{},claimed:{},proto:{},lastFree:'',day:today(),dayCoins:0,opened:0});
function load(){try{const r=localStorage.getItem(KEY);if(r)return Object.assign(fresh(),JSON.parse(r));}catch(e){}
 return memSave?JSON.parse(memSave):fresh();}
function save(){const j=JSON.stringify(S);memSave=j;try{localStorage.setItem(KEY,j);}catch(e){}}
S=load(); if(S.day!==today()){S.day=today();S.dayCoins=0;}
const $=s=>document.querySelector(s), esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let msgText='', view='packs', lastPack=[];
const setMsg=t=>{msgText=t;const m=$('#msg');if(m)m.textContent=t;};
const own=id=>S.owned[id]||0, craftCost=c=>CFG.recycle[c.raresa]*CFG.craftMult;

function rollRarity(){
 const have=new Set(CARDS.map(c=>c.raresa)); let tot=0;
 for(const r in CFG.weights) if(have.has(r)) tot+=CFG.weights[r];
 let x=Math.random()*tot;
 for(const r in CFG.weights){ if(!have.has(r)) continue; if((x-=CFG.weights[r])<0) return r; }
 return 'comuna';
}
function openPack(free){
 if(free){ if(S.lastFree===today()) return setMsg('Your free pack for today was already opened.'); S.lastFree=today(); }
 else { if(S.coins<CFG.packCost) return setMsg('Not enough coins.'); S.coins-=CFG.packCost; }
 lastPack=[];
 for(let i=0;i<CFG.cardsPerPack;i++){
  const pool=CARDS.filter(c=>c.raresa===rollRarity());
  const c=pool[Math.floor(Math.random()*pool.length)];
  lastPack.push({id:c.id,nou:own(c.id)===0 && !lastPack.some(p=>p.id===c.id)}); S.owned[c.id]=own(c.id)+1;
 }
 S.opened++; save(); setMsg(''); render();
}
function recycle(id){
 const c=BYID[id], v=CFG.recycle[c.raresa], last=own(id)===1;
 const t=`Recycle one copy of ${c.nom} for ${v} coins?`+(last?`\n\nIt is your LAST copy. Crafting it again costs ${craftCost(c)} coins.`:'');
 if(!confirm(t)) return; S.owned[id]--; if(!S.owned[id]) delete S.owned[id]; S.coins+=v; save(); setMsg(`+${v} coins.`); render();
}
function craft(id){
 const c=BYID[id], p=craftCost(c); if(S.coins<p) return setMsg('Not enough coins.');
 if(!confirm(`Craft ${c.nom} for ${p} coins?`)) return; S.coins-=p; S.owned[id]=1; save(); setMsg(`Crafted ${c.nom}.`); render();
}
const have=m=>m.ids.filter(i=>own(i)>0).length;
function claim(mid){
 const m=MIS.find(x=>x.id===mid); if(have(m)<m.ids.length) return;
 if(m.tipus==='protocol'){
  if(S.dayCoins+m.premi>CFG.protoDailyCap) return setMsg(`Daily protocol limit reached (${CFG.protoDailyCap} coins/day).`);
  S.dayCoins+=m.premi; S.proto[mid]=(S.proto[mid]||0)+1;
 } else { if(S.claimed[mid]) return; S.claimed[mid]=true; }
 S.coins+=m.premi; save(); setMsg(`+${m.premi} coins: ${m.nom}.`); render();
}
function slot(c,opts={}){
 const n=own(c.id);
 if(!n && opts.ghost) return `<div class="slot"><article class="carta ghost" style="--r:${c.color}"><header><h2>${esc(c.nom)}</h2><span>${c.rlabel}</span></header>
  <div class="img"><div class="sense-img"><svg viewBox="0 0 100 100">${c.icona}</svg><span>${c.cat}</span></div></div></article>
  <button class="btn" data-craft="${c.id}" ${S.coins<craftCost(c)?'disabled':''}>Craft · ${craftCost(c)} coins</button></div>`;
 return `<div class="slot ${opts.nou?'new':''}">${opts.nou?'<span class="badge">NEW</span>':''}${c.html}
  <div class="cnt">${opts.nou!==undefined?'':`Owned ×${n}`}</div>${opts.nou!==undefined?'':`<button class="btn" data-rec="${c.id}">Recycle one · +${CFG.recycle[c.raresa]}</button>`}</div>`;
}
function vPacks(){
 const free=S.lastFree!==today();
 let h=`<div class="row"><button class="btn pri" id="bFree" ${free?'':'disabled'}>Daily free pack</button>
  <button class="btn pri" id="bPack" ${S.coins<CFG.packCost?'disabled':''}>Open a pack · ${CFG.packCost} coins</button>
  <span class="cnt">${CFG.cardsPerPack} cards per pack · packs opened: ${S.opened}</span></div>`;
 if(lastPack.length) h+=`<div class="pack reveal">${lastPack.map((p,i)=>`<div style="animation-delay:${i*.25}s">${slot(BYID[p.id],{nou:p.nou})}</div>`).join('')}</div>`;
 else h+=`<p class="cnt">Open a pack to get cards. Duplicates can be recycled for coins in the Collection tab.</p>`;
 return h;
}
function vColl(){
 const f=window.F||(window.F={cat:'',st:'all',set:''});
 const cats=[...new Set(CARDS.map(c=>c.cat))].sort(), sets=[...new Set(CARDS.flatMap(c=>c.sets))].sort();
 let list=CARDS.filter(c=>(!f.cat||c.cat===f.cat)&&(!f.set||c.sets.includes(f.set))&&(f.st==='all'||(f.st==='owned')===(own(c.id)>0)));
 const total=Object.keys(S.owned).length;
 return `<div class="row"><b>${total} / ${CARDS.length} cards</b>
  <select id="fCat"><option value="">All categories</option>${cats.map(x=>`<option ${f.cat===x?'selected':''}>${esc(x)}</option>`).join('')}</select>
  <select id="fSet"><option value="">All collections</option>${sets.map(x=>`<option value="${esc(x)}" ${f.set===x?'selected':''}>${esc(D.nomsSet[x]||x)}</option>`).join('')}</select>
  <select id="fSt">${[['all','All'],['owned','Owned'],['missing','Missing']].map(([v,l])=>`<option value="${v}" ${f.st===v?'selected':''}>${l}</option>`).join('')}</select></div>
  <div class="grid" style="padding:0">${list.map(c=>slot(c,{ghost:true})).join('')||'<p class="cnt">No cards match.</p>'}</div>`;
}
function vMis(){
 const row=m=>{const h=have(m),n=m.ids.length,ok=h===n,once=m.tipus!=='protocol',dn=once&&S.claimed[m.id];
  return `<div class="mis"><div class="info"><h3>${esc(m.nom)} <span class="cnt">· ${m.tipus}</span></h3><p>${esc(m.desc)}</p>
   <p>${m.ids.map(i=>`<span style="color:${own(i)?'#3f9b5c':'#6b7686'}">${esc(BYID[i].nom)}</span>`).join(' + ')}</p>
   <div class="bar"><i style="width:${100*h/n}%"></i></div></div>
   ${dn?'<span class="done">★ Badge earned</span>':`<button class="btn pri" data-claim="${esc(m.id)}" ${ok?'':'disabled'}>Claim +${m.premi}${once?'':' (repeatable)'}</button>`}
   ${!once&&S.proto[m.id]?`<span class="cnt">done ×${S.proto[m.id]}</span>`:''}</div>`;};
 return `<h2 class="sec">Protocols</h2><p class="cnt">Own all the cards to complete a protocol. Cards are not consumed. Daily limit: ${CFG.protoDailyCap} coins (used today: ${S.dayCoins}).</p>
  ${MIS.filter(m=>m.tipus==='protocol').map(row).join('')}<h2 class="sec">Collections</h2>${MIS.filter(m=>m.tipus!=='protocol').map(row).join('')}`;
}
function vSave(){
 return `<h2 class="sec">Save data</h2><p class="cnt">Your progress lives in this browser only. Copy the text below to back it up, or paste a backup and press Import.</p>
  <textarea id="sv">${esc(JSON.stringify(S))}</textarea><div class="row"><button class="btn" id="bImp">Import</button><button class="btn" id="bRes">Reset game</button></div>`;
}
function render(){
 $('#coins').textContent=`● ${S.coins} coins`;
 document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.v===view));
 $('#app').innerHTML=`<div class="msg" id="msg">${esc(msgText)}</div>`+({packs:vPacks,coll:vColl,mis:vMis,save:vSave}[view])();
 const on=(s,f)=>{const e=$(s);if(e)e.onclick=f;};
 on('#bFree',()=>openPack(true)); on('#bPack',()=>openPack(false));
 document.querySelectorAll('[data-rec]').forEach(b=>b.onclick=()=>recycle(+b.dataset.rec));
 document.querySelectorAll('[data-craft]').forEach(b=>b.onclick=()=>craft(+b.dataset.craft));
 document.querySelectorAll('[data-claim]').forEach(b=>b.onclick=()=>claim(b.dataset.claim));
 [['#fCat','cat'],['#fSet','set'],['#fSt','st']].forEach(([s,k])=>{const e=$(s);if(e)e.onchange=()=>{window.F[k]=e.value;render();};});
 on('#bImp',()=>{try{const o=JSON.parse($('#sv').value);if(typeof o.coins!=='number'||typeof o.owned!=='object')throw 0;S=Object.assign(fresh(),o);save();setMsg('Imported.');render();}catch(e){setMsg('That is not a valid backup.');}});
 on('#bRes',()=>{if(confirm('Delete all progress?')){S=fresh();save();lastPack=[];setMsg('Game reset.');render();}});
}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{view=b.dataset.v;setMsg('');render();});
render();
"""

def main():
    cartes, misions = construeix_dades()
    dades = json.dumps({"cartes": cartes, "misions": misions, "nomsSet": NOMS_COLECCIO}, ensure_ascii=False).replace("</", "<\\/")
    pagina = (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
              f'<title>BIO Cards</title><style>{gw.CSS}{CSS_JOC}</style>'
              f'<header class="top"><h1>BIO Cards</h1><nav><button data-v="packs">Packs</button> <button data-v="coll">Collection</button> '
              f'<button data-v="mis">Missions</button> <button data-v="save">Save</button></nav><span class="coins" id="coins"></span></header>'
              f'<main id="app"></main><script id="dades" type="application/json">{dades}</script><script>{JS}</script></html>')
    (ARREL / "web").mkdir(exist_ok=True)
    (ARREL / "web" / "joc.html").write_text(pagina, encoding="utf-8")
    print(f"web/joc.html generat: {len(cartes)} cartes, {len(misions)} missions")

if __name__ == "__main__":
    main()
