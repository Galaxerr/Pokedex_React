"""Type and type-effectiveness models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.pokemon import PokemonType


class Type(Base):
    __tablename__ = "type"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20))
    pokemon: Mapped[list[PokemonType]] = relationship(back_populates="type")
    attacking_relations: Mapped[list[TypeRelation]] = relationship(
        foreign_keys="TypeRelation.attacker_type", back_populates="attacker"
    )
    defending_relations: Mapped[list[TypeRelation]] = relationship(
        foreign_keys="TypeRelation.defender_type", back_populates="defender"
    )


class TypeRelation(Base):
    __tablename__ = "type_relation"
    attacker_type: Mapped[int] = mapped_column(
        ForeignKey("type.id", ondelete="CASCADE"), primary_key=True
    )
    defender_type: Mapped[int] = mapped_column(
        ForeignKey("type.id", ondelete="CASCADE"), primary_key=True
    )
    multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    attacker: Mapped[Type] = relationship(
        foreign_keys=[attacker_type], back_populates="attacking_relations"
    )
    defender: Mapped[Type] = relationship(
        foreign_keys=[defender_type], back_populates="defending_relations"
    )
