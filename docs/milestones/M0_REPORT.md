# M0 — Scaffolding Pokédex

Data: 2026-09-30. Responsabile: CTO. Milestone completata; M1 non autorizzata.

## Cosa è stato fatto

- [GAL-4](/GAL/issues/GAL-4): scaffold FastAPI/Python 3.12, uv e lockfile, Ruff/mypy/pytest, percorsi backend inerti.
- [GAL-5](/GAL/issues/GAL-5): scaffold React 18/TypeScript/Vite, Tailwind, ESLint/Prettier/Vitest, test smoke, placeholder dei percorsi frontend. Consegna già accettata e chiusa dal CTO; [report originale conservato](/GAL/issues/GAL-5#document-completion-report). Nessuna riassegnazione per ripetere lavoro completato.
- [GAL-6](/GAL/issues/GAL-6): Compose frontend/backend/PostgreSQL 16/Redis, Nginx statico e proxy, CI solo file, ignore/env, README e configurazione pre-commit.
- Integrazione CTO: Docker backend usa uv.lock e ambiente /opt/venv, non nascosto dal bind mount; .dockerignore nei due effettivi contesti di build; esclusione cache e tsbuildinfo; placeholder public e test richiesti; aggiunta tooling pre-commit, MSW e openapi-typescript ai lockfile; controlli format in CI; hook locali configurati, mai installati.
- Workspace condiviso direttamente nella radice assegnata. Un solo specialista, nessuna nuova assunzione in questo heartbeat. Nessun modello, migrazione, seed, API Pokémon, health applicativo o funzionalità delle milestone successive implementato. Il percorso shadcn/ui è predisposto, senza generare componenti di prodotto.

## Verifiche eseguite ed esito

Verifiche CTO del 30 settembre, sul risultato integrato. I controlli frontend sono verifica finale dell'integrazione, non lavoro riassegnato allo specialista.

| Verifica | Esito ed evidenza |
| --- | --- |
| `uv sync --locked` | PASS, 64 pacchetti risolti, 62 installati/controllati nell'ambiente di sviluppo |
| `uv run ruff format --check .` | PASS, 39 file formattati |
| `uv run ruff check .` | PASS |
| `uv run mypy app` | PASS, 32 file sorgente |
| `uv run pytest` | PASS, 1 test in 0,31 s; nessun test di dominio anticipato |
| Uvicorn reale, GET `/openapi.json` | HTTP 200; startup e shutdown completi nei log. Arresto intenzionale SIGTERM, returncode -15; non interpretato come errore di avvio |
| `npm run format` | PASS |
| `npm run lint` | PASS |
| `npm run typecheck` | PASS |
| `npm test` | PASS, 1 test Vitest/Testing Library |
| `npm run build` | PASS, 31 moduli, build Vite in 1,12 s |
| Vite reale, GET `/` | HTTP 200, entrypoint src/main.tsx presente; arresto con exit 0 |
| `POSTGRES_PASSWORD=validation-only docker compose config --quiet` | PASS |
| `POSTGRES_PASSWORD=validation-only docker compose build` | PASS, entrambe le immagini costruite; npm ci e build frontend eseguiti anche nell'immagine Node 22 |
| Struttura | PASS: 72 percorsi richiesti presenti, nessuna radice pokedex annidata |
| Revisione confini M0 | Placeholder inerti; nessuna richiesta PokéAPI né persistenza implementata |
| Scansione segreti | 105 file sorgente/configurazione ispezionati con pattern per chiavi private/token; zero corrispondenze. Nessun file .env presente; esempi con soli placeholder |

Ambiente locale: Python 3.12.3, uv 0.11.15, Node 24.11.0, npm 11.6.1; Docker Engine 29.6.0, Compose 5.1.4. Build container: Python 3.12 e Node 22. Gli smoke test hanno scelto porte loopback libere e arrestato i processi nel blocco finally. Nessun servizio lasciato attivo.

## Come verificare a mano

Dalla radice `/home/galaxer/Desktop/Pokedex_React`:

```bash
cd backend
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy app
uv run pytest
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In un altro terminale: `curl --fail http://127.0.0.1:8000/openapi.json`; poi Ctrl-C sul server. In questo runner uv si trova in `/home/galaxer/.local/bin`: se necessario aggiungere quella directory al PATH. La cache usata per le verifiche è `backend/.cache/uv`, esclusa dal versionamento.

```bash
cd frontend
npm ci
npm run format
npm run lint
npm run typecheck
npm test
npm run build
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

In un altro terminale: `curl --fail http://127.0.0.1:5173/`; aprire la pagina placeholder Pokédex e poi Ctrl-C sul server.

```bash
# Dalla radice, validazione e build senza avvio di servizi:
POSTGRES_PASSWORD=validation-only docker compose config --quiet
POSTGRES_PASSWORD=validation-only docker compose build
# Avvio manuale completo dopo aver configurato una password locale in .env:
cp .env.example .env
# Modificare POSTGRES_PASSWORD in .env prima dell'avvio.
docker compose up --build
# Arresto senza cancellare volumi/dati:
docker compose down
```

I comandi di avvio completo sono istruzioni manuali, non prove di un collaudo completo del cluster. Per format/lint usare direttamente i comandi sopra; non installare hook pre-commit e non eseguire operazioni Git aggiuntive.

## Problemi noti e decisioni

- Tailwind segnala assenza di utility nello scaffold: osservazione non bloccante, come richiesto.
- npm segnala 7 vulnerabilità (5 moderate, 1 high, 1 critical). Registrate come non bloccanti M0 su indicazione esplicita; nessun `audit fix --force` o aggiornamento major non richiesto. Questo report non certifica sicurezza per un rilascio pubblico.
- Compose validato e immagini costruite; non eseguito `compose up` completo con Postgres/Redis e proxy HTTP end-to-end. Non sono dichiarati test DB, seed, API di dominio, browser/e2e, cache o rate limiting: fuori M0.
- Il control plane runtime `127.0.0.1:3100` non è raggiungibile dal sandbox (curl exit 7/HTTP 000), ma è raggiungibile dal contesto host autorizzato. Nessun URL alternativo è stato provato funzionante. Non è dichiarata una riparazione infrastrutturale permanente. Resta il processo temporaneo: escalation ordinaria quando consentita; dopo due scritture fallite consegna tramite runtime e persistenza CTO per conto dello specialista. [GAL-5](/GAL/issues/GAL-5) è già done e il suo report è conservato; [GAL-6](/GAL/issues/GAL-6) ha ora registrato autonomamente done.
- `git status --short` include cancellazioni di file storici Django/React già assenti all'ispezione di questo heartbeat. Non sono state eseguite cancellazioni dal CTO in questo run né recuperi dalla history. Lo snapshot sotto descrive l'intero working tree, non attribuisce tutte le modifiche a M0. Il CEO deve evidenziare queste assenze al board prima del commit manuale; nessuna operazione Git vietata è necessaria per consegnare lo scaffold.
- BRIEF_ORIGINALE.md non è presente nella radice corrente; il brief integrale resta nel documento del [task padre](/GAL/issues/GAL-2#document-brief) e nelle istruzioni gestite. Non è stato inventato un nuovo originale.
- CI predisposta solo come file, mai eseguita su GitHub; nessun push, commit, PR, hook o pubblicazione. Scansione segreti euristica, non garanzia assoluta.

## Commit suggerito

`chore: scaffold pokedex M0 workspace and tooling`

Nessun commit effettuato. Prossimo responsabile: CEO, per comunicare la consegna e i limiti al board. Tutti fermi fino alla conferma esplicita trasmessa dal CEO: «commit fatto, procedi con M1».

## File creati/modificati — stato del working tree

Output integrale di `git status --short` dopo la creazione del report. Le directory `??` sono raggruppate dal comando; i loro contenuti sono gli scaffold descritti sopra. Le righe `D` sono segnalate separatamente tra i problemi noti e non sono una richiesta di cancellazione.

```text
 M README.md
 D backend/docker-compose
 D backend/docker-compose.yaml
 D backend/poetry.lock
 D backend/pokedex/db.sqlite3
 D backend/pokedex/manage.py
 D backend/pokedex/pokedb/__init__.py
 D backend/pokedex/pokedb/__pycache__/__init__.cpython-312.pyc
 D backend/pokedex/pokedb/__pycache__/admin.cpython-312.pyc
 D backend/pokedex/pokedb/__pycache__/apps.cpython-312.pyc
 D backend/pokedex/pokedb/__pycache__/models.cpython-312.pyc
 D backend/pokedex/pokedb/__pycache__/serializers.cpython-312.pyc
 D backend/pokedex/pokedb/__pycache__/views.cpython-312.pyc
 D backend/pokedex/pokedb/admin.py
 D backend/pokedex/pokedb/apps.py
 D backend/pokedex/pokedb/management/__pycache__/__init__.cpython-312.pyc
 D backend/pokedex/pokedb/management/commands/__pycache__/__init__.cpython-312.pyc
 D backend/pokedex/pokedb/management/commands/__pycache__/populate_pokemon.cpython-312.pyc
 D backend/pokedex/pokedb/management/commands/populate_pokemon.py
 D backend/pokedex/pokedb/migrations/0001_initial.py
 D backend/pokedex/pokedb/migrations/0002_pokemon_description_pokemon_entry.py
 D backend/pokedex/pokedb/migrations/0003_pokemon_images.py
 D backend/pokedex/pokedb/migrations/__init__.py
 D backend/pokedex/pokedb/migrations/__pycache__/0001_initial.cpython-312.pyc
 D backend/pokedex/pokedb/migrations/__pycache__/0002_pokemon_description_pokemon_entry.cpython-312.pyc
 D backend/pokedex/pokedb/migrations/__pycache__/0003_pokemon_images.cpython-312.pyc
 D backend/pokedex/pokedb/migrations/__pycache__/__init__.cpython-312.pyc
 D backend/pokedex/pokedb/models.py
 D backend/pokedex/pokedb/serializers.py
 D backend/pokedex/pokedb/tests.py
 D backend/pokedex/pokedb/views.py
 D backend/pokedex/pokedex/__init__.py
 D backend/pokedex/pokedex/__pycache__/__init__.cpython-312.pyc
 D backend/pokedex/pokedex/__pycache__/settings.cpython-312.pyc
 D backend/pokedex/pokedex/__pycache__/urls.cpython-312.pyc
 D backend/pokedex/pokedex/__pycache__/wsgi.cpython-312.pyc
 D backend/pokedex/pokedex/asgi.py
 D backend/pokedex/pokedex/settings.py
 D backend/pokedex/pokedex/urls.py
 D backend/pokedex/pokedex/wsgi.py
 M backend/pyproject.toml
 M frontend/.gitignore
 D frontend/.vite/deps/_metadata.json
 D frontend/.vite/deps/package.json
 D frontend/README.md
 M frontend/eslint.config.js
 M frontend/index.html
 M frontend/package-lock.json
 M frontend/package.json
 D frontend/public/vite.svg
 D frontend/src/App.css
 D frontend/src/App.jsx
 D "frontend/src/assets/Pok\303\251_Ball_icon.png"
 D frontend/src/assets/react.svg
 D frontend/src/components/PokemonCard.jsx
 D frontend/src/components/SearchBar.jsx
 D frontend/src/css/Pokedex.css
 D frontend/src/css/PokemonCard.css
 D frontend/src/css/PokemonDetails.css
 D frontend/src/css/SearchBar.css
 D frontend/src/hooks/usePokemonDetails.js
 D frontend/src/hooks/usePokemonList.js
 D frontend/src/index.css
 D frontend/src/main.jsx
 D frontend/src/pages/Pokedex.jsx
 D frontend/src/pages/PokemonDetails.jsx
 D frontend/vite.config.js
?? .dockerignore
?? .env.example
?? .github/
?? .gitignore
?? .pre-commit-config.yaml
?? backend/.dockerignore
?? backend/.env.example
?? backend/.gitignore
?? backend/Dockerfile
?? backend/alembic.ini
?? backend/alembic/
?? backend/app/
?? backend/scripts/
?? backend/tests/
?? backend/uv.lock
?? docker-compose.yml
?? docs/
?? frontend/.dockerignore
?? frontend/.env.example
?? frontend/.prettierrc
?? frontend/Dockerfile
?? frontend/nginx.conf
?? frontend/postcss.config.cjs
?? frontend/public/.gitkeep
?? frontend/src/App.tsx
?? frontend/src/api/
?? frontend/src/components/layout/
?? frontend/src/components/pokemon/
?? frontend/src/components/ui/
?? frontend/src/hooks/index.ts
?? frontend/src/i18n/
?? frontend/src/lib/
?? frontend/src/main.tsx
?? frontend/src/pages/FavoritesPage.tsx
?? frontend/src/pages/HomePage.tsx
?? frontend/src/pages/NotFoundPage.tsx
?? frontend/src/pages/PokemonDetailPage.tsx
?? frontend/src/pages/TypesPage.tsx
?? frontend/src/router.tsx
?? frontend/src/store/
?? frontend/src/styles.css
?? frontend/src/tests/
?? frontend/src/vite-env.d.ts
?? frontend/tailwind.config.ts
?? frontend/tsconfig.app.json
?? frontend/tsconfig.json
?? frontend/tsconfig.node.json
?? frontend/vite.config.ts
```
