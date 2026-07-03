## Slice
- `image derivative generation behavior`

## Source Of Truth
- `MyFlightbook.Image/MFBImageInfo.cs`
- Behavior: `image derivative generation behavior`

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
- current-stack file: `apps/worker/src/myflightbook_worker/image_tasks.py`
- current-stack file: `apps/worker/src/myflightbook_worker/main.py`

## Current-Stack Touchpoints
- `apps/worker/src/myflightbook_worker/image_tasks.py`: current thumbnail and web-derivative worker task anchor
- `apps/worker/src/myflightbook_worker/main.py`: current worker registration and runtime entry point

## In Scope
- preserve the exact worker or background behavior named in the ledger for `image derivative generation behavior`.
- keep row scope limited to the selected async processing surface.
- preserve queue, derivative, or persisted-state semantics only where they belong to this one background row.

## Out Of Scope
- unrelated worker tasks, synchronous request-path exports, or broader orchestration changes outside the selected row.
- adjacent media or telemetry parser rows.
- changing the row boundary into a multi-task batch.

## Acceptance Criteria
- the worker path is bounded to the exact `image derivative generation behavior` surface.
- the proof path satisfies the ledger target for this row: `worker check + fixture`.
- no unrelated background behavior is silently absorbed.

## Fixtures And Proof
- store new fixtures or worker proof inputs under `apps/api/tests/fixtures/background/background-image-derivative-generation/`.
- prove the exact background surface with the smallest truthful combination of worker checks, state-transition assertions, and output fixtures.
- proof targets:
  - the exact `image derivative generation behavior` boundary matches the selected legacy source.
  - the row's declared proof target is satisfied: `worker check + fixture`.
  - if implementation requires redefining another worker row, return the slice to Architect before widening scope.

## Environment
- `Full container/parity path`: the selected row is worker-backed or runtime-dependent, so its truthful proving path ultimately depends on the parity services documented in `local-dev.md`.

## Escalation Risks
- if the selected legacy evidence turns out to describe a request-path flow rather than one bounded async background contract, stop with `blocked on contract`.
- if another worker materially changes `apps/worker/src/myflightbook_worker/image_tasks.py` or `apps/worker/src/myflightbook_worker/main.py` before scaffolding begins, re-check conflicting workspace state.

## Feature Handoff Payload
- Target TODO location: `apps/worker/src/myflightbook_worker/image_tasks.py`
- `TODO (Codex): scaffold the exact worker or background seam for image derivative generation behavior, scope limit to background-image-derivative-generation only, proof target worker check + fixture for the single background row`
- Target TODO location: `apps/worker/src/myflightbook_worker/main.py`
- `TODO (Codex): add or extend the smallest adjacent runtime or state-transition seam for image derivative generation behavior, scope limit to background-image-derivative-generation only, proof target bounded worker parity for the exact background row`
