# Feature Scaffold Handoff Template

> Canonical location: `docs/agents/templates/feature-handoff.md`
> Also referenced as: `docs/agents/feature-scaffold-handoff-template.md`

Use this exact structure for every Feature Scaffolder handoff. If any section is missing, if TODOs are not code-adjacent, or if the handoff includes business logic instead of structural preparation, the handoff is invalid and the Coder must reject it.

## Required Structure

### Slice

- one-line name for the exact concrete surface inherited from the Architect handoff

### Validated Architect Handoff

- link or reference to the active Architect handoff
- confirmation that the Architect handoff matched the required template
- confirmation that the handoff covered exactly one concrete surface

### Target Files

- exact current-stack file paths where structure was prepared
- exact current-stack file paths where TODOs were added
- brief reason each file is implicated

### Structural Preparation Completed

- exact non-business-logic setup completed
- placeholder files, imports, stubs, wiring, or doc scaffolding added
- anything intentionally left untouched for the Coder

### TODOs Added

For each TODO, record:

- exact file path and location
- exact `TODO (Codex)[slice_id]: action, scope limit, proof target` text

### Proof Targets

- map each TODO to the fixture, test, shadow comparison, or verification target it is preparing for
- note any proof dependency that still needs escalation

### Doc Updates

- migration or agent docs updated because of the scaffolding
- state `none` if no docs changed

### Escalation Risks

- unresolved placement ambiguity
- dirty-tree conflicts
- contract or proof risks that block safe coding
- state `none` if no escalation risk remains

### Coder Handoff Payload

- exact next files the Coder should touch
- the first TODO batch the Coder should close
- any explicit scope limit the Coder must not cross
