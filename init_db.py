"""Crea db/cartes.sqlite, carrega el pilot i assigna la raresa per percentils dins de cada categoria."""
import csv, sqlite3, sys
from pathlib import Path

ARREL = Path(__file__).parent
# (percentil mínim, raresa): el 50% més baix és comú, el 1% més alt llegendari
LLINDARS = [(0.99, "llegendaria"), (0.95, "epica"), (0.80, "rara"), (0.50, "poc_comuna"), (0.0, "comuna")]

def assigna_raresa(con):
    for (cat,) in con.execute("SELECT DISTINCT categoria FROM carta").fetchall():
        files = con.execute("SELECT id FROM carta WHERE categoria=? ORDER BY popularitat, id", (cat,)).fetchall()
        n = len(files)
        for i, (cid,) in enumerate(files):
            pct = i / n if n > 1 else 0.0
            raresa = next(r for p, r in LLINDARS if pct >= p)
            con.execute("UPDATE carta SET raresa=? WHERE id=?", (raresa, cid))

def main(db=ARREL / "db" / "cartes.sqlite"):
    con = sqlite3.connect(db)
    con.executescript((ARREL / "db" / "schema.sql").read_text(encoding="utf-8"))
    with open(ARREL / "pilot" / "pilot.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if con.execute("SELECT 1 FROM carta WHERE categoria=? AND nom=?", (r["categoria"], r["nom"])).fetchone():
                continue  # font_id pot ser NULL i UNIQUE no ho detecta
            con.execute(
                "INSERT INTO carta (categoria,nom,font,font_id,coleccions,popularitat,popularitat_tipus,estadistiques)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (r["categoria"], r["nom"], r["font"], r["font_id"] or None, r["coleccions"] or None,
                 float(r["popularitat"]), r["popularitat_tipus"], r["estadistiques"] or None))
    assigna_raresa(con)
    con.commit()
    for row in con.execute("SELECT categoria, nom, raresa FROM carta ORDER BY categoria, popularitat"):
        print(*row, sep=" | ")

if __name__ == "__main__":
    main(*sys.argv[1:])
