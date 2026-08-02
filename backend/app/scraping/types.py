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


@dataclass(frozen=True)
class ParsedStanding:
    conference: str
    team_name: str
    conference_wins: int
    conference_losses: int
    overall_wins: int
    overall_losses: int
    streak: str


@dataclass(frozen=True)
class ParsedLeaderEntry:
    category: str
    metric: str
    player_name: str
    games_played: int
    value_text: str
    value_numeric: float


@dataclass(frozen=True)
class ParsedDrive:
    sequence: int
    team: str
    quarter: int
    start_clock: str
    possession_duration: str
    start_spot: str
    plays: int
    yards: int
    result: str


@dataclass(frozen=True)
class ParsedGamebook:
    source_game_id: str
    played_at: datetime
    opponent: str
    upike_score: int
    opponent_score: int
    location: str
    stadium: str
    attendance: int | None
    team_stats: dict[str, object]
    drives: list[ParsedDrive]


@dataclass(frozen=True)
class ParsedPrestoIntel:
    year: int
    label: str
    retrieved_at: datetime
    standings_url: str
    leaders_url: str
    gamebook_url: str
    standings: list[ParsedStanding]
    leaders: list[ParsedLeaderEntry]
    gamebook: ParsedGamebook
