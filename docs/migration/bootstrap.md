# MyFlightbook Migration Bootstrap

This document explains how the side-by-side migration workspace is bootstrapped today. It is the operational guide for the new stack, not the live execution ledger. For the repo-wide loop, use [repo-completion-protocol.md](repo-completion-protocol.md). For the live row state, use [parity-status-ledger.md](parity-status-ledger.md). For family order and census source, use [contract-inventory.md](contract-inventory.md).

## Canonical Migration Docs

- [repo-completion-protocol.md](repo-completion-protocol.md): canonical repo-wide execution loop and strict repo finish line
- [parity-status-ledger.md](parity-status-ledger.md): canonical live execution state and next incomplete row
- [contract-inventory.md](contract-inventory.md): canonical parity family order, census source, fixture expectations, and worker rules
- [execution-playbook.md](execution-playbook.md): exact workflow for advancing one ledger row
- [../infrastructure/local-dev.md](../infrastructure/local-dev.md): environment truth, startup modes, and shutdown behavior
- [../agents/autonomous-execution-protocol.md](../agents/autonomous-execution-protocol.md): role-independent autonomy, escalation, and completion-state rules

## Target Stack

- Backend: FastAPI + SQLAlchemy + Alembic + Postgres/PostGIS
- Frontend: Next.js App Router + TypeScript
- Background processing: Python worker using `arq` with Redis
- Media and telemetry storage: S3-compatible object storage via MinIO locally and S3-compatible providers in production
- Typed contracts: FastAPI OpenAPI feeding `packages/api-client`

## Current Implementation Scope

The migration workspace already provides a runnable initial platform:

- canonical ORM models for users, aircraft, airports, flights, telemetry uploads, images, and legacy ID mappings
- initial REST endpoints for auth bootstrap, profile, aircraft, flights, totals, telemetry, and images
- a Next.js dashboard shell for core logbook flows
- import scaffolding for legacy MySQL extraction and mapping rows
- telemetry parser coverage and parity-oriented fixtures under `apps/api/tests`
- local infrastructure paths for Postgres, Redis, MinIO, and the worker

## Development Modes

Choose one mode deliberately based on the work you are doing.

| Mode | Primary command | Prerequisites | Starts | Does not start |
| --- | --- | --- | --- | --- |
| Windows fast path | `powershell -ExecutionPolicy Bypass -File .\scripts\dev-up.ps1 -Seed` | `apps/api/.venv`, `npm.cmd`, PostgreSQL 16 service or an external DB reachable from `apps/api/.env` | Alembic migration, local Postgres service if present, MinIO, API, web, demo seed | Redis, worker, Docker services |
| Full container/parity path | `docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker` | Docker Desktop or compatible Docker runtime, valid `apps/api/.env` for API and worker access | Postgres, Redis, MinIO, worker | API, web, demo seed |

Notes:

- `dev-up.ps1` is the default path for day-to-day API and web iteration on Windows.
- The full container path is the correct path when the row touches Redis-backed worker behavior or needs the full parity backing services.
- `dev-down.ps1` only stops repo-started API, web, and MinIO processes. Use `docker compose -f .\infra\docker-compose.yml down` for Docker services.

## Parity-First Bootstrap Sequence

When starting or resuming a migration row:

1. Choose the next incomplete row from [parity-status-ledger.md](parity-status-ledger.md).
2. Use [repo-completion-protocol.md](repo-completion-protocol.md) to determine the current owner and required persisted artifact updates.
3. Follow [execution-playbook.md](execution-playbook.md) to capture fixtures, shadow expectations, and acceptance criteria before implementing.
4. Bring up the environment mode that matches the row.
5. Implement backend or compatibility behavior first.
6. Update `packages/api-client` only after the backend contract is stable.
7. Add or adjust web UI only if the row has a user-facing requirement in the new stack.
8. Add worker work only if the row truly requires background processing.

## Intentionally Deferred

These items are still outside the currently implemented platform:

- production-ready Google and Apple OAuth flows
- complete telemetry parser parity across every legacy workflow
- full legacy import replay and production-grade import operations
- admin, billing, partner integrations, and the remaining MVC and mobile surfaces
- production observability, deployment automation, and a full CI gate

## Recommended Next Implementation Steps

For parity-first work, the default next steps are:

1. Run the non-optional census and row-selection loop from `repo-completion-protocol.md`.
2. Pick the next incomplete `WebService.cs`, MVC, telemetry, or background row from `parity-status-ledger.md`.
3. Capture deterministic fixtures and expected outputs before expanding the implementation.
4. Close the compatibility gap in the API and service layer first.
5. Extend `packages/api-client` and `apps/web` only where the new stack needs to consume that behavior.
6. Keep the code backlog live with inline `TODO (Codex):` comments under `apps/`.
