from app.scraping.base import FootballSourceAdapter, SourceBlockedError
from app.scraping.client import PoliteHttpClient
from app.scraping.types import ParsedSeason


class NAIAAdapter(FootballSourceAdapter):
    source_name = "naia"
    parser_version = "presto-naia-discovery-v1"
    verified_2025_schedule = "https://naiastats.prestosports.com/sports/fball/2025-26/schedule"
    verified_2025_standings = (
        "https://naiastats.prestosports.com/sports/fball/2025-26/conf/Appalachian/standings"
        "?jsRendering=true"
    )

    def __init__(self, client: PoliteHttpClient) -> None:
        self.client = client

    async def discover_seasons(self) -> list[int]:
        await self.client.fetch(self.source_name, self.verified_2025_schedule)
        return [2025]

    async def discover_team_pages(self, season: int) -> list[str]:
        return [self.verified_2025_schedule, self.verified_2025_standings] if season == 2025 else []

    async def scrape_schedule(self, season: int) -> ParsedSeason:
        raise SourceBlockedError(
            "NAIA Stats currently presents a Cloudflare challenge; no bypass is attempted"
        )
