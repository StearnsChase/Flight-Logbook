# AI Agents Documentation

This document is the entry point and dispatch rulebook for AI agents working in the Flight Logbook workspace. The goal is autonomous, parity-first delivery with strict role separation, persisted handoffs, truthful verification, and a controlled path for changing the contract.

## Role Tiers

| Tier | Who | Responsibility |
| --- | --- | --- |
| 1 | PM (you) | Approve features, direct row selection, unblock blocked rows |
| 2 | Architect | Receive PM brief, plan one row, produce decision-complete handoff |
| 3 | Feature Scaffolder | Scaffold structure from Architect handoff, plant TODOs |
| 4 | Coder | Close TODOs, run proofs, report completion state |

No autonomous agent runs above the Architect. The PM is the top tier.

## Operating Posture

- Default to the migration workspace unless the task explicitly targets the legacy reference system.
- The PM delivers input to the Architect in one of two forms:
  - **New feature or contract change**: an approved proposal at `docs/changes/proposals/<change-id>/proposal.md`, recorded in `docs/changes/approved-change-register.md`.
  - **Parity ledger work**: a short directive — "next row" or a named `slice_id`.
- Treat [`docs/changes/approved-change-register.md`](docs/changes/approved-change-register.md) as the canonical record of explicitly approved changes waiting for or already past rowization.
- Treat [`docs/migration/parity-status-ledger.md`](docs/migration/parity-status-ledger.md) as the live execution state and next-slice selector.
- Treat [`docs/migration/contract-inventory.md`](docs/migration/contract-inventory.md) as the family-order source and census source.
- Treat [`docs/agents/autonomous-execution-protocol.md`](docs/agents/autonomous-execution-protocol.md) as the canonical operating system for execution-role behavior, handoffs, escalation, verification, and completion states.
- Treat [`docs/infrastructure/local-dev.md`](docs/infrastructure/local-dev.md) as the source of truth for environment behavior.

## Launch Artifacts

Fresh sessions should start from the role launch artifact before opening the role doc:

- Architect: [`docs/agents/architect-start-prompt.md`](docs/agents/architect-start-prompt.md) and [`docs/agents/architect-handoff-template.md`](docs/agents/architect-handoff-template.md)
- Feature Scaffolder: [`docs/agents/feature-start-prompt.md`](docs/agents/feature-start-prompt.md) and [`docs/agents/feature-scaffold-handoff-template.md`](docs/agents/feature-scaffold-handoff-template.md)
- Coder: [`docs/agents/coder-start-prompt.md`](docs/agents/coder-start-prompt.md) and [`docs/agents/coder-batch-report-template.md`](docs/agents/coder-batch-report-template.md)

For PM intake guidance (structuring new features or contract changes before briefing the Architect): [`docs/agents/agent-discussion.md`](docs/agents/agent-discussion.md) and [`docs/changes/change-proposal-template.md`](docs/changes/change-proposal-template.md)

## Execution Path

1. the active role start prompt under `docs/agents/`
2. the active role doc under `docs/agents/`
3. the active role template when producing or validating a handoff or batch report
4. the PM brief or approved proposal
5. `docs/migration/parity-status-ledger.md`
6. the slice folder under `docs/migration/handoffs/<slice-id>/` when the ledger row already has one
7. the exact legacy source file, current scanner output, and current git status for the row

Before a run-to-completion handoff starts, clear known `blocked on contract` rows in scope through Discussion so the Architect receives an autonomy-ready backlog rather than repo-level ambiguity cleanup.

Execution begins only when the work is already rowized into exact ledger rows.

## Role Dispatch

- [Architect](docs/agents/agent-architect.md): receives the PM brief, selects or confirms one row, plans from a narrow evidence budget, produces the decision-complete handoff.
- [Feature Scaffolder](docs/agents/agent-feature.md): reads the Architect artifact, makes the minimum structural preparation, seeds `TODO (Codex)[slice_id]:` comments next to implementation points.
- [Coder](docs/agents/agent-coder.md): reads the slice folder, closes TODO batches, runs the smallest proving checks, records the result in the batch report.

