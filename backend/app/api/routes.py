import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Game, Player, Season
from app.schemas import (
    GamePage,
    GameRead,
    HealthRead,
    PageMeta,
    PlayerPage,
    PlayerRead,
    SeasonPage,
)

router = APIRouter(prefix="/api")
DBSession = Annotated[Session, Depends(get_db)]


@router.get("/health", response_model=HealthRead, tags=["system"])
def health() -> HealthRead:
    return HealthRead(status="ok", service="upike-football-intelligence", version="0.1.0")


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
            statement.order_by(Player.display_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return PlayerPage(data=players, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/players/{player_id}", response_model=PlayerRead, tags=["players"])
def get_player(player_id: uuid.UUID, db: DBSession) -> Player:
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail={"code": "player_not_found"})
    return player
