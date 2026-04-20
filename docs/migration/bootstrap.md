# MyFlightbook Migration Bootstrap

This repository now contains two systems side by side:

- `MyFlightbook.*` and `MyFlightbook.Web`: the legacy .NET/MySQL application.
- `apps/api`, `apps/web`, `apps/worker`, and `packages/api-client`: the new migration workspace.

## Target stack

- Backend: FastAPI + SQLAlchemy + Alembic + Postgres/PostGIS
- Frontend: Next.js App Router + TypeScript
- Media and telemetry background work: Python worker + S3-compatible storage
- Typed contracts: FastAPI OpenAPI feeding the TypeScript client package

## Current implementation scope

This bootstrap establishes the first runnable slice of the new platform:

- canonical ORM models for users, aircraft, airports, flights, telemetry uploads, images, and legacy ID mappings
- initial REST endpoints for auth bootstrap, profile, aircraft, flights, totals, telemetry, and images
- a Next.js dashboard shell for the core logbook flows
- import and parity scaffolding for legacy MySQL extraction and telemetry fixture tracking
- local development infrastructure for Postgres/PostGIS and MinIO

## What is intentionally deferred

- production-ready Google/Apple OAuth flows
- background queue infrastructure and media processing execution
- full telemetry parser parity
- admin, billing, partner integrations, and mobile/public API surfaces
- complete legacy data import implementation

## Recommended next implementation steps

1. Install dependencies for `apps/api`, `apps/web`, and `packages/api-client`.
2. Bring up `infra/docker-compose.yml`.
3. Run the initial Alembic migration.
4. Replace the auth bootstrap placeholder with real OIDC verification and session issuance.
5. Flesh out the legacy import pipeline and golden parity fixtures.
