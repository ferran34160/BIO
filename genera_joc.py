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

IC = {
    "home": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M5 9h14"/></svg>',
    "album": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/></svg>',
    "cols": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></svg>',
    "mis": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l2.6 5.6 6 .8-4.4 4.2 1.1 6L12 16.8 6.7 19.6l1.1-6L3.4 9.4l6-.8z"/></svg>',
    "shop": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a4 4 0 0 0-5 5L3 18l3 3 6.7-6.7a4 4 0 0 0 5-5l-2.5 2.5-2.2-.5-.5-2.2z"/></svg>',
    "perfil": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.5 3.5-7 8-7s8 2.5 8 7"/></svg>',
}

def main():
    cartes, misions = construeix_dades()
    dades = json.dumps({"cartes": cartes, "misions": misions}, ensure_ascii=False).replace("</", "<\\/")
    css = (ARREL / "joc_src" / "joc.css").read_text(encoding="utf-8")
    js = (ARREL / "joc_src" / "joc.js").read_text(encoding="utf-8")
    tabs = [("home", "Home"), ("album", "Album"), ("cols", "Collections"), ("mis", "Missions"), ("shop", "Workshop")]
    nav = "".join(f'<button data-v="{k}">{IC[k]}{n}</button>' for k, n in tabs)
    pagina = (f'<!doctype html><html lang="en"><meta charset="utf-8">'
              f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
              f'<meta name="theme-color" content="#14122B"><meta name="apple-mobile-web-app-capable" content="yes">'
              f'<title>BIO Cards</title><style>{gw.CSS}{css}</style>'
              f'<header class="top"><h1 id="title">BIO Cards</h1><span class="coins" id="coins"></span>'
              f'<button class="iconbtn" id="bProfile" aria-label="Profile">{IC["perfil"]}</button></header>'
              f'<nav class="tabs">{nav}</nav><main id="app"></main><div id="overlayHost"></div><div id="modalHost"></div>'
              f'<script id="dades" type="application/json">{dades}</script><script>{js}</script></html>')
    (ARREL / "web").mkdir(exist_ok=True)
    (ARREL / "web" / "joc.html").write_text(pagina, encoding="utf-8")
    (ARREL / "docs").mkdir(exist_ok=True)
    (ARREL / "docs" / "index.html").write_text(pagina, encoding="utf-8")  # per publicar-ho amb GitHub Pages
    print(f"web/joc.html i docs/index.html generats: {len(cartes)} cartes, {len(misions)} missions")

if __name__ == "__main__":
    main()
