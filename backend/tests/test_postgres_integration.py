"""Acceptance coverage against a real PostgreSQL database, not SQLite or mocks."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.models import (
    Ability,
    Move,
    Pokemon,
    PokemonAbility,
    PokemonMove,
    PokemonType,
    Species,
    Type,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_pokemon_and_associations_persist_and_query(
    postgres_session: AsyncSession,
) -> None:
    species = Species(id=990001, generation=9, flavor_text={"en": "integration fixture"})
    fire = Type(id=990001, name="integration-fire", color="#aa0000")
    ability = Ability(id=990001, name="integration-ability")
    move = Move(id=990001, name="integration-move")
    pokemon = Pokemon(
        id=990001,
        name="integrationmon",
        height=7,
        weight=70,
        base_experience=100,
        species=species,
        types=[PokemonType(type=fire, slot=1)],
        abilities=[PokemonAbility(ability=ability, is_hidden=True)],
        moves=[PokemonMove(move=move, version_group="integration", level=12, method="level-up")],
    )
    postgres_session.add(pokemon)
    await postgres_session.commit()

    read_session_factory = async_sessionmaker(
        bind=postgres_session.bind,
        expire_on_commit=False,
    )
    async with read_session_factory() as read_session:
        query = (
            select(Pokemon)
            .options(
                selectinload(Pokemon.types).selectinload(PokemonType.type),
                selectinload(Pokemon.abilities).selectinload(PokemonAbility.ability),
                selectinload(Pokemon.moves).selectinload(PokemonMove.move),
            )
            .where(Pokemon.id == pokemon.id)
        )
        result = await read_session.execute(query)
        persisted = result.scalar_one()

    assert persisted.name == "integrationmon"
    assert [(item.type.name, item.slot) for item in persisted.types] == [("integration-fire", 1)]
    assert [(item.ability.name, item.is_hidden) for item in persisted.abilities] == [
        ("integration-ability", True)
    ]
    assert [(item.move.name, item.level, item.method) for item in persisted.moves] == [
        ("integration-move", 12, "level-up")
    ]
