# M1.2 — Seed evidence

## Implementazione

`backend/scripts/seed_from_pokeapi.py` scarica il catalogo PokéAPI, tutte le specie
referenziate, tipi ed efficacia, e normalizza abilità, mosse, statistiche e catene
evolutive. I dati vengono scaricati prima della transazione PostgreSQL; il database
viene sostituito in ordine FK-safe in una singola transazione. Un errore fa rollback
completo. `--cache-dir` è opzionale e va usato solo in un percorso ignorato.

## Comandi riproducibili

```bash
cd backend
export PATH="/home/galaxer/.local/bin:$PATH"
export UV_PYTHON=3.12
export UV_CACHE_DIR="$PWD/.cache/uv"
uv run alembic upgrade head
uv run python scripts/seed_from_pokeapi.py --database-url "$DATABASE_URL" --cache-dir .cache/pokeapi
uv run python scripts/seed_from_pokeapi.py --database-url "$DATABASE_URL" --cache-dir .cache/pokeapi
uv run pytest tests/test_seed.py tests/test_data_integrity.py
```

`--limit 3` è disponibile per una verifica rapida senza dichiarare il catalogo completo.

## Evidenza di questa esecuzione

- Bootstrap toolchain: `uv sync --directory backend --group dev` completato.
- `uv run --directory backend ruff format --check scripts/seed_from_pokeapi.py tests/test_seed.py tests/test_data_integrity.py`: OK, 3 file già formattati.
- `uv run --directory backend ruff check scripts/seed_from_pokeapi.py tests/test_seed.py tests/test_data_integrity.py`: OK.
- `uv run --directory backend mypy scripts/seed_from_pokeapi.py`: OK, nessun problema.
- `uv run --directory backend pytest tests/test_seed.py tests/test_data_integrity.py`: OK, 4 test passati.
- Verifica infrastruttura: `docker compose ps` non ha potuto interrogare Docker (`permission denied` su `/var/run/docker.sock`); `pg_isready` su localhost:5432 e localhost:5434 non ha trovato PostgreSQL.
- Seed PostgreSQL 16 completo, seconda esecuzione e confronto conteggi: non dichiarati
  qui perché non è disponibile un database PostgreSQL raggiungibile. Il CTO deve
  registrare i conteggi reali, i controlli FK, le lingue IT/EN e i campioni
  rappresentativi nel report M1 principale dopo aver eseguito i comandi sopra in un
  ambiente con PostgreSQL 16 e accesso a PokéAPI.
- Nessun dump o segreto viene scritto nel repository; la cache è ignorabile.

### Heartbeat di verifica 2026-10-01

- `uv run --directory backend pytest tests/test_seed.py tests/test_data_integrity.py`: OK, 4 test passati in 1.83 s.
- `uv run --directory backend ruff check scripts/seed_from_pokeapi.py tests/test_seed.py tests/test_data_integrity.py`: OK.
- `uv run --directory backend mypy scripts/seed_from_pokeapi.py`: OK, nessun problema.
- `pg_isready -h 127.0.0.1 -p 5432` e `pg_isready -h 127.0.0.1 -p 5434`: nessuna risposta.
- `docker ps`: non eseguibile per permesso negato su `/var/run/docker.sock`.

Il limite PostgreSQL 16 reale non è rimosso; restano da eseguire migrazione, seed doppio,
conteggi, controlli FK e campioni IT/EN in un ambiente con database raggiungibile.

## Stato di consegna

Implementazione e verifiche statiche/unitarie completate. Popolamento reale non
verificato per il blocker infrastrutturale sopra; il task non va considerato prova di
catalogo completo finché il CTO non registra una run PostgreSQL 16 riuscita.

## Revisione CTO — 2026-10-01, GAL-9

Accettazione respinta per due difetti riprodotti prima del popolamento. Il precedente
limite di raggiungibilità è superato: `pg_isready -h 127.0.0.1 -p 5434`, eseguito
dall'host con escalation ordinaria, restituisce `accepting connections`.

1. Dalla radice, `uv run --directory backend python scripts/seed_from_pokeapi.py --help`
   fallisce all'importazione con `ModuleNotFoundError: No module named 'app'`.
   Il comando documentato non è quindi eseguibile nell'ambiente attuale.
