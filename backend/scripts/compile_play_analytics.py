"""Compile a UPIKE coaching export and official gamebooks into analytics JSON.

The Excel export supplies coaching tags (formation, call, motion, result and gain).
Official NAIA gamebook rows supply opponent, game context, play descriptions and
player names.  Alignment is sequence based and the output retains match confidence
so downstream views never imply more certainty than the sources support.
"""

from __future__ import annotations

import json
import math
import re
import statistics
import sys
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SEASON = sys.argv[1] if len(sys.argv) > 1 else "2025"
if SEASON not in {"2024", "2025"}:
    raise SystemExit("Season must be 2024 or 2025")
LABEL = {"2024": "2024-25", "2025": "2025-26"}[SEASON]
WORKBOOK_PATH = ROOT / (
    "INFO/24-25 Data/FROM HUDL play by play.xlsx"
    if SEASON == "2024"
    else "INFO/25-26 Play DATA/PlaylistData_2026-08-02.xlsx"
)
GAMEBOOK_PATH = ROOT / f"backend/data/raw/upike_gamebook_plays_{SEASON}.json"
BOARD_PATH = ROOT / "backend/data/compiled/upike_stat_board.json"
OUTPUT_PATH = ROOT / f"backend/data/compiled/upike_play_analytics_{SEASON}.json"
OFFICIAL_2024_GAME_LOG = (
    "https://naiastats.prestosports.com/sports/fball/2024-25/teams/pikevilleky?view=gamelog"
)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PDF_BY_GAME = {
    "20250830_dizi": "Football at Georgetown Edited xml 9-2.pdf",
    "20250913_kqps": "UPike at Campbellsville FB Edited xml 9-16.pdf",
    "20250920_xzbh": "FB vs. Cumberland 9-20 Edited xml.pdf",
    "20250927_uiom": "Football at Maryville 9-27 Edited XML.pdf",
    "20251011_j14v": "URG at UPike Football 10-11 Edited xml.pdf",
    "20251018_1r1b": "Point at UPike Football Edited xml 10-20.pdf",
    "20251025_nhhj": "\\UPike at Bluefield 10-25 Edited xml.pdf",
    "20251101_rdne": "Union vs upike.pdf",
    "20251108_iabb": "KCU at UPike Football 11-8 Edited xml.pdf",
    "20251115_cb1j": "Reinhardt vs upike-boxscore_20251115_0318.pdf",
}


def read_xlsx(path: Path) -> list[dict[str, Any]]:
    """Read the first worksheet with the Python standard library only."""
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", NS):
                shared.append("".join(node.text or "" for node in item.findall(".//m:t", NS)))
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    def column_index(reference: str) -> int:
        letters = re.match(r"[A-Z]+", reference)
        result = 0
        for char in letters.group(0) if letters else "A":
            result = result * 26 + ord(char) - 64
        return result - 1

    values: list[list[Any]] = []
    for row in sheet.findall(".//m:sheetData/m:row", NS):
        cells: dict[int, Any] = {}
        for cell in row.findall("m:c", NS):
            index = column_index(cell.attrib.get("r", "A1"))
            value_node = cell.find("m:v", NS)
            if value_node is None:
                value: Any = None
            elif cell.attrib.get("t") == "s":
                value = shared[int(value_node.text or 0)]
            else:
                raw = value_node.text or ""
                try:
                    numeric = float(raw)
                    value = int(numeric) if numeric.is_integer() else numeric
                except ValueError:
                    value = raw
            cells[index] = value
        width = max(cells, default=-1) + 1
        values.append([cells.get(index) for index in range(width)])
    headers = [str(value or "").strip() for value in values[0]]
    return [
        dict(zip(headers, row + [None] * (len(headers) - len(row)), strict=False))
        for row in values[1:]
    ]


def result_family(value: object) -> str:
    text = "" if value is None else str(value)
    for prefix in ("Complete", "Rush", "Interception"):
        if text.startswith(prefix):
            return prefix
    return text


def official_result(description: str) -> str:
    text = description.casefold()
    if "timeout" in text:
        return "Timeout"
    if "penalty" in text and not any(
        token in text
        for token in ("pass complete", "pass incomplete", "rush", "sacked", "intercepted")
    ):
        return "Penalty"
    if "pass intercepted" in text:
        return "Interception, Def TD" if "touchdown" in text else "Interception"
    if "pass complete" in text:
        if "fumble" in text:
            return "Complete, Fumble"
        return "Complete, TD" if "touchdown" in text else "Complete"
    if "pass incomplete" in text:
        return "Incomplete"
    if "sacked" in text:
        return "Sack"
    if re.search(r"\brush\b.*\bfor\b", text):
        if "fumble" in text:
            return "Fumble"
        return "Rush, TD" if "touchdown" in text else "Rush"
    if "fumble" in text:
        return "Fumble"
    return "Other"


