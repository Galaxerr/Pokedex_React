from sqlalchemy import ForeignKey

from app.core.database import Base
from app.models import Evolution, PokemonMove, PokemonStat, PokemonType, Species, TypeRelation


def test_all_domain_tables_are_registered() -> None:
    assert {
        "pokemon",
        "pokemon_stat",
        "type",
        "pokemon_type",
        "type_relation",
        "ability",
        "pokemon_ability",
        "move",
        "pokemon_move",
        "species",
        "evolution",
    } <= set(Base.metadata.tables)


def test_nullable_pokeapi_details_are_preserved() -> None:
    assert PokemonMove.__table__.c.version_group.nullable
    assert PokemonMove.__table__.c.level.nullable
    assert PokemonMove.__table__.c.method.nullable
    assert Evolution.__table__.c.trigger.nullable
    assert Evolution.__table__.c.min_level.nullable
    assert Species.__table__.c.flavor_text.nullable


def test_required_association_foreign_keys_and_indexes_exist() -> None:
    assert any(
        isinstance(fk, ForeignKey) and fk.target_fullname == "pokemon.id"
        for fk in PokemonStat.__table__.foreign_keys
    )
    assert any(
        isinstance(fk, ForeignKey) and fk.target_fullname == "type.id"
        for fk in PokemonType.__table__.foreign_keys
    )
    assert any(
        isinstance(fk, ForeignKey) and fk.target_fullname == "type.id"
        for fk in TypeRelation.__table__.foreign_keys
    )
    assert "ix_pokemon_name_trgm" in {
        index.name for index in Base.metadata.tables["pokemon"].indexes
    }
    assert "ix_pokemon_type_type_id" in {
        index.name for index in Base.metadata.tables["pokemon_type"].indexes
    }
