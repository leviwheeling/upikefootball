"""Create initial provenance-first core tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.String(32), nullable=True),
        sa.UniqueConstraint("source", "url", "sha256", name="uq_source_document_version"),
    )
    op.create_table(
        "seasons",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False, unique=True),
        sa.Column("label", sa.String(16), nullable=False),
        sa.Column("data_completeness", sa.String(16), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), sa.ForeignKey("source_documents.id")),
    )
    op.create_table(
        "players",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("normalized_name", sa.String(160), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_player_id", sa.String(128), nullable=False),
        sa.Column("jersey_number", sa.String(8)),
        sa.Column("position", sa.String(16)),
        sa.Column("source_url", sa.Text()),
        sa.Column("source_document_id", sa.Uuid(), sa.ForeignKey("source_documents.id")),
        sa.UniqueConstraint("source", "source_player_id", name="uq_source_player"),
    )
    op.create_index("ix_players_normalized_name", "players", ["normalized_name"])
    op.create_table(
        "games",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("season_id", sa.Uuid(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_game_id", sa.String(128), nullable=False),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opponent", sa.String(160), nullable=False),
        sa.Column("site", sa.String(16), nullable=False),
        sa.Column("result", sa.String(1)),
        sa.Column("upike_score", sa.Integer()),
        sa.Column("opponent_score", sa.Integer()),
        sa.Column("attendance", sa.Integer()),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), sa.ForeignKey("source_documents.id")),
        sa.UniqueConstraint("source", "source_game_id", name="uq_source_game"),
    )


def downgrade() -> None:
    op.drop_table("games")
    op.drop_index("ix_players_normalized_name", table_name="players")
    op.drop_table("players")
    op.drop_table("seasons")
    op.drop_table("source_documents")
