## Slice
- `ForeFlight import conversion flow`

## Source Of Truth
- `MyFlightbook.Web/Areas/mvc/Controllers/ImportController.cs`
- Flow: `ForeFlight import conversion flow`

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
- legacy file: `MyFlightbook.Web/Areas/mvc/Controllers/ImportController.cs` (`ForeFlight import conversion flow`)
- current-stack file: `apps/api/src/myflightbook_api/services/importers/flights.py`
- current-stack file: `apps/api/tests/test_import_foreflight.py`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/services/importers/flights.py`: current importer conversion anchor for the exact source format.
- `apps/api/tests/test_import_foreflight.py`: current proof surface for the exact importer conversion row.

## In Scope
- preserve importer-specific header detection, field normalization, row-skip and error behavior, and converted flight payloads for `ForeFlight import conversion flow` only.
- keep row scope limited to the one external import source already named in the ledger.
- preserve source-specific mapping rules without widening into other importers.

## Out Of Scope
- other import-source rows, aircraft import review flows, and generic MVC import pages outside the selected conversion surface.
- worker replay or bulk import orchestration.
- unrelated CSV normalization changes that affect other import rows.

## Acceptance Criteria
- the current importer path is bounded to the exact `ForeFlight import conversion flow` conversion surface.
- fixture-backed import proof satisfies the ledger target for this row: `fixture + import test`.
- no other importer behavior is folded into the same row.

## Fixtures And Proof
- add or extend fixtures under `apps/api/tests/fixtures/imports/import-foreflight-conversion/`.
- prove the exact conversion behavior through `apps/api/tests/test_import_foreflight.py` and the importer path in `apps/api/src/myflightbook_api/services/importers/flights.py`.
- proof targets:
  - source-specific headers are recognized correctly.
  - converted flights preserve the selected row's mapped fields and row-skip or error semantics.
  - the row's declared proof target is satisfied: `fixture + import test`.
- if preserving this conversion source requires a shared import rewrite that changes adjacent importer contracts, stop and return the row to Architect.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- importer-header normalization is shared across formats; if exact-source parity cannot be bounded to this row, stop with `blocked on contract`.
- if another worker changes `apps/api/src/myflightbook_api/services/importers/flights.py` or `apps/api/tests/test_import_foreflight.py` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/services/importers/flights.py`
- `TODO (Codex): scaffold the exact ForeFlight import conversion flow conversion path, scope limit to import-foreflight-conversion only, proof target fixture + import test with source-specific fixtures`
- Target TODO location: `apps/api/tests/test_import_foreflight.py`
- `TODO (Codex): add or extend source-specific import assertions for ForeFlight import conversion flow, scope limit to import-foreflight-conversion only, proof target golden converted-flight parity for the exact importer row`
