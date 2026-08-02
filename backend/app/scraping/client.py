import asyncio
import gzip
import hashlib
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
import structlog

from app.config import Settings
from app.scraping.base import SourceBlockedError, SourcePage

log = structlog.get_logger(__name__)


@dataclass
class HostThrottle:
    last_request: float = 0.0


class PoliteHttpClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._hosts: dict[str, HostThrottle] = {}
        self._robots: dict[str, RobotFileParser] = {}
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=settings.scraper_timeout_seconds,
            headers={"User-Agent": settings.scraper_user_agent, "Accept-Encoding": "gzip"},
        )

    async def __aenter__(self) -> "PoliteHttpClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def fetch(self, source: str, url: str, retries: int = 3) -> SourcePage:
        await self._assert_allowed(url)
        host = urlparse(url).netloc
        throttle = self._hosts.setdefault(host, HostThrottle())
        wait = self.settings.scraper_min_delay_seconds - (time.monotonic() - throttle.last_request)
        if wait > 0:
            await asyncio.sleep(wait)

        for attempt in range(retries):
            log.info("source_fetch_started", source=source, url=url, attempt=attempt + 1)
            response = await self._client.get(url)
            throttle.last_request = time.monotonic()
            if response.status_code == 403 and (
                response.headers.get("cf-mitigated") == "challenge"
                or "Just a moment" in response.text[:500]
            ):
                raise SourceBlockedError(
                    f"{host} presented a Cloudflare challenge; automated access was stopped"
                )
            if response.status_code not in {429, 500, 502, 503, 504}:
                response.raise_for_status()
                log.info(
                    "source_fetch_completed",
                    source=source,
                    url=str(response.url),
                    status_code=response.status_code,
                    content_bytes=len(response.content),
                )
                return SourcePage(
                    source=source,
                    url=str(response.url),
                    status_code=response.status_code,
                    content_type=response.headers.get("content-type", "application/octet-stream"),
                    content=response.content,
                    retrieved_at=datetime.now(UTC),
                )
            if attempt < retries - 1:
                await asyncio.sleep((2**attempt) + random.uniform(0, 0.5))
        response.raise_for_status()
        raise AssertionError("unreachable")

    async def _assert_allowed(self, url: str) -> None:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots.get(origin)
        if parser is None:
            robots_url = f"{origin}/robots.txt"
            parser = RobotFileParser(robots_url)
            try:
                response = await self._client.get(robots_url)
                parser.parse(response.text.splitlines())
            except httpx.HTTPError:
                parser.parse([])
            self._robots[origin] = parser
        if not parser.can_fetch(self.settings.scraper_user_agent, url):
            raise SourceBlockedError(f"robots.txt does not permit fetching {url}")

    def store_raw(self, page: SourcePage, season: int | None = None) -> tuple[str, str]:
        digest = hashlib.sha256(page.content).hexdigest()
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        suffix = Path(urlparse(page.url).path).suffix or ".html"
        directory = self.settings.raw_document_root / page.source / str(season or "unknown")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{timestamp}-{digest[:16]}{suffix}.gz"
        with gzip.open(path, "wb") as file:
            file.write(page.content)
        return digest, str(path)
