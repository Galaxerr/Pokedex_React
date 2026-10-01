"""Initial Pokémon catalog schema with fuzzy-search support."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "species",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("flavor_text", sa.JSON()),
        sa.Column("generation", sa.Integer()),
        sa.Column("is_legendary", sa.Boolean()),
        sa.Column("evolution_chain_id", sa.Integer()),
    )
    op.create_table(
        "type",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("color", sa.String(20)),
    )
    op.create_table(
        "ability",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )
    op.create_table(
        "move",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )
    op.create_table(
        "pokemon",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("height", sa.Integer()),
        sa.Column("weight", sa.Integer()),
        sa.Column("base_experience", sa.Integer()),
        sa.Column("sprite_url", sa.String(500)),
        sa.Column("artwork_url", sa.String(500)),
        sa.Column("species_id", sa.Integer(), sa.ForeignKey("species.id", ondelete="SET NULL")),
    )
    op.create_index(
        "ix_pokemon_name_trgm",
        "pokemon",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_table(
        "pokemon_stat",
        sa.Column(
            "pokemon_id",
            sa.Integer(),
            sa.ForeignKey("pokemon.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("stat_name", sa.String(50), primary_key=True),
        sa.Column("base_value", sa.Integer()),
    )
    op.create_table(
        "pokemon_type",
        sa.Column(
            "pokemon_id",
            sa.Integer(),
            sa.ForeignKey("pokemon.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "type_id", sa.Integer(), sa.ForeignKey("type.id", ondelete="RESTRICT"), primary_key=True
        ),
        sa.Column("slot", sa.Integer()),
    )
    op.create_index("ix_pokemon_type_type_id", "pokemon_type", ["type_id"])
    op.create_table(
        "type_relation",
        sa.Column(
            "attacker_type",
            sa.Integer(),
            sa.ForeignKey("type.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "defender_type",
            sa.Integer(),
            sa.ForeignKey("type.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("multiplier", sa.Float(), nullable=False),
    )
    op.create_table(
        "pokemon_ability",
        sa.Column(
            "pokemon_id",
            sa.Integer(),
            sa.ForeignKey("pokemon.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "ability_id",
            sa.Integer(),
            sa.ForeignKey("ability.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "pokemon_move",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "pokemon_id",
            sa.Integer(),
            sa.ForeignKey("pokemon.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "move_id", sa.Integer(), sa.ForeignKey("move.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("version_group", sa.String(100)),
        sa.Column("level", sa.Integer()),
        sa.Column("method", sa.String(100)),
    )
    op.create_table(
        "evolution",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "from_species_id",
            sa.Integer(),
            sa.ForeignKey("species.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_species_id",
            sa.Integer(),
            sa.ForeignKey("species.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger", sa.String(100)),
        sa.Column("min_level", sa.Integer()),
    )


def downgrade() -> None:
    for table in (
        "evolution",
        "pokemon_move",
        "pokemon_ability",
        "type_relation",
        "pokemon_type",
        "pokemon_stat",
        "pokemon",
        "move",
        "ability",
        "type",
        "species",
    ):
        op.drop_table(table)
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
