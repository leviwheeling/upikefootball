from pathlib import Path

from app.scraping.parsers.upike_stats_v1 import (
    PARSER_VERSION,
    discover_upike_seasons,
    parse_upike_cumulative_stats,
)

FIXTURE = Path(__file__).parent / "fixtures/source/upike_2025_stats.html"
SOURCE_URL = "https://upikebears.com/sports/football/stats/2025"


def test_real_2025_sidearm_fixture_parses_games_and_players() -> None:
    parsed = parse_upike_cumulative_stats(FIXTURE.read_bytes(), SOURCE_URL)

    assert PARSER_VERSION == "upike-sidearm-stats-v1"
    assert parsed.year == 2025
    assert len(parsed.games) == 10
    assert len(parsed.players) == 60
    assert parsed.games[0].source_game_id == "8824"
    assert parsed.games[0].opponent == "Georgetown"
    assert parsed.games[0].upike_score == 17
    assert parsed.games[0].opponent_score == 34
    assert parsed.games[0].site == "away"
    assert parsed.players[0].source_player_id == "9235"
    assert parsed.players[0].display_name == "Williams, Amon"


def test_discovers_only_seasons_present_in_real_selector() -> None:
    seasons = discover_upike_seasons(FIXTURE.read_bytes())
    assert seasons[0] == 2025
    assert seasons[-1] == 2011
    assert len(seasons) == 15


def test_missing_optional_attendance_is_not_fabricated() -> None:
    content = FIXTURE.read_text().replace(">3102</td>", "></td>", 1)
    parsed = parse_upike_cumulative_stats(content, SOURCE_URL)
    assert parsed.games[0].attendance is None
