from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ParsedPlayer:
    source_player_id: str
    display_name: str
    jersey_number: str | None
    position: str | None
    source_url: str | None


@dataclass(frozen=True)
class ParsedGame:
    source_game_id: str
    played_at: datetime | None
    opponent: str
    site: str
    result: str | None
    upike_score: int | None
    opponent_score: int | None
    attendance: int | None
    source_url: str


@dataclass(frozen=True)
class ParsedSeason:
    year: int
    label: str
    games: list[ParsedGame] = field(default_factory=list)
    players: list[ParsedPlayer] = field(default_factory=list)
    source_url: str | None = None
    retrieved_at: datetime | None = None
    status_code: int | None = None
    content_type: str | None = None
    source_sha256: str | None = None
    storage_path: str | None = None
    parser_version: str | None = None
