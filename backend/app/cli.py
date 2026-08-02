import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.logging import configure_logging
from app.models import Game, Player, Season, SourceDocument
from app.scraping.adapters import AACAdapter, NAIAAdapter, UPIKEAthleticsAdapter
from app.scraping.base import SourceBlockedError
from app.scraping.client import PoliteHttpClient
from app.scraping.discovery import discover_sources, write_reports
from app.scraping.parsers.upike_stats_v1 import PARSER_VERSION, parse_upike_cumulative_stats
from app.services.importer import import_parsed_season

configure_logging()
cli = typer.Typer(no_args_is_help=True, help="UPIKE Football Intelligence operations")


async def _discover() -> None:
    settings = get_settings()
    async with PoliteHttpClient(settings) as client:
        results = await discover_sources(client)
    output_dir = Path("../discovery") if Path("../discovery").exists() else Path("discovery")
    write_reports(results, output_dir)
    typer.echo(json.dumps({item.source: item.status for item in results}, indent=2))


@cli.command("discover-sources")
def discover_sources_command() -> None:
    """Inspect the verified public source entrypoints and write JSON/Markdown reports."""
    asyncio.run(_discover())


def _adapter(
    source: str, client: PoliteHttpClient
) -> AACAdapter | NAIAAdapter | UPIKEAthleticsAdapter:
    if source == "aac":
        return AACAdapter(client)
    if source == "naia":
        return NAIAAdapter(client)
    if source == "upike":
        return UPIKEAthleticsAdapter(client)
    raise typer.BadParameter("source must be one of: aac, naia, upike")


async def _scrape(source: str, season: int) -> None:
    settings = get_settings()
    async with PoliteHttpClient(settings) as client:
        adapter = _adapter(source, client)
        try:
            parsed = await adapter.scrape_schedule(season)
        except SourceBlockedError as exc:
            typer.echo(f"blocked: {exc}", err=True)
            raise typer.Exit(2) from exc
    with SessionLocal() as db:
        result = import_parsed_season(db, parsed, source=source, source_document_id=None)
    typer.echo(json.dumps(result, indent=2))


@cli.command()
def scrape(
    source: Annotated[str, typer.Option(help="aac, naia, or upike")],
    season: Annotated[str, typer.Option(help="Starting year, e.g. 2025 or 2025-26")],
) -> None:
    try:
        season_year = int(season.split("-", maxsplit=1)[0])
    except ValueError as exc:
        raise typer.BadParameter("season must start with a four-digit year") from exc
    if not 1900 <= season_year <= 2100:
        raise typer.BadParameter("season year is outside the supported range")
    asyncio.run(_scrape(source, season_year))


@cli.command("scrape-all")
def scrape_all(
    season: Annotated[int, typer.Option()] = datetime.now(UTC).year,
    incremental: Annotated[bool, typer.Option()] = False,
) -> None:
    """Run each adapter; blocked sources are reported without bypass attempts."""
    typer.echo(f"scrape run season={season} incremental={incremental}")
    for source in ("upike", "aac", "naia"):
        try:
            asyncio.run(_scrape(source, season))
        except typer.Exit:
            continue


@cli.command("seed-fixture")
def seed_fixture(
    fixture: Annotated[Path, typer.Option()] = Path("tests/fixtures/source/upike_2025_stats.html"),
) -> None:
    """Import the saved real UPIKE fixture through the production parser/importer."""
    content = fixture.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    url = "https://upikebears.com/sports/football/stats/2025"
    parsed = parse_upike_cumulative_stats(content, url)
    with SessionLocal() as db:
        document = db.scalar(
            select(SourceDocument).where(
                SourceDocument.source == "upike",
                SourceDocument.url == url,
                SourceDocument.sha256 == digest,
            )
        )
        if document is None:
            document = SourceDocument(
                source="upike",
                url=url,
                retrieved_at=datetime(2026, 8, 2, tzinfo=UTC),
                status_code=200,
                content_type="text/html; charset=utf-8",
                sha256=digest,
                storage_path=str(fixture),
                parser_version=PARSER_VERSION,
            )
            db.add(document)
            db.flush()
        result = import_parsed_season(
            db, parsed, source="upike", source_document_id=document.id
        )
    typer.echo(json.dumps(result, indent=2))


@cli.command()
def reconcile() -> None:
    typer.echo("No cross-source candidate records are available yet; nothing was merged.")


@cli.command()
def calculate() -> None:
    typer.echo("Advanced metrics remain unavailable until required underlying fields are imported.")


@cli.command()
def validate() -> None:
    with SessionLocal() as db:
        bad_scores = db.scalar(
            select(func.count()).select_from(Game).where(
                (Game.upike_score < 0) | (Game.opponent_score < 0)
            )
        ) or 0
        counts = {
            "seasons": db.scalar(select(func.count()).select_from(Season)) or 0,
            "games": db.scalar(select(func.count()).select_from(Game)) or 0,
            "players": db.scalar(select(func.count()).select_from(Player)) or 0,
            "invalid_negative_scores": bad_scores,
        }
    typer.echo(json.dumps(counts, indent=2))
    if bad_scores:
        raise typer.Exit(1)


if __name__ == "__main__":
    cli()
