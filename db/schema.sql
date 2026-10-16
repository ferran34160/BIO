-- Esquema comú de cartes. Una fila per carta, estadístiques en JSON per categoria.
CREATE TABLE IF NOT EXISTS carta (
  id            INTEGER PRIMARY KEY,
  categoria     TEXT NOT NULL CHECK (categoria IN
                ('gen','molecula','cientific','concepte','tecnica','aparell','reactiu','linia_cellular','descobriment')),
  nom           TEXT NOT NULL,
  font          TEXT NOT NULL,            -- uniprot, mesh, wikidata, cellosaurus, manual...
  font_id       TEXT,                     -- identificador a la font (NULL = pendent de resoldre)
  definicio     TEXT,
  definicio_font TEXT,                    -- d'on ve la definició (obligatori si hi ha definició)
  imatge_url    TEXT,
  imatge_autor  TEXT,
  imatge_llicencia TEXT,
  popularitat   REAL,                     -- mesura bruta, depèn de la categoria
  popularitat_tipus TEXT,                 -- p. ex. 'articles_pubmed', 'llengues_wikipedia'
  raresa        TEXT CHECK (raresa IN ('comuna','poc_comuna','rara','epica','llegendaria')),
  estadistiques TEXT,                     -- JSON: {"cromosoma":"17","longitud_aa":393}
  coleccions    TEXT,                     -- llista separada per comes: 'cancer,supressors'
  verificada    INTEGER NOT NULL DEFAULT 0,
  UNIQUE (font, font_id)
);
CREATE INDEX IF NOT EXISTS ix_carta_cat ON carta(categoria);
