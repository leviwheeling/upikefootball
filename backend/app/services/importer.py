import re
import unicodedata
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Game, Player, Season, SourceDocument
from app.scraping.types import ParsedSeason


def normalize_player_name(value: str) -> str:
    """Conservative normalization for search; never used alone to merge identities."""
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", ascii_value.casefold())).strip()


def import_parsed_season(
    db: Session,
    parsed: ParsedSeason,
    *,
    source: str,
    source_document_id: uuid.UUID | None,
) -> dict[str, int]:
    if source_document_id is None and all(
        (
            parsed.source_url,
            parsed.retrieved_at,
            parsed.status_code is not None,
            parsed.content_type,
            parsed.source_sha256,
            parsed.storage_path,
        )
    ):
        document = db.scalar(
            select(SourceDocument).where(
                SourceDocument.source == source,
                SourceDocument.url == parsed.source_url,
                SourceDocument.sha256 == parsed.source_sha256,
            )
        )
        if document is None:
            document = SourceDocument(
                source=source,
                url=parsed.source_url,
                retrieved_at=parsed.retrieved_at,
                status_code=parsed.status_code,
                content_type=parsed.content_type,
                sha256=parsed.source_sha256,
                storage_path=parsed.storage_path,
                parser_version=parsed.parser_version,
            )
            db.add(document)
            db.flush()
        source_document_id = document.id

    season = db.scalar(select(Season).where(Season.year == parsed.year))
    inserted_season = season is None
    if season is None:
        season = Season(
            year=parsed.year,
            label=parsed.label,
            data_completeness="partial",
            source_document_id=source_document_id,
        )
        db.add(season)
        db.flush()

    inserted_games = 0
    for game_item in parsed.games:
        existing_game = db.scalar(
            select(Game).where(
                Game.source == source,
                Game.source_game_id == game_item.source_game_id,
            )
        )
        if existing_game is not None:
            continue
        db.add(
            Game(
                season_id=season.id,
                source=source,
                source_game_id=game_item.source_game_id,
                played_at=game_item.played_at,
                opponent=game_item.opponent,
                site=game_item.site,
                result=game_item.result,
                upike_score=game_item.upike_score,
                opponent_score=game_item.opponent_score,
                attendance=game_item.attendance,
                source_url=game_item.source_url,
                source_document_id=source_document_id,
            )
        )
        inserted_games += 1

    inserted_players = 0
    for player_item in parsed.players:
        existing_player = db.scalar(
            select(Player).where(
                Player.source == source,
                Player.source_player_id == player_item.source_player_id,
            )
        )
        if existing_player is not None:
            continue
        db.add(
            Player(
                display_name=player_item.display_name,
                normalized_name=normalize_player_name(player_item.display_name),
                source=source,
                source_player_id=player_item.source_player_id,
                jersey_number=player_item.jersey_number,
                position=player_item.position,
                source_url=player_item.source_url,
                source_document_id=source_document_id,
            )
        )
        inserted_players += 1

    db.commit()
    return {
        "seasons": int(inserted_season),
        "games": inserted_games,
        "players": inserted_players,
    }
