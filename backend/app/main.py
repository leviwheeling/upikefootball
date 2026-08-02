from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.logging import configure_logging

settings = get_settings()
configure_logging()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Provenance-first UPIKE football history API. Calculated, inferred, and unavailable "
        "values are labeled explicitly."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs", "health": "/api/health"}
