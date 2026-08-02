from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ConferenceStanding, Gamebook, GameDrive, LeaderEntry
from app.scraping.parsers.presto_browser_v1 import parse_presto_browser_fixture
from app.services.importer import import_presto_intel

FIXTURE = Path(__file__).parent / "fixtures/source/presto_2025_browser.json"


def test_browser_fixture_contains_only_observed_intelligence() -> None:
    parsed = parse_presto_browser_fixture(FIXTURE.read_bytes())

    assert len(parsed.standings) == 7
    assert len(parsed.leaders) == 38
    assert len(parsed.gamebook.drives) == 29
    assert parsed.gamebook.upike_score == 51
    assert parsed.gamebook.opponent_score == 42
    assert parsed.gamebook.attendance == 1134


def test_presto_import_is_idempotent(db: Session) -> None:
    content = FIXTURE.read_bytes()
    parsed = parse_presto_browser_fixture(content)

    first = import_presto_intel(db, parsed, content=content, storage_path=str(FIXTURE))
    second = import_presto_intel(db, parsed, content=content, storage_path=str(FIXTURE))

    assert first == {
        "standings": 7,
        "leader_entries": 38,
        "gamebooks": 1,
        "drives": 29,
    }
    assert second == {
        "standings": 0,
        "leader_entries": 0,
        "gamebooks": 0,
        "drives": 0,
    }
    assert db.scalar(select(func.count()).select_from(ConferenceStanding)) == 7
    assert db.scalar(select(func.count()).select_from(LeaderEntry)) == 38
    assert db.scalar(select(func.count()).select_from(Gamebook)) == 1
    assert db.scalar(select(func.count()).select_from(GameDrive)) == 29
