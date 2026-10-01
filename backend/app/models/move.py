"""Move and lossless Pokémon/move learning-method association models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.pokemon import Pokemon


class Move(Base):
    __tablename__ = "move"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    pokemon: Mapped[list[PokemonMove]] = relationship(back_populates="move")


class PokemonMove(Base):
    __tablename__ = "pokemon_move"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"), nullable=False
    )
    move_id: Mapped[int] = mapped_column(ForeignKey("move.id", ondelete="CASCADE"), nullable=False)
    version_group: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str | None] = mapped_column(String(100))
    pokemon: Mapped[Pokemon] = relationship(back_populates="moves")
    move: Mapped[Move] = relationship(back_populates="pokemon")
