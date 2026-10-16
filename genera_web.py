"""Genera web/index.html (àlbum estàtic) a partir de db/cartes.sqlite. Ús: python genera_web.py"""
import html, json, sqlite3
from pathlib import Path

ARREL = Path(__file__).parent
COLORS = {"comuna": "#8a8f98", "poc_comuna": "#3f9b5c", "rara": "#2f7fd1", "epica": "#8e4fd1", "llegendaria": "#e0a21a"}
ETIQ_RARESA = {"comuna": "Comuna", "poc_comuna": "Poc comuna", "rara": "Rara", "epica": "Èpica", "llegendaria": "Llegendària"}
ETIQ_CAT = {"gen": "Gen / proteïna", "molecula": "Molècula", "cientific": "Científic", "concepte": "Concepte",
            "tecnica": "Tècnica", "aparell": "Aparell", "reactiu": "Reactiu", "linia_cellular": "Línia cel·lular",
            "descobriment": "Descobriment"}
ETIQ_STAT = {"cromosoma": "Cromosoma", "longitud_aa": "Longitud (aa)"}

def carta_html(c):
    e = html.escape
    color = COLORS.get(c["raresa"], COLORS["comuna"])
    if c["imatge_url"]:
        img = (f'<img src="{e(c["imatge_url"])}" alt="{e(c["nom"])}" loading="lazy">'
               f'<div class="cred">{e(c["imatge_autor"] or "")} · {e(c["imatge_llicencia"] or "")}</div>')
    else:
        img = f'<div class="sense-img">{e(ETIQ_CAT[c["categoria"]])}</div>'
    stats = "".join(f'<li><span>{e(ETIQ_STAT.get(k, k))}</span><b>{e(str(v))}</b></li>'
                    for k, v in json.loads(c["estadistiques"] or "{}").items())
    defin = (f'<p class="def">{e(c["definicio"])}</p><p class="font">Font: {e(c["definicio_font"] or "")}</p>'
             if c["definicio"] else '<p class="def buit">Definició pendent</p>')
    return (f'<article class="carta" style="--r:{color}"><header><h2>{e(c["nom"])}</h2>'
            f'<span>{e(ETIQ_RARESA.get(c["raresa"], ""))}</span></header>'
            f'<div class="img">{img}</div><div class="cat">{e(ETIQ_CAT[c["categoria"]])}</div>'
            f'{defin}<ul class="stats">{stats}</ul></article>')

CSS = """body{margin:0;font:15px system-ui,sans-serif;background:#10141b;color:#e8ecf2}
h1{padding:20px 16px 0;margin:0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;padding:16px}
.carta{background:#1a212c;border:3px solid var(--r);border-radius:14px;padding:10px;display:flex;flex-direction:column;gap:8px}
header{display:flex;justify-content:space-between;align-items:baseline;gap:8px}h2{margin:0;font-size:18px}
header span{color:var(--r);font-size:12px;font-weight:700;text-transform:uppercase}
.img{height:160px;background:#0c1016;border-radius:8px;overflow:hidden;position:relative;display:flex}
.img img{width:100%;height:100%;object-fit:contain}.cred{position:absolute;bottom:0;left:0;right:0;font-size:10px;
background:#000a;padding:2px 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sense-img{margin:auto;color:#6b7686}.cat{font-size:12px;color:#9aa6b6}.def{margin:0;font-size:13px;line-height:1.4;
display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}.def.buit{color:#6b7686;font-style:italic}
.font{margin:0;font-size:10px;color:#6b7686}.stats{list-style:none;margin:0;padding:0;display:flex;gap:12px;font-size:12px}
.stats span{color:#9aa6b6;margin-right:4px}"""

def main():
    con = sqlite3.connect(ARREL / "db" / "cartes.sqlite")
    con.row_factory = sqlite3.Row
    cartes = con.execute("SELECT * FROM carta ORDER BY categoria, nom").fetchall()
    pagina = (f'<!doctype html><html lang="ca"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
              f'<title>Àlbum BIO</title><style>{CSS}</style><h1>Àlbum ({len(cartes)} cartes)</h1>'
              f'<div class="grid">{"".join(carta_html(c) for c in cartes)}</div></html>')
    (ARREL / "web").mkdir(exist_ok=True)
    (ARREL / "web" / "index.html").write_text(pagina, encoding="utf-8")
    print(f"web/index.html generat amb {len(cartes)} cartes")

if __name__ == "__main__":
    main()
