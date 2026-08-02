# Proposed repository tree

```text
.
├── backend/
│   ├── alembic/                 # versioned PostgreSQL migrations
│   ├── app/
│   │   ├── api/                 # REST resources
│   │   ├── scraping/
│   │   │   ├── adapters/        # AAC, NAIA, UPIKE implementations
│   │   │   └── parsers/         # source/layout-specific parser versions
│   │   ├── services/            # import and later reconciliation/analytics
│   │   ├── models.py            # persisted source and canonical foundation
│   │   └── worker.py            # Redis/Celery worker
│   ├── data/raw/                # gzip raw-response store (not committed)
│   └── tests/fixtures/source/   # immutable representative real fixtures
├── frontend/
│   ├── app/                     # Next.js App Router
│   ├── components/              # domain and shadcn-style UI components
│   └── lib/                     # typed API client
├── discovery/                   # reports, robots evidence, access responses
├── docs/                        # architecture and operating methodology
├── .github/workflows/ci.yml
├── docker-compose.yml
└── Makefile
```

Later phases add `source_*` statistical tables, canonical roster memberships, game facts, drives, plays, reconciliation candidates, metric definitions/values, model registry, records, and data-quality issues without collapsing those concerns into the core files.
