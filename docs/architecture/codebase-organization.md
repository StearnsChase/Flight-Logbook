# Codebase Organization And Parity Slice Workflow

This document describes the actual structure of the migration workspace and the recommended workflow for moving one approved, rowized surface efficiently. For backlog order, use [../migration/contract-inventory.md](../migration/contract-inventory.md). For pre-execution contract changes, use [../changes/change-intake-protocol.md](../changes/change-intake-protocol.md). For the exact implementation checklist, use [../migration/execution-playbook.md](../migration/execution-playbook.md).

## Repository Structure

### Legacy Reference Surfaces

- `MyFlightbook.Web/AppCode/WebService.cs`: legacy SOAP and mobile contract surface
- `MyFlightbook.Web/Areas/mvc/Controllers`: MVC web surface
- `MyFlightbook.Web/AppCode/Flights/*` and `UserAccounts/Profile.cs`: embedded domain behavior

### Migration Workspace

#### Backend (`apps/api/src/myflightbook_api`)

- `api/routes/`: FastAPI route modules wired into `main.py`
- `schemas/`: Pydantic request and response contracts
- `models/`: SQLAlchemy ORM models
- `services/`: business behavior by domain, including `services/compat` for legacy-facing compatibility work
- `db/`: database configuration and session helpers
- `core/`: application settings, auth, and logging
- `jobs/` and `workers/`: queue handoff definitions where API behavior needs async execution

#### Frontend (`apps/web`)

- `app/`: App Router routes and layouts
- `src/components/`: reusable UI components
- `src/lib/`: utilities, formatters, and app-specific helpers

#### Shared Contracts (`packages/api-client`)

- generated OpenAPI types and typed client helpers used by the frontend

#### Tests And Fixtures

- `apps/api/tests/`: backend unit, integration, and parity tests
- `apps/api/tests/fixtures/`: golden fixtures grouped by domain area
- `apps/web/tests/`: frontend unit and component tests
- `apps/worker/tests/`: worker unit tests

## Parity Slice Workflow

Do not treat this repo like a pure greenfield build. The efficient unit of work is a legacy surface plus the minimum new-stack changes needed to reproduce it safely.

### Step 1: Choose The Legacy Surface

- If there is an approved but unrowized change, let the Architect rowize it before normal slice selection.
- Otherwise start from the current backlog order in `contract-inventory.md` and the next incomplete row in `parity-status-ledger.md`.
- Pick a concrete surface such as a `WebService.cs` method, a telemetry parser, an MVC action flow, an import/export behavior, a domain behavior, a media behavior, or a background flow.
- Define the acceptance target in terms of observable behavior, not just code placement.

### Step 2: Capture Contract And Fixture Evidence

- Record the legacy inputs, outputs, and edge cases before implementing.
- Add or extend golden fixtures under `apps/api/tests/fixtures`.
- Decide whether the slice needs direct fixture comparison, shadow comparison, or both.

### Step 3: Map Identity, IDs, And Data Dependencies

- Identify legacy IDs that require mapping tables in the new database.
- Identify any auth, profile, aircraft, totals, or geography dependencies that the slice relies on.
- Keep compatibility behavior in the backend first so the new system can be verified independently of UI work.

### Step 4: Implement Backend Behavior

- Add or extend ORM models, schemas, service logic, and route wiring in `apps/api`.
- Use `services/compat` or domain services where the slice is reproducing legacy behavior rather than creating a new product-only flow.
- Keep route handlers thin and push calculations into services.

### Step 5: Update Shared Contracts

- Regenerate or adjust `packages/api-client` only after the backend contract is stable.
- Keep the generated OpenAPI types aligned with the actual FastAPI surface.

### Step 6: Add Or Adjust UI Only When Needed

- If the selected legacy surface feeds a new-stack UI flow, update `apps/web`.
- If the slice is mobile compatibility or backend parity only, do not create UI work just to satisfy the generic monorepo pattern.

### Step 7: Add Worker Behavior Only When The Slice Needs Async Processing

- Use `apps/worker` for telemetry parsing, media processing, or other Redis-backed background jobs.
- Do not force worker work into a slice that can be verified synchronously.

### Step 8: Verify, Remove TODOs, And Advance The Backlog

- Run the slice-specific parity checks described in `docs/testing.md`.
- Remove completed inline `TODO (Codex):` comments from `apps/`.
- Update `contract-inventory.md` only through the approved change path when family scope, family order, or contract surface changed.
