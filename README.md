# UPIKE Football Intelligence

UPIKE Football Intelligence is a source-linked football stat board for the University of Pikeville. The Python FastAPI application serves both the API and the statically exported Next.js dashboard from one process.

No values are fabricated. Source-specific values and raw documents are retained; future reconciliation selects canonical values without deleting disagreements.

## Local development

Run the API:

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

Run the dashboard in a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:3000>. The development dashboard calls the API at <http://localhost:8000>.

## One-service Render deployment

The root `render.yaml` deploys the entire application as one native Python web service. `render-build.sh` installs the Python package, exports the Next.js dashboard, and copies it into FastAPI's static directory. FastAPI then serves the dashboard and `/api` from the same origin.

In Render, create a **Blueprint**, connect this repository, and apply `render.yaml`. No separate frontend service, Redis instance, or database is required for the compiled stat board.

For an existing manually created Python service, use:

- Build Command: `bash render-build.sh`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Useful commands

```bash
make test
make lint
make scrape-discover
make scrape-season SOURCE=upike SEASON=2025
make validate-data
```

The discovery command is intentionally slow. AAC and NAIA publish a 10-second crawl delay in `robots.txt`; the client applies the strictest configured delay, caches responses, backs off on transient failures, and does not attempt to bypass Cloudflare challenges.

## Data

The compiled board includes four schedules, 2024 and 2025 team/game statistics, 2025 player category tables, and source-verified player appearances. Source URLs and supplied reference documents are retained in the repository.

See [Architecture](docs/architecture.md), [Source inventory](docs/source-inventory.md), [database design](docs/database.md), and [scraper guide](docs/scraping.md).
