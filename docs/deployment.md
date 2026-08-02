# Deployment and operations

## Render: one web service

The repository root contains a Render Blueprint and a multi-stage Dockerfile. The frontend is compiled to static files during the image build, then copied into the final Python image. FastAPI serves both the site and `/api` on Render's `PORT`.

Create a Render Blueprint from the repository and apply `render.yaml`. The compiled stat board does not require PostgreSQL or Redis. Its SQLite setting only supports the secondary database-backed endpoints and is ephemeral on the free service.

The health check is `/api/health`; API documentation remains available at `/docs`.

## Extended ingestion infrastructure

Managed PostgreSQL and Redis are only needed if the background importer and Celery worker are enabled later. In that configuration, run Alembic before rollout and persist `RAW_DOCUMENT_ROOT` to durable object storage or a backed-up volume.

Back up PostgreSQL with `make backup`. Restore into a clean database with `gunzip -c backup.sql.gz | psql ...`, then verify `alembic current` and run `python -m app.cli validate`.

Do not run multiple recurring scrape schedulers without a distributed lock. Treat source markup changes and cross-source conflicts as reviewable incidents, not automatic overwrite events.
