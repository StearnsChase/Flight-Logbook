# API Development Guide

This guide covers the real conventions and workflows for the FastAPI backend in `apps/api`.

## Layout

- `src/myflightbook_api/api/routes/`: route modules that are included from `myflightbook_api/main.py`
- `src/myflightbook_api/schemas/`: request and response contracts
- `src/myflightbook_api/models/`: ORM models and enums
- `src/myflightbook_api/services/`: domain behavior, compatibility logic, importers, and background-job handoff
- `src/myflightbook_api/db/`: database helpers and URL handling
- `tests/`: unit, integration, and parity tests
- `alembic/`: schema migration scripts

## Preferred Workflow

For parity-first work:

1. pick the legacy surface from `docs/migration/contract-inventory.md`
2. capture fixtures and expected behavior using `docs/migration/execution-playbook.md`
3. implement or extend the backend behavior
4. update the typed client only after the API contract is stable

## Running Locally

Two local modes exist:

- Windows fast path:
  `powershell -ExecutionPolicy Bypass -File .\scripts\dev-up.ps1 -Seed`
- Full parity backing services:
  `docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker`

If you need to start the API manually:

`.\apps\api\.venv\Scripts\python.exe -m uvicorn myflightbook_api.main:app --host 127.0.0.1 --port 8000`

## Database Migrations

We use Alembic for schema changes.

From `apps/api`:

- create a migration:
  `.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "Description of change"`
- apply migrations:
  `.\.venv\Scripts\python.exe -m alembic upgrade head`

## Adding Or Updating Routes

1. Add or update request and response schemas in `schemas/`.
2. Add or update the supporting domain logic in `services/`.
3. Add or update the route module under `api/routes/`.
4. Include the route in `myflightbook_api/main.py` if it is a new module.
5. Extend parity tests, fixtures, or compatibility tests before closing the slice.

## Background Job Handoff

- Use the API layer to enqueue worker jobs only when the slice truly needs async execution.
- The current worker runtime is `arq` with Redis, not a generic future queue.
- Keep synchronous parity behavior in the API until the async handoff is justified by the slice requirements.
