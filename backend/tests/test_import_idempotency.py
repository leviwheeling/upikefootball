from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Game, Player, Season
from app.scraping.parsers.upike_stats_v1 import parse_upike_cumulative_stats
from app.services.importer import import_parsed_season

FIXTURE = Path(__file__).parent / "fixtures/source/upike_2025_stats.html"


def test_fixture_import_is_idempotent(db: Session) -> None:
    parsed = parse_upike_cumulative_stats(
        FIXTURE.read_bytes(), "https://upikebears.com/sports/football/stats/2025"
    )

    first = import_parsed_season(db, parsed, source="upike", source_document_id=None)
    second = import_parsed_season(db, parsed, source="upike", source_document_id=None)

    assert first["games"] == 10
    assert first["players"] == 60
    assert second["games"] == 0
    assert second["players"] == 0
    assert db.scalar(select(func.count()).select_from(Season)) == 1
    assert db.scalar(select(func.count()).select_from(Game)) == 10
    assert db.scalar(select(func.count()).select_from(Player)) == 60
