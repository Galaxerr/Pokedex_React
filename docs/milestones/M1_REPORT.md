# M1 — Backend dati: report finale

Data: 2026-10-02. Responsabile: CTO. Esito: **completata**.

## Attività completate

- Modelli SQLAlchemy async, relazioni e tabelle associative; migrazione Alembic
  `0001_initial_schema`, PostgreSQL 16, pg_trgm, GIN su pokemon.name e indice
  pokemon_type.type_id.
- Seed httpx del catalogo completo, paginazione, normalizzazione e importazione
  transazionale con ordine compatibile con le FK; rilancio senza duplicati.
- Test ORM su database isolato e regressioni del seed, inclusi risorse non
  referenziate, paginazione ed entrypoint CLI.
- Accettati [GAL-8](/GAL/issues/GAL-8), [GAL-11](/GAL/issues/GAL-11),
  [GAL-10](/GAL/issues/GAL-10) e [GAL-9](/GAL/issues/GAL-9).
  Nessuna API M2 implementata.

## Evidenze e verifiche eseguite

Le prove PostgreSQL già concluse non sono state ripetute in questo heartbeat.
Fonti dettagliate, con comandi ed errori precedenti conservati:
[ORM](GAL8_POSTGRES_TESTS.md), [revisione indipendente](GAL8_REVIEW.md),
[seed e audit riproducibili](M1_SEED_EVIDENCE.md).

- PostgreSQL **16.15**: migrazione da database vuoto PASS; schema, FK, pg_trgm
  e indici richiesti PASS. Persistenza e rilettura ORM da nuova sessione,
  comprese associazioni molti-a-molti: PASS.
- Verifica finale GAL-9: **13 test passati**, Ruff check PASS, Ruff format
  **45 file conformi**, mypy app + seed **33 file**, PASS.
- Due seed completi su container temporaneo nuovo: entrambi exit 0. Confronto
  indipendente degli ID con listing PokéAPI letti online in ciascun audit:
  Pokémon 1351, specie 1025, tipi 21, abilità 374, mosse 937, catene 540;
  nessun ID mancante o aggiuntivo. Le catene sono rappresentate dagli ID nelle
  specie; la tabella evolution contiene gli archi.
- Zero duplicati nelle 11 tabelle e zero orfani sulle 12 FK in entrambi gli audit.
  Verificate relazioni tipi, abilità nascosta, evoluzione, efficacia e mosse di
  Bulbasaur; presenti anche mosse non referenziate dai Pokémon.
- Testi di tutte le specie corrispondenti ai payload sorgente normalizzati:
  **898 IT, 1025 EN**. Le altre 127 specie non hanno testo IT nella sorgente;
  non sono state inventate traduzioni.
- Database applicativo intatto; container finale temporaneo rimosso.
- Verifica aggiuntiva di chiusura GAL-7: avvio reale Uvicorn su loopback porta
  58417, `GET /openapi.json` HTTP **200**, arresto pulito. Nessun server residuo.
- Struttura backend/frontend preservata, nessuna cartella pokedex annidata;
  nessun riferimento PokéAPI/httpx in backend/app. Scansione euristica di 49
  file sorgente/evidenza: zero chiavi private o token riconoscibili, zero file
  oltre 1 MB. Non è una garanzia assoluta di assenza di segreti; cache, .env e
  dipendenze sono escluse tramite .gitignore e non compaiono nello status.

| Tabella | Primo seed | Secondo seed |
| --- | ---: | ---: |
| ability | 374 | 374 |
| evolution | 485 | 485 |
| move | 937 | 937 |
| pokemon | 1351 | 1351 |
| pokemon_ability | 2943 | 2943 |
| pokemon_move | 638321 | 638321 |
| pokemon_stat | 8106 | 8106 |
| pokemon_type | 2116 | 2116 |
| species | 1025 | 1025 |
| type | 21 | 21 |
| type_relation | 120 | 120 |

## File creati/modificati e versionamento

