## Slice
- `aircraft category and classification behavior`

## Source Of Truth
- `MyFlightbook.AircraftSupport/CategoryClass.cs`
- Behavior: `aircraft category and classification behavior`

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
- legacy file: `MyFlightbook.AircraftSupport/CategoryClass.cs`
- current-stack file: `apps/api/src/myflightbook_api/services/aircraft/user_aircraft.py`
- current-stack file: `apps/api/tests/test_service_user_aircraft.py`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/services/aircraft/user_aircraft.py`: current aircraft creation and make-model projection service anchor
- `apps/api/tests/test_service_user_aircraft.py`: current aircraft-service proof surface

## In Scope
- preserve the exact domain behavior named in the ledger for `aircraft category and classification behavior`.
- keep row scope limited to the selected calculation, derivation, classification, or rating behavior.
- preserve the returned values, classification decisions, or discrepancy semantics that belong to this one domain surface.

## Out Of Scope
- adjacent controller flows, web-page scaffolding, or worker orchestration not required by the exact domain behavior.
- broad model rewrites beyond the smallest bounded domain extraction needed for this row.
- changing adjacent domain rows.

## Acceptance Criteria
- the current stack has a bounded service or model seam for `aircraft category and classification behavior` only.
- the proof path satisfies the ledger target for this row: `fixture + service test`.
- the row does not silently absorb adjacent domain behaviors.

## Fixtures And Proof
- store new fixtures or shadow-comparison artifacts under `apps/api/tests/fixtures/domain/domain-aircraft-category-classification/`.
- use the smallest truthful service-test or route-adjacent proof path anchored on `apps/api/src/myflightbook_api/services/aircraft/user_aircraft.py` and `apps/api/tests/test_service_user_aircraft.py`.
- proof targets:
  - the exact `aircraft category and classification behavior` boundary matches the legacy source named above.
  - the row's declared proof target is satisfied: `fixture + service test`.
  - if implementation requires a new domain package boundary beyond the touched files, return the row to Architect before widening the slice.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- if the exact `aircraft category and classification behavior` boundary turns out to span more than one legacy contract surface, stop with `blocked on contract`.
- if another worker materially changes `apps/api/src/myflightbook_api/services/aircraft/user_aircraft.py` or `apps/api/tests/test_service_user_aircraft.py` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/services/aircraft/user_aircraft.py`
- `TODO (Codex): scaffold the exact service or model boundary for aircraft category and classification behavior, scope limit to domain-aircraft-category-classification only, proof target fixture + service test for the single domain surface`
- Target TODO location: `apps/api/tests/test_service_user_aircraft.py`
- `TODO (Codex): scaffold the smallest adjacent proof or consumer seam for aircraft category and classification behavior, scope limit to domain-aircraft-category-classification only, proof target bounded parity coverage for the exact domain row`
