# Deployment and operations

Use managed PostgreSQL and Redis in production, build the two application images, run Alembic before rollout, and persist `RAW_DOCUMENT_ROOT` to durable object storage or a backed-up volume. Terminate TLS at the platform edge and restrict CORS to the deployed frontend origin.

Back up PostgreSQL with `make backup`. Restore into a clean database with `gunzip -c backup.sql.gz | psql ...`, then verify `alembic current` and run `python -m app.cli validate`.

Do not run multiple recurring scrape schedulers without a distributed lock. Treat source markup changes and cross-source conflicts as reviewable incidents, not automatic overwrite events.