def parse_context(context: str) -> tuple[int | None, int | None, int | None]:
    match = re.match(r"^(1st|2nd|3rd|4th) and (\d+|Goal) at ([A-Z .()]+?)(\d+)$", context, re.I)
    if not match:
        return None, None, None
    down = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4}[match.group(1).lower()]
    spot = int(match.group(4))
    yard_line = -spot if "PIKE" in match.group(3).upper() else spot
    distance = spot if match.group(2).casefold() == "goal" else int(match.group(2))
    return down, distance, yard_line


def parse_gain(description: str) -> int | None:
    text = description.casefold()
    loss = re.search(r"for loss of (\d+) yards?", text)
    if loss:
        return -int(loss.group(1))
    if "for no gain" in text:
        return 0
    gain = re.search(r"for (-?\d+) yards?", text)
    return int(gain.group(1)) if gain else None


def extract_offense(game: dict[str, Any]) -> list[dict[str, Any]]:
    in_pbp = False
    possession: str | None = None
    quarter: int | None = None
    drive = 0
    output: list[dict[str, Any]] = []
    for row in game["rows"]:
        if not row:
            continue
        joined = " ".join(row)
        if joined.startswith("Quarters:"):
            in_pbp = True
            continue
        if not in_pbp:
            continue
        if len(row) == 1 and row[0] in {"1st", "2nd", "3rd", "4th"}:
            quarter = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4}[row[0]]
            continue
        if len(row) == 1 and re.search(r" at \d\d:\d\d$", row[0]):
            possession = "UPIKE" if row[0].casefold().startswith("pikeville") else "OPP"
            continue
        if len(row) != 2 or not re.match(r"^(1st|2nd|3rd|4th) and ", row[0], re.I):
            continue
        context, description = row
        lowered = description.casefold()
        if "drive start" in lowered:
            if possession == "UPIKE":
                drive += 1
            continue
        if possession != "UPIKE" or any(token in lowered for token in ("start of ", "end of game")):
            continue
        result = official_result(description)
        if result == "Other":
            continue
        down, distance, yard_line = parse_context(context)
        clock = None
        clock_match = re.search(r"clock (\d\d:\d\d)", description)
        if clock_match:
            clock = clock_match.group(1)
        output.append(
            {
                "context": context,
                "description": description,
                "result": result,
                "down": down,
                "distance": distance,
                "yard_line": yard_line,
                "gain": parse_gain(description),
                "quarter": quarter,
                "drive": drive,
                "clock": clock,
            }
        )
    return output


def numeric_cost(left: object, right: object, missing: float, close: float, far: float) -> float:
    if left is None or right is None:
        return missing
    try:
        delta = abs(float(left) - float(right))
    except (TypeError, ValueError):
        return far
    if delta == 0:
        return 0.0
    if delta <= 1:
        return close
    if delta <= 3:
        return (close + far) / 2
    return far


def match_cost(workbook: dict[str, Any], official: dict[str, Any]) -> float:
    wb_result = workbook.get("RESULT")
    off_result = official["result"]
    if wb_result is None:
        result_cost = 0.8
    elif wb_result == off_result:
        result_cost = 0.0
    elif result_family(wb_result) == result_family(off_result):
        result_cost = 0.25
    elif wb_result == "Penalty" and "penalty" in official["description"].casefold():
        result_cost = 0.65
    else:
        result_cost = 3.0
    down = workbook.get("DN")
    down_cost = (
        0.1
        if down in (None, 0) or official["down"] is None
        else (0.0 if down == official["down"] else 0.7)
    )
    return (
        result_cost
        + down_cost
        + numeric_cost(workbook.get("DIST"), official["distance"], 0.1, 0.08, 0.45)
        + numeric_cost(workbook.get("YARD LN"), official["yard_line"], 0.1, 0.06, 0.35)
        + numeric_cost(workbook.get("GN/LS"), official["gain"], 0.08, 0.05, 0.35)
    )


def align(
    workbook: list[dict[str, Any]], official: list[dict[str, Any]]
) -> list[tuple[int, int, float]]:
    """Needleman-Wunsch sequence alignment; pure stdlib and deterministic."""
    m, n = len(workbook), len(official)
    gap = 2.0
    costs = [[math.inf] * (n + 1) for _ in range(m + 1)]
    back = [bytearray(n + 1) for _ in range(m + 1)]
    for j in range(n + 1):
        costs[0][j] = j * gap
    for i in range(m + 1):
        costs[i][0] = i * gap
    for i in range(1, m + 1):
        previous = costs[i - 1]
        current = costs[i]
        for j in range(1, n + 1):
            direct_cost = match_cost(workbook[i - 1], official[j - 1])
            choices = (previous[j - 1] + direct_cost, previous[j] + gap, current[j - 1] + gap)
            action = min(range(3), key=choices.__getitem__)
            current[j] = choices[action]
            back[i][j] = action
    matches: list[tuple[int, int, float]] = []
    i, j = m, n
    while i or j:
        action = back[i][j]
        if i and j and action == 0:
            matches.append((i - 1, j - 1, match_cost(workbook[i - 1], official[j - 1])))
            i -= 1
            j -= 1
        elif i and (not j or action == 1):
            i -= 1
        else:
            j -= 1
    return list(reversed(matches))


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


