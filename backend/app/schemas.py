import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class SeasonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    year: int
    label: str
    data_completeness: str


class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    season_id: uuid.UUID
    played_at: datetime | None
    opponent: str
    site: str
    result: str | None
    upike_score: int | None
    opponent_score: int | None
    attendance: int | None
    source: str
    source_url: str


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    jersey_number: str | None
    position: str | None
    source: str
    source_url: str | None


class SeasonPage(BaseModel):
    data: list[SeasonRead]
    meta: PageMeta


class GamePage(BaseModel):
    data: list[GameRead]
    meta: PageMeta


class PlayerPage(BaseModel):
    data: list[PlayerRead]
    meta: PageMeta


class ConferenceStandingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    season_id: uuid.UUID
    conference: str
    team_name: str
    conference_wins: int
    conference_losses: int
    overall_wins: int
    overall_losses: int
    streak: str
    source: str
    source_url: str


class LeaderEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    season_id: uuid.UUID
    category: str
    metric: str
    player_name: str
    games_played: int
    value_text: str
    value_numeric: float
    source: str
    source_url: str


class GamebookRead(BaseModel):
    id: uuid.UUID
    season_id: uuid.UUID
    played_at: datetime
    opponent: str
    upike_score: int
    opponent_score: int
    location: str
    stadium: str
    attendance: int | None
    team_stats: dict[str, object]
    drive_count: int
    source: str
    source_url: str


class ConferenceStandingPage(BaseModel):
    data: list[ConferenceStandingRead]
    meta: PageMeta


class LeaderEntryPage(BaseModel):
    data: list[LeaderEntryRead]
    meta: PageMeta


class GamebookPage(BaseModel):
    data: list[GamebookRead]
    meta: PageMeta


class HealthRead(BaseModel):
    status: str
    service: str
    version: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, str] = Field(default_factory=dict)
