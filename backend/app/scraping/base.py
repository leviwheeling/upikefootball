from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime

from app.scraping.types import ParsedSeason


class SourceBlockedError(RuntimeError):
    """Raised when a source presents an access restriction we will not bypass."""


@dataclass(frozen=True)
class SourcePage:
    source: str
    url: str
    status_code: int
    content_type: str
    content: bytes
    retrieved_at: datetime


class FootballSourceAdapter(ABC):
    source_name: str
    parser_version: str

    @abstractmethod
    async def discover_seasons(self) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    async def discover_team_pages(self, season: int) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    async def scrape_schedule(self, season: int) -> ParsedSeason:
        raise NotImplementedError

    async def scrape_roster(self, season: int) -> ParsedSeason:
        raise NotImplementedError("roster parser is not implemented for this adapter version")

    async def scrape_team_season_statistics(self, season: int) -> ParsedSeason:
        raise NotImplementedError("team statistics parser is not implemented")

    async def scrape_player_season_statistics(self, season: int) -> ParsedSeason:
        raise NotImplementedError("player statistics parser is not implemented")

    async def scrape_game_metadata(self, season: int) -> AsyncIterator[ParsedSeason]:
        if False:
            yield ParsedSeason(year=season, label=str(season))

    async def scrape_box_score(self, source_game_id: str) -> SourcePage:
        raise NotImplementedError("box-score parser is not implemented")

    async def scrape_team_game_statistics(self, source_game_id: str) -> SourcePage:
        raise NotImplementedError("team game statistics parser is not implemented")

    async def scrape_player_game_statistics(self, source_game_id: str) -> SourcePage:
        raise NotImplementedError("player game statistics parser is not implemented")

    async def scrape_scoring_summary(self, source_game_id: str) -> SourcePage:
        raise NotImplementedError("scoring summary parser is not implemented")

    async def scrape_drives(self, source_game_id: str) -> SourcePage:
        raise NotImplementedError("drive parser is not implemented")

    async def scrape_play_by_play(self, source_game_id: str) -> SourcePage:
        raise NotImplementedError("play-by-play parser is not implemented")

    async def scrape_rankings(self, season: int) -> SourcePage:
        raise NotImplementedError("rankings parser is not implemented")

    async def scrape_standings(self, season: int) -> SourcePage:
        raise NotImplementedError("standings parser is not implemented")