NAME_ALIASES = {
    "Deajuan McDougle": ("deajuanmcdougl",),
    "Demarcus Calhoun": ("demarcuscalhou",),
    "D'Andre Stafford": ("dandrestaffor",),
    "Jalen Royal-Eiland": ("jalenroyaleil",),
    "Kenyon Slaughter": ("kenyonslaughte",),
    "Miguel Hernandez": ("miguelhernande", "mhernandez"),
    "Tayden Carpenter": ("taydencarpente",),
    "Tyrese Christian": ("tyresechristia",),
}


def name_in_text(text: str, name: str) -> bool:
    compact = normalize_name(text)
    parts = name.split()
    variants = [normalize_name(name)]
    if len(parts) >= 2:
        variants.append(normalize_name(parts[-1] + " " + " ".join(parts[:-1])))
    variants.extend(NAME_ALIASES.get(name, ()))
    return any(variant in compact for variant in variants)


def players_in_text(description: str, player_names: Iterable[str]) -> list[str]:
    found = [name for name in player_names if name_in_text(description, name)]
    return sorted(
        set(found), key=lambda name: description.casefold().find(name.split()[-1].casefold())
    )


def player_roles(description: str, player_names: Iterable[str]) -> dict[str, Any]:
    found = players_in_text(description, player_names)
    lowered = description.casefold()
    passer = rusher = target = None
    if (
        " pass " in lowered
        or " pass complete" in lowered
        or " pass incomplete" in lowered
        or " pass intercepted" in lowered
        or " sacked" in lowered
    ):
        marker = min(
            (
                lowered.find(token)
                for token in (
                    " pass ",
                    " pass complete",
                    " pass incomplete",
                    " pass intercepted",
                    " sacked",
                )
                if lowered.find(token) >= 0
            ),
            default=len(lowered),
        )
        passer = next((name for name in found if name_in_text(description[:marker], name)), None)
        if " to " in lowered:
            after = description[lowered.find(" to ") + 4 :]
            target = next((name for name in found if name_in_text(after, name)), None)
    if " rush " in lowered:
        marker = lowered.find(" rush ")
        rusher = next((name for name in found if name_in_text(description[:marker], name)), None)
    return {"players": found, "passer": passer, "rusher": rusher, "target": target}


def play_type(result: str | None, call: str | None) -> str:
    result_text = result or ""
    if result_text.startswith("Rush") or result_text == "Fumble":
        return "Run"
    if result_text.startswith("Complete") or result_text in {
        "Incomplete",
        "Interception",
        "Interception, Def TD",
        "Sack",
    }:
        return "Pass"
    call_text = str(call or "").casefold()
    if any(token in call_text for token in ("zone", "power", "counter", "draw", "sweep")):
        return "Run"
    return "Other"


def field_zone(yard_line: int | float | None) -> str:
    if yard_line is None:
        return "Unknown"
    yard = float(yard_line)
    if yard <= -80:
        return "Backed Up"
    if yard < -20:
        return "Own Territory"
    if yard <= 20:
        return "Midfield"
    if yard < 80:
        return "Plus Territory"
    return "Red Zone"


def distance_bucket(distance: int | float | None) -> str:
    if distance is None:
        return "Unknown"
    if distance <= 3:
        return "Short (1-3)"
    if distance <= 6:
        return "Medium (4-6)"
    if distance <= 10:
        return "Long (7-10)"
    return "Very Long (11+)"


def success(
    down: int | None, distance: float | None, gain: float | None, result: str | None
) -> bool | None:
    if (
        result in {None, "Penalty", "Timeout", "None", "Downed"}
        or down is None
        or distance is None
        or gain is None
    ):
        return None
    if "TD" in result:
        return True
    threshold = {1: 0.5, 2: 0.7, 3: 1.0, 4: 1.0}.get(int(down), 1.0)
    return gain >= distance * threshold


def pct(numerator: int | float, denominator: int | float) -> float | None:
    return round(100 * numerator / denominator, 1) if denominator else None


def aggregate(rows: list[dict[str, Any]], key: str, min_plays: int = 1) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = row.get(key)
        if value not in (None, "", "Unknown"):
            groups[str(value)].append(row)
    output = []
    for label, items in groups.items():
        eligible = [item for item in items if item["success"] is not None]
        gains = [float(item["gain"]) for item in items if item.get("gain") is not None]
        successes = sum(item["success"] is True for item in eligible)
        if len(items) < min_plays:
            continue
        output.append(
            {
                "label": label,
                "plays": len(items),
                "graded_plays": len(eligible),
                "successes": successes,
                "success_rate": pct(successes, len(eligible)),
                "total_yards": round(sum(gains), 1),
                "yards_per_play": round(statistics.fmean(gains), 2) if gains else None,
                "explosives": sum(bool(item["explosive"]) for item in items),
                "touchdowns": sum(bool(item["touchdown"]) for item in items),
                "negative_plays": sum(bool(item["negative"]) for item in items),
                "turnover_events": sum(bool(item["turnover_event"]) for item in items),
            }
        )
    return sorted(output, key=lambda item: (-item["plays"], item["label"]))


