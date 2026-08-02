import hashlib
import re
import unicodedata
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ConferenceStanding,
    Game,
    Gamebook,
    GameDrive,
    LeaderEntry,
    Player,
    Season,
    SourceDocument,
)
from app.scraping.parsers.presto_browser_v1 import PARSER_VERSION as PRESTO_PARSER_VERSION
from app.scraping.types import ParsedPrestoIntel, ParsedSeason


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


def import_presto_intel(
    db: Session, parsed: ParsedPrestoIntel, *, content: bytes, storage_path: str
) -> dict[str, int]:
    """Idempotently import browser-observed PrestoSports records with source provenance."""
    digest = hashlib.sha256(content).hexdigest()
    documents: dict[str, SourceDocument] = {}
    for name, url in (
        ("standings", parsed.standings_url),
        ("leaders", parsed.leaders_url),
        ("gamebook", parsed.gamebook_url),
    ):
        document = db.scalar(
            select(SourceDocument).where(
                SourceDocument.source == "naia",
                SourceDocument.url == url,
                SourceDocument.sha256 == digest,
            )
        )
        if document is None:
            document = SourceDocument(
                source="naia",
                url=url,
                retrieved_at=parsed.retrieved_at,
                status_code=200,
                content_type="application/json; normalized-browser-capture",
                sha256=digest,
                storage_path=storage_path,
                parser_version=PRESTO_PARSER_VERSION,
            )
            db.add(document)
            db.flush()
        documents[name] = document

    season = db.scalar(select(Season).where(Season.year == parsed.year))
    if season is None:
        season = Season(
            year=parsed.year,
            label=parsed.label,
            data_completeness="partial",
            source_document_id=documents["standings"].id,
        )
        db.add(season)
        db.flush()

    inserted_standings = 0
    for standing_item in parsed.standings:
        existing_standing = db.scalar(
            select(ConferenceStanding).where(
                ConferenceStanding.source == "naia",
                ConferenceStanding.season_id == season.id,
                ConferenceStanding.conference == standing_item.conference,
                ConferenceStanding.team_name == standing_item.team_name,
            )
        )
        if existing_standing is None:
            db.add(
                ConferenceStanding(
                    season_id=season.id,
                    source="naia",
                    conference=standing_item.conference,
                    team_name=standing_item.team_name,
                    conference_wins=standing_item.conference_wins,
                    conference_losses=standing_item.conference_losses,
                    overall_wins=standing_item.overall_wins,
                    overall_losses=standing_item.overall_losses,
                    streak=standing_item.streak,
                    source_url=parsed.standings_url,
                    source_document_id=documents["standings"].id,
                )
            )
            inserted_standings += 1

    inserted_leaders = 0
    for leader_item in parsed.leaders:
        existing_leader = db.scalar(
            select(LeaderEntry).where(
                LeaderEntry.source == "naia",
                LeaderEntry.season_id == season.id,
                LeaderEntry.category == leader_item.category,
                LeaderEntry.metric == leader_item.metric,
                LeaderEntry.player_name == leader_item.player_name,
            )
        )
        if existing_leader is None:
            db.add(
                LeaderEntry(
                    season_id=season.id,
                    source="naia",
                    category=leader_item.category,
                    metric=leader_item.metric,
                    player_name=leader_item.player_name,
                    games_played=leader_item.games_played,
                    value_text=leader_item.value_text,
                    value_numeric=leader_item.value_numeric,
                    source_url=parsed.leaders_url,
                    source_document_id=documents["leaders"].id,
                )
            )
            inserted_leaders += 1

    inserted_gamebooks = 0
    inserted_drives = 0
    gamebook = db.scalar(
        select(Gamebook).where(
            Gamebook.source == "naia",
            Gamebook.source_game_id == parsed.gamebook.source_game_id,
        )
    )
    if gamebook is None:
        gamebook = Gamebook(
            season_id=season.id,
            source="naia",
            source_game_id=parsed.gamebook.source_game_id,
            played_at=parsed.gamebook.played_at,
            opponent=parsed.gamebook.opponent,
            upike_score=parsed.gamebook.upike_score,
            opponent_score=parsed.gamebook.opponent_score,
            location=parsed.gamebook.location,
            stadium=parsed.gamebook.stadium,
            attendance=parsed.gamebook.attendance,
            team_stats=parsed.gamebook.team_stats,
            source_url=parsed.gamebook_url,
            source_document_id=documents["gamebook"].id,
        )
        db.add(gamebook)
        db.flush()
        inserted_gamebooks = 1
        for drive in parsed.gamebook.drives:
            db.add(
                GameDrive(
                    gamebook_id=gamebook.id,
                    sequence=drive.sequence,
                    team=drive.team,
                    quarter=drive.quarter,
                    start_clock=drive.start_clock,
                    possession_duration=drive.possession_duration,
                    start_spot=drive.start_spot,
                    plays=drive.plays,
                    yards=drive.yards,
                    result=drive.result,
                )
            )
            inserted_drives += 1

    db.commit()
    return {
        "standings": inserted_standings,
        "leader_entries": inserted_leaders,
        "gamebooks": inserted_gamebooks,
        "drives": inserted_drives,
    }
