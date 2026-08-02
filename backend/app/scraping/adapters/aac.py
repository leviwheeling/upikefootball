from app.scraping.base import FootballSourceAdapter, SourceBlockedError
from app.scraping.client import PoliteHttpClient
from app.scraping.types import ParsedSeason


class AACAdapter(FootballSourceAdapter):
    source_name = "aac"
    parser_version = "presto-aac-discovery-v1"
    verified_2025_landing = "https://aac.prestosports.com/sports/fball/2025-26"

    def __init__(self, client: PoliteHttpClient) -> None:
        self.client = client

    async def discover_seasons(self) -> list[int]:
        await self.client.fetch(self.source_name, self.verified_2025_landing)
        return [2025]

    async def discover_team_pages(self, season: int) -> list[str]:
        if season != 2025:
            return []
        return [self.verified_2025_landing]

    async def scrape_schedule(self, season: int) -> ParsedSeason:
        raise SourceBlockedError(
            "AAC currently presents a Cloudflare challenge to the polite HTTP client; "
            "no bypass is attempted"
        )
