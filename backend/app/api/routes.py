import json
import uuid
from pathlib import Path
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import (
    ConferenceStanding,
    Game,
    Gamebook,
    LeaderEntry,
    Player,
    Practice,
    PracticePlay,
    Season,
)
from app.schemas import (
    ConferenceStandingPage,
    GamebookPage,
    GamebookRead,
    GamePage,
    GameRead,
    HealthRead,
    LeaderEntryPage,
    PageMeta,
    PlayerPage,
    PlayerRead,
    PracticeCreate,
    PracticeDashboardRead,
    PracticePlayCreate,
    PracticePlayRead,
    PracticePlayUpdate,
    PracticeRead,
    PracticeUpdate,
    SeasonPage,
)
from app.services.practice_analytics import practice_dashboard, practice_play_tags, practice_to_dict

router = APIRouter(prefix="/api")
DBSession = Annotated[Session, Depends(get_db)]
STAT_BOARD_PATH = Path(__file__).resolve().parents[2] / "data/compiled/upike_stat_board.json"
DATA_ROOT = Path(__file__).resolve().parents[2]
PLAY_ANALYTICS_PATHS = {
    season: DATA_ROOT / f"data/compiled/upike_play_analytics_{season}.json"
    for season in ("2024", "2025")
}


@router.get("/health", response_model=HealthRead, tags=["system"])
def health() -> HealthRead:
    return HealthRead(status="ok", service="upike-football-intelligence", version="0.1.0")


@router.get("/stat-board", tags=["intelligence"])
def stat_board() -> dict[str, object]:
    """Return the compiled AAC/NAIA stat board from the supplied source documents."""
    return cast(dict[str, object], json.loads(STAT_BOARD_PATH.read_text()))


@router.get("/play-analytics", tags=["intelligence"])
def play_analytics(season: str = Query("2025", pattern="^(2024|2025)$")) -> dict[str, object]:
    """Return source-linked play, game, situation and player analytics by season."""
    return cast(dict[str, object], json.loads(PLAY_ANALYTICS_PATHS[season].read_text()))


