import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scraping.base import SourceBlockedError
from app.scraping.client import PoliteHttpClient


@dataclass
class DiscoveryResult:
    source: str
    requested_url: str
    status: str
    http_status: int | None
    canonical_url: str | None
    title: str | None
    season: int | None
    team_identity: str | None
    source_systems: list[str]
    navigation_links: list[str]
    table_headers: list[list[str]]
    embedded_json_blocks: int
    script_urls: list[str]
    api_candidates: list[str]
    player_links: list[str]
    game_links: list[str]
    box_score_links: list[str]
    play_by_play_links: list[str]
    roster_links: list[str]
    pagination_links: list[str]
    downloadable_files: list[str]
    notes: list[str]


def inspect_html(
    source: str, requested_url: str, status: int, final_url: str, html: bytes
) -> DiscoveryResult:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    canonical = soup.select_one('link[rel="canonical"]')
    links = [urljoin(final_url, str(a.get("href"))) for a in soup.select("a[href]")]
    scripts = [urljoin(final_url, str(s.get("src"))) for s in soup.select("script[src]")]
    text = soup.get_text(" ", strip=True)
    systems: list[str] = []
    markup = html[:200_000].decode("utf-8", "ignore").casefold()
    if "sidearm" in markup:
        systems.append("SIDEARM Sports")
    if "prestosports" in markup or "prestosports" in final_url:
        systems.append("PrestoSports")
    season_match = re.search(r"\b(20\d{2})(?:-\d{2})?\b", title or text[:1000])

    def matching(*needles: str) -> list[str]:
        return sorted({link for link in links if any(n in link.casefold() for n in needles)})

    table_headers = [
        [" ".join(cell.get_text(" ", strip=True).split()) for cell in table.select("thead th")]
        for table in soup.select("table")
    ]
    return DiscoveryResult(
        source=source,
        requested_url=requested_url,
        status="ok",
        http_status=status,
        canonical_url=str(canonical.get("href")) if canonical else final_url,
        title=title,
        season=int(season_match.group(1)) if season_match else None,
        team_identity="University of Pikeville" if "Pikeville" in text else None,
        source_systems=systems,
        navigation_links=sorted(set(links))[:250],
        table_headers=table_headers,
        embedded_json_blocks=len(
            soup.select('script[type="application/ld+json"], script[type="application/json"]')
        ),
        script_urls=sorted(set(scripts)),
        api_candidates=matching("/api/", ".json", ".xml", "ajax", "stats"),
        player_links=matching("/roster/", "/players/"),
        game_links=matching("/game/", "game_id="),
        box_score_links=matching("boxscore", "boxscores"),
        play_by_play_links=matching("play-by-play", "view=plays"),
        roster_links=matching("/roster"),
        pagination_links=matching("page=", "start="),
        downloadable_files=matching(".pdf", ".csv", ".xml", ".xlsx"),
        notes=[],
    )


async def discover_sources(client: PoliteHttpClient) -> list[DiscoveryResult]:
    targets = {
        "upike": "https://upikebears.com/sports/football/stats/2025",
        "aac": "https://aac.prestosports.com/sports/fball/2025-26",
        "naia": "https://naiastats.prestosports.com/sports/fball/2025-26/conf/Appalachian/standings?jsRendering=true",
    }
    results: list[DiscoveryResult] = []
    for source, url in targets.items():
        try:
            page = await client.fetch(source, url)
            client.store_raw(page, 2025)
            results.append(inspect_html(source, url, page.status_code, page.url, page.content))
        except SourceBlockedError as exc:
            results.append(
                DiscoveryResult(
                    source=source,
                    requested_url=url,
                    status="blocked",
                    http_status=403,
                    canonical_url=url,
                    title=None,
                    season=2025,
                    team_identity="University of Pikeville",
                    source_systems=["PrestoSports", "Cloudflare"],
                    navigation_links=[], table_headers=[], embedded_json_blocks=0,
                    script_urls=[], api_candidates=[], player_links=[], game_links=[],
                    box_score_links=[], play_by_play_links=[], roster_links=[],
                    pagination_links=[], downloadable_files=[], notes=[str(exc)],
                )
            )
    return results


def write_reports(results: list[DiscoveryResult], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    payload = {"generated_at": generated_at, "sources": [asdict(item) for item in results]}
    (output_dir / "source-discovery.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = ["# Source discovery report", "", f"Generated: {generated_at}", ""]
    for item in results:
        lines.extend(
            [
                f"## {item.source.upper()}", "",
                f"- URL: {item.requested_url}",
                f"- Status: {item.status} ({item.http_status or 'unknown'})",
                f"- Title: {item.title or 'Unavailable'}",
                f"- System: {', '.join(item.source_systems) or 'Unknown'}",
                f"- Tables: {len(item.table_headers)}",
                f"- Player links: {len(item.player_links)}",
                f"- Box-score links: {len(item.box_score_links)}",
                f"- Downloads: {len(item.downloadable_files)}",
                *(f"- Note: {note}" for note in item.notes), "",
            ]
        )
    (output_dir / "source-discovery.md").write_text("\n".join(lines))
