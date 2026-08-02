"""Extract source-linked UPIKE player history from saved SIDEARM stat pages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

TABLE_CATEGORIES = {
    "Individual Rushing Statistics": "Rushing",
    "Individual Passing Statistics": "Passing",
    "Individual Receiving Statistics": "Receiving",
    "Individual Defensive Statistics": "Defensive",
    "Individual Punting Statistics": "Punting",
    "Individual Field Goals Statistics": "Field Goals",
    "Individual Kickoffs Statistics": "Kickoffs",
    "Individual Punt Return Statistics": "Punt Returns",
    "Individual Kickoff Return Statistics": "Kickoff Returns",
    "Individual Scoring Statistics": "Scoring",
}

SCORING_HEADERS = [
    "#",
    "Player",
    "TD",
    "FG",
    "SAF",
    "KICK",
    "RUSH",
    "RCV",
    "PASS",
    "DXP",
    "PTS",
    "Bio Link",
]


def clean(value: str) -> str:
    return " ".join(value.split())


def display_name(source_name: str) -> str:
    if "," not in source_name:
        return clean(source_name)
    last, first = source_name.split(",", maxsplit=1)
    return clean(f"{first} {last}")


def name_key(value: str) -> str:
    without_suffix = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", value.casefold())
    return re.sub(r"[^a-z0-9]", "", without_suffix)


def caption_text(table: Tag) -> str:
    caption = table.find("caption")
    return clean(caption.get_text(" ", strip=True)) if isinstance(caption, Tag) else ""


def headers_for(table: Tag, caption: str) -> list[str]:
    if caption == "Individual Scoring Statistics":
        return SCORING_HEADERS
    thead = table.find("thead")
    first_row = thead.find("tr") if isinstance(thead, Tag) else None
    if not isinstance(first_row, Tag):
        return []
    return [clean(cell.get_text(" ", strip=True)) for cell in first_row.find_all("th")]


def parse_page(path: Path, year: int, current_players: dict[str, str]) -> dict[str, Any]:
    soup = BeautifulSoup(path.read_text(), "html.parser")
    players: dict[str, dict[str, Any]] = {}

    participation = next(
        (
            table
            for table in soup.find_all("table")
            if isinstance(table, Tag) and caption_text(table) == "Player Participation"
        ),
        None,
    )
    if isinstance(participation, Tag):
        for row in participation.select("tbody tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 3:
                continue
            link = cells[1].find("a")
            if not isinstance(link, Tag):
                continue
            source_name = display_name(link.get_text(" ", strip=True))
            current_name = current_players.get(name_key(source_name))
            if current_name is None:
                continue
            players[current_name] = {
                "jersey": clean(cells[0].get_text(" ", strip=True)),
                "games": int(clean(cells[2].get_text(" ", strip=True)) or "0"),
                "categories": {},
            }

    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        caption = caption_text(table)
        category = TABLE_CATEGORIES.get(caption)
        if category is None:
            continue
        headers = headers_for(table, caption)
        tbody = table.find("tbody")
        if not headers or not isinstance(tbody, Tag):
            continue
        for row in tbody.find_all("tr", recursive=False):
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) != len(headers) or len(cells) < 3:
                continue
            link = cells[1].find("a")
            if not isinstance(link, Tag):
                continue
            source_name = display_name(link.get_text(" ", strip=True))
            current_name = current_players.get(name_key(source_name))
            if current_name is None:
                continue
            values = [clean(cell.get_text(" ", strip=True)) for cell in cells]
            stats = {
                key: value
                for key, value in zip(headers, values, strict=True)
                if key not in {"#", "Player", "Bio Link"}
            }
            player = players.setdefault(
                current_name,
                {"jersey": values[0], "games": 0, "categories": {}},
            )
            player["categories"][category] = stats

    return {
        "label": f"{year}-{str(year + 1)[-2:]}",
        "source_url": f"https://upikebears.com/sports/football/stats/{year}",
        "players": players,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("season", nargs="+", help="YEAR=/path/to/stats.html")
    args = parser.parse_args()

    board = json.loads(args.board.read_text())
    current_names = {
        row["player"]
        for category in board["seasons"]["2025"]["players"].values()
        for row in category["rows"]
    }
    current_players = {name_key(name): name for name in current_names}

    seasons: dict[str, Any] = {}
    for item in args.season:
        year_text, path_text = item.split("=", maxsplit=1)
        year = int(year_text)
        seasons[year_text] = parse_page(Path(path_text), year, current_players)

    payload = {
        "sources": [
            {"label": season["label"], "url": season["source_url"]}
            for season in seasons.values()
        ],
        "seasons": seasons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        "Extracted",
        sum(len(season["players"]) for season in seasons.values()),
        "matched player-seasons",
    )


if __name__ == "__main__":
    main()