`git status --short` all'inizio di questo heartbeat: vuoto. Implementazione ed
evidenze erano già state committate con le deroghe circoscritte autorizzate:
`3c32592` (schema/test ORM) e `967ab50` (seed/test/evidenze). Identificativi ricavati
dalle consegne Paperclip, senza consultare la storia Git e senza ripetere commit.

Lo status rilevato durante la revisione seed, conservato nell'evidenza, elencava:
README.md, backend/scripts/seed_from_pokeapi.py,
backend/tests/test_data_integrity.py, backend/tests/test_seed.py,
docs/milestones/M1_SEED_EVIDENCE.md. Modelli/migrazione e test ORM sono documentati
nei report GAL-8; non si ricostruisce retroattivamente uno status dopo il commit.

Unico file nuovo di questa chiusura, da `git status --short`:

```text
?? docs/milestones/M1_REPORT.md
```

Nessun nuovo commit, add, push, PR o lettura di .git in questo heartbeat.

## Come verificare manualmente

Dalla radice, per ripetere la prova completa su un container isolato nuovo:

```bash
docker run --name pokedex-m1-check -e POSTGRES_HOST_AUTH_METHOD=trust \
  -e POSTGRES_DB=gal9_verify -p 127.0.0.1:55439:5432 -d postgres:16-alpine
docker exec pokedex-m1-check pg_isready -U postgres -d gal9_verify
export PATH="/home/galaxer/.local/bin:$PATH"
export UV_PYTHON=3.12 UV_CACHE_DIR="$PWD/backend/.cache/uv"
export DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55439/gal9_verify"
uv run --directory backend alembic upgrade head
uv run --directory backend python scripts/seed_from_pokeapi.py --cache-dir .cache/pokeapi
# Eseguire audit.py e relations.py documentati in M1_SEED_EVIDENCE.md.
uv run --directory backend python scripts/seed_from_pokeapi.py --cache-dir .cache/pokeapi
# Ripetere gli audit e confrontare gli output.
docker exec pokedex-m1-check createdb -U postgres gal9_test
export POKEDEX_TEST_DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55439/gal9_test"
uv run --directory backend pytest
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
uv run --directory backend mypy app scripts/seed_from_pokeapi.py
uv run --directory backend uvicorn app.main:app --host 127.0.0.1 --port 58417
# In un secondo terminale:
curl --fail http://127.0.0.1:58417/openapi.json
# Fermare Uvicorn con Ctrl-C; rimuovere soltanto il container temporaneo:
docker rm -f pokedex-m1-check
```

Attendere `accepting connections` prima di migrare. Configurazione trust solo per
questo container usa e getta esposto su loopback. Ogni nuova esecuzione del test
ORM richiede un database vuoto distinto: il guard rifiuta database non vuoti,
nomi non test, host remoti e driver non PostgreSQL. Il seed sostituisce i dati
nelle tabelle gestite: usare esclusivamente il database temporaneo per queste prove.

## Limiti e decisioni

- Cataloghi online osservati il 2026-10-02; dettagli dalla cache acquisita il
  2026-10-01. I totali upstream possono cambiare: gli audit confrontano gli ID
  correnti, non assumono costanti.
- Il report indipendente GAL-8 riporta «12 tabelle applicative più alembic_version»;
  l'audit finale enumera **11 tabelle applicative**, più alembic_version.
  Si usa il conteggio finale effettivo, distinguendolo dalle **12 FK**.
- Popolamento di accettazione solo isolato, non del database applicativo.
- Avvertenza Tailwind e sette vulnerabilità npm segnalate in M0 restano limiti
  ereditati, non rivalutati in M1; nessuna attività frontend/M6 aggiunta.
- Paperclip raggiungibile dal contesto host autorizzato; il fallimento di accesso
  dalla sandbox non costituisce indisponibilità del servizio.

## Commit suggerito e prossimo passo

`docs(milestone): record M1 backend data acceptance`

Il commit suggerito riguarda questo report finale; i due commit tecnici sono già
completati. Il CEO notifica il board e attende la conferma esplicita
«commit fatto, procedi con M2». CTO e sotto-agenti restano fermi; nessun lavoro M2,
neppure preparatorio, è autorizzato dalla chiusura M1.
