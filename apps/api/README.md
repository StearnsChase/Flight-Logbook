# MyFlightbook API

This is the new FastAPI backend for the MyFlightbook migration workspace.

## Responsibilities

- canonical REST API for the web-only v1 release
- Postgres/PostGIS persistence using SQLAlchemy and Alembic
- legacy MySQL import and ID mapping support
- background-job orchestration handoff for telemetry and media processing

## Current status

This implementation is the bootstrap slice, not parity-complete:

- canonical models and migrations are in place
- placeholder auth bootstrap supports local development before real OIDC is wired in
- profile, aircraft, flights, totals, telemetry, and images endpoints are available
- import scaffolding targets the current legacy MySQL tables

## Local setup

1. Copy `.env.example` to `.env`.
2. Start local infrastructure from `../../infra/docker-compose.yml`.
3. Install the package with `pip install -e .[dev]`.
4. Run `alembic upgrade head`.
5. Start the API with `uvicorn myflightbook_api.main:app --reload`.
