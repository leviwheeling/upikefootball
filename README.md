# UPIKE Football Intelligence

UPIKE Football Intelligence is a provenance-first historical football data platform for University of Pikeville football. This repository contains the Phase 1 foundation: a real-source discovery workflow, typed source adapters, a fixture-verified SIDEARM parser, an idempotent PostgreSQL importer, documented REST endpoints, a responsive Next.js dashboard, migrations, background-job plumbing, and tests.

No values are fabricated. Source-specific values and raw documents are retained; future reconciliation selects canonical values without deleting disagreements.

## Quick start

Requirements: Docker Desktop and Docker Compose.

```bash
cp .env.example .env
docker compose up --build -d postgres redis
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.cli seed-fixture
docker compose up --build backend frontend worker
```

Open the dashboard at <http://localhost:3000> and API docs at <http://localhost:8000/docs>.

## Useful commands

```bash
make test
make lint
make scrape-discover
make scrape-season SOURCE=upike SEASON=2025
make validate-data
```

The discovery command is intentionally slow. AAC and NAIA publish a 10-second crawl delay in `robots.txt`; the client applies the strictest configured delay, caches responses, backs off on transient failures, and does not attempt to bypass Cloudflare challenges.

## Current phase and limitations

This is the requested initial deliverable, not the completed multi-phase historical database. UPIKE's 2025 cumulative-statistics page is the first verified parser. AAC and NAIA URLs are documented from live discovery, but automated retrieval currently receives a Cloudflare challenge, so those adapters stop and report a blocked source instead of bypassing it. Detailed game books, play-by-play, full reconciliation tooling, and modeling remain subsequent phases.

See [Architecture](docs/architecture.md), [Source inventory](docs/source-inventory.md), [database design](docs/database.md), and [scraper guide](docs/scraping.md).
