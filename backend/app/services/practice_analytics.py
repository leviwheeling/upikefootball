from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from app.models import Practice, PracticePlay

ATTEMPT_RESULTS = {"COMPLETE", "INCOMPLETE"}


def _has_phrase(note: str, *phrases: str) -> bool:
    return any(re.search(rf"\b{re.escape(phrase)}\b", note) for phrase in phrases)


def practice_play_tags(play: PracticePlay) -> list[str]:
    note = " ".join((play.notes or "").upper().replace("-", " ").split())
    tags: list[str] = []

    if _has_phrase(note, "ON TARGET"):
        tags.append("On target")
    if _has_phrase(
        note, "GOOD READ", "GREAT READ", "FANTASTIC READ", "PROPER READ", "CORRECT READ"
    ):
        tags.append("Positive read")
    if _has_phrase(note, "POOR READ", "BAD READ", "INCORRECT READ"):
        tags.append("Negative read")
    if _has_phrase(
        note, "GOOD TIMING", "GREAT TIMING", "FANTASTIC TIMING", "PROPER TIMING"
    ):
        tags.append("Positive timing")
    if _has_phrase(note, "POOR TIMING"):
        tags.append("Negative timing")
    if _has_phrase(note, "RECEIVER DROP", "RECIEVER DROP", "RECIVER DROP"):
        tags.append("Receiver drop")
    if _has_phrase(note, "CHECKDOWN"):
        tags.append("Checkdown")
    if _has_phrase(note, "OVERTHROW"):
        tags.append("Overthrow")
    if _has_phrase(note, "HIGH BALL", "PLACED A BIT HIGH"):
        tags.append("High ball")
    if _has_phrase(note, "LOW BALL", "LOW"):
        tags.append("Low ball")
    return tags


def summarize_plays(plays: Iterable[PracticePlay]) -> dict[str, int | float | None]:
    rows = list(plays)
    summary: dict[str, int | float | None] = {
        "plays": len(rows),
        "attempts": 0,
        "completions": 0,
        "incompletions": 0,
        "completion_pct": None,
        "on_target": 0,
        "positive_reads": 0,
        "negative_reads": 0,
        "positive_timing": 0,
        "negative_timing": 0,
        "receiver_drops": 0,
        "checkdowns": 0,
    }
    tag_fields = {
        "On target": "on_target",
        "Positive read": "positive_reads",
        "Negative read": "negative_reads",
        "Positive timing": "positive_timing",
        "Negative timing": "negative_timing",
        "Receiver drop": "receiver_drops",
        "Checkdown": "checkdowns",
    }
    for play in rows:
        result = play.result.upper()
        if result in ATTEMPT_RESULTS:
            summary["attempts"] = int(summary["attempts"] or 0) + 1
        if result == "COMPLETE":
            summary["completions"] = int(summary["completions"] or 0) + 1
        elif result == "INCOMPLETE":
            summary["incompletions"] = int(summary["incompletions"] or 0) + 1
        for tag in practice_play_tags(play):
            field = tag_fields.get(tag)
            if field:
                summary[field] = int(summary[field] or 0) + 1
    attempts = int(summary["attempts"] or 0)
    if attempts:
        summary["completion_pct"] = round(int(summary["completions"] or 0) / attempts * 100, 1)
    return summary


def practice_to_dict(practice: Practice) -> dict[str, Any]:
    plays = sorted(practice.plays, key=lambda row: row.sequence)
    return {
        "id": practice.id,
        "season_year": practice.season_year,
        "title": practice.title,
        "practice_date": practice.practice_date,
        "practice_type": practice.practice_type,
        "notes": practice.notes,
        "source_label": practice.source_label,
        "created_at": practice.created_at,
        "updated_at": practice.updated_at,
        "summary": summarize_plays(plays),
        "plays": [
            {
                "id": play.id,
                "sequence": play.sequence,
                "quarterback_number": play.quarterback_number,
                "quarterback_name": play.quarterback_name,
                "intended_receiver": play.intended_receiver,
                "result": play.result,
                "notes": play.notes,
                "tags": practice_play_tags(play),
            }
            for play in plays
        ],
    }


def practice_dashboard(practices: list[Practice], season_year: int) -> dict[str, Any]:
    all_plays = [play for practice in practices for play in practice.plays]
    grouped: dict[str, list[tuple[Practice, PracticePlay]]] = defaultdict(list)
    for practice in practices:
        for play in practice.plays:
            name = (play.quarterback_name or "").strip()
            number = (play.quarterback_number or "").strip()
            key = f"name:{name.casefold()}" if name else f"number:{number or 'unassigned'}"
            grouped[key].append((practice, play))

    quarterbacks: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        plays = [play for _, play in rows]
        first = plays[0]
        name = (first.quarterback_name or "").strip()
        qb_number = (first.quarterback_number or "").strip() or None
        quarterbacks.append(
            {
                "key": key,
                "display_name": name or (f"QB #{qb_number}" if qb_number else "Unassigned QB"),
                "quarterback_number": qb_number,
                "practices": len({practice.id for practice, _ in rows}),
                **summarize_plays(plays),
            }
        )
    quarterbacks.sort(key=lambda row: (-int(row["attempts"] or 0), str(row["display_name"])))
    return {
        "season_year": season_year,
        "overview": summarize_plays(all_plays),
        "practices": [practice_to_dict(practice) for practice in practices],
        "quarterbacks": quarterbacks,
    }
