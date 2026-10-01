# GAL-8 PostgreSQL ORM test evidence

This document records the implementation for GAL-11. GAL-8 is technically accepted;
see the final acceptance section below. Earlier failed results are retained as history.
The scope is limited to SQLAlchemy integration tests and test-only configuration.

## Safety contract

The integration suite reads only `POKEDEX_TEST_DATABASE_URL`; it never falls back to
`DATABASE_URL`. Before running Alembic it checks that the `public` schema contains no
user tables other than a possible `alembic_version`. It refuses non-local hosts and
database names without `test`, `testing`, or `integration`. Tests do not drop, truncate,
or delete data. Use a newly created PostgreSQL 16 database such as `pokedex_test`.

The test commits one deterministic fixture row set to prove persistence across the
database session. Recreate the disposable database before repeating the suite.

## Exact verification commands

From the repository root, with PostgreSQL 16 running and an isolated empty database:

```bash
cd backend
export POKEDEX_TEST_DATABASE_URL='postgresql+asyncpg://localhost:5432/pokedex_test'
uv run pytest -m integration -q
uv run pytest -q
uv run ruff check app tests
uv run mypy app tests
```

The first command runs `alembic upgrade head` from the fixture against the empty test
database, then verifies persistence and queries through `pokemon_type`,
`pokemon_ability`, and `pokemon_move` with async SQLAlchemy sessions. It is not a skip:
missing configuration or an unsafe/non-empty database fails the test explicitly.

For an independently observable empty-database migration check, point `DATABASE_URL`
at a separate empty PostgreSQL 16 database and run:

```bash
cd backend
DATABASE_URL="$POKEDEX_TEST_DATABASE_URL" uv run alembic upgrade head
```

Do not run that command against an application or user database.

## Results and limits

Results must be filled with the real command output by the CTO/reviewer in the runtime
where PostgreSQL 16 is available. This workspace heartbeat had no reachable Paperclip
control-plane service and no PostgreSQL service was available, so no test is claimed as
passed here. Existing static/unit tests remain unchanged; the new acceptance evidence
requires the explicit PostgreSQL environment above.

Files added/changed by this task:

- `backend/tests/conftest.py`
- `backend/tests/test_postgres_integration.py`
- `backend/pyproject.toml`
- `docs/milestones/GAL8_POSTGRES_TESTS.md`

## CTO verification — 2026-10-01

Acceptance failed; returned to the existing GAL-11 implementer. No commit performed.

- Project Compose PostgreSQL was already healthy; `SHOW server_version` returned
  `16.15`. No restart or shared infrastructure change was needed.
- Created only `pokedex_test_gal11_1604` using
  `docker compose exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" pokedex_test_gal11_1604'`.
  The application database was not used. The disposable database is retained.
- Used the existing `backend/.venv/bin/` executables (uv was outside sandbox PATH).
  Test URL used localhost port **5434**, the published project Compose port;
  credentials were supplied from current Compose configuration, not stored here.
  Container initialization credentials initially failed authentication; using current
  Compose configuration resolved this environment mismatch without altering roles.
- From `backend`, with `POKEDEX_TEST_DATABASE_URL` targeting that new database:
  `.venv/bin/pytest -q --tb=short` produced **1 failed, 5 passed**.
  Fixture Alembic output: `Context impl PostgresqlImpl` and
  `Running upgrade -> 0001_initial_schema` (clean migration succeeded).
- Exact implementation failure at `tests/test_postgres_integration.py:43`,
  `await postgres_session.commit()`: `RuntimeError: ... got Future ... attached to
  a different loop`. The session-scoped engine pool is used across different
  pytest-asyncio loops. Persistence/query and association acceptance remains unproven.
  Execution reached the real asyncpg/PostgreSQL connection; no SQLite/mock substituted.
- `.venv/bin/pytest -m 'not integration' -q`: **5 passed, 1 deselected**.
- `.venv/bin/ruff check app tests`: **failed**, `I001 Import block is un-sorted or
  un-formatted`, `tests/test_postgres_integration.py:3:1`.
- `.venv/bin/mypy app tests`: **passed**, no issues in 40 source files.
- Direct calls to `_test_database_url()` confirmed rejection of missing test URL,
  normal database name `pokedex`, SQLite driver, and non-local host. These checks
  reject before connection and never target the development database.
- Repeating `.venv/bin/pytest -m integration -q --tb=short` against the now-migrated
  isolated DB correctly failed before migration with `Refusing integration tests
  because the dedicated database is not empty` (11 catalog tables listed).

Next owner: GAL-11 implementer, fix only event-loop fixture compatibility and import
ordering; prove reload through a fresh session to avoid identity-map-only assertions.
Then CTO reruns on a newly named empty isolated database and reviewer checks the new
ORM evidence. Schema redesign and M2 remain out of scope. Use a different empty test
DB for each full/integration run: the two documented commands cannot run successively
on the same populated database by design. No API/repository path was added for M2.

## Implementer correction — 2026-10-01

- Configured pytest-asyncio fixture and test loop scope to `session`, matching the
  session-scoped async engine and preventing cross-loop asyncpg futures.
- The persistence assertion now reads through a separate `AsyncSession` after commit,
  covering database reload rather than the original identity map.
- Ruff import ordering is corrected.
- Local evidence after the correction: `.venv/bin/pytest -m 'not integration' -q`
  **5 passed, 1 deselected**; `.venv/bin/ruff check app tests` **passed**;
  `.venv/bin/mypy app tests` **passed**; `python3 -m compileall -q backend/tests`
  **passed**.
- PostgreSQL integration remains pending CTO execution against a newly created empty
  PostgreSQL 16 database; no integration pass is claimed here.

## Final acceptance — 2026-10-01

Accepted by the CTO following the independent review in
[GAL8_REVIEW.md](GAL8_REVIEW.md) and the explicit board confirmation in
[GAL-7 comment b02553e4](http://localhost:3100/GAL/issues/GAL-7#comment-b02553e4-8d92-460a-8e5c-b12b069c1087).

- Reviewer executed the corrected integration test on an empty, isolated PostgreSQL
  **16.15** database: **1 passed, 5 deselected**.
- Alembic migration, persisted/requeried ORM objects and all representative
  many-to-many associations passed. The application database remained untouched.
- Corrected unit-test, Ruff and mypy results are recorded above by the implementer.
- This heartbeat reconciles existing evidence; it does not claim a new test run.
- Earlier acceptance failures and pending statements above are superseded.
- API and repository operations are outside GAL-8. Seed is the next M1 task, GAL-9,
  and is not an acceptance condition for GAL-8.
