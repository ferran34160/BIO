#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recompte_oncologia.py - Compta quants elements útils tindria un joc de cartes
sobre recerca en càncer, a partir de fonts obertes. NO baixa dades: només recomptes.

Només fa servir la biblioteca estàndard de Python (3.8 o superior).

Ús:
    python recompte_oncologia.py --contacte elteu@correu.cat

Opcions:
    --grups uniprot,chembl,mesh,wikidata   (per defecte, tots; útil per repetir un sol grup)

Cada recompte és independent: si un falla, es mostra l'error i continua amb els altres.
Avís important: l'script s'ha provat només amb respostes simulades, no contra els
serveis reals. Si surt un «ERROR» o un «filtre sense efecte?», enganxa'm la sortida.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PAUSA = 1.0
UA = "RecompteOncologia/0.1 (sense contacte)"

UNIPROT = "https://rest.uniprot.org/uniprotkb/search"
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data/%s.json"
MESH = "https://id.nlm.nih.gov/mesh/sparql"
WDQS = "https://query.wikidata.org/sparql"
WD_API = "https://www.wikidata.org/w/api.php"

ANY_INICI, ANY_FI, PAS = 1850, 2016, 25


# --------------------------------------------------------------------------
# Xarxa
# --------------------------------------------------------------------------

