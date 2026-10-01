from pathlib import Path


def test_initial_migration_contains_required_postgres_features() -> None:
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0001_initial_schema.py"
    source = migration.read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS pg_trgm" in source
    assert '"pokemon_type"' in source
    assert '"pokemon_move"' in source
    assert '"evolution"' in source
    assert '"ix_pokemon_name_trgm"' in source
    assert '"ix_pokemon_type_type_id"' in source
