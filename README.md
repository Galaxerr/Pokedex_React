# Pokédex

Scaffold M0 per una web app Pokédex con backend FastAPI e frontend React/Vite.
M0 contiene tooling, configurazioni eseguibili e struttura iniziale. Le risorse
Pokémon, migrazioni, seed, API di dominio e funzionalità UI appartengono a milestone
successive e non sono incluse in questo confine.

## Prerequisiti

- Docker Engine 24+ e Docker Compose v2 (`docker compose version`)
- Python 3.12+ e [uv](https://docs.astral.sh/uv/)
- Node.js 22+ e npm

## Configurazione locale

I segreti non sono versionati. Copiare `.env.example` in `.env` e impostare almeno
`POSTGRES_PASSWORD`; `.env` è escluso da Git e Docker. Non usare questi valori in
ambienti condivisi o di produzione.

```bash
cp .env.example .env
docker compose config >/dev/null
```

## Avvio con Docker

```bash
docker compose up --build
```

Servizi esposti: frontend `http://localhost:5173`, backend `http://localhost:8000`,
documentazione FastAPI `http://localhost:8000/docs`, PostgreSQL `localhost:5432` e
Redis `localhost:6379`. Il reverse proxy del frontend inoltra `/api/` al backend.

Per fermare i container senza rimuovere i dati locali:

```bash
docker compose down
```

## Verifiche locali senza Docker

Backend:

```bash
cd backend
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy app
uv run pytest
uv run uvicorn app.main:app --reload
```

Frontend, in un secondo terminale:

```bash
cd frontend
npm ci
npm run format
npm run lint
npm run typecheck
npm test -- --run
npm run build
npm run dev
```

La CI ripete lint, typecheck, test e build sui due workspace. Il file
`.pre-commit-config.yaml` è solo configurazione. Non installare hook: scriverebbero
in `.git`. Eseguire manualmente i comandi Ruff e Prettier sopra elencati.

## M0 e prossimi confini

Sono inclusi solo scaffolding, configurazione, containerizzazione, CI e documentazione.
Non sono inclusi schema dati, migrazioni Alembic, seed da PokéAPI, repository/API
Pokémon, autenticazione o implementazione delle pagine di dominio.
