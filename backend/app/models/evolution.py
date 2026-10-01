"""Directed evolution edges and their trigger details."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.species import Species


class Evolution(Base):
    __tablename__ = "evolution"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id", ondelete="CASCADE"), nullable=False
    )
    to_species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id", ondelete="CASCADE"), nullable=False
    )
    trigger: Mapped[str | None] = mapped_column(String(100))
    min_level: Mapped[int | None] = mapped_column(Integer)
    from_species: Mapped[Species] = relationship(
        foreign_keys=[from_species_id], back_populates="outgoing_evolutions"
    )
    to_species: Mapped[Species] = relationship(
        foreign_keys=[to_species_id], back_populates="incoming_evolutions"
    )
