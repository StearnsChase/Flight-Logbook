## Slice
- `image storage defaults behavior`

## Source Of Truth
- `MyFlightbook.Image/MFBImageInfo.cs`
- Behavior: `image storage defaults behavior`

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
- legacy file: `MyFlightbook.Image/MFBImageInfo.cs`
- current-stack file: `apps/api/src/myflightbook_api/models/media.py`
- current-stack file: `apps/api/src/myflightbook_api/services/media/images.py`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/models/media.py`: current persisted media metadata anchor for storage keys and ownership
- `apps/api/src/myflightbook_api/services/media/images.py`: current media-processing service that applies storage defaults

## In Scope
- preserve the exact media behavior named in the ledger for `image storage defaults behavior`.
- keep row scope limited to storage defaults, annotation behavior, or processing behavior for this one media surface.
- preserve URL, metadata, and mutation semantics that belong to the selected row.

## Out Of Scope
- unrelated image rows, broad storage redesign, and web or worker orchestration outside the exact media behavior.
- changing adjacent media contracts.
- sweeping changes to upload flows that belong to other rows.

## Acceptance Criteria
- the current stack has a bounded media seam for `image storage defaults behavior` only.
- the proof path satisfies the ledger target for this row: `fixture + media test`.
- no other media row is silently absorbed.

## Fixtures And Proof
- store new fixtures under `apps/api/tests/fixtures/media/media-image-storage-defaults/`.
- prove the selected media behavior with the smallest truthful combination of metadata assertions, image-processing tests, or route-adjacent checks.
- proof targets:
  - the exact `image storage defaults behavior` boundary matches the selected legacy source.
  - the row's declared proof target is satisfied: `fixture + media test`.
  - if implementation requires shared media-model redesign beyond this row, return the row to Architect before widening scope.

## Environment
- `Windows fast path`: the selected row can be planned and initially proven inside the API and web workspace without starting Redis or the worker.

## Escalation Risks
- if the exact media behavior spans more than one storage contract or requires widening into the worker rows, stop with `blocked on contract`.
- if another worker materially changes `apps/api/src/myflightbook_api/models/media.py` or `apps/api/src/myflightbook_api/services/media/images.py` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/models/media.py`
- `TODO (Codex): scaffold the exact media seam for image storage defaults behavior, scope limit to media-image-storage-defaults only, proof target fixture + media test for the single media row`
- Target TODO location: `apps/api/src/myflightbook_api/services/media/images.py`
- `TODO (Codex): add or extend the smallest adjacent proof or metadata wiring for image storage defaults behavior, scope limit to media-image-storage-defaults only, proof target bounded parity coverage for the exact media row`
