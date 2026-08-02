from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models import ConferenceStanding, Season, SourceDocument


def test_seasons_endpoint_is_paginated(db: Session) -> None:
    db.add(Season(year=2025, label="2025", data_completeness="partial"))
    db.commit()

    def override_db():  # type: ignore[no-untyped-def]
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        response = TestClient(app).get("/api/seasons?page=1&page_size=10")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["meta"] == {"page": 1, "page_size": 10, "total": 1}
    assert response.json()["data"][0]["year"] == 2025


def test_page_size_is_validated() -> None:
    response = TestClient(app).get("/api/games?page_size=1000")
    assert response.status_code == 422


def test_stat_board_contains_all_compiled_seasons_and_player_tables() -> None:
    response = TestClient(app).get("/api/stat-board")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload["seasons"]) == {"2023", "2024", "2025", "2026"}
    assert len(payload["seasons"]["2025"]["team_stats"]) == 52
    assert len(payload["seasons"]["2025"]["game_log"]) == 10
    assert (
        sum(len(category["rows"]) for category in payload["seasons"]["2025"]["players"].values())
        == 103
    )
    assert len(payload["seasons"]["2025"]["appearances"]) == 54
    assert len(payload["seasons"]["2025"]["appearances"]["Xavier Malone"]) == 10
    assert payload["seasons"]["2025"]["game_log"][0]["game_id"] == "20250830_dizi"
    assert payload["seasons"]["2025"]["game_log"][0]["source_url"].endswith(
        "20250830_dizi.xml"
    )
    assert len(payload["player_profiles"]) == 54
    assert sum(len(profile["seasons"]) > 1 for profile in payload["player_profiles"].values()) == 29
    assert sum(len(profile["seasons"]) for profile in payload["player_profiles"].values()) == 94
    assert payload["player_profiles"]["Xavier Malone"]["career"]["passing_yards"] == 5476
    assert [
        season["label"] for season in payload["player_profiles"]["Xavier Malone"]["seasons"]
    ] == ["2022-23", "2023-24", "2025-26"]
    assert payload["player_profiles"]["Grant Scott"]["career"]["receiving_yards"] == 823
    assert payload["player_profiles"]["Xavier Malone"]["seasons"][0]["source_url"] == (
        "https://upikebears.com/sports/football/stats/2022"
    )


def test_local_loopback_origin_is_allowed() -> None:
    response = TestClient(app).get("/api/health", headers={"Origin": "http://127.0.0.1:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_standings_endpoint_returns_source_linked_rows(db: Session) -> None:
    season = Season(year=2025, label="2025", data_completeness="partial")
    db.add(season)
    db.flush()
    document = SourceDocument(
        source="naia",
        url="https://naiastats.prestosports.com/standings",
        retrieved_at=datetime.now(UTC),
        status_code=200,
        content_type="application/json",
        sha256="a" * 64,
        storage_path="fixture.json",
        parser_version="test",
    )
    db.add(document)
    db.flush()
    db.add(
        ConferenceStanding(
            season_id=season.id,
            source="naia",
            conference="AAC",
            team_name="Pikeville (KY)",
            conference_wins=4,
            conference_losses=2,
            overall_wins=4,
            overall_losses=6,
            streak="Lost 1",
            source_url=document.url,
            source_document_id=document.id,
        )
    )
    db.commit()

    def override_db():  # type: ignore[no-untyped-def]
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        response = TestClient(app).get("/api/standings?season=2025")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"][0]["team_name"] == "Pikeville (KY)"
    assert response.json()["data"][0]["source_url"] == document.url