class ErrorHTTP(Exception):
    def __init__(self, codi, cos):
        if cos.lstrip()[:5].lower() in ("<!doc", "<html"):
            text = re.sub(r"(?is)<(script|style).*?</\1>", " ", cos)
            text = re.sub(r"(?s)<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()[:200]
            resum = "(pàgina HTML d'error del servidor: «%s»)" % text
        else:
            resum = cos[:160].replace("\n", " ")
        super().__init__("HTTP %s: %s" % (codi, resum))
        self.codi = codi
        self.cos = cos


class Timeout(Exception):
    pass


def get(url, params=None, accept="application/json"):
    """GET amb reintents. Retorna (json, capçaleres)."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    for intent in range(4):
        time.sleep(PAUSA)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=100) as r:
                cos = r.read().decode("utf-8", "replace")
                return (json.loads(cos) if cos.strip() else {}), r.headers
        except urllib.error.HTTPError as e:
            cos = e.read().decode("utf-8", "replace")
            if e.code in (429, 503) and intent < 3:
                try:
                    espera = int(e.headers.get("Retry-After", "20"))
                except (TypeError, ValueError):
                    espera = 20
                time.sleep(min(max(espera, 5), 90))
                continue
            raise ErrorHTTP(e.code, cos)
        except (OSError, ValueError):
            if intent < 3:
                time.sleep(10 * (intent + 1))
                continue
            raise


# --------------------------------------------------------------------------
# Recomptes per font
# --------------------------------------------------------------------------

def uniprot(consulta):
    _, cap = get(UNIPROT, {"query": consulta, "size": 1, "format": "json"})
    total = cap.get("x-total-results")
    if total is None:
        raise RuntimeError("UniProt no ha enviat x-total-results")
    return int(total)


def chembl(recurs, filtres):
    p = {"limit": 1}
    p.update(filtres)
    try:
        dades, _ = get(CHEMBL % recurs, p, accept="*/*")
    except ErrorHTTP as e:
        if e.codi < 500:
            raise
        # alternativa: sense el sufix .json i demanant el format per paràmetre
        q = dict(p)
        q["format"] = "json"
        dades, _ = get("https://www.ebi.ac.uk/chembl/api/data/%s" % recurs, q, accept="*/*")
    return int(dades["page_meta"]["total_count"])


MESH_PREFIX = ("PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#> "
               "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ")
# Només descriptors amb l'adreça canònica (.../mesh/D123456): evita comptar les
# versions antigues de cada any, que inflaven el recompte per un factor ~12.
MESH_D = ' FILTER(STRSTARTS(STR(?d), "http://id.nlm.nih.gov/mesh/D"))'


def mesh(cos):
    q = MESH_PREFIX + "SELECT (COUNT(DISTINCT ?d) AS ?total) WHERE { " + cos + " }"
    dades, _ = get(MESH, {"query": q, "format": "JSON"})
    return int(dades["results"]["bindings"][0]["total"]["value"])


def mesh_arbre(prefix, amb_nota=False):
    """Descriptors MeSH la numeració d'arbre dels quals comença per `prefix` (p. ex. E05)."""
    cos = ("?d a meshv:TopicalDescriptor ; meshv:treeNumber ?t . ?t rdfs:label ?et . "
           'FILTER(STRSTARTS(STR(?et), "%s"))' % prefix)
    if amb_nota:
        cos += " ?d meshv:preferredConcept ?c . ?c meshv:scopeNote ?nota ."
    return mesh(cos + MESH_D)


def cellosaurus_total():
    dades, _ = get("https://api.cellosaurus.org/release-info")
    return int(dades["Cellosaurus"]["header"]["release"]["nb-cell-lines"])


def _wd(trios, ini=None, fi=None):
    filtre = ""
    if ini is not None:
        filtre = (' FILTER(?nai >= "%04d-01-01T00:00:00Z"^^xsd:dateTime && '
                  '?nai < "%04d-01-01T00:00:00Z"^^xsd:dateTime)' % (ini, fi))
    q = "SELECT (COUNT(DISTINCT ?s) AS ?total) WHERE { " + trios + filtre + " }"
    try:
        dades, _ = get(WDQS, {"query": q, "format": "json"},
                       accept="application/sparql-results+json")
    except ErrorHTTP as e:
        if e.codi in (500, 502, 503, 504) or "imeout" in e.cos:
            raise Timeout(str(e))
        raise
    except OSError as e:
        raise Timeout(str(e))
    return int(dades["results"]["bindings"][0]["total"]["value"])


def _wd_rang(trios, ini, fi):
    try:
        return _wd(trios, ini, fi)
    except Timeout:
        if fi - ini <= 1:
            raise
        mig = (ini + fi) // 2
        return _wd_rang(trios, ini, mig) + _wd_rang(trios, mig, fi)


def wd_compta(trios, dividir=True):
    """Compta amb Wikidata. Si fa timeout, ho parteix per anys de naixement
    (1850-2015; aproximat, perquè algú pot tenir dues dates de naixement)."""
    try:
        return _wd(trios)
    except Timeout:
        if not dividir:
            raise
        return sum(_wd_rang(trios, ini, min(ini + PAS, ANY_FI))
                   for ini in range(ANY_INICI, ANY_FI, PAS))


# Identificadors de Wikidata i paraula que ha de contenir el seu nom en anglès.
# Es comprova abans de comptar: si no quadra, aquell recompte se salta.
WD_IDS = {
    "Q864503":  "biologist",
    "Q3126128": "geneticist",
    "Q593644":  "chemist",
    "Q39631":   "physician",
    "Q162555":  "oncolog",
    "Q80061":   "physiology or medicine",
    "Q3247516": "techni",   # candidat a «tècnica de laboratori» (el va donar la cerca per nom)
    "P267":     "atc",      # propietat «codi ATC»
    "P117":     "structure",  # propietat «estructura química» (imatge)
}


def wd_valida():
    dades, _ = get(WD_API, {"action": "wbgetentities", "ids": "|".join(WD_IDS),
                            "props": "labels", "languages": "en", "format": "json"})
    bons = set()
    print("   Comprovació d'identificadors de Wikidata:")
    for q, paraula in WD_IDS.items():
        ent = (dades.get("entities") or {}).get(q, {})
        nom = ((ent.get("labels") or {}).get("en") or {}).get("value", "?")
        ok = paraula in nom.lower()
        print("     %s = «%s» %s" % (q, nom, "" if ok else "  <-- NO QUADRA, s'omet"))
        if ok:
            bons.add(q)
    return bons


# Ocupacions que es busquen pel nom (en lloc de recordar-ne l'identificador).
WD_CERCA = {
    "biochemist": "bioquímics",
    "molecular biologist": "biòlegs moleculars",
    "immunologist": "immunòlegs",
    "pharmacologist": "farmacòlegs",
    "oncologist": "oncòlegs",
}
PARAULES_DESC = ("scientist", "researcher", "physician", "doctor", "specialist",
                 "occupation", "profession", "person")

# Classes d'aparells i tècniques. Cada carta seria un TIPUS (p. ex. «centrífuga»),
# és a dir, una subclasse d'aquestes classes, no un exemplar concret.
WD_CLASSES = {
    "laboratory equipment": "aparells de laboratori",
    "scientific instrument": "instruments científics",
}
PARAULES_CLASSE = ("equipment", "instrument", "apparatus", "technique", "method",
                   "procedure", "device", "tool")


def wd_resol(cerca=None, paraules=None, titol="Cerca d'identificadors per nom"):
    """Busca l'identificador de cada nom de `cerca` (per defecte, WD_CERCA).
    Retorna {qid: categoria}."""
    cerca = WD_CERCA if cerca is None else cerca
    paraules = PARAULES_DESC if paraules is None else paraules
    trobats = {}
    print("   %s:" % titol)
    for nom, cat in cerca.items():
        try:
            dades, _ = get(WD_API, {"action": "wbsearchentities", "search": nom,
                                    "language": "en", "type": "item", "limit": 10,
                                    "format": "json"})
        except Exception as e:
            print("     %s -> ERROR: %s" % (nom, e))
            continue
        cands = dades.get("search") or []
        tria = None
        for r in cands:
            desc = (r.get("description") or "").lower()
            if (r.get("label") or "").lower() == nom and any(w in desc for w in paraules):
                tria = r
                break
        if tria:
            print("     %s -> %s («%s»)" % (nom, tria["id"], tria.get("description", "")))
            trobats[tria["id"]] = cat
        else:
            vistos = ", ".join("%s «%s»" % (r.get("id"), r.get("description", ""))
                               for r in cands[:3]) or "cap resultat"
            print("     %s -> cap candidat clar, s'omet. Primers resultats: %s" % (nom, vistos))
    return trobats


# --------------------------------------------------------------------------
# Llista de recomptes
# --------------------------------------------------------------------------

HUM = "(organism_id:9606) AND (reviewed:true)"


def construeix(grups, wd_bons, wd_extra, wd_classes=None):
    wd_classes = wd_classes or {}
    """Retorna una llista de (grup, id, descripció, funció, id_base)."""
    p = []
    if "uniprot" in grups:
        p += [
            ("uniprot", "up_hum", "Proteïnes humanes revisades (Swiss-Prot)",
             lambda: uniprot(HUM), None),
            ("uniprot", "up_onc", "  de les quals, proto-oncògens (KW-0656)",
             lambda: uniprot(HUM + " AND (keyword:KW-0656)"), "up_hum"),
            ("uniprot", "up_sup", "  de les quals, supressors tumorals (KW-0043)",
             lambda: uniprot(HUM + " AND (keyword:KW-0043)"), "up_hum"),
            ("uniprot", "up_cancer", "  amb malaltia anotada que esmenta «cancer»",
             lambda: uniprot(HUM + " AND (cc_disease:cancer)"), "up_hum"),
            ("uniprot", "up_3d", "  amb estructura 3D coneguda",
             lambda: uniprot(HUM + " AND (structure_3d:true)"), "up_hum"),
        ]
    if "chembl" in grups:
        p += [
            ("chembl", "ch_tot", "Compostos a ChEMBL",
             lambda: chembl("molecule", {}), None),
            ("chembl", "ch_aprov", "  aprovats (max_phase = 4)",
             lambda: chembl("molecule", {"max_phase": 4}), "ch_tot"),
            ("chembl", "ch_clin", "  aprovats o en assaigs clínics (max_phase >= 1)",
             lambda: chembl("molecule", {"max_phase__gte": 1}), "ch_tot"),
            ("chembl", "ch_ind", "Indicacions de fàrmacs (files, no fàrmacs únics)",
             lambda: chembl("drug_indication", {}), None),
            ("chembl", "ch_ind_onc", "  les que esmenten «neoplasm» al MeSH",
             lambda: chembl("drug_indication", {"mesh_heading__icontains": "neoplasm"}),
             "ch_ind"),
            ("chembl", "ch_drug", "Fàrmacs (taula «drug», els aprovats)",
             lambda: chembl("drug", {}), None),
            ("chembl", "ch_atc", "Codis ATC (un per substància)",
             lambda: chembl("atc_classification", {}), None),
            ("chembl", "ch_atc_onc", "  antineoplàstics (ATC que comença per L01)",
             lambda: chembl("atc_classification", {"level5__startswith": "L01"}), "ch_atc"),
        ]
    if "mesh" in grups:
        p += [
            ("mesh", "me_tot", "Descriptors MeSH (temes)",
             lambda: mesh("?d a meshv:TopicalDescriptor ." + MESH_D), None),
            ("mesh", "me_nota", "  amb nota de definició (scope note)",
             lambda: mesh("?d a meshv:TopicalDescriptor ; meshv:preferredConcept ?c . "
                          "?c meshv:scopeNote ?nota ." + MESH_D), "me_tot"),
            ("mesh", "me_c04", "  dins l'arbre Neoplasmes (C04)",
             lambda: mesh("?d a meshv:TopicalDescriptor ; meshv:treeNumber ?t . "
                          "?t rdfs:label ?et . FILTER(STRSTARTS(STR(?et), \"C04\"))" + MESH_D),
             "me_tot"),
            ("mesh", "me_e05", "Tècniques d'investigació (arbre E05)",
             lambda: mesh_arbre("E05"), "me_tot"),
            ("mesh", "me_e05n", "  amb nota de definició",
             lambda: mesh_arbre("E05", True), "me_e05"),
            ("mesh", "me_e07", "Equipament i subministraments (arbre E07)",
             lambda: mesh_arbre("E07"), "me_tot"),
            ("mesh", "me_e07n", "  amb nota de definició",
             lambda: mesh_arbre("E07", True), "me_e07"),
        ]
    if "wikidata" in grups:
        def persones(q, camp="wdt:P106"):
            return "?s %s wd:%s ; wdt:P18 ?img ; wdt:P569 ?nai ." % (camp, q)
        noms = {"Q864503": "biòlegs", "Q3126128": "genetistes",
                "Q593644": "químics", "Q39631": "metges"}
        noms.update(wd_extra)
        for q, nom in noms.items():
            if q in wd_bons or q in wd_extra:
                p.append(("wikidata", "wd_" + q,
                          "%s amb foto i data de naixement" % nom.capitalize(),
                          lambda q=q: wd_compta(persones(q)), None))
        if "Q162555" in wd_bons:
            p.append(("wikidata", "wd_onc", "Persones amb camp de treball «oncologia», amb foto",
                      lambda: wd_compta(persones("Q162555", "wdt:P101")), None))
        if "Q80061" in wd_bons:
            p += [
                ("wikidata", "wd_nobel", "Premis Nobel de Fisiologia o Medicina (persones)",
                 lambda: wd_compta("?s wdt:P166 wd:Q80061 .", dividir=False), None),
                ("wikidata", "wd_nobel_foto", "  d'aquests, amb foto a Commons",
                 lambda: wd_compta("?s wdt:P166 wd:Q80061 ; wdt:P18 ?img .", dividir=False),
                 "wd_nobel"),
            ]
        if "P267" in wd_bons:
            atc = '?s wdt:P267 ?atc . FILTER(STRSTARTS(STR(?atc), "L01"))'
            p.append(("wikidata", "wd_atc", "Substàncies amb codi ATC L01 (antineoplàstics)",
                      lambda: wd_compta(atc, dividir=False), None))
            if "P117" in wd_bons:
                p.append(("wikidata", "wd_atc_img", "  amb dibuix de l'estructura química",
                          lambda: wd_compta(atc + " ?s wdt:P117 ?est .", dividir=False),
                          "wd_atc"))
        for q, cat in wd_classes.items():
            p += [
                ("wikidata", "wd_k_" + q, "Tipus de «%s» (subclasses)" % cat,
                 lambda q=q: wd_compta("?s wdt:P279+ wd:%s ." % q, dividir=False), None),
                ("wikidata", "wd_ki_" + q, "  amb imatge a Commons",
                 lambda q=q: wd_compta("?s wdt:P279+ wd:%s ; wdt:P18 ?img ." % q, dividir=False),
                 "wd_k_" + q),
            ]
    if "cellosaurus" in grups:
        p.append(("cellosaurus", "cl_tot",
                  "Línies cel·lulars a Cellosaurus (total, no només càncer)",
                  cellosaurus_total, None))
    return p


def fmt(n):
    return "{:,}".format(n).replace(",", ".")


def main():
    global UA
    ap = argparse.ArgumentParser(description="Recomptes per a un joc de cartes de recerca en càncer.")
    ap.add_argument("--contacte", required=True,
                    help="el teu correu o web; els serveis demanen identificar qui fa les peticions")
    ap.add_argument("--grups", default="uniprot,chembl,mesh,wikidata,cellosaurus")
    ap.add_argument("--sortida", default="recompte_oncologia.json")
    args = ap.parse_args()
    UA = "RecompteOncologia/0.1 (%s) python-urllib" % args.contacte
    grups = [g.strip() for g in args.grups.split(",") if g.strip()]

    wd_bons = set()
    wd_extra = {}
    wd_classes = {}
    if "wikidata" in grups:
        try:
            wd_bons = wd_valida()
        except Exception as e:
            print("   ERROR validant els identificadors: %s" % e)
        wd_extra = wd_resol()
        wd_classes = wd_resol(WD_CLASSES, PARAULES_CLASSE, "Cerca de classes per nom")
        if "Q3247516" in wd_bons:
            wd_classes["Q3247516"] = "tècniques de laboratori"

    resultats = {}
    errors = {}
    avisos = []
    grup_actual = None
    try:
        for grup, ident, desc, funcio, base in construeix(grups, wd_bons, wd_extra, wd_classes):
            if grup != grup_actual:
                print("== %s" % grup)
                grup_actual = grup
            try:
                n = funcio()
            except Exception as e:
                errors[ident] = str(e)
                print("   %-58s ERROR: %s" % (desc, e))
                continue
            resultats[ident] = n
            marca = ""
            if base in resultats and n == resultats[base] and n > 0:
                marca = "   <-- filtre sense efecte? (igual que el total)"
                avisos.append(ident)
            print("   %-58s %12s%s" % (desc, fmt(n), marca))
    except KeyboardInterrupt:
        print("\nAturat. Es mostra el que hi havia.")

    with open(args.sortida, "w", encoding="utf-8") as f:
        json.dump({"resultats": resultats, "errors": errors, "avisos": avisos},
                  f, ensure_ascii=False, indent=2)
    print("\nGuardat a %s. Recomptes: %d, errors: %d, avisos: %d."
          % (args.sortida, len(resultats), len(errors), len(avisos)))
    print("Enganxa'm tot el que ha sortit per pantalla.")


if __name__ == "__main__":
    main()