@router.get("/seasons", response_model=SeasonPage, tags=["seasons"])
def list_seasons(
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> SeasonPage:
    total = db.scalar(select(func.count()).select_from(Season)) or 0
    seasons = list(
        db.scalars(
            select(Season)
            .order_by(Season.year.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return SeasonPage(data=seasons, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/games", response_model=GamePage, tags=["games"])
def list_games(
    db: DBSession,
    season: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> GamePage:
    statement = select(Game).join(Season)
    count_statement = select(func.count()).select_from(Game).join(Season)
    if season is not None:
        statement = statement.where(Season.year == season)
        count_statement = count_statement.where(Season.year == season)
    total = db.scalar(count_statement) or 0
    games = list(
        db.scalars(
            statement.order_by(Game.played_at.desc().nullslast())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return GamePage(data=games, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/games/{game_id}", response_model=GameRead, tags=["games"])
def get_game(game_id: uuid.UUID, db: DBSession) -> Game:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail={"code": "game_not_found"})
    return game


@router.get("/players", response_model=PlayerPage, tags=["players"])
def list_players(
    db: DBSession,
    search: str | None = Query(None, min_length=2, max_length=80),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> PlayerPage:
    statement = select(Player)
    count_statement = select(func.count()).select_from(Player)
    if search:
        pattern = f"%{search.casefold()}%"
        statement = statement.where(Player.normalized_name.like(pattern))
        count_statement = count_statement.where(Player.normalized_name.like(pattern))
    total = db.scalar(count_statement) or 0
    players = list(
        db.scalars(
            statement.order_by(Player.display_name).offset((page - 1) * page_size).limit(page_size)
        )
    )
    return PlayerPage(data=players, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/players/{player_id}", response_model=PlayerRead, tags=["players"])
def get_player(player_id: uuid.UUID, db: DBSession) -> Player:
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail={"code": "player_not_found"})
    return player


def _practice_or_404(practice_id: uuid.UUID, db: Session) -> Practice:
    practice = db.scalar(
        select(Practice).where(Practice.id == practice_id).options(selectinload(Practice.plays))
    )
    if practice is None:
        raise HTTPException(status_code=404, detail={"code": "practice_not_found"})
    return practice


@router.get("/practice-dashboard", response_model=PracticeDashboardRead, tags=["practices"])
def get_practice_dashboard(
    db: DBSession,
    season: int = Query(2026, ge=2026, le=2100),
) -> dict[str, object]:
    practices = list(
        db.scalars(
            select(Practice)
            .where(Practice.season_year == season)
            .options(selectinload(Practice.plays))
            .order_by(Practice.created_at.desc())
        )
    )
    return cast(dict[str, object], practice_dashboard(practices, season))


@router.post("/practices", response_model=PracticeRead, status_code=201, tags=["practices"])
def create_practice(payload: PracticeCreate, db: DBSession) -> dict[str, object]:
    practice = Practice(**payload.model_dump())
    db.add(practice)
    db.commit()
    return cast(dict[str, object], practice_to_dict(_practice_or_404(practice.id, db)))


@router.patch("/practices/{practice_id}", response_model=PracticeRead, tags=["practices"])
def update_practice(
    practice_id: uuid.UUID,
    payload: PracticeUpdate,
    db: DBSession,
) -> dict[str, object]:
    practice = _practice_or_404(practice_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(practice, field, value)
    db.commit()
    return cast(dict[str, object], practice_to_dict(_practice_or_404(practice.id, db)))


@router.delete("/practices/{practice_id}", status_code=204, tags=["practices"])
def delete_practice(practice_id: uuid.UUID, db: DBSession) -> None:
    practice = _practice_or_404(practice_id, db)
    db.delete(practice)
    db.commit()


@router.post(
    "/practices/{practice_id}/plays",
    response_model=PracticePlayRead,
    status_code=201,
    tags=["practices"],
)
def create_practice_play(
    practice_id: uuid.UUID,
    payload: PracticePlayCreate,
    db: DBSession,
) -> dict[str, object]:
    _practice_or_404(practice_id, db)
    play = PracticePlay(practice_id=practice_id, **payload.model_dump())
    db.add(play)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "practice_play_sequence_exists"},
        ) from exc
    db.refresh(play)
    return {
        "id": play.id,
        "sequence": play.sequence,
        "quarterback_number": play.quarterback_number,
        "quarterback_name": play.quarterback_name,
        "intended_receiver": play.intended_receiver,
        "result": play.result,
        "notes": play.notes,
        "tags": practice_play_tags(play),
    }


@router.patch("/practice-plays/{play_id}", response_model=PracticePlayRead, tags=["practices"])
def update_practice_play(
    play_id: uuid.UUID,
    payload: PracticePlayUpdate,
    db: DBSession,
) -> dict[str, object]:
    play = db.get(PracticePlay, play_id)
    if play is None:
        raise HTTPException(status_code=404, detail={"code": "practice_play_not_found"})
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(play, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "practice_play_sequence_exists"},
        ) from exc
    db.refresh(play)
    return {
        "id": play.id,
        "sequence": play.sequence,
        "quarterback_number": play.quarterback_number,
        "quarterback_name": play.quarterback_name,
        "intended_receiver": play.intended_receiver,
        "result": play.result,
        "notes": play.notes,
        "tags": practice_play_tags(play),
    }


@router.delete("/practice-plays/{play_id}", status_code=204, tags=["practices"])
def delete_practice_play(play_id: uuid.UUID, db: DBSession) -> None:
    play = db.get(PracticePlay, play_id)
    if play is None:
        raise HTTPException(status_code=404, detail={"code": "practice_play_not_found"})
    db.delete(play)
    db.commit()


@router.get("/standings", response_model=ConferenceStandingPage, tags=["intelligence"])
def list_standings(
    db: DBSession,
    season: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> ConferenceStandingPage:
    statement = select(ConferenceStanding).join(Season)
    count_statement = select(func.count()).select_from(ConferenceStanding).join(Season)
    if season is not None:
        statement = statement.where(Season.year == season)
        count_statement = count_statement.where(Season.year == season)
    total = db.scalar(count_statement) or 0
    rows = list(
        db.scalars(
            statement.order_by(
                ConferenceStanding.conference_wins.desc(),
                ConferenceStanding.conference_losses,
                ConferenceStanding.team_name,
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return ConferenceStandingPage(
        data=rows, meta=PageMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/leaders", response_model=LeaderEntryPage, tags=["intelligence"])
def list_leaders(
    db: DBSession,
    season: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
) -> LeaderEntryPage:
    statement = select(LeaderEntry).join(Season)
    count_statement = select(func.count()).select_from(LeaderEntry).join(Season)
    if season is not None:
        statement = statement.where(Season.year == season)
        count_statement = count_statement.where(Season.year == season)
    total = db.scalar(count_statement) or 0
    rows = list(
        db.scalars(
            statement.order_by(
                LeaderEntry.category, LeaderEntry.metric, LeaderEntry.value_numeric.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return LeaderEntryPage(data=rows, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/gamebooks", response_model=GamebookPage, tags=["intelligence"])
def list_gamebooks(
    db: DBSession,
    season: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
) -> GamebookPage:
    statement = select(Gamebook).join(Season)
    count_statement = select(func.count()).select_from(Gamebook).join(Season)
    if season is not None:
        statement = statement.where(Season.year == season)
        count_statement = count_statement.where(Season.year == season)
    total = db.scalar(count_statement) or 0
    books = list(
        db.scalars(
            statement.order_by(Gamebook.played_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    data = [
        GamebookRead(
            id=book.id,
            season_id=book.season_id,
            played_at=book.played_at,
            opponent=book.opponent,
            upike_score=book.upike_score,
            opponent_score=book.opponent_score,
            location=book.location,
            stadium=book.stadium,
            attendance=book.attendance,
            team_stats=book.team_stats,
            drive_count=len(book.drives),
            source=book.source,
            source_url=book.source_url,
        )
        for book in books
    ]
    return GamebookPage(data=data, meta=PageMeta(page=page, page_size=page_size, total=total))
