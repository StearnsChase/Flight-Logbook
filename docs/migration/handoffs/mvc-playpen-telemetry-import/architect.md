## Slice
- `telemetry-import utility flow` from `PlaypenController.cs`

## Source Of Truth
- `MyFlightbook.Web/Areas/mvc/Controllers/PlaypenController.cs`
- Flow: `telemetry-import utility flow`

## Originating Change
- none

## Approved Evidence Reviewed
- `docs/migration/repo-completion-protocol.md`
- `docs/migration/parity-status-ledger.md`
- `docs/changes/approved-change-register.md`
- `docs/migration/contract-inventory.md`
- `docs/migration/execution-playbook.md`
- `docs/infrastructure/local-dev.md`
- current scanner output: empty
- current `git status --short`
- legacy file: `MyFlightbook.Web/Areas/mvc/Controllers/PlaypenController.cs` (`telemetry-import utility flow`)
- current-stack file: `apps/api/src/myflightbook_api/api/routes/telemetry.py`
- current-stack file: `apps/web/src/lib/api.ts`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/api/routes/telemetry.py`: current telemetry route boundary and nearest utility and import seam
- `apps/web/src/lib/api.ts`: current web client boundary for utility-route scaffolding

## In Scope
- preserve the exact controller-flow boundary named in the ledger for `telemetry-import utility flow`.
- keep the new-stack work limited to the route, page, redirect, partial-render, or export behavior exercised by this one MVC flow.
- preserve request gating, returned data or file shape, and side effects inside the exact flow boundary.

## Out Of Scope
- other actions in `PlaypenController.cs` outside the selected `telemetry-import utility flow` row.
- broad UI redesign or multi-controller consolidation.
- changing the parity target for adjacent MVC rows.

## Acceptance Criteria
- the new stack has a bounded scaffold for the exact `telemetry-import utility flow` flow and nothing broader.
- the proof path satisfies the ledger target for this row: `fixture + utility parity`.
- the row does not silently absorb unrelated actions from `PlaypenController.cs`.

## Fixtures And Proof
- capture the exact controller-flow inputs and outputs needed to satisfy the ledger proof target: `fixture + utility parity`.
- store any new fixtures or golden outputs under `apps/api/tests/fixtures/mvc/mvc-playpen-telemetry-import/`.
- prove the row with the smallest truthful combination of route tests, service tests, file-export fixtures, or UI parity checks once the exact route segment exists.
- if the flow depends on session-heavy or partial-render behavior that cannot be bounded inside this one row without redefining adjacent rows, stop and return the row to Architect.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- the current web app is still at a thin-shell stage, so if implementing `telemetry-import utility flow` requires rowizing additional route families before this flow can be bounded, stop with `blocked on contract`.
- if another worker materially reshapes `apps/api/src/myflightbook_api/api/routes/telemetry.py` or `apps/web/src/lib/api.ts` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/api/routes/telemetry.py`
- `TODO (Codex): scaffold the exact new-stack service or route boundary needed for telemetry-import utility flow, scope limit to mvc-playpen-telemetry-import only, proof target fixture + utility parity for the single MVC flow`
- Target TODO location: `apps/web/src/lib/api.ts`
- `TODO (Codex): scaffold the minimal web entry point, route shell, or client wiring needed for telemetry-import utility flow, scope limit to mvc-playpen-telemetry-import only, proof target bounded parity checks for the exact MVC flow`

