"""Pokémon and Pokémon-owned association models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ability import PokemonAbility
    from app.models.move import PokemonMove
    from app.models.species import Species
    from app.models.type import Type


class Pokemon(Base):
    __tablename__ = "pokemon"
    __table_args__ = (
        Index(
            "ix_pokemon_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    height: Mapped[int | None] = mapped_column(Integer)
    weight: Mapped[int | None] = mapped_column(Integer)
    base_experience: Mapped[int | None] = mapped_column(Integer)
    sprite_url: Mapped[str | None] = mapped_column(String(500))
    artwork_url: Mapped[str | None] = mapped_column(String(500))
    species_id: Mapped[int | None] = mapped_column(ForeignKey("species.id", ondelete="SET NULL"))
    species: Mapped[Species | None] = relationship(back_populates="pokemon")
    stats: Mapped[list[PokemonStat]] = relationship(
        back_populates="pokemon", cascade="all, delete-orphan"
    )
    types: Mapped[list[PokemonType]] = relationship(
        back_populates="pokemon", cascade="all, delete-orphan"
    )
    abilities: Mapped[list[PokemonAbility]] = relationship(
        back_populates="pokemon", cascade="all, delete-orphan"
    )
    moves: Mapped[list[PokemonMove]] = relationship(
        back_populates="pokemon", cascade="all, delete-orphan"
    )


class PokemonStat(Base):
    __tablename__ = "pokemon_stat"
    __table_args__ = (Index("uq_pokemon_stat_name", "pokemon_id", "stat_name", unique=True),)
    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True
    )
    stat_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    base_value: Mapped[int | None] = mapped_column(Integer)
    pokemon: Mapped[Pokemon] = relationship(back_populates="stats")


class PokemonType(Base):
    """Ordered association; slot preserves PokéAPI ordering."""

    __tablename__ = "pokemon_type"
    __table_args__ = (Index("ix_pokemon_type_type_id", "type_id"),)
    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True
    )
    type_id: Mapped[int] = mapped_column(
        ForeignKey("type.id", ondelete="RESTRICT"), primary_key=True
    )
    slot: Mapped[int | None] = mapped_column(Integer)
    pokemon: Mapped[Pokemon] = relationship(back_populates="types")
    type: Mapped[Type] = relationship(back_populates="pokemon")