2. Il loader costruisce `species/{id}` anziché usare la risorsa `pokemon-species`.
   Riproduzione senza database, dalla radice con la toolchain sopra configurata:

   ```bash
   uv run --directory backend python - <<'PY'
   import asyncio
   import httpx
   from scripts.seed_from_pokeapi import PokeApiClient, collect_catalog
   async def check():
       async with httpx.AsyncClient(timeout=30) as client:
           await collect_catalog(PokeApiClient(client, retries=0), limit=1)
   asyncio.run(check())
   PY
   ```

   Esito reale: `RuntimeError: PokéAPI request failed after 1 attempts:
   https://pokeapi.co/api/v2/species/1`, causato da `400 Bad Request`.
   Controllo HTTP diretto: `/api/v2/species/1/` = 400;
   `/api/v2/pokemon-species/1/` = 200.

Verifiche ripetute dal CTO:

- `uv run --directory backend pytest tests/test_seed.py tests/test_data_integrity.py`:
  4 passed in 1.86 s.
- `uv run --directory backend ruff check scripts/seed_from_pokeapi.py tests/test_seed.py tests/test_data_integrity.py`:
  pass.
- `uv run --directory backend ruff format --check scripts/seed_from_pokeapi.py tests/test_seed.py tests/test_data_integrity.py`:
  3 files already formatted.
- `uv run --directory backend mypy scripts/seed_from_pokeapi.py`: pass.

I test attuali non esercitano `collect_catalog`; il test con `RecordingSession`
non prova FK né idempotenza su PostgreSQL. L'implementatore deve correggere entrypoint
e risorsa specie, aggiungere regressioni pertinenti e restituire il task al CTO.
Verificare inoltre paginazione: il loader attuale legge una sola pagina e non segue
`next`. Migrazione isolata, seed completo doppio, conteggi di tutte le tabelle,
FK, duplicati e copertura IT/EN restano da eseguire dopo le correzioni.
Nessun database modificato, nessun processo seed lasciato attivo, nessun commit.

## Correzioni implementatore — 2026-10-01

- L'entrypoint inserisce il percorso `backend` quando eseguito come script, quindi
  `uv run --directory backend python scripts/seed_from_pokeapi.py --help` ora termina
  con codice 0 e mostra le opzioni CLI.
- Le specie vengono richieste da `pokemon-species/{id}`; il precedente endpoint
  `species/{id}` non viene più costruito.
- `collect_listing` segue `next` per i listing Pokémon e tipi e rispetta `--limit`.
- Test aggiunti per paginazione, limite e endpoint specie; suite pertinente:
  `6 passed`.
- Ruff format/check e mypy del seed: superati.

Questa correzione non costituisce ancora evidenza di popolamento PostgreSQL 16:
migrazione isolata, seed completo eseguito due volte, conteggi, FK, duplicati e
copertura IT/EN devono essere verificati dal CTO nell'ambiente database disponibile.

## Seconda revisione CTO — 2026-10-01

Il precedente limite infrastrutturale è superato con escalation ordinaria. Le
correzioni entrypoint, endpoint specie e paginazione sono verificate. Nessuna
modifica al database applicativo: tutte le prove usano il container temporaneo
`pokedex-gal9-verify`, PostgreSQL **16.15**, porta host **55439**.

### Comandi realmente eseguiti dalla radice

```bash
docker run --name pokedex-gal9-verify --label paperclip.issue=GAL-9 \
  -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=gal9_verify \
  -p 127.0.0.1:55439:5432 -d postgres:16-alpine
export PATH="/home/galaxer/.local/bin:$PATH"
export UV_PYTHON=3.12 UV_CACHE_DIR="$PWD/backend/.cache/uv"
export DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55439/gal9_verify"
uv run --directory backend alembic upgrade head
uv run --directory backend python scripts/seed_from_pokeapi.py --cache-dir .cache/pokeapi
uv run --directory backend python scripts/seed_from_pokeapi.py --cache-dir .cache/pokeapi
docker exec pokedex-gal9-verify createdb -U postgres gal9_test
export POKEDEX_TEST_DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55439/gal9_test"
uv run --directory backend pytest
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
uv run --directory backend mypy app scripts/seed_from_pokeapi.py
uv run --directory backend python scripts/seed_from_pokeapi.py --help
```

