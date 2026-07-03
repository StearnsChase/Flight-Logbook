## Slice
- `commit flow` from `FlightEditController.cs`

## Source Of Truth
- `MyFlightbook.Web/Areas/mvc/Controllers/FlightEditController.cs`
- Flow: `commit flow`

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
- legacy file: `MyFlightbook.Web/Areas/mvc/Controllers/FlightEditController.cs` (`commit flow`)
- current-stack file: `apps/api/src/myflightbook_api/api/routes/flights.py`
- current-stack file: `apps/web/src/components/flight-composer.tsx`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/api/routes/flights.py`: current flight CRUD route boundary and nearest edit and commit seam
- `apps/web/src/components/flight-composer.tsx`: current flight-entry UI anchor for edit and commit scaffolding

## In Scope
- preserve the exact controller-flow boundary named in the ledger for `commit flow`.
- keep the new-stack work limited to the route, page, redirect, partial-render, or export behavior exercised by this one MVC flow.
- preserve request gating, returned data or file shape, and side effects inside the exact flow boundary.

## Out Of Scope
- other actions in `FlightEditController.cs` outside the selected `commit flow` row.
- broad UI redesign or multi-controller consolidation.
- changing the parity target for adjacent MVC rows.

## Acceptance Criteria
- the new stack has a bounded scaffold for the exact `commit flow` flow and nothing broader.
- the proof path satisfies the ledger target for this row: `service tests + ui parity`.
- the row does not silently absorb unrelated actions from `FlightEditController.cs`.

## Fixtures And Proof
- capture the exact controller-flow inputs and outputs needed to satisfy the ledger proof target: `service tests + ui parity`.
- store any new fixtures or golden outputs under `apps/api/tests/fixtures/mvc/mvc-flight-edit-commit/`.
- prove the row with the smallest truthful combination of route tests, service tests, file-export fixtures, or UI parity checks once the exact route segment exists.
- if the flow depends on session-heavy or partial-render behavior that cannot be bounded inside this one row without redefining adjacent rows, stop and return the row to Architect.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- the current web app is still at a thin-shell stage, so if implementing `commit flow` requires rowizing additional route families before this flow can be bounded, stop with `blocked on contract`.
- if another worker materially reshapes `apps/api/src/myflightbook_api/api/routes/flights.py` or `apps/web/src/components/flight-composer.tsx` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/api/routes/flights.py`
- `TODO (Codex): scaffold the exact new-stack service or route boundary needed for commit flow, scope limit to mvc-flight-edit-commit only, proof target service tests + ui parity for the single MVC flow`
- Target TODO location: `apps/web/src/components/flight-composer.tsx`
- `TODO (Codex): scaffold the minimal web entry point, route shell, or client wiring needed for commit flow, scope limit to mvc-flight-edit-commit only, proof target bounded parity checks for the exact MVC flow`

