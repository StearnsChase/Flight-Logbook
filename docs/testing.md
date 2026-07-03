# Testing Strategy

This repo is not aiming only for generic unit-test coverage. The primary goal is confidence that each migrated slice matches legacy behavior closely enough to retire the old surface safely.

## Quality Bar

For autonomous work, "perfect code" means:

- the delivered behavior matches the intended contract
- the diff stays scoped to the current slice
- the smallest relevant tests or fixtures prove the changed behavior
- unproven behavior is reported explicitly rather than implied

## Testing Layers

### Backend Unit And Integration Tests (`apps/api/tests`)

- use `pytest`
- keep isolated business-logic tests close to the domain behavior being ported
- cover route-to-service behavior for the new API surface
- verify migrations, model contracts, and compatibility logic where the slice depends on them

### Parity Gates

Every migration slice should define and satisfy the parity gates that apply to it:

- legacy mobile compatibility tests for `WebService.cs` replacement behavior
- golden fixtures under `apps/api/tests/fixtures`
- shadow comparisons when a legacy calculation still needs direct output comparison
- telemetry parser coverage for supported formats such as `Airbly`, `Baju`, `CSV`, `GPX`, `IGC`, `KML`, and `NMEA`
- slice-specific acceptance criteria tied to the chosen legacy surface

Examples already present in the repo include:

- `apps/api/tests/test_legacy_mobile_compat.py`
- `apps/api/tests/test_telemetry_registry.py`
- compatibility fixtures under `apps/api/tests/fixtures/`

Extend those patterns instead of inventing one-off test styles for each slice.

### Frontend Tests (`apps/web/tests`)

- use Vitest for component and UI behavior
- test frontend flows only when the slice has a real new-stack UI requirement
- keep frontend assertions aligned with the backend contract rather than duplicating backend business rules in the browser
- if a touched frontend behavior has no adequate test, add the smallest new test that proves it

### Worker Tests (`apps/worker/tests`)

- use `pytest`
- mock Redis, object storage, and database dependencies where possible
- verify task idempotency, retry-safe state transitions, and storage side effects
- require worker-specific proof only when the slice actually depends on async behavior

## Completion States And Required Evidence

The authoritative state vocabulary lives in `docs/agents/autonomous-execution-protocol.md`. Testing and reporting must align with it.

| State | Verification expectation | Reporting requirement |
| --- | --- | --- |
| `verified complete` | The smallest relevant checks were run and passed for the batch or slice. | List the exact commands or checks run and confirm the matching TODOs were removed. |
| `implemented pending verification` | The code landed, but the full proving step could not be run locally. | List executed checks, missing checks, blocker, and the next required verification step. |
| `blocked on environment` | Progress or proof cannot continue because required runtime pieces are unavailable. | Record the attempted command or check and the missing dependency or service. |
| `blocked on contract` | Implementation cannot be proven safe because the legacy behavior is ambiguous. | Record the exact source of ambiguity and the missing evidence. |
| `blocked on conflicting workspace state` | Same-scope dirty-tree edits or failures prevent safe proof or integration. | Record the conflicting files or failures and why integration is unsafe. |

## Verification Rules

- Run the smallest check that can truthfully validate the current batch.
- Prefer targeted parity tests, fixtures, and route or service checks over broad untargeted runs.
- If the current repo lacks an adequate proving check for the touched behavior, add the smallest new test or fixture that does.
- Do not claim `verified complete` unless the relevant proof actually ran and passed.
- Best-effort completion is allowed only as `implemented pending verification`.

## Slice Acceptance Checklist

Before closing a parity slice, confirm:

1. the legacy surface and expected outputs were captured before implementation
2. the backend behavior is covered by tests or fixtures appropriate to the slice
3. any API contract changes are reflected in `packages/api-client`
4. frontend coverage exists only where the slice actually needs UI behavior
5. worker coverage exists only where the slice actually needs async behavior
6. completed `TODO (Codex):` comments were removed and the next gap was identified
7. the reported completion state matches the evidence actually collected

## Test Command Guidance

Prefer running the smallest command that proves the slice:

- API tests from `apps/api`:
  `.\.venv\Scripts\python.exe -m pytest`
- Web tests from the repo root:
  `npm run test --workspace @myflightbook/web`

Add broader verification only when the slice crosses multiple boundaries.
