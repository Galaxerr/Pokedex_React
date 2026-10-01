# GAL-8 — Revisione indipendente PostgreSQL 16

## Verdetto

**PASS per migrazione, schema e persistenza ORM su PostgreSQL reale; API/repository fuori perimetro M1.**

La migrazione `0001_initial_schema` è stata eseguita con `alembic upgrade head` contro
un database PostgreSQL 16 isolato e vuoto. Lo schema, le FK e gli indici richiesti sono
presenti. La suite di integrazione GAL-11 usa un database PostgreSQL dedicato e vuoto,
applica Alembic dalla fixture e rilegge i dati da una nuova sessione. API e repository
completi non sono valutati: appartengono a M2 e non sono implementati nel perimetro M1.

## Ambiente e isolamento

- Compose: servizio `postgres`, immagine `postgres:16-alpine`, porta host `5434`.
- Versione rilevata: `PostgreSQL 16.15 on x86_64-pc-linux-musl`.
- Database persistente di progetto `pokedex`: ispezionato soltanto; risultava senza tabelle
  applicative (`public_tables = 0`). Nessun dato è stato cancellato o modificato.
- Database di revisione: `gal8_review`, ruolo dedicato `gal8_review`, creato separatamente
  per questa verifica. Nessun seed eseguito.

## Comandi ed esiti

```bash
docker compose up -d postgres  # supply credentials through the local environment
docker exec pokedex_react-postgres-1 psql -U pokedex -d postgres \
  -c "CREATE ROLE gal8_review LOGIN PASSWORD '...';"
docker exec pokedex_react-postgres-1 psql -U pokedex -d postgres \
  -c "CREATE DATABASE gal8_review OWNER gal8_review;"
DATABASE_URL='postgresql+asyncpg://gal8_review:...@127.0.0.1:5434/gal8_review' \
  backend/.venv/bin/alembic upgrade head
```

Esito: upgrade riuscito, revisione `0001_initial_schema` applicata.

Verifica ORM indipendente su un secondo database vuoto isolato:

```bash
cd backend
POKEDEX_TEST_DATABASE_URL='postgresql+asyncpg://...@127.0.0.1:5434/pokedex_test_gal10_<timestamp>' \
  .venv/bin/pytest -m integration -q --tb=short
```

Esito effettivo: **1 passed, 5 deselected**, su PostgreSQL **16.15**. La fixture ha
verificato lo schema pubblico vuoto, eseguito `alembic upgrade head`, quindi il test ha
committato e riletto da una nuova `AsyncSession` un `Pokemon` con associazioni
`pokemon_type`, `pokemon_ability` e `pokemon_move`. Le credenziali non sono riportate.

```bash
backend/.venv/bin/pytest -q
```

Esito: **5 passed**.

## Prove schema

Sul database `gal8_review` sono state verificate:

- 12 tabelle applicative più `alembic_version`;
- estensione `pg_trgm` presente;
- `ix_pokemon_name_trgm`: GIN su `pokemon.name` con `gin_trgm_ops`;
- `ix_pokemon_type_type_id`: indice B-tree su `pokemon_type.type_id`;
- 12 FK: `pokemon`, `pokemon_stat`, `pokemon_type`, `pokemon_ability`,
  `pokemon_move`, `type_relation`, `evolution` verso le rispettive tabelle;
- migrazione da database vuoto isolato completata senza dipendere da seed o dati preesistenti.

## Limiti e handoff CTO

La prova copre persistenza e query ORM del modello/associazioni M1, ma non endpoint HTTP,
repository applicativo o seed; API e repository sono M2; il seed appartiene al successivo task M1 GAL-9. Il database di test
è stato lasciato intatto e il database applicativo non è stato modificato o cancellato.

File report creato: `docs/milestones/GAL8_REVIEW.md`.