Il container è usa e getta, senza credenziali e con porta esposta solo su loopback;
questa configurazione non è destinata all’applicazione. Alembic ha migrato uno
schema pulito a `0001_initial_schema`. Suite: **12 passed in 3.34 s**; Ruff check
pass; format **45 files already formatted**; mypy **33 source files**, pass;
entrypoint help exit 0. Due tentativi iniziali della suite hanno dato 11 passed e
1 errore di configurazione: URL test assente, poi nome `gal9_tests` rifiutato dalla
protezione della fixture. L’esecuzione finale usa `gal9_test` conforme e pulito.

### Primo seed completo e audit

Primo seed CLI: exit 0, transazione completata. Attesi sotto = righe normalizzate
dalla sorgente raccolta; non sono automaticamente i totali dei listing ufficiali.

| Tabella | Atteso dalla raccolta | Osservato primo seed |
| --- | ---: | ---: |
| pokemon | 1351 | 1351 |
| species | 1025 | 1025 |
| type | 21 | 21 |
| pokemon_stat | 8106 | 8106 |
| pokemon_type | 2116 | 2116 |
| type_relation | 120 | 120 |
| ability | 313 | 313 |
| pokemon_ability | 2943 | 2943 |
| move | 833 | 833 |
| pokemon_move | 638321 | 638321 |
| evolution | 485 | 485 |

Audit SQL: zero gruppi duplicati sulle colonne sorgente in tutte le 11 tabelle,
zero riferimenti orfani su tutte le 12 FK. Per JSON si usa cast `::jsonb` nel
raggruppamento. Un primo tentativo del solo script di audit falliva perché JSON
non ha operatore di uguaglianza; corretto il cast, audit passato. Questo non era
un difetto del seed. Lingue: **898 IT**, **1025 EN**, uguali alle disponibilità
nei payload specie. Campioni letti: Bulbasaur (altezza 7, peso 69), Pikachu (4,60),
Mewtwo (20,1220), Deoxys Attack (17,608), Pecharunt (3,3). Testi IT/EN presenti nei
primi quattro; Pecharunt ha EN e non IT anche nella sorgente. Esempio IT Bulbasaur:
«Alla nascita gli è stato piantato sulla schiena un seme raro. La pianta sboccia e
cresce con lui.»

Query riproducibili (psql sul container isolato):

```sql
SELECT count(*) FROM pokemon;
SELECT count(*) FILTER (WHERE flavor_text::jsonb ? 'it') AS it,
       count(*) FILTER (WHERE flavor_text::jsonb ? 'en') AS en FROM species;
SELECT count(*) FROM pokemon p LEFT JOIN species s ON s.id=p.species_id
WHERE p.species_id IS NOT NULL AND s.id IS NULL;
SELECT pokemon_id,move_id,version_group,level,method,count(*)
FROM pokemon_move GROUP BY pokemon_id,move_id,version_group,level,method
HAVING count(*) > 1;
SELECT p.name,s.flavor_text->>'it',s.flavor_text->>'en'
FROM pokemon p JOIN species s ON s.id=p.species_id
WHERE p.id IN (1,25,150,1025,10001);
```

### Difetto di completezza riscontrato

Il catalogo ufficiale restituisce **374 abilità** e **937 mosse**, mentre il seed
inserisce solamente le **313 abilità** e **833 mosse** referenziate nei dettagli
Pokémon: mancano **61 abilità e 104 mosse**. Pokémon, specie e tipi coincidono con
i listing ufficiali (1351,1025,21). Esempi mancanti: abilità `embody-aspect`,
`mountaineer`; mosse `struggle`, `happy-hour`, `celebrate`, `hold-hands`, `hold-back`.
Non è accettabile attestare il catalogo completo confrontando soltanto il DB con
il sottoinsieme prodotto dallo stesso loader.

Riproduzione dei conteggi ufficiali:

