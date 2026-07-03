# Architect Handoff Template

Use this exact structure for every Architect handoff. If any section is missing, or if the handoff covers more than one concrete source-of-truth surface, the handoff is invalid and downstream roles must reject it.

## One-Surface Rule

Each handoff may cover exactly one of the following:

- one `WebService.cs` method
- one MVC action flow
- one telemetry parser slice
- one import or export flow
- one domain behavior
- one media behavior
- one background or worker flow
- one rowized approved feature surface

Do not use this template for domain batches, multi-surface roadmaps, or loosely related clusters.

## Required Structure

### Slice

- one-line name for the exact concrete surface

### Source Of Truth

- exact legacy file path, approved change artifact path, or both
- exact method, action, parser, behavior, or approved feature surface name
- any additional evidence used from the approved evidence budget

### Originating Change

- `change_id` when the row came from `docs/changes/`
- state `none` when the row came directly from the parity census

### Approved Evidence Reviewed

- `docs/migration/contract-inventory.md`
- `docs/migration/execution-playbook.md`
- `docs/infrastructure/local-dev.md`
- current scanner output
- current `git status --short`
- the exact legacy source
- at most two directly relevant current-stack files

List the exact items actually reviewed. Do not list evidence you did not inspect.

### Current-Stack Touchpoints

- the exact current-stack file or files where the Feature Scaffolder or Coder will work
- the reason each file is implicated

### In Scope

- the exact behavior this handoff covers
- the exact output or state transitions that must match the source of truth

### Out Of Scope

- adjacent legacy behavior explicitly excluded from this handoff
- any related batch or domain work that must not be folded in

### Acceptance Criteria

- observable behavior that must be true when the slice is done
- success conditions written so the next role does not have to infer intent

### Fixtures And Proof

- required fixtures, shadow comparisons, or tests
- the exact proof target each one covers
- note any proof gap that would force escalation

### Environment

- `Windows fast path` or `full container/parity path`
- brief reason for the choice

### Escalation Risks

- specific ambiguities or blockers that could force `blocked on contract`, `blocked on environment`, or `blocked on conflicting workspace state`

### Feature Handoff Payload

- exact file location where TODOs belong
- one or more `TODO (Codex):` instructions
- each TODO must state:
  action,
  scope limit,
  proof target

## Example Skeleton

```md
## Slice
- Legacy mobile auth bootstrap response from `WebService.cs`

## Source Of Truth
- `MyFlightbook.Web/AppCode/WebService.cs`
- Method: `SomeExactMethod`

## Originating Change
- none

## Approved Evidence Reviewed
- `docs/migration/contract-inventory.md`
- `docs/migration/execution-playbook.md`
- `docs/infrastructure/local-dev.md`
- current scanner output: empty
- current `git status --short`
- legacy file: `MyFlightbook.Web/AppCode/WebService.cs`
- current-stack touchpoints reviewed:
  - `apps/api/src/...`
  - `apps/api/tests/...`

## Current-Stack Touchpoints
- `apps/api/src/...`: target compat service insertion point
- `apps/api/tests/...`: target parity test location

## In Scope
- ...

## Out Of Scope
- ...

## Acceptance Criteria
- ...

## Fixtures And Proof
- ...

## Environment
- Windows fast path: backend-only compatibility work with no Redis dependency

## Escalation Risks
- ...

## Feature Handoff Payload
- Target TODO location: `apps/api/src/...`
- `TODO (Codex): implement exact compat response, scope limit to current row only, proof target compatibility test for SomeExactMethod`
```