Auto-dispatch rules:

1. If the PM has delivered an approved proposal that is not yet rowized, the Architect owns the next step.
2. If the next ledger row is `unplanned` or `architecting`, the Architect owns the work.
3. If the row is `architected` but code-adjacent TODOs or structural preparation are missing, the Feature Scaffolder owns the work.
4. If the row is `scaffolded` or has live `TODO (Codex)[...]`:` items in `apps/`, the Coder owns the next TODO batch.
5. Roles auto-advance to the next role unless an escalation trigger from the autonomous execution protocol fires.

For repo-wide autonomous completion, the PM Assistant must first resolve any known `blocked on contract` rows in scope before step 1 above is allowed to start.

## Validation Rules

- A change proposal is valid only if it matches `docs/changes/change-proposal-template.md`.
- An Architect handoff is valid only if it matches `docs/agents/architect-handoff-template.md`.
- A Feature handoff is valid only if it matches `docs/agents/feature-scaffold-handoff-template.md`.
- A Coder report is valid only if it matches `docs/agents/coder-batch-report-template.md`.
- A handoff or proposal is invalid if any required template section is missing.
- An Architect handoff is invalid if it plans more than one concrete legacy surface.
- Feature and Coder must reject invalid Architect handoffs instead of inferring the missing structure.
- Coder must reject invalid Feature handoffs instead of inferring the missing structure.

## Live State Rules

- Use the change register for approved-but-not-yet-rowized work.
- Use the parity status ledger, not the scanner alone, to decide whether the repo is complete.
- On Windows, use `powershell -ExecutionPolicy Bypass -File .\scripts\find-codex-todos.ps1` before edits, after TODO-batch completion, and before handoff.
- If the scanner fails or returns malformed output, fall back to the raw `rg` search documented in `docs/migration/contract-inventory.md`. If neither path works, report `blocked on environment`.
- Empty scanner output does not automatically mean the repo is done. If the ledger still has incomplete rows, or the change register still has approved unrowized changes, route back to the governing protocol.
- Preserve unrelated dirty-tree edits. Never reset or overwrite another worker's in-flight changes without explicit instruction.
- Report completion using the fixed completion-state vocabulary defined in the autonomous execution protocol.
- The repo is complete only when every ledger row reaches `verified complete`.

## Domain Documentation

Use these docs when shaping or executing work in the new stack:

- [PM Intake Guide](docs/agents/agent-discussion.md)
- [Approved Change Register](docs/changes/approved-change-register.md)
- [Parity Status Ledger](docs/migration/parity-status-ledger.md)
- [Legacy Contract Inventory](docs/migration/contract-inventory.md)
- [Repo Completion Protocol](docs/migration/repo-completion-protocol.md)
- [Migration Execution Playbook](docs/migration/execution-playbook.md)
- [Local Development Infrastructure](docs/infrastructure/local-dev.md)
- [Autonomous Execution Protocol](docs/agents/autonomous-execution-protocol.md)
- [Agent Team Directory](docs/agents/README.md)

## Workspace Overview

The project is operating side by side:

- Legacy reference: `MyFlightbook.*` and `MyFlightbook.Web`
- New stack: `apps/api`, `apps/web`, `apps/worker`, and `packages/api-client`

When making changes:

1. If you have a new feature or contract change, structure it as a proposal and deliver the approved version to the Architect.
2. For parity work, tell the Architect "next row" or name the `slice_id`.
3. If the change is rowized, the Architect selects the row and the triad runs from there.
4. Use the slice folder under `docs/migration/handoffs/<slice-id>/` when it exists.
5. Use the smallest environment and smallest proving check that can truthfully advance the current row.
