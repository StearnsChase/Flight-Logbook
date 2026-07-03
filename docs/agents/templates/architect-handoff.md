# Architect Handoff Template

> Canonical location: `docs/agents/templates/architect-handoff.md`
> Also referenced as: `docs/agents/architect-handoff-template.md`

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

- list the exact items actually reviewed
- do not list evidence you did not inspect

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

- specific ambiguities or blockers that could force a blocked state
- state `none` if no escalation risk exists

### Feature Handoff Payload

- exact file location where TODOs belong
- one or more `TODO (Codex)[slice_id]:` instructions
- each TODO must state: action, scope limit, proof target
