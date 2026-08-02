import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from app.scraping.types import ParsedGame, ParsedPlayer, ParsedSeason

PARSER_VERSION = "upike-sidearm-stats-v1"
class ParseError(ValueError):
    pass


def _text(node: Tag | None) -> str:
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _score(value: str) -> tuple[int | None, int | None]:
    match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", value)
    return (int(match.group(1)), int(match.group(2))) if match else (None, None)


def parse_upike_cumulative_stats(html: bytes | str, source_url: str) -> ParsedSeason:
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.select_one("article.sidearm-cume-stats h1")) or _text(soup.title)
    year_match = re.search(r"\b(20\d{2})\b", title)
    if not year_match:
        raise ParseError("UPIKE cumulative stats page does not contain a season year")
    year = int(year_match.group(1))

    players: dict[str, ParsedPlayer] = {}
    for link in soup.select("a[data-player-id]"):
        player_id = str(link.get("data-player-id", "")).strip()
        if not player_id or player_id in players:
            continue
        row = link.find_parent("tr")
        jersey_cell = row.find("td") if row else None
        bio_link = row.select_one('td[data-label="BIO"] a') if row else None
        display_name = _text(link)
        if not display_name:
            continue
        players[player_id] = ParsedPlayer(
            source_player_id=player_id,
            display_name=display_name,
            jersey_number=_text(jersey_cell) or None,
            position=None,
            source_url=urljoin(source_url, str(bio_link.get("href"))) if bio_link else None,
        )

    result_table = soup.select_one("#gbg_results table")
    if result_table is None:
        raise ParseError("UPIKE cumulative stats page is missing the game-by-game results table")

    games: list[ParsedGame] = []
    for row in result_table.select("tbody tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) < 7:
            continue
        opponent_link = cells[1].find("a")
        if opponent_link is None:
            continue
        href = str(opponent_link.get("href", ""))
        source_game_id = parse_qs(urlparse(href).query).get("id", [""])[0]
        if not source_game_id:
            continue
        date_text = _text(cells[0])
        played_at = datetime.strptime(date_text, "%m/%d/%Y").replace(tzinfo=UTC)
        site_text = _text(cells[1]).casefold()
        if site_text.startswith("at "):
            site = "away"
        elif site_text.startswith("vs "):
            site = "home"
        else:
            site = "neutral"
        upike_score, opponent_score = _score(_text(cells[3]))
        attendance_text = _text(cells[6]).replace(",", "")
        games.append(
            ParsedGame(
                source_game_id=source_game_id,
                played_at=played_at,
                opponent=str(opponent_link.get("data-team-name") or _text(opponent_link)),
                site=site,
                result=_text(cells[2]) or None,
                upike_score=upike_score,
                opponent_score=opponent_score,
                attendance=int(attendance_text) if attendance_text.isdigit() else None,
                source_url=urljoin(source_url, href),
            )
        )

    return ParsedSeason(year=year, label=str(year), games=games, players=list(players.values()))


def discover_upike_seasons(html: bytes | str) -> list[int]:
    soup = BeautifulSoup(html, "html.parser")
    years: set[int] = set()
    for option in soup.select('option[value*="/sports/football/stats/"]'):
        match = re.search(r"/stats/(20\d{2})", str(option.get("value", "")))
        if match:
            years.add(int(match.group(1)))
    return sorted(years, reverse=True)
