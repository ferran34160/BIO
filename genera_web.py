"""Genera web/index.html (àlbum estàtic) a partir de db/cartes.sqlite. Ús: python genera_web.py"""
import html, json, sqlite3
from pathlib import Path

ARREL = Path(__file__).parent
COLORS = {"comuna": "#8a8f98", "poc_comuna": "#3f9b5c", "rara": "#2f7fd1", "epica": "#8e4fd1", "llegendaria": "#e0a21a"}
ETIQ_RARESA = {"comuna": "Common", "poc_comuna": "Uncommon", "rara": "Rare", "epica": "Epic", "llegendaria": "Legendary"}
ETIQ_CAT = {"gen": "Gene / protein", "molecula": "Molecule", "cientific": "Scientist", "concepte": "Concept",
            "tecnica": "Technique", "aparell": "Instrument", "reactiu": "Reagent", "linia_cellular": "Cell line",
            "descobriment": "Discovery"}
ETIQ_STAT = {"cromosoma": "Chromosome", "longitud_aa": "Length (aa)"}

# Il·lustracions de plantilla per a les cartes sense imatge lliure: dibuixos propis (sense drets), un per categoria.
# Totes usen el color de la raresa (currentColor) sobre fons fosc, viewBox 100x100.
ICONES = {
    "gen": '<path d="M30 8c0 28 40 36 40 84M70 8c0 28-40 36-40 84" fill="none" stroke="currentColor" stroke-width="4"/>'
           '<path d="M36 22h28M33 40h34M33 60h34M36 78h28" stroke="currentColor" stroke-width="3" opacity=".6"/>',
    "molecula": '<path d="M50 14l28 16v32L50 78 22 62V30z" fill="none" stroke="currentColor" stroke-width="4"/>'
                '<circle cx="50" cy="14" r="6" fill="currentColor"/><circle cx="78" cy="62" r="6" fill="currentColor"/>'
                '<circle cx="22" cy="62" r="6" fill="currentColor"/><path d="M50 78v14" stroke="currentColor" stroke-width="4"/>',
    "cientific": '<circle cx="50" cy="32" r="16" fill="currentColor" opacity=".85"/>'
                 '<path d="M18 90c0-22 14-36 32-36s32 14 32 36z" fill="currentColor" opacity=".85"/>',
    "concepte": '<path d="M50 10a24 24 0 0 0-14 44c4 3 6 7 6 12h16c0-5 2-9 6-12A24 24 0 0 0 50 10z" fill="none" stroke="currentColor" stroke-width="4"/>'
                '<path d="M40 76h20M43 86h14" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>',
    "tecnica": '<path d="M38 10h24M42 10v28L22 78a8 8 0 0 0 7 12h42a8 8 0 0 0 7-12L58 38V10" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/>'
               '<path d="M30 64h40" stroke="currentColor" stroke-width="4" opacity=".6"/>',
    "aparell": '<circle cx="50" cy="50" r="16" fill="none" stroke="currentColor" stroke-width="4"/>'
               '<path d="M50 10v16M50 74v16M10 50h16M74 50h16M22 22l11 11M67 67l11 11M78 22L67 33M33 67L22 78" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>',
    "reactiu": '<path d="M40 10h20M44 10v22L24 76a10 10 0 0 0 9 14h34a10 10 0 0 0 9-14L56 32V10" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/>'
               '<path d="M30 66c10-6 16 6 40 0l6 10a6 6 0 0 1-5 9H31a6 6 0 0 1-5-9z" fill="currentColor" opacity=".7"/>',
    "linia_cellular": '<ellipse cx="50" cy="50" rx="40" ry="34" fill="none" stroke="currentColor" stroke-width="4"/>'
                      '<circle cx="46" cy="46" r="14" fill="currentColor" opacity=".8"/><circle cx="70" cy="62" r="4" fill="currentColor"/>'
                      '<circle cx="30" cy="66" r="3" fill="currentColor"/><circle cx="68" cy="34" r="3" fill="currentColor"/>',
    "descobriment": '<path d="M50 8l11 27 29 3-22 20 7 29-25-15-25 15 7-29L10 38l29-3z" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/>',
}

def carta_html(c):
    e = html.escape
    color = COLORS.get(c["raresa"], COLORS["comuna"])
    if c["imatge_url"]:
        img = (f'<img src="{e(c["imatge_url"])}" alt="{e(c["nom"])}" loading="lazy">'
               f'<div class="cred">{e(c["imatge_autor"] or "")} · {e(c["imatge_llicencia"] or "")}</div>')
    else:
        img = (f'<div class="sense-img"><svg viewBox="0 0 100 100" aria-hidden="true">{ICONES[c["categoria"]]}</svg>'
               f'<span>{e(ETIQ_CAT[c["categoria"]])}</span></div>')
    stats = "".join(f'<li><span>{e(ETIQ_STAT.get(k, k))}</span><b>{e(str(v))}</b></li>'
                    for k, v in json.loads(c["estadistiques"] or "{}").items())
    defin = (f'<p class="def">{e(c["definicio"])}</p><p class="font">Source: {e(c["definicio_font"] or "")}</p>'
             if c["definicio"] else '<p class="def buit">Definition pending</p>')
    r = c["raresa"] or "comuna"
    estrelles = "★" * (list(COLORS).index(r) + 1)
    return (f'<article class="carta" data-r="{r}" style="--r:{color}"><i class="orn tl"></i><i class="orn tr"></i>'
            f'<i class="orn bl"></i><i class="orn br"></i><header><h2>{e(c["nom"])}</h2>'
            f'<span class="rb">{e(ETIQ_RARESA.get(r, ""))}<b>{estrelles}</b></span></header>'
            f'<div class="img">{img}</div><div class="cat">{e(ETIQ_CAT[c["categoria"]])}</div>'
            f'{defin}<ul class="stats">{stats}</ul></article>')

CSS = ("""body{margin:0;font:15px system-ui,sans-serif;background:#10141b;color:#e8ecf2}
h1{padding:20px 16px 0;margin:0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;padding:16px}
""" + (Path(__file__).parent / "joc_src" / "carta.css").read_text(encoding="utf-8"))

def main():
    con = sqlite3.connect(ARREL / "db" / "cartes.sqlite")
    con.row_factory = sqlite3.Row
    cartes = con.execute("SELECT * FROM carta ORDER BY categoria, nom").fetchall()
    pagina = (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
              f'<title>BIO Album</title><style>{CSS}</style><h1>Album ({len(cartes)} cards)</h1>'
              f'<div class="grid">{"".join(carta_html(c) for c in cartes)}</div></html>')
    (ARREL / "web").mkdir(exist_ok=True)
    (ARREL / "web" / "index.html").write_text(pagina, encoding="utf-8")
    print(f"web/index.html generated with {len(cartes)} cards")

if __name__ == "__main__":
    main()
