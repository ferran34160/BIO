"""Genera web/joc.html: el joc (sobres, col·lecció, monedes, missions) en una sola pàgina estàtica.
L'estat del jugador es guarda al navegador (localStorage). Ús: python genera_joc.py"""
import json, sqlite3
from pathlib import Path

import genera_web as gw

ARREL = Path(__file__).parent

# Col·leccions: etiqueta de la BD -> nom que es mostra
NOMS_COLECCIO = {"cancer": "Cancer", "oncogenes": "Oncogenes", "suppressors": "Tumor suppressors",
                 "nobel": "Nobel laureates", "cell-lines": "Cell lines", "immunotherapy": "Immunotherapy targets",
                 "antineoplastics": "Cancer drugs", "apoptosis": "Apoptosis genes"}

# Protocols: es completen tenint (no gastant) totes les cartes. Fets a mà; cal revisar-los amb criteri científic.
PROTOCOLS = [
    ("Run a gel", "Separate DNA fragments by size.", ["Gel electrophoresis", "Agarose", "Ethidium bromide", "Pipette"]),
    ("Build a PCR", "Amplify a DNA region.", ["PCR", "Thermal cycler", "Pipette", "Gel electrophoresis"]),
    ("Grow cells", "Keep a cell line alive in culture.", ["Cell culture", "Biosafety cabinet", "Trypsin", "Hemocytometer", "HeLa"]),
    ("Find a protein", "Detect one protein in a lysate.", ["Western blot", "SDS", "Gel electrophoresis", "PBS"]),
    ("Image the cell", "Look at stained cells.", ["Microscope", "Fluorescence microscopy", "Immunofluorescence", "Formaldehyde"]),
    ("Sort cells", "Count and sort cells by markers.", ["Flow cytometry", "Hemocytometer", "Cell culture"]),
    ("Stain a tissue", "Fix and stain a tissue section for the microscope.", ["Formaldehyde", "Hematoxylin", "Eosin", "Microscope"]),
    ("Clone a gene", "Insert a gene into a plasmid and select the bacteria.", ["Molecular cloning", "PCR", "Transfection", "Ampicillin", "Petri dish"]),
    ("Test a drug", "Treat cultured cancer cells and count the survivors.", ["Cell culture", "Cisplatin", "MCF-7", "Hemocytometer"]),
]

# Mateixa economia que el joc d'esports (android/.../Motor.kt): destruir 5/15/50/200/1000, fabricar x5,
# premi de col·lecció = meitat de la suma dels valors + 10.
VALOR_RECICLAR = {"comuna": 5, "poc_comuna": 15, "rara": 50, "epica": 200, "llegendaria": 1000}

def construeix_dades():
    con = sqlite3.connect(ARREL / "db" / "cartes.sqlite")
    con.row_factory = sqlite3.Row
    cartes, per_nom = [], {}
    # Només entren al joc les cartes completes: sense definició (font citada) no es publiquen.
    for c in con.execute("SELECT * FROM carta WHERE definicio IS NOT NULL ORDER BY categoria, nom"):
        raresa = c["raresa"] or "comuna"
        meta = {"id": c["id"], "nom": c["nom"], "cat": gw.ETIQ_CAT[c["categoria"]], "raresa": raresa,
                "rlabel": gw.ETIQ_RARESA[raresa], "color": gw.COLORS[raresa],
                "sets": [x for x in (c["coleccions"] or "").split(",") if x],
                "pop": c["popularitat"] or 0, "html": gw.carta_html(c), "icona": gw.ICONES[c["categoria"]]}
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
        if faltes:  # protocol que depèn de cartes que encara no són a la base de dades
            print(f"  (protocol «{nom}» omès: falten {faltes})")
            continue
        misions.append({"id": f"proto:{nom}", "tipus": "protocol", "nom": nom, "desc": desc,
                        "ids": [per_nom[n] for n in noms], "premi": 25})
    return cartes, misions

IC = {
    "home": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3l9 8h-3v9h-5v-6h-2v6H6v-9H3z"/></svg>',
    "album": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-8-5.2-8-11a4.6 4.6 0 0 1 8-3 4.6 4.6 0 0 1 8 3c0 5.800-8 11-8 11z"/></svg>',
    "all": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>',
    "mis": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-2 15l-5-5 1.400-1.400L10 14.200l7.600-7.600L19 8z"/></svg>',
    "shop": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M22 19l-8.500-8.500a5 5 0 0 0-6.800-6.300l3.400 3.400-2.500 2.500-3.400-3.400A5 5 0 0 0 10.500 13.500L19 22z"/></svg>',
    "perfil": '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.500 3.500-7 8-7s8 2.500 8 7z"/></svg>',
}

def main():
    cartes, misions = construeix_dades()
    dades = json.dumps({"cartes": cartes, "misions": misions, "colors": gw.COLORS}, ensure_ascii=False).replace("</", "<\\/")
    css = (ARREL / "joc_src" / "joc.css").read_text(encoding="utf-8")
    js = (ARREL / "joc_src" / "joc.js").read_text(encoding="utf-8")
    tabs = [("home", "Home"), ("album", "Album"), ("all", "All"), ("mis", "Missions"), ("shop", "Workshop")]
    nav = "".join(f'<button data-v="{k}">{IC[k]}{n}</button>' for k, n in tabs)
    pagina = (f'<!doctype html><html lang="en"><meta charset="utf-8">'
              f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
              f'<meta name="theme-color" content="#0A0A0A"><meta name="apple-mobile-web-app-capable" content="yes">'
              f'<title>BIO Cards</title><style>{gw.CSS}{css}</style>'
              f'<header class="top"><span class="pill" id="coins"></span>'
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