def official_player_stats(board: dict[str, Any], player: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for category_name, category in board["seasons"][SEASON].get("players", {}).items():
        for row in category["rows"]:
            if row.get("player") == player:
                result[category_name] = {
                    column: row.get(column, "-") for column in category["columns"]
                }
    return result


CANONICAL_2024_NAMES = {
    "BAKER Lee Kirkland": "Lee Kirkland",
    "D'Andre Staffor": "D'Andre Stafford",
    "Jalen Royal-Eil": "Jalen Royal-Eiland",
    "Kenyon Slaughte": "Kenyon Slaughter",
    "Tayden Carpente": "Tayden Carpenter",
    "Tyrese Christia": "Tyrese Christian",
    "ST. Lee Kirkland": "Lee Kirkland",
}


def discover_offensive_players(plays: Iterable[dict[str, Any]]) -> list[str]:
    """Recover 2024 offensive identities from official play descriptions."""
    names: set[str] = set()
    for play in plays:
        description = str(play.get("description", ""))
        actor = re.match(r"^(.+?) (?:pass|rush|sacked)\b", description, re.I)
        if actor:
            names.add(actor.group(1).strip())
        target = re.search(
            r"\bto ([A-Z][A-Za-z'’.-]+(?: [A-Z][A-Za-z'’.-]+){1,3})(?: for|\s*\(|,|\.)", description
        )
        if target:
            names.add(target.group(1).strip())
    cleaned = {
        CANONICAL_2024_NAMES.get(name, name)
        for name in names
        if name.casefold() != "team" and not re.search(r"\d|yardline", name, re.I)
    }
    return sorted(cleaned)


def supplied_player_stats(
    gamebooks: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Index exact per-game individual tables extracted from supplied PDFs."""
    output: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for game in gamebooks:
        for category, rows in game.get("player_stats", {}).items():
            for row in rows:
                player = str(row["player"])
                entry = output[player].setdefault(
                    game["game_id"],
                    {
                        "game_id": game["game_id"],
                        "date": game["date"],
                        "opponent": game["opponent"],
                        "categories": {},
                    },
                )
                entry["categories"][category] = row
    return output


def supplied_total(games: dict[str, dict[str, Any]], category: str, metric: str) -> int:
    return round(
        sum(float(game["categories"].get(category, {}).get(metric, 0)) for game in games.values())
    )


def main() -> None:
    workbook = read_xlsx(WORKBOOK_PATH)
    gamebooks = json.loads(GAMEBOOK_PATH.read_text())
    if SEASON == "2024":
        for game in gamebooks:
            game["url"] = OFFICIAL_2024_GAME_LOG
    board = json.loads(BOARD_PATH.read_text())
    official: list[dict[str, Any]] = []
    for game_index, game in enumerate(gamebooks):
        game["plays"] = extract_offense(game)
        for play_index, item in enumerate(game["plays"]):
            official.append({**item, "game_index": game_index, "game_play_index": play_index})
    gamebook_player_stats = supplied_player_stats(gamebooks)
    player_names = sorted(
        set(board.get("player_profiles", {}))
        | set(gamebook_player_stats)
        | (set(discover_offensive_players(official)) if SEASON == "2024" else set())
    )

    by_workbook: dict[int, tuple[dict[str, Any], float]] = {}
    game_index_by_workbook: dict[int, int] = {}
    game_snap_by_workbook: dict[int, int] = {}
    if SEASON == "2024":
        # The supplied HUDL playlist is grouped by game, but is not chronological and
        # omits St. Andrews. PLAY # drops identify the 11 source-game boundaries.
        segment_starts = [0]
        for index in range(1, len(workbook)):
            previous = workbook[index - 1].get("PLAY #")
            current = workbook[index].get("PLAY #")
            if (
                isinstance(previous, (int, float))
                and isinstance(current, (int, float))
                and current < previous
            ):
                segment_starts.append(index)
        segment_bounds = [*segment_starts, len(workbook)]
        candidates: list[tuple[float, int, int, list[tuple[int, int, float]]]] = []
        for segment_index, (start, end) in enumerate(
            zip(segment_bounds[:-1], segment_bounds[1:], strict=True)
        ):
            for game_index, game in enumerate(gamebooks):
                matches = align(workbook[start:end], game["plays"])
                average_cost = sum(cost for _, _, cost in matches) / max(len(matches), 1)
                candidates.append((average_cost, segment_index, game_index, matches))
        assigned_segments: set[int] = set()
        assigned_games: set[int] = set()
        for _, segment_index, game_index, matches in sorted(candidates):
            if segment_index in assigned_segments or game_index in assigned_games:
                continue
            assigned_segments.add(segment_index)
            assigned_games.add(game_index)
            start, end = segment_bounds[segment_index : segment_index + 2]
            for local_index in range(end - start):
                workbook_index = start + local_index
                game_index_by_workbook[workbook_index] = game_index
                game_snap_by_workbook[workbook_index] = local_index + 1
            for workbook_local, official_local, cost in matches:
                by_workbook[start + workbook_local] = (
                    gamebooks[game_index]["plays"][official_local],
                    cost,
                )
    else:
        matches = align(workbook, official)
        by_workbook = {
            workbook_index: (official[official_index], cost)
            for workbook_index, official_index, cost in matches
        }
        first_match: dict[int, int] = {}
        for workbook_index, official_index, _ in matches:
            first_match.setdefault(official[official_index]["game_index"], workbook_index)
        starts = [first_match.get(game_index, 0) for game_index in range(len(gamebooks))]
        starts[0] = 0
        boundaries = [*starts, len(workbook)]
        for workbook_index in range(len(workbook)):
            game_index = max(index for index, start in enumerate(starts) if start <= workbook_index)
            game_index_by_workbook[workbook_index] = game_index
            game_snap_by_workbook[workbook_index] = workbook_index - boundaries[game_index] + 1

    board_game_log = board["seasons"][SEASON].get("game_log", [])
    for index, row in enumerate(board_game_log):
        if not row.get("game_id") and index < len(gamebooks):
            row["game_id"] = gamebooks[index]["game_id"]
    game_log = {row.get("game_id"): row for row in board_game_log}
    snaps: list[dict[str, Any]] = []
    for workbook_index, raw in enumerate(workbook):
        game_index = game_index_by_workbook[workbook_index]
        game = gamebooks[game_index]
        match = by_workbook.get(workbook_index)
        official_row = match[0] if match else None
        cost = match[1] if match else None
        result = str(raw.get("RESULT") or "None")
        gain_value = raw.get("GN/LS")
        gain = float(gain_value) if isinstance(gain_value, (int, float)) else None
        down_value = raw.get("DN")
        down = int(down_value) if isinstance(down_value, (int, float)) and down_value else None
        distance_value = raw.get("DIST")
        distance = float(distance_value) if isinstance(distance_value, (int, float)) else None
        yard_value = raw.get("YARD LN")
        yard_line = int(yard_value) if isinstance(yard_value, (int, float)) else None
        kind = play_type(result, raw.get("OFF PLAY"))
        no_play = bool(official_row and "NO PLAY" in official_row["description"].upper())
        graded = None if no_play else success(down, distance, gain, result)
        roles = (
            player_roles(official_row["description"], player_names)
            if official_row
            else {"players": [], "passer": None, "rusher": None, "target": None}
        )
        confidence = (
            "unmatched"
            if cost is None
            else "high"
            if cost <= 0.35
            else "medium"
            if cost <= 1.15
            else "low"
        )
        snap = {
            "id": f"{game['game_id']}-{game_snap_by_workbook[workbook_index]:03d}",
            "season": SEASON,
            "game_id": game["game_id"],
            "game_snap": game_snap_by_workbook[workbook_index],
            "season_snap": workbook_index + 1,
            "source_play_number": raw.get("PLAY #"),
            "date": game["date"],
            "opponent": game["opponent"],
            "source_url": game["url"],
            "quarter": official_row.get("quarter") if official_row else None,
            "drive": official_row.get("drive") if official_row else None,
            "clock": official_row.get("clock") if official_row else None,
            "context": official_row.get("context") if official_row else None,
            "description": official_row.get("description") if official_row else None,
            "down": down,
            "distance": distance,
            "yard_line": yard_line,
            "gain": gain,
            "result": result,
            "play_type": kind,
            "formation": raw.get("FORMATION"),
            "shift": raw.get("SHIFT"),
            "motion": raw.get("MOTION"),
            "off_play": raw.get("OFF PLAY"),
            "def_front": raw.get("DEF FRONT"),
            "def_stunt": raw.get("DEF STUNT"),
            "blitz": raw.get("BLITZ"),
            "coverage": raw.get("COVERAGE"),
            "play_family": raw.get("PLAY FAMILY"),
            "field_zone": field_zone(yard_line),
            "distance_bucket": distance_bucket(distance),
            "success": graded,
            "explosive": bool(
                not no_play
                and gain is not None
                and (
                    (kind == "Run" and gain >= 10)
                    or (kind == "Pass" and result.startswith("Complete") and gain >= 15)
                )
            ),
            "negative": bool(
                not no_play
                and (
                    (gain is not None and gain < 0)
                    or result in {"Sack", "Interception", "Interception, Def TD", "Fumble"}
                )
            ),
            "touchdown": bool(not no_play and "TD" in result),
            "turnover_event": bool(
                not no_play
                and result in {"Interception", "Interception, Def TD", "Fumble", "Complete, Fumble"}
            ),
            "conversion": bool(
                not no_play
                and down in {3, 4}
                and distance is not None
                and gain is not None
                and gain >= distance
            ),
            "no_play": no_play,
            "players": roles["players"],
            "passer": roles["passer"],
            "rusher": roles["rusher"],
            "target": roles["target"],
            "match_confidence": confidence,
            "alignment_cost": round(cost, 3) if cost is not None else None,
        }
        snaps.append(snap)

    game_rows = []
    for game in gamebooks:
        items = [row for row in snaps if row["game_id"] == game["game_id"]]
        eligible = [row for row in items if row["success"] is not None]
        gains = [row["gain"] for row in items if row["gain"] is not None]
        official_log = game_log.get(game["game_id"], {})
        score = str(official_log.get("score", ""))
        score_numbers = [int(value) for value in re.findall(r"\d+", score)]
        if len(score_numbers) > 1 and score.startswith("L"):
            opponent_score, upike_score = score_numbers[:2]
        else:
            upike_score = score_numbers[0] if score_numbers else None
            opponent_score = score_numbers[1] if len(score_numbers) > 1 else None
        game_rows.append(
            {
                "game_id": game["game_id"],
                "date": game["date"],
                "opponent": game["opponent"],
                "result": score,
                "upike_score": upike_score,
                "opponent_score": opponent_score,
                "point_margin": upike_score - opponent_score
                if upike_score is not None and opponent_score is not None
                else None,
                "source_url": game["url"],
                "source_pdf": game.get("source_pdf")
                or str(
                    (
                        ROOT / "INFO/25-26 Play DATA/Per game" / PDF_BY_GAME[game["game_id"]]
                    ).relative_to(ROOT)
                ),
                "tagged_rows": len(items),
                "linked_rows": sum(row["description"] is not None for row in items),
                "graded_plays": len(eligible),
                "success_rate": pct(sum(row["success"] is True for row in eligible), len(eligible)),
                "tagged_yards": round(sum(gains), 1),
                "yards_per_play": round(statistics.fmean(gains), 2) if gains else None,
                "explosives": sum(row["explosive"] for row in items),
                "negative_plays": sum(row["negative"] for row in items),
                "turnover_events": sum(row["turnover_event"] for row in items),
                "third_down": {
                    "made": sum(row["down"] == 3 and row["conversion"] for row in items),
                    "attempts": sum(
                        row["down"] == 3 and row["success"] is not None for row in items
                    ),
                },
                "fourth_down": {
                    "made": sum(row["down"] == 4 and row["conversion"] for row in items),
                    "attempts": sum(
                        row["down"] == 4 and row["success"] is not None for row in items
                    ),
                },
                "official_team_stats": {
                    key: official_log.get(key)
                    for key in (
                        "yds",
                        "pass",
                        "c_a",
                        "comp_pct",
                        "rush",
                        "rush_att",
                        "yards_per_rush",
                        "int",
                        "fum",
                        "sacks",
                        "penalty_yards",
                        "possession",
                    )
                },
            }
        )

    player_rows = []
    for player in player_names:
        items = [row for row in snaps if player in row["players"]]
        supplied_games = gamebook_player_stats.get(player, {})
        board_stats = official_player_stats(board, player)
        if not items and not board_stats and not supplied_games:
            continue
        passing = [row for row in items if row["passer"] == player]
        rushing = [row for row in items if row["rusher"] == player]
        targets = [row for row in items if row["target"] == player]
        pass_attempts = sum(
            row["result"]
            in {
                "Complete",
                "Complete, TD",
                "Complete, Fumble",
                "Incomplete",
                "Interception",
                "Interception, Def TD",
            }
            for row in passing
        )
        completions = sum(str(row["result"]).startswith("Complete") for row in passing)
        passing_yards = round(
            sum(row["gain"] or 0 for row in passing if str(row["result"]).startswith("Complete"))
        )
        passing_touchdowns = sum(row["passer"] == player and row["touchdown"] for row in passing)
        interceptions = sum(str(row["result"]).startswith("Interception") for row in passing)
        rush_attempts = len([row for row in rushing if row["result"] not in {"Penalty", "None"}])
        rushing_yards = round(sum(row["gain"] or 0 for row in rushing))
        rushing_touchdowns = sum(row["rusher"] == player and row["touchdown"] for row in rushing)
        receptions = sum(str(row["result"]).startswith("Complete") for row in targets)
        receiving_yards = round(
            sum(row["gain"] or 0 for row in targets if str(row["result"]).startswith("Complete"))
        )
        receiving_touchdowns = sum(row["target"] == player and row["touchdown"] for row in targets)
        by_game = [
            {
                "game_id": game["game_id"],
                "date": game["date"],
                "opponent": game["opponent"],
                "plays": len(game_items),
                "passing_yards": round(
                    sum(
                        row["gain"] or 0
                        for row in game_items
                        if row["passer"] == player and str(row["result"]).startswith("Complete")
                    )
                ),
                "rushing_yards": round(
                    sum(row["gain"] or 0 for row in game_items if row["rusher"] == player)
                ),
                "receiving_yards": round(
                    sum(
                        row["gain"] or 0
                        for row in game_items
                        if row["target"] == player and str(row["result"]).startswith("Complete")
                    )
                ),
                "touchdowns": sum(
                    row["touchdown"] and player in {row["passer"], row["rusher"], row["target"]}
                    for row in game_items
                ),
            }
            for game in gamebooks
            if (game_items := [row for row in items if row["game_id"] == game["game_id"]])
        ]
        games = len({row["game_id"] for row in items})
        official_stats = board_stats
        if supplied_games:
            pass_attempts = supplied_total(supplied_games, "Passing", "attempts")
            completions = supplied_total(supplied_games, "Passing", "completions")
            passing_yards = supplied_total(supplied_games, "Passing", "yards")
            passing_touchdowns = supplied_total(supplied_games, "Passing", "touchdowns")
            interceptions = supplied_total(supplied_games, "Passing", "interceptions")
            rush_attempts = supplied_total(supplied_games, "Rushing", "attempts")
            rushing_yards = supplied_total(supplied_games, "Rushing", "yards")
            rushing_touchdowns = supplied_total(supplied_games, "Rushing", "touchdowns")
            receptions = supplied_total(supplied_games, "Receiving", "receptions")
            receiving_yards = supplied_total(supplied_games, "Receiving", "yards")
            receiving_touchdowns = supplied_total(supplied_games, "Receiving", "touchdowns")
            games = len(supplied_games)
            official_stats = {
                "Passing": {
                    "CMP": str(completions),
                    "ATT": str(pass_attempts),
                    "YDS": str(passing_yards),
                    "TD": str(passing_touchdowns),
                    "INT": str(interceptions),
                },
                "Rushing": {
                    "ATT": str(rush_attempts),
                    "YDS": str(rushing_yards),
                    "TD": str(rushing_touchdowns),
                },
                "Receiving": {
                    "REC": str(receptions),
                    "YDS": str(receiving_yards),
                    "TD": str(receiving_touchdowns),
                },
            }
            by_game = []
            for game in gamebooks:
                supplied = supplied_games.get(game["game_id"])
                if not supplied:
                    continue
                categories = supplied["categories"]
                by_game.append(
                    {
                        "game_id": game["game_id"],
                        "date": game["date"],
                        "opponent": game["opponent"],
                        "plays": sum(row["game_id"] == game["game_id"] for row in items),
                        "passing_yards": categories.get("Passing", {}).get("yards", 0),
                        "rushing_yards": categories.get("Rushing", {}).get("yards", 0),
                        "receiving_yards": categories.get("Receiving", {}).get("yards", 0),
                        "touchdowns": sum(
                            categories.get(category, {}).get("touchdowns", 0)
                            for category in ("Passing", "Rushing", "Receiving")
                        ),
                    }
                )
        player_rows.append(
            {
                "player": player,
                "games": games,
                "plays": len(items),
                "pass_attempts": pass_attempts,
                "completions": completions,
                "passing_yards": passing_yards,
                "passing_touchdowns": passing_touchdowns,
                "interceptions": interceptions,
                "rush_attempts": rush_attempts,
                "rushing_yards": rushing_yards,
                "rushing_touchdowns": rushing_touchdowns,
                "targets": len(targets),
                "receptions": receptions,
                "receiving_yards": receiving_yards,
                "receiving_touchdowns": receiving_touchdowns,
                "explosives": sum(row["explosive"] for row in items),
                "successful_plays": sum(row["success"] is True for row in items),
                "official_season_stats": official_stats,
                "game_ids": [item["game_id"] for item in by_game],
                "by_game": by_game,
            }
        )
    player_rows.sort(key=lambda item: (-item["plays"], item["player"]))

    graded = [row for row in snaps if row["success"] is not None]
    linked = [row for row in snaps if row["description"]]
    calls = aggregate(snaps, "off_play")
    formations = aggregate(snaps, "formation")
    situations = {
        "down": aggregate(snaps, "down"),
        "distance": aggregate(snaps, "distance_bucket"),
        "field_zone": aggregate(snaps, "field_zone"),
        "play_type": aggregate(snaps, "play_type"),
        "motion": aggregate(
            [
                {**row, "motion_state": "Motion" if row.get("motion") else "No motion tag"}
                for row in snaps
            ],
            "motion_state",
        ),
        "shift": aggregate(
            [
                {**row, "shift_state": "Shift" if row.get("shift") else "No shift tag"}
                for row in snaps
            ],
            "shift_state",
        ),
    }
    qualified_calls = [
        row for row in calls if row["graded_plays"] >= 8 and row["success_rate"] is not None
    ]
    qualified_formations = [
        row for row in formations if row["graded_plays"] >= 12 and row["success_rate"] is not None
    ]
    top_calls = sorted(
        qualified_calls,
        key=lambda item: (-(item["success_rate"] or 0), -(item["yards_per_play"] or 0)),
    )[:8]
    low_calls = sorted(
        qualified_calls, key=lambda item: ((item["success_rate"] or 0), item["yards_per_play"] or 0)
    )[:8]
    top_formations = sorted(
        qualified_formations,
        key=lambda item: (-(item["success_rate"] or 0), -(item["yards_per_play"] or 0)),
    )[:6]
    losses = sorted(
        (game for game in game_rows if (game["point_margin"] or 0) < 0),
        key=lambda item: item["point_margin"],
    )
    recommendations = []
    if top_calls:
        best = top_calls[0]
        recommendations.append(
            {
                "type": "strength",
                "title": f"Protect {best['label']}",
                "evidence": (
                    f"{best['success_rate']}% success on {best['graded_plays']} graded "
                    f"snaps; {best['yards_per_play']} yards per play."
                ),
                "filter": {"off_play": best["label"]},
            }
        )
    if low_calls:
        lowest = low_calls[0]
        recommendations.append(
            {
                "type": "review",
                "title": f"Audit {lowest['label']}",
                "evidence": (
                    f"{lowest['success_rate']}% success on {lowest['graded_plays']} graded "
                    f"snaps with {lowest['negative_plays']} negative plays."
                ),
                "filter": {"off_play": lowest["label"]},
            }
        )
    if top_formations:
        best = top_formations[0]
        recommendations.append(
            {
                "type": "strength",
                "title": f"Build from {best['label']}",
                "evidence": (
                    f"Best qualified formation by success rate: {best['success_rate']}% "
                    f"across {best['graded_plays']} graded snaps."
                ),
                "filter": {"formation": best["label"]},
            }
        )
    if losses:
        worst = losses[0]
        recommendations.append(
            {
                "type": "game",
                "title": f"Largest scoreboard loss: {worst['opponent']}",
                "evidence": (
                    f"Actual margin {worst['point_margin']} with {worst['negative_plays']} "
                    f"tagged negative plays and {worst['turnover_events']} tagged turnover events."
                ),
                "filter": {"game_id": worst["game_id"]},
            }
        )

    output = {
        "season": SEASON,
        "label": LABEL,
        "generated_from": {
            "coaching_workbook": str(WORKBOOK_PATH.relative_to(ROOT)),
            "official_gamebooks": f"{len(gamebooks)} official gamebooks supplied for {LABEL}",
            "official_play_by_play": str(GAMEBOOK_PATH.relative_to(ROOT)),
        },
        "definitions": {
            "success": (
                "1st down: at least 50% of distance; 2nd: at least 70%; 3rd/4th: "
                "conversion. Touchdowns count as successful. Penalties, timeouts and "
                "ungraded rows are excluded."
            ),
            "explosive": "Run of 10+ tagged yards or completed pass of 15+ tagged yards.",
            "negative": "Negative tagged gain, sack, interception or fumble event.",
            "turnover_event": (
                "Interception or fumble-tagged event. Fumble lost is not inferred when "
                "the source does not establish possession."
            ),
            "analysis": (
                "Descriptive association from supplied tags and official gamebooks; not "
                "causal certainty. Qualified calls require 8 graded snaps and formations "
                "require 12."
            ),
        },
        "coverage": {
            "tagged_rows": len(snaps),
            "linked_official_rows": len(linked),
            "linked_pct": pct(len(linked), len(snaps)),
            "high_confidence_rows": sum(row["match_confidence"] == "high" for row in snaps),
            "medium_confidence_rows": sum(row["match_confidence"] == "medium" for row in snaps),
            "low_confidence_rows": sum(row["match_confidence"] == "low" for row in snaps),
            "unmatched_rows": sum(row["match_confidence"] == "unmatched" for row in snaps),
            "official_offense_events": len(official),
            "games": len(game_rows),
            "players_with_attribution": sum(item["plays"] > 0 for item in player_rows),
            "roster_players_with_official_stats": len(player_rows),
        },
        "overview": {
            "graded_plays": len(graded),
            "successes": sum(row["success"] is True for row in graded),
            "success_rate": pct(sum(row["success"] is True for row in graded), len(graded)),
            "total_tagged_yards": round(sum(row["gain"] or 0 for row in snaps), 1),
            "yards_per_graded_play": round(
                statistics.fmean(row["gain"] for row in graded if row["gain"] is not None), 2
            ),
            "explosives": sum(row["explosive"] for row in snaps),
            "negative_plays": sum(row["negative"] for row in snaps),
            "touchdowns": sum(row["touchdown"] for row in snaps),
            "turnover_events": sum(row["turnover_event"] for row in snaps),
        },
        "recommendations": recommendations,
        "top_calls": top_calls,
        "review_calls": low_calls,
        "top_formations": top_formations,
        "play_calls": calls,
        "formations": formations,
        "situations": situations,
        "games": game_rows,
        "players": player_rows,
        "snaps": snaps,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(OUTPUT_PATH),
                "coverage": output["coverage"],
                "overview": output["overview"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