```bash
backend/.venv/bin/python - <<'PY'
import httpx
for endpoint in ("pokemon", "pokemon-species", "type", "ability", "move"):
    response = httpx.get(f"https://pokeapi.co/api/v2/{endpoint}?limit=1", timeout=30)
    response.raise_for_status()
    print(endpoint, response.json()["count"])
PY
docker exec pokedex-gal9-verify psql -U postgres -d gal9_verify -c \
  "SELECT count(*) FROM ability; SELECT count(*) FROM move; SELECT * FROM move WHERE name='struggle';"
```

Correzione richiesta all’implementatore esistente: acquisire i listing paginati
completi di ability e move, preservare le associazioni, aggiungere regressioni con
risorse non referenziate da Pokémon e prova di copertura contro i listing. Nessuna
modifica richiesta allo schema già accettato. Poi restituire questo stesso task
al CTO per nuovo doppio seed pulito e audit. Nessun commit autorizzabile finché
le prove di completezza non passano; M2 ferma.

### Esito secondo seed e disposizione

Secondo seed CLI: **exit 0**, stessi conteggi della tabella precedente per tutte
le 11 tabelle. Secondo audit: **PASS**, conteggi attesi/osservati invariati,
zero duplicati e zero orfani sulle 12 FK; lingue e campioni identici al primo audit.
Conferma SQL del difetto: ability=313, move=833, `WHERE name='struggle'` = 0 righe.

Accettazione finale **sospesa per difetto di copertura**, non per infrastruttura né
per idempotenza. File M1.2 nel working tree (`git status --short`): README.md,
backend/scripts/seed_from_pokeapi.py, backend/tests/test_data_integrity.py,
backend/tests/test_seed.py, docs/milestones/M1_SEED_EVIDENCE.md. In questa revisione
CTO è stato modificato solo il documento di evidenza. Nessun commit, nessun push.
Il container temporaneo verrà rimosso al termine delle prove; la cache sorgente
resta in backend/.cache/pokeapi, ignorata, per agevolare la correzione.

## Correzione copertura anagrafiche — 2026-10-01

Il loader ora acquisisce anche i listing paginati ufficiali `ability` e `move`
(seguendo `next`) prima di elaborare i dettagli Pokémon. Le associazioni
`pokemon_ability` e `pokemon_move` continuano a essere derivate dai dettagli,
mentre le anagrafiche non referenziate non vengono più perse.

Regressioni aggiunte in `backend/tests/test_seed.py`: una risorsa ability e una
move presenti solo nei listing vengono conservate, e la paginazione del listing
ability viene verificata indipendentemente dalle associazioni Pokémon.

Verifiche eseguite dopo la correzione:

- `uv run --directory backend ruff format --check scripts/seed_from_pokeapi.py tests/test_seed.py tests/test_data_integrity.py`: OK dopo formattazione Ruff.
- `uv run --directory backend ruff check scripts/seed_from_pokeapi.py tests/test_seed.py tests/test_data_integrity.py`: OK.
- `uv run --directory backend mypy scripts/seed_from_pokeapi.py`: OK, nessun problema.
- `uv run --directory backend pytest tests/test_seed.py tests/test_data_integrity.py`: **7 passed** in 1.84 s.

Il doppio seed PostgreSQL 16 e il confronto indipendente dei conteggi ufficiali
devono essere rieseguiti dal CTO su un database isolato pulito; questa modifica
non ha toccato alcun database e non costituisce da sola accettazione M1.2.


## Verifica finale CTO — 2026-10-02

Ripresa dopo interruzione del runtime. Container nuovo `pokedex-gal9-20261002`,
PostgreSQL 16.15, database `gal9_verify`, porta loopback 55439; database applicativo
intatto. Alembic da schema vuoto a `0001_initial_schema`: PASS.

Primo seed completo: exit 0. Audit indipendente via httpx, senza loader né cache
per le liste: paginazione `limit=200`, `next` seguita fino a null. Confrontati gli
insiemi degli ID, non soltanto i conteggi. Pokémon 1351 (7 pagine), specie 1025
(6), tipi 21 (1), abilità 374 (2), mosse 937 (5), catene 540 (3): nessun ID
mancante o extra. Le catene sono rappresentate da `species.evolution_chain_id`,
mentre `evolution` contiene gli archi, non una riga per catena.

