"""Omple db/cartes.sqlite amb dades reals per a les cartes del pilot (a executar a l'ordinador de l'usuari).

Només biblioteca estàndard. Ús:  python descarrega_pilot.py --contacte correu@exemple.cat
  UniProt  -> definició (comentari FUNCTION), longitud de la proteïna  (cartes categoria 'gen')
  MeSH     -> definició (scope note) per a cartes amb font 'mesh'
  Wikipedia/Commons -> imatge amb autor i llicència (només llicències lliures)
Les cartes queden amb verificada=0: cal revisar-les abans de donar-les per bones.
"""
import argparse, html, json, re, sqlite3, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

DB = Path(__file__).parent / "db" / "cartes.sqlite"
# Correspondències que no es poden deduir del nom (revisar-les si una carta surt buida o equivocada)
MESH_LABEL = {"PCR": "Polymerase Chain Reaction", "Citometria de flux": "Flow Cytometry"}
WIKI_TITLE = {"PCR": "Polymerase chain reaction", "Citometria de flux": "Flow cytometry",
              "Termociclador": "Thermal cycler", "Microscopi": "Microscope", "HeLa": "HeLa",
              "DMSO": "Dimethyl sulfoxide", "Henrietta Lacks": "Henrietta Lacks"}
LLICENCIES_LLIURES = re.compile(r"^(CC[ -]BY|CC0|Public domain|PD)", re.I)

def get_json(url, ua, pausa=1.0):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
    for intent in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                dades = json.load(r)
            time.sleep(pausa)
            return dades
        except urllib.error.HTTPError as e:
            if e.code != 429 or intent == 4:
                raise
            espera = int(e.headers.get("Retry-After") or 0) or 10 * (intent + 1)
            print(f"    429, espero {espera} s...")
            time.sleep(espera)

def uniprot(carta, ua):
    d = get_json(f"https://rest.uniprot.org/uniprotkb/{carta['font_id']}.json", ua)
    funcio = next((c["texts"][0]["value"] for c in d.get("comments", [])
                   if c.get("commentType") == "FUNCTION" and c.get("texts")), None)
    estad = json.loads(carta["estadistiques"] or "{}")
    estad["longitud_aa"] = d["sequence"]["length"]
    return {"definicio": funcio, "definicio_font": f"UniProt {carta['font_id']} (CC BY 4.0, a verificar)",
            "estadistiques": json.dumps(estad)}

def mesh(carta, ua):
    label = MESH_LABEL.get(carta["nom"], carta["nom"])
    trobats = get_json("https://id.nlm.nih.gov/mesh/lookup/descriptor?" + urllib.parse.urlencode(
        {"label": label, "match": "exact", "limit": 1}), ua)
    if not trobats:
        print(f"    MeSH: cap descriptor amb l'etiqueta exacta «{label}»")
        return {}
    uri = trobats[0]["resource"]
    q = ('PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#> '
         f'SELECT ?note WHERE {{ <{uri}> meshv:preferredConcept ?c . ?c meshv:scopeNote ?note }} LIMIT 1')
    b = get_json("https://id.nlm.nih.gov/mesh/sparql?" + urllib.parse.urlencode(
        {"query": q, "format": "JSON"}), ua)["results"]["bindings"]
    if not b:
        print(f"    MeSH: {uri} no té scope note")
        return {}
    return {"font_id": uri.rsplit("/", 1)[-1], "definicio": b[0]["note"]["value"],
            "definicio_font": f"MeSH (NLM), descriptor «{label}»"}

def imatge(carta, ua):
    titol = WIKI_TITLE.get(carta["nom"], carta["nom"])
    w = get_json("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "prop": "pageimages", "piprop": "original|name", "titles": titol,
         "redirects": 1, "format": "json"}), ua)
    pag = next(iter(w["query"]["pages"].values()))
    if "pageimage" not in pag:
        return {}
    c = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 600,
         "titles": "File:" + pag["pageimage"], "format": "json"}), ua)
    info = next(iter(c["query"]["pages"].values()))["imageinfo"][0]
    meta = info["extmetadata"]
    llic = meta.get("LicenseShortName", {}).get("value", "")
    if not LLICENCIES_LLIURES.match(llic):
        return {}
    autor = html.unescape(re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))).strip()
    return {"imatge_url": info.get("thumburl") or info["url"], "imatge_autor": autor or "desconegut",
            "imatge_llicencia": llic}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contacte", required=True, help="correu per al User-Agent")
    ua = f"BIO-cartes/0.1 ({ap.parse_args().contacte})"
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for carta in con.execute("SELECT * FROM carta").fetchall():
        canvis = {}
        for pas, aplica in (("uniprot", carta["font"] == "uniprot"), ("mesh", carta["font"] == "mesh"),
                            ("imatge", carta["font"] != "uniprot")):
            camp = "imatge_url" if pas == "imatge" else "definicio"
            if not aplica or carta[camp]:
                continue
            try:
                canvis.update({"uniprot": uniprot, "mesh": mesh, "imatge": imatge}[pas](carta, ua))
            except Exception as e:  # una carta amb error no atura la resta
                print(f"  ! {carta['nom']} ({pas}): {e}")
        if canvis:
            con.execute(f"UPDATE carta SET {', '.join(k + '=?' for k in canvis)} WHERE id=?",
                        (*canvis.values(), carta["id"]))
            con.commit()
        print(f"{carta['nom']}: {', '.join(canvis) or 'res'}")

if __name__ == "__main__":
    main()
