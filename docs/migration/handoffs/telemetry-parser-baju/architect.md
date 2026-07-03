## Slice
- `Baju` telemetry parser parity

## Source Of Truth
- `MyFlightbook.Telemetry/Baju.cs`
- Parser behavior: `Baju`

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
- legacy file: `MyFlightbook.Telemetry/Baju.cs`
- current-stack file: `apps/api/src/myflightbook_api/services/telemetry/baju.py`
- current-stack file: `apps/api/tests/test_telemetry_baju.py`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/services/telemetry/baju.py`: current parser implementation anchor for the exact `Baju` format.
- `apps/api/tests/test_telemetry_baju.py`: current parser proof surface for `Baju` fixtures and point extraction.

## In Scope
- preserve parser detection and point extraction semantics for the exact `Baju` format only.
- keep row scope limited to the one parser family already named in the ledger.
- preserve format-specific failures and edge-case handling inside the parser boundary.

## Out Of Scope
- parser-registry changes that alter the contract for other telemetry formats beyond the smallest exact-format wiring.
- telemetry upload workflow, worker processing, or export behavior.
- changes to any other parser row.

## Acceptance Criteria
- the current-stack parser for `Baju` is bounded to the exact legacy parser surface.
- fixture-backed parsing proof satisfies the ledger target for this row: `fixture + parser test`.
- no unrelated parser formats are folded into the same row.

## Fixtures And Proof
- add or extend parser fixtures under `apps/api/tests/fixtures/telemetry/telemetry-parser-baju/`.
- prove the row through `apps/api/tests/test_telemetry_baju.py` and, when necessary, the shared registry ordering check.
- proof targets:
  - the exact `Baju` parser accepts the legacy source format.
  - parsed telemetry points and parser failure modes remain bounded to the selected format.
  - the row's declared proof target is satisfied: `fixture + parser test`.
- if preserving `Baju` requires changing a shared telemetry base contract that affects adjacent parser rows, stop and return the row to Architect.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- parser-base or registry changes can bleed across formats; if the exact `Baju` row cannot be isolated, stop with `blocked on contract`.
- if another worker changes `apps/api/src/myflightbook_api/services/telemetry/baju.py` or `apps/api/tests/test_telemetry_baju.py` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/services/telemetry/baju.py`
- `TODO (Codex): scaffold the exact Baju parser parity work, scope limit to telemetry-parser-baju only, proof target fixture + parser test with format-specific fixtures`
- Target TODO location: `apps/api/tests/test_telemetry_baju.py`
- `TODO (Codex): add or extend Baju parser fixtures and assertions, scope limit to telemetry-parser-baju only, proof target the exact parser acceptance and point extraction surface`
