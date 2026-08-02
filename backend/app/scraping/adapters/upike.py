from dataclasses import replace

from app.scraping.base import FootballSourceAdapter
from app.scraping.client import PoliteHttpClient
from app.scraping.parsers.upike_stats_v1 import (
    PARSER_VERSION,
    discover_upike_seasons,
    parse_upike_cumulative_stats,
)
from app.scraping.types import ParsedSeason


class UPIKEAthleticsAdapter(FootballSourceAdapter):
    source_name = "upike"
    parser_version = PARSER_VERSION
    stats_url = "https://upikebears.com/sports/football/stats"

    def __init__(self, client: PoliteHttpClient) -> None:
        self.client = client

    async def discover_seasons(self) -> list[int]:
        page = await self.client.fetch(self.source_name, self.stats_url)
        return discover_upike_seasons(page.content)

    async def discover_team_pages(self, season: int) -> list[str]:
        # This URL form was verified from the live 2025 season selector and fixture.
        return [f"https://upikebears.com/sports/football/stats/{season}"]

    async def scrape_schedule(self, season: int) -> ParsedSeason:
        url = (await self.discover_team_pages(season))[0]
        page = await self.client.fetch(self.source_name, url)
        digest, storage_path = self.client.store_raw(page, season)
        parsed = parse_upike_cumulative_stats(page.content, page.url)
        return replace(
            parsed,
            source_url=page.url,
            retrieved_at=page.retrieved_at,
            status_code=page.status_code,
            content_type=page.content_type,
            source_sha256=digest,
            storage_path=storage_path,
            parser_version=self.parser_version,
        )

    async def scrape_roster(self, season: int) -> ParsedSeason:
        # The cumulative page contains stable roster bio IDs for players with statistics.
        return await self.scrape_schedule(season)

    async def scrape_team_season_statistics(self, season: int) -> ParsedSeason:
        return await self.scrape_schedule(season)

    async def scrape_player_season_statistics(self, season: int) -> ParsedSeason:
        return await self.scrape_schedule(season)
