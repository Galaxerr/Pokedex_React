from __future__ import annotations

import pytest

from scripts.seed_from_pokeapi import replace_catalog


class RecordingSession:
    def __init__(self) -> None:
        self.deleted: list[object] = []
        self.rows: list[object] = []

    async def execute(self, statement: object) -> None:
        self.deleted.append(statement)

    def add_all(self, rows: list[object]) -> None:
        self.rows.extend(rows)

    async def flush(self) -> None:
        return None


@pytest.mark.asyncio
async def test_replace_catalog_rebuilds_all_seed_owned_tables_without_duplicates() -> None:
    catalog = {
        "pokemon": [{"id": 1, "name": "bulbasaur", "species_id": 1}],
        "stats": [{"pokemon_id": 1, "stat_name": "hp", "base_value": 45}],
        "types": [{"id": 12, "name": "grass", "color": None}],
        "pokemon_types": [{"pokemon_id": 1, "type_id": 12, "slot": 1}],
        "type_relations": [],
        "abilities": [],
        "pokemon_abilities": [],
        "moves": [],
        "pokemon_moves": [],
        "species": [
            {
                "id": 1,
                "flavor_text": {"en": "seed"},
                "generation": 1,
                "is_legendary": False,
                "evolution_chain_id": 1,
            }
        ],
        "evolutions": [],
    }
    first = RecordingSession()
    second = RecordingSession()
    await replace_catalog(first, catalog)
    await replace_catalog(second, catalog)
    assert len(first.deleted) == len(second.deleted) == 11
    assert [type(row) for row in first.rows] == [type(row) for row in second.rows]
    assert len(first.rows) == len(second.rows) == 5
