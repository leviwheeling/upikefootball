SHELL := /bin/sh
SEASON ?= 2025
SOURCE ?= upike

.PHONY: setup dev down test lint seed migrate scrape-discover scrape-season scrape-all scrape-update calculate-metrics validate-data backup

setup:
	test -f .env || cp .env.example .env
	docker compose build
	docker compose run --rm backend alembic upgrade head

dev:
	docker compose up --build

down:
	docker compose down

test:
	docker compose run --rm backend pytest
	docker compose run --rm frontend npm test -- --run

lint:
	docker compose run --rm backend ruff check .
	docker compose run --rm backend mypy app
	docker compose run --rm frontend npm run lint

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python -m app.cli seed-fixture

scrape-discover:
	docker compose run --rm backend python -m app.cli discover-sources

scrape-season:
	docker compose run --rm backend python -m app.cli scrape --source $(SOURCE) --season $(SEASON)

scrape-all:
	docker compose run --rm backend python -m app.cli scrape-all

scrape-update:
	docker compose run --rm backend python -m app.cli scrape-all --incremental

calculate-metrics:
	docker compose run --rm backend python -m app.cli calculate

validate-data:
	docker compose run --rm backend python -m app.cli validate

backup:
	mkdir -p backups
	docker compose exec -T postgres pg_dump -U $${POSTGRES_USER:-upike} $${POSTGRES_DB:-upike_intel} | gzip > backups/upike-intel-$$(date +%Y%m%d-%H%M%S).sql.gz
