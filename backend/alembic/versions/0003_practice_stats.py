"""Add editable practice and practice-play tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_practice_stats"
down_revision: str | None = "0002_presto_intel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "practices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("season_year", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("practice_date", sa.Date(), nullable=True),
        sa.Column("practice_type", sa.String(48), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_label", sa.String(160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_practices_season_year", "practices", ["season_year"])
    op.create_table(
        "practice_plays",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "practice_id",
            sa.Uuid(),
            sa.ForeignKey("practices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("quarterback_number", sa.String(12), nullable=True),
        sa.Column("quarterback_name", sa.String(160), nullable=True),
        sa.Column("intended_receiver", sa.String(160), nullable=True),
        sa.Column("result", sa.String(24), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("practice_id", "sequence", name="uq_practice_play_sequence"),
    )
    op.create_index("ix_practice_plays_practice_id", "practice_plays", ["practice_id"])


def downgrade() -> None:
    op.drop_index("ix_practice_plays_practice_id", table_name="practice_plays")
    op.drop_table("practice_plays")
    op.drop_index("ix_practices_season_year", table_name="practices")
    op.drop_table("practices")
