## Slice
- `AuthTokenForUser` from `WebService.cs`

## Source Of Truth
- `MyFlightbook.Web/AppCode/WebService.cs`
- Method: `AuthTokenForUser`

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
- legacy file: `MyFlightbook.Web/AppCode/WebService.cs` (`AuthTokenForUser`)
- current-stack file: `apps/api/src/myflightbook_api/services/compat/legacy_mobile.py`
- current-stack file: `apps/api/tests/test_legacy_mobile_compat.py`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/services/compat/legacy_mobile.py`: compat-layer insertion point for emulating the exact `WebService.cs::AuthTokenForUser` request boundary, legacy auth and error semantics, and the returned payload or mutation side effects without widening into adjacent mobile rows.
- `apps/api/tests/test_legacy_mobile_compat.py`: fixture-backed compatibility proof surface for the exact mobile contract row.

## In Scope
- preserve the authenticated request boundary, legacy error or null behavior, response shape, and persistence or deletion side effects exercised by `WebService.cs::AuthTokenForUser`.
- keep any ordering, filtering, or serialization rules inside the exact `AuthTokenForUser` boundary.
- limit the row to the single mobile surface already named in the ledger.

## Out Of Scope
- any other `WebService.cs` method, even when it shares helper code or payload types.
- broad domain-model refactors, new web UI work, and worker behavior unless the exact `AuthTokenForUser` surface cannot execute without the smallest compat-only linkage.
- changing the approved parity target for adjacent mobile rows.

## Acceptance Criteria
- the compat layer exposes a bounded emulation path for `WebService.cs::AuthTokenForUser` only.
- fixture-backed compatibility coverage proves the exact `AuthTokenForUser` request boundary and the returned payload or side-effect outcome against legacy expectations.
- implementation stays scoped to the exact row and does not fold in adjacent mobile methods.

## Fixtures And Proof
- add or extend fixture-backed tests in `apps/api/tests/test_legacy_mobile_compat.py`.
- store new golden fixtures under `apps/api/tests/fixtures/compat/legacy_mobile/auth-token-for-user/`.
- proof targets:
  - auth, null, and error semantics match the exact `WebService.cs::AuthTokenForUser` boundary.
  - serialized payload fields or mutation side effects match the exact legacy surface for this row.
  - no unrelated mobile method behavior is added under the same fixture.
- if the exact method depends on an unmapped legacy type or helper that cannot be represented without changing another row's contract, stop and return the row to Architect.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- if `legacy_mobile.py` or its fixtures are already being reshaped for another row, re-check conflicting write scope before scaffolding begins.
- if `WebService.cs::AuthTokenForUser` relies on additional legacy response members or side effects that are not representable inside the current compat boundary without widening into another row, stop with `blocked on contract`.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/services/compat/legacy_mobile.py`
- `TODO (Codex): scaffold the exact WebService.cs::AuthTokenForUser compatibility entrypoint and any row-local payload helpers, scope limit to ws-auth-token-for-user only, proof target fixture-backed legacy mobile parity coverage for the exact method boundary`
- Target TODO location: `apps/api/tests/test_legacy_mobile_compat.py`
- `TODO (Codex): add or extend fixture-backed coverage for WebService.cs::AuthTokenForUser`, scope limit to `ws-auth-token-for-user` only, proof target golden compatibility assertions for the exact request boundary and returned payload or side effect`
