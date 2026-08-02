import json
from datetime import datetime

from app.scraping.types import (
    ParsedDrive,
    ParsedGamebook,
    ParsedLeaderEntry,
    ParsedPrestoIntel,
    ParsedStanding,
)

PARSER_VERSION = "presto-browser-v1"


def _https_url(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.startswith("https://naiastats.prestosports.com/"):
        raise ValueError(f"{field} must be a naiastats.prestosports.com HTTPS URL")
    return value


def parse_presto_browser_fixture(content: bytes) -> ParsedPrestoIntel:
    """Parse a saved, normalized capture produced through a normal browser session."""
    raw = json.loads(content)
    if raw.get("capture_method") != "normal_browser_session":
        raise ValueError("fixture is not marked as a normal browser-session capture")

    year = int(raw["season"]["year"])
    standings_url = _https_url(raw["sources"]["standings"], "standings URL")
    leaders_url = _https_url(raw["sources"]["leaders"], "leaders URL")
    gamebook_url = _https_url(raw["sources"]["gamebook"], "gamebook URL")

    standings = [
        ParsedStanding(
            conference=str(item["conference"]),
            team_name=str(item["team"]),
            conference_wins=int(item["conference_wins"]),
            conference_losses=int(item["conference_losses"]),
            overall_wins=int(item["overall_wins"]),
            overall_losses=int(item["overall_losses"]),
            streak=str(item["streak"]),
        )
        for item in raw["standings"]
    ]
    leaders = [
        ParsedLeaderEntry(
            category=str(item["category"]),
            metric=str(item["metric"]),
            player_name=str(item["player"]),
            games_played=int(item["games_played"]),
            value_text=str(item["value"]),
            value_numeric=float(str(item["value"]).rstrip("%")),
        )
        for item in raw["leaders"]
    ]
    book = raw["gamebook"]
    drives = [
        ParsedDrive(
            sequence=index,
            team=str(item["team"]),
            quarter=int(item["quarter"]),
            start_clock=str(item["start_clock"]),
            possession_duration=str(item["possession_duration"]),
            start_spot=str(item["start_spot"]),
            plays=int(item["plays"]),
            yards=int(item["yards"]),
            result=str(item["result"]),
        )
        for index, item in enumerate(book["drives"], start=1)
    ]
    gamebook = ParsedGamebook(
        source_game_id=str(book["source_game_id"]),
        played_at=datetime.fromisoformat(str(book["played_at"])),
        opponent=str(book["opponent"]),
        upike_score=int(book["upike_score"]),
        opponent_score=int(book["opponent_score"]),
        location=str(book["location"]),
        stadium=str(book["stadium"]),
        attendance=int(book["attendance"]) if book.get("attendance") is not None else None,
        team_stats=dict(book["team_stats"]),
        drives=drives,
    )
    if not standings or not leaders or not drives:
        raise ValueError("browser fixture must include standings, leaders, and drives")
    return ParsedPrestoIntel(
        year=year,
        label=str(raw["season"]["label"]),
        retrieved_at=datetime.fromisoformat(str(raw["retrieved_at"])),
        standings_url=standings_url,
        leaders_url=leaders_url,
        gamebook_url=gamebook_url,
        standings=standings,
        leaders=leaders,
        gamebook=gamebook,
    )
