## Slice
- `authorize flow` from `oAuthController.cs`

## Source Of Truth
- `MyFlightbook.Web/Areas/mvc/Controllers/oAuthController.cs`
- Flow: `authorize flow`

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
- legacy file: `MyFlightbook.Web/Areas/mvc/Controllers/oAuthController.cs` (`authorize flow`)
- current-stack file: `apps/api/src/myflightbook_api/api/routes/auth.py`
- current-stack file: `apps/web/app/page.tsx`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/api/routes/auth.py`: current auth route boundary and nearest OAuth-adjacent identity integration seam
- `apps/web/app/page.tsx`: current public entry page and first web insertion point for OAuth-facing route scaffolding

## In Scope
- preserve the exact controller-flow boundary named in the ledger for `authorize flow`.
- keep the new-stack work limited to the route, page, redirect, partial-render, or export behavior exercised by this one MVC flow.
- preserve request gating, returned data or file shape, and side effects inside the exact flow boundary.

## Out Of Scope
- other actions in `oAuthController.cs` outside the selected `authorize flow` row.
- broad UI redesign or multi-controller consolidation.
- changing the parity target for adjacent MVC rows.

## Acceptance Criteria
- the new stack has a bounded scaffold for the exact `authorize flow` flow and nothing broader.
- the proof path satisfies the ledger target for this row: `route tests + auth parity`.
- the row does not silently absorb unrelated actions from `oAuthController.cs`.

## Fixtures And Proof
- capture the exact controller-flow inputs and outputs needed to satisfy the ledger proof target: `route tests + auth parity`.
- store any new fixtures or golden outputs under `apps/api/tests/fixtures/mvc/mvc-oauth-authorize/`.
- prove the row with the smallest truthful combination of route tests, service tests, file-export fixtures, or UI parity checks once the exact route segment exists.
- if the flow depends on session-heavy or partial-render behavior that cannot be bounded inside this one row without redefining adjacent rows, stop and return the row to Architect.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- the current web app is still at a thin-shell stage, so if implementing `authorize flow` requires rowizing additional route families before this flow can be bounded, stop with `blocked on contract`.
- if another worker materially reshapes `apps/api/src/myflightbook_api/api/routes/auth.py` or `apps/web/app/page.tsx` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/api/routes/auth.py`
- `TODO (Codex): scaffold the exact new-stack service or route boundary needed for authorize flow, scope limit to mvc-oauth-authorize only, proof target route tests + auth parity for the single MVC flow`
- Target TODO location: `apps/web/app/page.tsx`
- `TODO (Codex): scaffold the minimal web entry point, route shell, or client wiring needed for authorize flow, scope limit to mvc-oauth-authorize only, proof target bounded parity checks for the exact MVC flow`

