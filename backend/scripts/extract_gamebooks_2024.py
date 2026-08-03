"""Extract normalized play rows from the supplied 2024-25 PDF gamebooks."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "INFO/24-25 Data/Games 24-25"
OUTPUT = ROOT / "backend/data/raw/upike_gamebook_plays_2024.json"

GAMES = [
    (
        "20240829_campbellsville",
        "Campbellsville at UPIKE Stat Corrections 10-19 (Attendance).pdf",
        "Aug 29",
        "vs. Campbellsville (KY)",
    ),
    (
        "20240907_georgetown",
        "GC at UPIKE Stats Corrections 10-29 (Attendance).pdf",
        "Sep 7",
        "vs. Georgetown (Ky.)",
    ),
    (
        "20240914_cumberlands",
        "UPIKE at UC Stat Corrections 9-19.pdf",
        "Sep 14",
        "at Cumberlands (Ky.)",
    ),
    (
        "20240921_faulkner",
        "-UPIKE at Faulkner Stat Corrections 10-18.pdf",
        "Sep 21",
        "at Faulkner (AL)",
    ),
    (
        "20241005_reinhardt",
        "RU at UPIKE Stat Corrections 10-29 (Attendance).pdf",
        "Oct 5",
        "vs. Reinhardt (Ga.)",
    ),
    ("20241012_kcu", "2UPIKE at KCU Stat Corrections 10-24.pdf", "Oct 12", "at Kentucky Christian"),
    (
        "20241019_union",
        "UPIKE at Union Stat Corrections 10-24.pdf",
        "Oct 19",
        "at Union Commonwealth",
    ),
    (
        "20241026_bluefield",
        "Bluefield at UPIKE Stat Corrections 10-30.pdf",
        "Oct 26",
        "vs. Bluefield (VA)",
    ),
    ("20241102_point", "UPIKE at PU FB Stat Corrections 11-7 xml.pdf", "Nov 2", "at Point"),
    (
        "20241116_st_andrews",
        "SAU at UPIKE FB Stat Corrections 11-17.pdf",
        "Nov 16",
        "vs. St. Andrews (NC)",
    ),
    ("20241123_0514", "BAKER-UPIKEboxscore_20241123_0514.pdf", "Nov 23", "at Baker"),
    ("20241130_0443", "KEISER UPIKE-boxscore_20241130_0443.pdf", "Nov 30", "at Keiser (Fla.)"),
]

PLAY_START = re.compile(r"^((?:1st|2nd|3rd|4th) and (?:\d+|GOAL) at)\s+(.+)$", re.I)
NORMAL_SPOT = re.compile(r"^(.+?\d+)\s+(.+)$")
STANDALONE_SPOT = re.compile(r"^(?:.+?\d+|50\s+yardline)$")
POSSESSION = re.compile(r"^(.+?) at (\d\d:\d\d)$")
PLAYER_NAME_ALIASES = {
    "D'Andre Staffor": "D'Andre Stafford",
    "Jalen Royal-Eil": "Jalen Royal-Eiland",
    "Kenyon Slaughte": "Kenyon Slaughter",
    "Tayden Carpente": "Tayden Carpenter",
    "Tyrese Christia": "Tyrese Christian",
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_play_rows(pages: list[str]) -> list[list[str]]:
    rows: list[list[str]] = [["Quarters: 1st | 2nd | 3rd | 4th"]]
    quarter = 1
    rows.append(["1st"])
    current: list[str] | None = None

    def flush() -> None:
        nonlocal current
        if current:
            rows.append([current[0], clean(current[1])])
        current = None

    for page in pages[5:]:
        lines = [clean(line) for line in page.splitlines() if clean(line)]
        index = 0
        while index < len(lines):
            line = lines[index]
            if "Start of Quarter #2" in line or "Start of 2nd quarter" in line:
                flush()
                if quarter != 2:
                    quarter = 2
                    rows.append(["2nd"])
                index += 1
                continue
            if "Start of 2nd Half" in line or "Start of 3rd quarter" in line:
                flush()
                if quarter != 3:
                    quarter = 3
                    rows.append(["3rd"])
                index += 1
                continue
            if "Start of Quarter #4" in line or "Start of 4th quarter" in line:
                flush()
                if quarter != 4:
                    quarter = 4
                    rows.append(["4th"])
                index += 1
                continue

            play_match = PLAY_START.match(line)
            if play_match:
                flush()
                prefix, rest = play_match.groups()
                normal = NORMAL_SPOT.match(rest)
                if normal:
                    spot, description = normal.groups()
                    current = [f"{prefix} {spot}", description]
                elif index + 1 < len(lines) and STANDALONE_SPOT.match(lines[index + 1]):
                    current = [f"{prefix} {lines[index + 1]}", rest]
                    index += 1
                else:
                    current = [prefix, rest]
                index += 1
                continue

            possession = POSSESSION.match(line)
            if possession and not line.startswith(("Total", "Time of Possession")):
                flush()
                rows.append([line])
                index += 1
                continue

            if current and not line.startswith(
                (
                    "Total ",
                    "Pikeville (KY)",
                    "Campbellsville",
                    "Georgetown",
                    "Cumberlands",
                    "Faulkner",
                    "Reinhardt",
                    "Kentucky Christian",
                    "Union",
                    "Bluefield",
                    "Point",
                    "St. Andrews",
                    "Baker",
                    "Keiser",
                    "Play By Play",
                    "Start of",
                )
            ):
                current[1] += f" {line}"
            index += 1
    flush()
    return rows


def parse_player_stats(page: pdfplumber.page.Page) -> dict[str, list[dict[str, object]]]:
    """Parse the Pikeville half of the ruled individual-offense page."""
    pikeville_heading = next(
        (
            word
            for word in page.extract_words()
            if str(word["text"]).startswith("Pikeville") and float(word["top"]) < 80
        ),
        None,
    )
    is_left = bool(pikeville_heading and float(pikeville_heading["x0"]) < page.width / 2)
    crop_box = (0, 55, 307, 390) if is_left else (305, 55, page.width, 390)
    text = page.crop(crop_box).extract_text(layout=True) or ""
    columns = {
        "Passing": [
            "completions",
            "attempts",
            "yards",
            "touchdowns",
            "interceptions",
            "long",
            "sacks",
        ],
        "Rushing": ["attempts", "gain", "loss", "yards", "touchdowns", "long", "average"],
        "Receiving": ["receptions", "yards", "touchdowns", "long"],
    }
    result: dict[str, list[dict[str, object]]] = {key: [] for key in columns}
    section: str | None = None
    for raw_line in text.splitlines():
        line = clean(raw_line)
        if line.startswith("Passing "):
            section = "Passing"
            continue
        if line.startswith("Rushing "):
            section = "Rushing"
            continue
        if line.startswith("Receiving "):
            section = "Receiving"
            continue
        if line.startswith(("Punting ", "All Returns", "Field Goals", "Kickoffs")):
            section = None
            continue
        if not section or not line or line.startswith("Totals"):
            continue
        row_match = re.match(r"^(.*?)\s{2,}(-?\d.*)$", raw_line.strip())
        if not row_match:
            continue
        name, values_text = row_match.groups()
        values = values_text.split()
        if len(values) < len(columns[section]):
            continue
        parsed: dict[str, object] = {"player": PLAYER_NAME_ALIASES.get(clean(name), clean(name))}
        for column, value in zip(columns[section], values, strict=False):
            try:
                parsed[column] = float(value) if "." in value else int(value)
            except ValueError:
                parsed[column] = value
        result[section].append(parsed)
    return result


def main() -> None:
    games: list[dict[str, object]] = []
    for game_id, filename, date, opponent in GAMES:
        source = SOURCE / filename
        with pdfplumber.open(source) as pdf:
            pages = [page.extract_text(layout=True) or "" for page in pdf.pages]
            player_stats = parse_player_stats(pdf.pages[2])
        games.append(
            {
                "game_id": game_id,
                "date": date,
                "opponent": opponent,
                "url": f"/api/play-analytics/gamebook/2024/{game_id}",
                "source_pdf": str(source.relative_to(ROOT)),
                "player_stats": player_stats,
                "rows": parse_play_rows(pages),
            }
        )
    OUTPUT.write_text(json.dumps(games, indent=2) + "\n")
    print(json.dumps({game["game_id"]: len(game["rows"]) for game in games}, indent=2))


if __name__ == "__main__":
    main()
