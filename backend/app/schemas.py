import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class PracticeCreate(BaseModel):
    season_year: int = Field(default=2026, ge=2026, le=2100)
    title: str = Field(min_length=1, max_length=160)
    practice_date: date | None = None
    practice_type: str = Field(default="Quarterbacks", min_length=1, max_length=48)
    notes: str | None = Field(default=None, max_length=4000)
    source_label: str | None = Field(default=None, max_length=160)


class PracticeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    practice_date: date | None = None
    practice_type: str | None = Field(default=None, min_length=1, max_length=48)
    notes: str | None = Field(default=None, max_length=4000)


class PracticePlayCreate(BaseModel):
    sequence: int = Field(ge=1, le=10000)
    quarterback_number: str | None = Field(default=None, max_length=12)
    quarterback_name: str | None = Field(default=None, max_length=160)
    intended_receiver: str | None = Field(default=None, max_length=160)
    result: str = Field(default="INCOMPLETE", min_length=1, max_length=24)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("result")
    @classmethod
    def normalize_result(cls, value: str) -> str:
        return value.strip().upper()


class PracticePlayUpdate(BaseModel):
    sequence: int | None = Field(default=None, ge=1, le=10000)
    quarterback_number: str | None = Field(default=None, max_length=12)
    quarterback_name: str | None = Field(default=None, max_length=160)
    intended_receiver: str | None = Field(default=None, max_length=160)
    result: str | None = Field(default=None, min_length=1, max_length=24)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("result")
    @classmethod
    def normalize_result(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class PracticeSummary(BaseModel):
    plays: int
    attempts: int
    completions: int
    incompletions: int
    completion_pct: float | None
    on_target: int
    positive_reads: int
    negative_reads: int
    positive_timing: int
    negative_timing: int
    receiver_drops: int
    checkdowns: int


class PracticePlayRead(BaseModel):
    id: uuid.UUID
    sequence: int
    quarterback_number: str | None
    quarterback_name: str | None
    intended_receiver: str | None
    result: str
    notes: str | None
    tags: list[str]


class PracticeRead(BaseModel):
    id: uuid.UUID
    season_year: int
    title: str
    practice_date: date | None
    practice_type: str
    notes: str | None
    source_label: str | None
    created_at: datetime
    updated_at: datetime
    summary: PracticeSummary
    plays: list[PracticePlayRead]


class PracticeQuarterbackSummary(PracticeSummary):
    key: str
    display_name: str
    quarterback_number: str | None
    practices: int


class PracticeDashboardRead(BaseModel):
    season_year: int
    overview: PracticeSummary
    practices: list[PracticeRead]
    quarterbacks: list[PracticeQuarterbackSummary]
