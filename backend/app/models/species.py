"""Species metadata, including multilingual flavor text supplied by the seed."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.evolution import Evolution
    from app.models.pokemon import Pokemon


class Species(Base):
    __tablename__ = "species"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flavor_text: Mapped[dict[str, str] | None] = mapped_column(JSON)
    generation: Mapped[int | None] = mapped_column(Integer)
    is_legendary: Mapped[bool | None] = mapped_column(Boolean)
    evolution_chain_id: Mapped[int | None] = mapped_column(Integer)
    pokemon: Mapped[list[Pokemon]] = relationship(back_populates="species")
    outgoing_evolutions: Mapped[list[Evolution]] = relationship(
        foreign_keys="Evolution.from_species_id", back_populates="from_species"
    )
    incoming_evolutions: Mapped[list[Evolution]] = relationship(
        foreign_keys="Evolution.to_species_id", back_populates="to_species"
    )
