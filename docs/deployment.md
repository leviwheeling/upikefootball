# Deployment and operations

## Render: one web service

The repository root contains a native-Python Render Blueprint. Its build script installs the Python package, compiles the frontend to static files, and copies those files into the FastAPI application. FastAPI serves both the site and `/api` on Render's `PORT`.

Create a Render Blueprint from the repository and apply `render.yaml`. Set the secret environment variable named `password` in Render to a long, unique value. `PASSWORD` and `SITE_PASSWORD` are also accepted for manually configured services. Never commit the password to the repository.

The password is checked only by FastAPI. Successful logins receive a signed, HttpOnly, SameSite cookie valid for seven days; production cookies are also marked Secure. Changing the password immediately invalidates existing sessions. Production fails closed with a `503` setup screen when no password is configured, so the analytics cannot accidentally deploy publicly.

The compiled stat board does not require PostgreSQL or Redis. Its SQLite setting only supports the secondary database-backed endpoints and is ephemeral on the free service.

The unauthenticated health check is `/api/health`. The site, JSON APIs, and API documentation at `/docs` require authentication.

For a manually created Python service, set the build command to `bash render-build.sh` and the start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Render's generic `gunicorn your_application.wsgi` placeholder is for WSGI applications and does not apply to FastAPI.

## Extended ingestion infrastructure

Managed PostgreSQL and Redis are only needed if the background importer and Celery worker are enabled later. In that configuration, run Alembic before rollout and persist `RAW_DOCUMENT_ROOT` to durable object storage or a backed-up volume.

Back up PostgreSQL with `make backup`. Restore into a clean database with `gunzip -c backup.sql.gz | psql ...`, then verify `alembic current` and run `python -m app.cli validate`.

Do not run multiple recurring scrape schedulers without a distributed lock. Treat source markup changes and cross-source conflicts as reviewable incidents, not automatic overwrite events.
