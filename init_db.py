"""Crea/actualitza db/cartes.sqlite, carrega pilot/pilot.csv i assigna la raresa per percentils dins de cada categoria."""
import csv, sqlite3, sys
from pathlib import Path

ARREL = Path(__file__).parent
# (percentil mínim, raresa): el 50% més baix és comú, el 1% més alt llegendari
LLINDARS = [(0.99, "llegendaria"), (0.95, "epica"), (0.80, "rara"), (0.50, "poc_comuna"), (0.0, "comuna")]
NOUS = ("etiqueta_font", "wiki_titol", "terme_pubmed")

def assigna_raresa(con):
    """Només per a cartes amb popularitat ja calculada."""
    for (cat,) in con.execute("SELECT DISTINCT categoria FROM carta WHERE popularitat IS NOT NULL").fetchall():
        files = con.execute("SELECT id FROM carta WHERE categoria=? AND popularitat IS NOT NULL ORDER BY popularitat, id", (cat,)).fetchall()
        n = len(files)
        for i, (cid,) in enumerate(files):
            pct = i / n if n > 1 else 0.0
            raresa = next(r for p, r in LLINDARS if pct >= p)
            con.execute("UPDATE carta SET raresa=? WHERE id=?", (raresa, cid))

def migra(con):
    """Afegeix les columnes noves a una base creada amb l'esquema antic."""
    existents = {r[1] for r in con.execute("PRAGMA table_info(carta)")}
    for col in NOUS:
        if col not in existents:
            con.execute(f"ALTER TABLE carta ADD COLUMN {col} TEXT")

def main(db=ARREL / "db" / "cartes.sqlite"):
    con = sqlite3.connect(db)
    con.executescript((ARREL / "db" / "schema.sql").read_text(encoding="utf-8"))
    migra(con)
    with open(ARREL / "pilot" / "pilot.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            vell = con.execute("SELECT id, popularitat_tipus FROM carta WHERE categoria=? AND nom=?",
                               (r["categoria"], r["nom"])).fetchone()
            if vell:  # font_id pot ser NULL i UNIQUE no ho detecta; actualitza només els camps de configuració
                con.execute("UPDATE carta SET coleccions=?, popularitat_tipus=?, etiqueta_font=?, wiki_titol=?, terme_pubmed=?,"
                            " popularitat=CASE WHEN popularitat_tipus IS ? THEN popularitat ELSE NULL END WHERE id=?",
                            (r["coleccions"] or None, r["popularitat_tipus"], r["etiqueta_font"] or None,
                             r["wiki_titol"] or None, r["terme_pubmed"] or None, r["popularitat_tipus"], vell[0]))
                continue
            con.execute(
                "INSERT INTO carta (categoria,nom,font,font_id,coleccions,popularitat_tipus,estadistiques,etiqueta_font,wiki_titol,terme_pubmed)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (r["categoria"], r["nom"], r["font"], r["font_id"] or None, r["coleccions"] or None,
                 r["popularitat_tipus"], r["estadistiques"] or None, r["etiqueta_font"] or None,
                 r["wiki_titol"] or None, r["terme_pubmed"] or None))
    assigna_raresa(con)
    con.commit()
    print(con.execute("SELECT COUNT(*) FROM carta").fetchone()[0], "cartes a la base de dades")

if __name__ == "__main__":
    main(*sys.argv[1:])
