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


class HealthRead(BaseModel):
    status: str
    service: str
    version: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, str] = Field(default_factory=dict)
