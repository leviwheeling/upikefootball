import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SourceDocument(Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        UniqueConstraint("source", "url", "sha256", name="uq_source_document_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(32))
    url: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status_code: Mapped[int]
    content_type: Mapped[str] = mapped_column(String(128))
    sha256: Mapped[str] = mapped_column(String(64))
    storage_path: Mapped[str] = mapped_column(Text)
    parser_version: Mapped[str | None] = mapped_column(String(32))


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    year: Mapped[int] = mapped_column(unique=True)
    label: Mapped[str] = mapped_column(String(16))
    data_completeness: Mapped[str] = mapped_column(String(16), default="partial")
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("source_documents.id"))
    games: Mapped[list["Game"]] = relationship(back_populates="season")


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("source", "source_player_id", name="uq_source_player"),
        Index("ix_players_normalized_name", "normalized_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(160))
    normalized_name: Mapped[str] = mapped_column(String(160))
    source: Mapped[str] = mapped_column(String(32))
    source_player_id: Mapped[str] = mapped_column(String(128))
    jersey_number: Mapped[str | None] = mapped_column(String(8))
    position: Mapped[str | None] = mapped_column(String(16))
    source_url: Mapped[str | None] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("source_documents.id"))


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (UniqueConstraint("source", "source_game_id", name="uq_source_game"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    source: Mapped[str] = mapped_column(String(32))
    source_game_id: Mapped[str] = mapped_column(String(128))
    played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opponent: Mapped[str] = mapped_column(String(160))
    site: Mapped[str] = mapped_column(String(16))
    result: Mapped[str | None] = mapped_column(String(1))
    upike_score: Mapped[int | None]
    opponent_score: Mapped[int | None]
    attendance: Mapped[int | None]
    source_url: Mapped[str] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("source_documents.id"))
    season: Mapped[Season] = relationship(back_populates="games")


class ConferenceStanding(Base):
    __tablename__ = "conference_standings"
    __table_args__ = (
        UniqueConstraint(
            "source", "season_id", "conference", "team_name", name="uq_conference_standing"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    source: Mapped[str] = mapped_column(String(32))
    conference: Mapped[str] = mapped_column(String(160))
    team_name: Mapped[str] = mapped_column(String(160))
    conference_wins: Mapped[int]
    conference_losses: Mapped[int]
    overall_wins: Mapped[int]
    overall_losses: Mapped[int]
    streak: Mapped[str] = mapped_column(String(24))
    source_url: Mapped[str] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_documents.id"))


class LeaderEntry(Base):
    __tablename__ = "leader_entries"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "season_id",
            "category",
            "metric",
            "player_name",
            name="uq_leader_entry",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    source: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(48))
    metric: Mapped[str] = mapped_column(String(80))
    player_name: Mapped[str] = mapped_column(String(160))
    games_played: Mapped[int]
    value_text: Mapped[str] = mapped_column(String(32))
    value_numeric: Mapped[float] = mapped_column(Float)
    source_url: Mapped[str] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_documents.id"))


class Gamebook(Base):
    __tablename__ = "gamebooks"
    __table_args__ = (UniqueConstraint("source", "source_game_id", name="uq_gamebook_source_game"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    source: Mapped[str] = mapped_column(String(32))
    source_game_id: Mapped[str] = mapped_column(String(128))
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    opponent: Mapped[str] = mapped_column(String(160))
    upike_score: Mapped[int]
    opponent_score: Mapped[int]
    location: Mapped[str] = mapped_column(String(160))
    stadium: Mapped[str] = mapped_column(String(160))
    attendance: Mapped[int | None]
    team_stats: Mapped[dict[str, object]] = mapped_column(JSON)
    source_url: Mapped[str] = mapped_column(Text)
    source_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_documents.id"))
    drives: Mapped[list["GameDrive"]] = relationship(
        back_populates="gamebook", cascade="all, delete-orphan"
    )


class GameDrive(Base):
    __tablename__ = "game_drives"
    __table_args__ = (
        UniqueConstraint("gamebook_id", "sequence", name="uq_gamebook_drive_sequence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    gamebook_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("gamebooks.id"))
    sequence: Mapped[int]
    team: Mapped[str] = mapped_column(String(160))
    quarter: Mapped[int]
    start_clock: Mapped[str] = mapped_column(String(8))
    possession_duration: Mapped[str] = mapped_column(String(8))
    start_spot: Mapped[str] = mapped_column(String(32))
    plays: Mapped[int]
    yards: Mapped[int]
    result: Mapped[str] = mapped_column(String(16))
    gamebook: Mapped[Gamebook] = relationship(back_populates="drives")