Suite completa: **13 passed in 2.94 s**; Ruff check PASS; format 45 file conformi;
mypy app + seed PASS su 33 file. Testi di tutte le 1025 specie confrontati con i
payload sorgente: corrispondenza esatta dopo normalizzazione; 898 IT e 1025 EN.
Controlli rappresentativi PASS: Bulbasaur erba/veleno, abilità nascosta chlorophyll,
Bulbasaur → Ivysaur al livello 16, fuoco → erba ×2, tackle associata a Bulbasaur,
mosse non referenziate struggle e happy-hour presenti. Campioni Pokémon:
Bulbasaur, Pikachu, Mewtwo, Pecharunt e Deoxys Attack, incluse varietà.

### Riproduzione di questa revisione

Dalla radice del workspace (toolchain e Docker installati):

```bash
docker run --name pokedex-gal9-20261002 --label paperclip.issue=GAL-9 \
  -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=gal9_verify \
  -p 127.0.0.1:55439:5432 -d postgres:16-alpine
export PATH="/home/galaxer/.local/bin:$PATH"
export UV_PYTHON=3.12 UV_CACHE_DIR="$PWD/backend/.cache/uv"
export DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55439/gal9_verify"
uv run --directory backend alembic upgrade head
uv run --directory backend python scripts/seed_from_pokeapi.py --cache-dir .cache/pokeapi
# Eseguire audit.py sotto, quindi ripetere seed e audit.
uv run --directory backend python scripts/seed_from_pokeapi.py --cache-dir .cache/pokeapi
docker exec pokedex-gal9-20261002 createdb -U postgres gal9_test
export POKEDEX_TEST_DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55439/gal9_test"
uv run --directory backend pytest
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
uv run --directory backend mypy app scripts/seed_from_pokeapi.py
```

La cache dei dettagli proviene dalle acquisizioni del 2026-10-01; i listing
indipendenti sono stati letti online durante ciascun audit del 2026-10-02.
Il test unitario RecordingSession non viene usato come prova di idempotenza SQL:
questa è verificata dai due seed reali e dai relativi audit.

### Script audit riproducibili

Salvare i blocchi seguenti nello scratch runtime come `audit.py` e `relations.py`;
eseguire dalla radice con `backend/.venv/bin/python <percorso-script>`.
Gli URL sono esclusivamente quelli del database temporaneo privo di password.


#### audit.py

```python
import asyncio,json,sys
import httpx,asyncpg
async def main():
 db=await asyncpg.connect('postgresql://postgres@127.0.0.1:55439/gal9_verify')
 result={'version':await db.fetchval('select version()'),'catalogs':{},'tables':{},'orphans':{}}
 async with httpx.AsyncClient(timeout=60) as client:
  for endpoint,table in [('pokemon','pokemon'),('pokemon-species','species'),('type','type'),('ability','ability'),('move','move'),('evolution-chain',None)]:
   url=f'https://pokeapi.co/api/v2/{endpoint}?limit=200&offset=0'; ids=set(); pages=0
   while url:
    resp=await client.get(url);resp.raise_for_status(); data=resp.json();pages+=1
    ids.update(int(x['url'].rstrip('/').split('/')[-1]) for x in data['results']);url=data['next']
   actual=set(await db.fetchval('select array_agg(id) from "'+table+'"')) if table else set(await db.fetchval('select array_agg(distinct evolution_chain_id) from species'))
   result['catalogs'][endpoint]={'official':data['count'],'listed':len(ids),'pages':pages,'db':len(actual),'missing':sorted(ids-actual),'extra':sorted(actual-ids)}
  tables=await db.fetch("select tablename from pg_tables where schemaname='public' and tablename<>'alembic_version' order by tablename")
  for row in tables:
   t=row[0]; cols=await db.fetch("select column_name,data_type from information_schema.columns where table_schema='public' and table_name=$1 order by ordinal_position",t)
   group=','.join('"'+c[0]+'"'+('::jsonb' if c[1]=='json' else '') for c in cols if c[0]!='id' or t in ['pokemon','species','type','ability','move'])
   result['tables'][t]={'count':await db.fetchval(f'select count(*) from "{t}"'),'duplicates':await db.fetchval(f'select count(*) from (select {group} from "{t}" group by {group} having count(*)>1) x')}
  fks=await db.fetch("""select c.conname,c.conrelid::regclass::text as src,c.confrelid::regclass::text as dst,a.attname as scol,b.attname as dcol from pg_constraint c join pg_attribute a on a.attrelid=c.conrelid and a.attnum=c.conkey[1] join pg_attribute b on b.attrelid=c.confrelid and b.attnum=c.confkey[1] where c.contype='f' and c.connamespace='public'::regnamespace""")
  for f in fks:
   result['orphans'][f['conname']]=await db.fetchval(f'''select count(*) from {f['src']} s left join {f['dst']} d on s."{f['scol']}"=d."{f['dcol']}" where s."{f['scol']}" is not null and d."{f['dcol']}" is null''')
  result['languages']=dict(await db.fetchrow("select count(*) filter(where flavor_text::jsonb ? 'it') as it,count(*) filter(where flavor_text::jsonb ? 'en') as en from species"))
  result['samples']=[dict(r) for r in await db.fetch("select p.id,p.name,p.height,p.weight,s.flavor_text->>'it' as it,s.flavor_text->>'en' as en from pokemon p join species s on p.species_id=s.id where p.id in (1,25,150,1025,10001) order by p.id")]
 await db.close(); print(json.dumps(result,ensure_ascii=False,indent=2))
asyncio.run(main())
```

