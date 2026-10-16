# Projecte: joc de cartes col·leccionables de biomedicina (amb el càncer com a col·lecció destacada)

Document de context per continuar el projecte. Resumeix el que l'usuari ha decidit, el que s'ha comprovat amb dades reals i el que encara és obert. Les coses marcades com a **proposta** les va suggerir Claude i **l'usuari encara no les ha confirmades**.

L'usuari parla català: respon-li en català.

Aquest projecte és **independent** del joc de cartes d'esports (una altra carpeta i un altre `CLAUDE.md`). N'hereta el mètode, no el contingut.

## 1. Què és

Joc de cartes col·leccionables, inspirat en la idea de **WikiMasters** (https://wiki-masters.com): cartes que surten de dades obertes reals, sobres a l'atzar, àlbum, col·leccions que cadascú tria. No es vol copiar WikiMasters, sinó aplicar la idea a un altre tema.

Tema: **recerca biomèdica**, amb **el càncer com a col·lecció destacada** (decisió de l'usuari). Cartes sobre descobriments, definicions, científics, molècules, gens i proteïnes, tècniques de laboratori, aparells, productes/reactius i línies cel·lulars.

## 2. Decisions de l'usuari

- **Abast: biomedicina àmplia, amb el càncer com a col·lecció destacada.** No un joc només de càncer.
- **És un experiment personal**, que es pot compartir amb l'equip del laboratori si queda bé.
- **No s'ha d'associar a cap institució ni laboratori** (ni noms, ni logos, ni dades internes).
- **Categories volgudes:** descobriments, definicions, científics, molècules, **tècniques de laboratori, aparells i productes** (aquestes tres ho va demanar explícitament).
- **Filosofia heretada del joc d'esports (decisions de l'usuari allà):** menys cartes que WikiMasters però totes ben fetes (amb imatge, informació completa); el nucli és col·leccionar el que cadascú vulgui; els duels entre amics no són prioritaris; res de diners reals; missions amb insígnies i/o monedes.
- **Fonts gratuïtes d'Internet**; sense pagar per dades.

## 3. Propostes de Claude (pendents de confirmar)

- **Productes:** només tipus genèrics (p. ex. «citòmetre de flux»), **sense marques, models, kits ni anticossos concrets** (logos i fotos de catàleg amb drets, i no hi ha font oberta). Reactius químics sí (DMSO, tripsina...).
- **Raresa per percentils dins de cada categoria**, no pel valor brut. Mesura de popularitat diferent per categoria (a verificar): gens → nombre d'articles publicats (NCBI gene2pubmed, de memòria); científics → nombre de llengües de la Viquipèdia o cites (OpenAlex); conceptes i tècniques → mencions a PubMed; aparells → llengües de la Viquipèdia.
- **Estadístiques reals a les cartes** (en lloc de popularitat/llargada): gens (cromosoma, longitud de la proteïna), molècules (pes molecular), científics (any de naixement, premis), tècniques i aparells (any d'invenció, qui els va crear).
- **Protocols com a missions** (el que diferencia el joc): una missió demana combinar cartes, p. ex. «munta una PCR» = termociclador + polimerasa + encebadors + gel d'agarosa. Serien unes quantes desenes, fetes a mà.
- **Economia heretada de l'esport:** destruir cartes dona monedes, fabricar cartes concretes amb monedes, confirmació abans de destruir, límit diari de monedes per missions. Mercat entre jugadors a la fase 2.
- **Línies cel·lulars només amb llindar de popularitat** (p. ex. les més citades), perquè la majoria són desconegudes. Descriure HeLa (Henrietta Lacks) amb respecte.

## 4. Dades comprovades (recomptes reals, executats a l'ordinador de l'usuari el 2026-10-16)

Script: `recompte_oncologia.py` (només biblioteca estàndard de Python; `--contacte <correu>` obligatori; `--grups uniprot,chembl,mesh,wikidata,cellosaurus`). Només compta, no baixa dades. Guarda el resultat a `recompte_oncologia.json`.

| Categoria | Recompte | Notes |
|---|---|---|
| Proteïnes humanes revisades (UniProt/Swiss-Prot) | 20.431 | 8.856 amb estructura 3D |
| Proto-oncògens (KW-0656) / supressors tumorals (KW-0043) | 231 / 187 | 197 amb malaltia anotada que esmenta «cancer» |
| Descriptors MeSH | 30.594 | 30.412 amb definició (scope note). Alguns són massa genèrics (p. ex. «Humans») |
| MeSH Neoplasmes (arbre C04) | 703 | |
| MeSH Tècniques d'investigació (E05) / Equipament (E07) | 1.213 / 345 | Tots amb definició; E07 barreja material clínic i de laboratori (inferit, no comprovat) |
| Biòlegs, genetistes, químics, metges amb foto i data de naixement (Wikidata) | 3.505 / 739 / 6.339 / 22.527 | Els metges són en la major part aliens al càncer |
| Bioquímics, biòlegs moleculars, immunòlegs, farmacòlegs, oncòlegs (amb foto) | 1.270 / 329 / 385 / 515 / 314 | Hi ha solapament entre ocupacions |
| Persones amb camp de treball «oncologia» amb foto | 111 | |
| Premis Nobel de Fisiologia o Medicina | 236 (229 amb foto) | |
| Substàncies amb codi ATC L01 (antineoplàstics) a Wikidata | 229 | 165 amb estructura química |
| Tipus d'aparells de laboratori / instruments científics (subclasses a Wikidata) | 589 / 734 | 215 / 312 amb imatge |
| Tipus de tècniques de laboratori (Wikidata, Q3247516) | 767 | **només 52 amb imatge** |
| Línies cel·lulars (Cellosaurus, v56.0, 2026-06-25) | 168.970 | No se sap quantes són tumorals. No s'han pogut filtrar per l'API |

**ChEMBL:** des de l'ordinador de l'usuari dona sempre **HTTP 500** (també al navegador); des del núvol funciona (2.921.148 compostos; la taula `drug` té 16.083 registres, sense saber què inclou). Possible bloqueig de la xarxa on treballa; provar des d'una altra xarxa. Els filtres `max_phase` semblen ignorats pel servei (retornen el total).

Estimació de cartes (Claude, a revisar): **uns 45.000–60.000** sense línies cel·lulars; només càncer, 2.000–4.000. Passar de 100.000 només és possible amb línies cel·lulars poc conegudes.

## 5. Fonts i llicències (comprovar abans de publicar)

- **Wikidata:** CC0. **MeSH:** la pàgina de l'NLM l'etiqueta com a domini públic. **NCI Thesaurus:** demana citar l'NCI com a font (>192.000 conceptes, >40.000 càncers i malalties relacionades).
- **UniProt** (de memòria CC BY 4.0), **ChEMBL** (llicència no comprovada), **Cellosaurus** (llicència no comprovada; de memòria CC BY 4.0): **comprovar-ho**.
- **Imatges de Wikimedia Commons:** lliures però **cada carta ha de mostrar autor i llicència**.
- **Definicions:** han de venir d'una font citada (MeSH, NCI), **no de text generat sense revisar**. Una definició errònia en un joc de ciència es nota. Evitar qualsevol cosa que sembli consell mèdic.

## 6. Problema principal: les imatges

Tenen imatge: científics (foto), gens amb estructura 3D (43%), molècules (es poden dibuixar a partir de l'estructura química), aparells (parcialment). **No en tenen:** conceptes MeSH (cap) i tècniques (52 de 767). Cal decidir una estratègia d'il·lustració per a aquestes cartes (dibuix esquemàtic generat amb codi, plantilles per categoria...) abans d'incloure-les. Idea a comprovar: estructures predites d'AlphaFold per als gens sense estructura 3D (llicència no comprovada).

## 7. Entorn

- Ordinador de l'usuari: Windows, Python instal·lat, executa els scripts des de la carpeta Descàrregues.
- **L'entorn núvol de Claude no pot accedir a Wikidata (proxy 403)** i només de forma limitada a altres serveis; si t'executes a l'ordinador de l'usuari, hauries de poder.
- Wikidata talla les consultes SPARQL a 60 s: cal partir-les (per anys de naixement, etc.). L'script `recompte_oncologia.py` ja ho fa.
- Perfil tècnic de l'usuari: bases de dades, scripts, R, GIS.

## 8. Preguntes obertes

1. Mesura de popularitat definitiva per categoria (secció 3) i com repartir les rareses.
2. Estratègia d'imatges per a conceptes i tècniques (secció 6).
3. Estadístiques de cada tipus de carta.
4. Quines col·leccions destacades (càncer: oncògens, supressors, antineoplàstics, Nobel, línies tumorals...) i si són curades o dinàmiques.
5. Llindar de qualitat per a conceptes MeSH (excloure els massa genèrics).
6. Fàrmacs aprovats exactes (ChEMBL no accessible des de la xarxa de l'usuari).
7. Tecnologia del joc (web, comptes d'usuari, sobres, col·lecció, missions) i si l'economia de monedes es manté tal com està.

## 9. Pla del prototip (proposta)

1. **Pilot de ~200 cartes** a mà o semiautomàtic (p. ex. TP53, BRCA1, KRAS, 20 fàrmacs, 30 científics amb Nobel, 30 conceptes, 30 tècniques, 30 aparells, 10 línies cel·lulars) per provar el disseny de la carta, el repartiment de rareses i les imatges.
2. **Pipeline de dades** per font, cap a una base de dades SQLite amb un esquema comú (identificador, categoria, nom, definició, imatge, autor i llicència, popularitat, estadístiques).
3. **Bucle de joc mínim:** sobres, col·lecció, destruir cartes per monedes, primeres missions i col·leccions.
4. La part social (mercat, gremis) només si el joc funciona.
