"""Ability and Pokémon/ability association models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.pokemon import Pokemon


class Ability(Base):
    __tablename__ = "ability"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    pokemon: Mapped[list[PokemonAbility]] = relationship(back_populates="ability")


class PokemonAbility(Base):
    __tablename__ = "pokemon_ability"
    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True
    )
    ability_id: Mapped[int] = mapped_column(
        ForeignKey("ability.id", ondelete="CASCADE"), primary_key=True
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pokemon: Mapped[Pokemon] = relationship(back_populates="abilities")
    ability: Mapped[Ability] = relationship(back_populates="pokemon")