#### relations.py

```python
import asyncio,json
from pathlib import Path
import asyncpg
async def main():
 db=await asyncpg.connect("postgresql://postgres@127.0.0.1:55439/gal9_verify")
 cache=Path("backend/.cache/pokeapi")
 languages={"it":0,"en":0}
 for row in await db.fetch("select id,flavor_text from species"):
  source=json.loads((cache/f"pokemon-species_{row[0]}.json").read_text())
  expected={}
  for entry in source["flavor_text_entries"]:
   lang=entry["language"]["name"]; text=" ".join(entry["flavor_text"].split())
   if text and lang not in expected: expected[lang]=text
  assert json.loads(row[1])==expected,row[0]
  for lang in languages: languages[lang]+=lang in expected
 assert await db.fetchval("select count(*) from evolution where from_species_id=1 and to_species_id=2 and trigger='level-up' and min_level=16")==1
 assert await db.fetchval("select count(*) from pokemon_type where pokemon_id=1 and type_id in (12,4)")==2
 assert await db.fetchval("select count(*) from pokemon_ability where pokemon_id=1 and ability_id=34 and is_hidden")==1
 assert await db.fetchval("select multiplier from type_relation where attacker_type=10 and defender_type=12")==2
 assert await db.fetchval("select count(*) from pokemon_move where pokemon_id=1 and move_id=33")>0
 assert await db.fetchval("select count(*) from move where name in ('struggle','happy-hour')")==2
 print("PASS: all 1025 species texts match source; languages",languages,"; representative evolution/types/hidden ability/type efficacy/moves/unreferenced moves verified")
 await db.close()
asyncio.run(main())
```

### Esito conclusivo

Secondo seed: exit 0. I due audit JSON sono identici: cataloghi completi,
conteggi stabili, zero duplicati nelle 11 tabelle, zero orfani sulle 12 FK,
lingue e campioni stabili. Accettazione tecnica M1.2: **PASS**.

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

File di implementazione/evidenze M1.2 rilevati con `git status --short`:
README.md; backend/scripts/seed_from_pokeapi.py; backend/tests/test_data_integrity.py;
backend/tests/test_seed.py; docs/milestones/M1_SEED_EVIDENCE.md.
Nessun segreto runtime inserito nei file; cache esclusa da `.gitignore`.

Commit locale autorizzato dopo queste prove:
`feat(seed): populate complete PokeAPI catalog with verification evidence`
con trailer `Co-Authored-By: Paperclip <noreply@paperclip.ing>`.
Nessun push. M2 resta ferma; il report finale M1 è responsabilità CTO sul padre GAL-7.

Pulizia verificata: `docker rm -f pokedex-gal9-20261002` riuscito dopo la
seconda verifica delle relazioni. Nessun processo seed rimasto attivo.
