## Slice
- `image retry and recovery behavior`

## Source Of Truth
- `MyFlightbook.Image/MFBPendingImage.cs`
- Behavior: `image retry and recovery behavior`

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
- legacy file: `MyFlightbook.Image/MFBPendingImage.cs`
- current-stack file: `apps/worker/src/myflightbook_worker/image_tasks.py`
- current-stack file: `apps/worker/src/myflightbook_worker/main.py`

## Current-Stack Touchpoints
- `apps/worker/src/myflightbook_worker/image_tasks.py`: current derivative task anchor that would participate in retries or recovery
- `apps/worker/src/myflightbook_worker/main.py`: current worker runtime and task registration seam

## In Scope
- document the exact blocker for `image retry and recovery behavior` so the row does not advance on guesswork.

## Out Of Scope
- inferring a single implementation contract from competing legacy surfaces.
- advancing this row to Feature Scaffolder before the ambiguity below is narrowed.

## Acceptance Criteria
- do not advance this row while the contract ambiguity remains unresolved.
- rewrite this blocker artifact into a valid Architect handoff only after the exact background surface is narrowed to one concrete contract.

## Fixtures And Proof
- no truthful proof path can be assigned while the contract remains ambiguous.
- if the contract is clarified later, store proof fixtures under `apps/api/tests/fixtures/background/background-image-retry-recovery/`.

## Environment
- `Full container/parity path`: the row is runtime-backed once clarified, but the current blocker is contract scope rather than environment readiness.

## Escalation Risks
- `legacy evidence for retry and recovery is split across pending-session images, SNS completion handling, and pending-video recovery paths, so advancing this row now would force a contract guess across multiple plausible background surfaces.`
- advancing now would force Feature or Coder to guess the contract, so the correct state is `blocked on contract`.

## Feature Handoff Payload
- blocked on contract: do not seed `TODO (Codex):` work for this row until Architect rewrites the slice against one concrete legacy source surface.
