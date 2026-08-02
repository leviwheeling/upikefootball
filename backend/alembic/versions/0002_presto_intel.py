"""Add source-linked PrestoSports intelligence tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_presto_intel"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conference_standings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("season_id", sa.Uuid(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("conference", sa.String(160), nullable=False),
        sa.Column("team_name", sa.String(160), nullable=False),
        sa.Column("conference_wins", sa.Integer(), nullable=False),
        sa.Column("conference_losses", sa.Integer(), nullable=False),
        sa.Column("overall_wins", sa.Integer(), nullable=False),
        sa.Column("overall_losses", sa.Integer(), nullable=False),
        sa.Column("streak", sa.String(24), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "source_document_id", sa.Uuid(), sa.ForeignKey("source_documents.id"), nullable=False
        ),
        sa.UniqueConstraint(
            "source", "season_id", "conference", "team_name", name="uq_conference_standing"
        ),
    )
    op.create_table(
        "leader_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("season_id", sa.Uuid(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("category", sa.String(48), nullable=False),
        sa.Column("metric", sa.String(80), nullable=False),
        sa.Column("player_name", sa.String(160), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=False),
        sa.Column("value_text", sa.String(32), nullable=False),
        sa.Column("value_numeric", sa.Float(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "source_document_id", sa.Uuid(), sa.ForeignKey("source_documents.id"), nullable=False
        ),
        sa.UniqueConstraint(
            "source",
            "season_id",
            "category",
            "metric",
            "player_name",
            name="uq_leader_entry",
        ),
    )
    op.create_table(
        "gamebooks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("season_id", sa.Uuid(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_game_id", sa.String(128), nullable=False),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opponent", sa.String(160), nullable=False),
        sa.Column("upike_score", sa.Integer(), nullable=False),
        sa.Column("opponent_score", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(160), nullable=False),
        sa.Column("stadium", sa.String(160), nullable=False),
        sa.Column("attendance", sa.Integer()),
        sa.Column("team_stats", sa.JSON(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "source_document_id", sa.Uuid(), sa.ForeignKey("source_documents.id"), nullable=False
        ),
        sa.UniqueConstraint("source", "source_game_id", name="uq_gamebook_source_game"),
    )
    op.create_table(
        "game_drives",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("gamebook_id", sa.Uuid(), sa.ForeignKey("gamebooks.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("team", sa.String(160), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=False),
        sa.Column("start_clock", sa.String(8), nullable=False),
        sa.Column("possession_duration", sa.String(8), nullable=False),
        sa.Column("start_spot", sa.String(32), nullable=False),
        sa.Column("plays", sa.Integer(), nullable=False),
        sa.Column("yards", sa.Integer(), nullable=False),
        sa.Column("result", sa.String(16), nullable=False),
        sa.UniqueConstraint("gamebook_id", "sequence", name="uq_gamebook_drive_sequence"),
    )


def downgrade() -> None:
    op.drop_table("game_drives")
    op.drop_table("gamebooks")
    op.drop_table("leader_entries")
    op.drop_table("conference_standings")
