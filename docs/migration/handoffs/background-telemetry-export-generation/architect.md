## Slice
- `telemetry export generation behavior`

## Source Of Truth
- `MyFlightbook.Web/AppCode/Places/FlightData.cs`
- Behavior: `telemetry export generation behavior`

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
- legacy file: `MyFlightbook.Web/AppCode/Places/FlightData.cs`
- current-stack file: `apps/worker/src/myflightbook_worker/main.py`
- current-stack file: `apps/api/src/myflightbook_api/api/routes/telemetry.py`

## Current-Stack Touchpoints
- `apps/worker/src/myflightbook_worker/main.py`: current worker runtime where any deferred export generation would have to live
- `apps/api/src/myflightbook_api/api/routes/telemetry.py`: current telemetry route boundary nearest export initiation

## In Scope
- document the exact blocker for `telemetry export generation behavior` so the row does not advance on guesswork.

## Out Of Scope
- inferring a single implementation contract from competing legacy surfaces.
- advancing this row to Feature Scaffolder before the ambiguity below is narrowed.

## Acceptance Criteria
- do not advance this row while the contract ambiguity remains unresolved.
- rewrite this blocker artifact into a valid Architect handoff only after the exact background surface is narrowed to one concrete contract.

## Fixtures And Proof
- no truthful proof path can be assigned while the contract remains ambiguous.
- if the contract is clarified later, store proof fixtures under `apps/api/tests/fixtures/background/background-telemetry-export-generation/`.

## Environment
- `Full container/parity path`: the row is runtime-backed once clarified, but the current blocker is contract scope rather than environment readiness.

## Escalation Risks
- `legacy evidence points to request-path GPX and KML export flows across `FlightData.cs`, `FlightsController.cs`, and `WebService.cs`, so there is not yet one concrete background export contract to hand off without guessing.`
- advancing now would force Feature or Coder to guess the contract, so the correct state is `blocked on contract`.

## Feature Handoff Payload
- blocked on contract: do not seed `TODO (Codex):` work for this row until Architect rewrites the slice against one concrete legacy source surface.
