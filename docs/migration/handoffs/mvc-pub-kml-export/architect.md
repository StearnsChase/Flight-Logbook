## Slice
- `KML export flow` from `PubController.cs`

## Source Of Truth
- `MyFlightbook.Web/Areas/mvc/Controllers/PubController.cs`
- Flow: `KML export flow`

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
- legacy file: `MyFlightbook.Web/Areas/mvc/Controllers/PubController.cs` (`KML export flow`)
- current-stack file: `apps/web/app/page.tsx`
- current-stack file: `apps/web/src/lib/api.ts`

## Current-Stack Touchpoints
- `apps/web/app/page.tsx`: current public web entry point and nearest read-only and public-route scaffold anchor
- `apps/web/src/lib/api.ts`: current client boundary for public data fetches and export links

## In Scope
- preserve the exact controller-flow boundary named in the ledger for `KML export flow`.
- keep the new-stack work limited to the route, page, redirect, partial-render, or export behavior exercised by this one MVC flow.
- preserve request gating, returned data or file shape, and side effects inside the exact flow boundary.

## Out Of Scope
- other actions in `PubController.cs` outside the selected `KML export flow` row.
- broad UI redesign or multi-controller consolidation.
- changing the parity target for adjacent MVC rows.

## Acceptance Criteria
- the new stack has a bounded scaffold for the exact `KML export flow` flow and nothing broader.
- the proof path satisfies the ledger target for this row: `route tests + fixture`.
- the row does not silently absorb unrelated actions from `PubController.cs`.

## Fixtures And Proof
- capture the exact controller-flow inputs and outputs needed to satisfy the ledger proof target: `route tests + fixture`.
- store any new fixtures or golden outputs under `apps/api/tests/fixtures/mvc/mvc-pub-kml-export/`.
- prove the row with the smallest truthful combination of route tests, service tests, file-export fixtures, or UI parity checks once the exact route segment exists.
- if the flow depends on session-heavy or partial-render behavior that cannot be bounded inside this one row without redefining adjacent rows, stop and return the row to Architect.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- the current web app is still at a thin-shell stage, so if implementing `KML export flow` requires rowizing additional route families before this flow can be bounded, stop with `blocked on contract`.
- if another worker materially reshapes `apps/web/app/page.tsx` or `apps/web/src/lib/api.ts` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/web/app/page.tsx`
- `TODO (Codex): scaffold the exact new-stack service or route boundary needed for KML export flow, scope limit to mvc-pub-kml-export only, proof target route tests + fixture for the single MVC flow`
- Target TODO location: `apps/web/src/lib/api.ts`
- `TODO (Codex): scaffold the minimal web entry point, route shell, or client wiring needed for KML export flow, scope limit to mvc-pub-kml-export only, proof target bounded parity checks for the exact MVC flow`

