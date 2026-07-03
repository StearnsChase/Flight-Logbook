## Slice
- `weather and day-night calculation behavior`

## Source Of Truth
- `MyFlightbook.Geography/Solar.cs`
- Behavior: `weather and day-night calculation behavior`

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
- legacy file: `MyFlightbook.Geography/Solar.cs`
- current-stack file: `apps/api/src/myflightbook_api/services/geography/solar.py`
- current-stack file: `apps/api/src/myflightbook_api/services/flights/lint.py`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/services/geography/solar.py`: current solar and sunrise-sunset calculation service anchor
- `apps/api/src/myflightbook_api/services/flights/lint.py`: nearest current consumer seam for flight-time interpretation and validation work

## In Scope
- preserve the exact domain behavior named in the ledger for `weather and day-night calculation behavior`.
- keep row scope limited to the selected calculation, derivation, classification, or rating behavior.
- preserve the returned values, classification decisions, or discrepancy semantics that belong to this one domain surface.

## Out Of Scope
- adjacent controller flows, web-page scaffolding, or worker orchestration not required by the exact domain behavior.
- broad model rewrites beyond the smallest bounded domain extraction needed for this row.
- changing adjacent domain rows.

## Acceptance Criteria
- the current stack has a bounded service or model seam for `weather and day-night calculation behavior` only.
- the proof path satisfies the ledger target for this row: `fixture + service test`.
- the row does not silently absorb adjacent domain behaviors.

## Fixtures And Proof
- store new fixtures or shadow-comparison artifacts under `apps/api/tests/fixtures/domain/domain-weather-day-night-calculation/`.
- use the smallest truthful service-test or route-adjacent proof path anchored on `apps/api/src/myflightbook_api/services/geography/solar.py` and `apps/api/src/myflightbook_api/services/flights/lint.py`.
- proof targets:
  - the exact `weather and day-night calculation behavior` boundary matches the legacy source named above.
  - the row's declared proof target is satisfied: `fixture + service test`.
  - if implementation requires a new domain package boundary beyond the touched files, return the row to Architect before widening the slice.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- if the exact `weather and day-night calculation behavior` boundary turns out to span more than one legacy contract surface, stop with `blocked on contract`.
- if another worker materially changes `apps/api/src/myflightbook_api/services/geography/solar.py` or `apps/api/src/myflightbook_api/services/flights/lint.py` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/services/geography/solar.py`
- `TODO (Codex): scaffold the exact service or model boundary for weather and day-night calculation behavior, scope limit to domain-weather-day-night-calculation only, proof target fixture + service test for the single domain surface`
- Target TODO location: `apps/api/src/myflightbook_api/services/flights/lint.py`
- `TODO (Codex): scaffold the smallest adjacent proof or consumer seam for weather and day-night calculation behavior, scope limit to domain-weather-day-night-calculation only, proof target bounded parity coverage for the exact domain row`
