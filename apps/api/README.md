# MyFlightbook API

This package is the FastAPI backend for the migration workspace. It is the main place where legacy compatibility behavior is being rebuilt and verified.

## Responsibilities

- canonical REST API for the new stack
- compatibility surface for legacy mobile and web behavior as slices are migrated
- Postgres and PostGIS persistence via SQLAlchemy and Alembic
- legacy MySQL import and ID mapping support
- background-job handoff for telemetry and media processing when async execution is justified

## Current Status

This is still a migration workspace, not a parity-complete replacement:

- canonical models and migrations are in place
- placeholder auth bootstrap supports local development before real OIDC is wired in
- profile, aircraft, flights, totals, telemetry, and images endpoints are available
- compatibility tests and fixtures already exist for selected legacy behaviors
- import scaffolding targets the current legacy MySQL tables

## Local Setup

### Windows Fast Path

Use:

`powershell -ExecutionPolicy Bypass -File .\scripts\dev-up.ps1 -Seed`

This is the default path for API and web iteration on Windows. It starts Alembic, MinIO, the API, and the web app. It does not start Redis or the worker.

### Full Parity Path

Use:

`docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker`

Then start the API manually if needed:

`.\apps\api\.venv\Scripts\python.exe -m uvicorn myflightbook_api.main:app --host 127.0.0.1 --port 8000`

## Development Workflow

1. choose the next slice from `docs/migration/contract-inventory.md`
2. follow `docs/migration/execution-playbook.md`
3. implement backend compatibility first
4. extend parity tests and fixtures before closing the slice
