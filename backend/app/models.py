import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
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
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id")
    )
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
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id")
    )


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
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id")
    )
    season: Mapped[Season] = relationship(back_populates="games")
