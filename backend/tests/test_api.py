from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models import Season


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


def test_local_loopback_origin_is_allowed() -> None:
    response = TestClient(app).get(
        "/api/health", headers={"Origin": "http://127.0.0.1:3000"}
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
