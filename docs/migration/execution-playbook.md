# Migration Execution Playbook

This is the canonical workflow for advancing one ledger row. Use it together with [repo-completion-protocol.md](repo-completion-protocol.md) and [parity-status-ledger.md](parity-status-ledger.md): the repo-completion protocol tells you how the triad keeps moving until the repo is done, the ledger tells you which exact row is next, and this playbook tells you how to stage and deliver that one row.

## Core Rule

The unit of work is not "build a new feature from scratch." The unit of work is "replace one exact ledger row with verified new-stack behavior."

## Role Ownership

- **Architect:** steps 1 through 3
- **Feature Scaffolder:** step 4
- **Coder:** steps 5 through 9

Automatic handoff behavior, escalation triggers, and completion states are defined in the autonomous execution protocol. Repo-wide row selection and ledger advancement are defined in the repo-completion protocol.

## Standard Row Workflow

### 1. Architect: Select Exactly One Ledger Row

- check for approved unrowized changes before normal row selection
- if an approved change is waiting, rowize it first
- otherwise pick the next incomplete row from `parity-status-ledger.md`
- confirm the exact source of truth, such as a `WebService.cs` method, an MVC action flow, a telemetry parser, an import/export behavior, a domain behavior, a media behavior, a background flow, or an approved feature artifact
- do not plan more than one concrete surface in the same handoff
- state what success looks like in observable behavior

### 2. Architect: Review Only The Approved Evidence Budget

- review only the approved evidence budget defined in `docs/agents/agent-architect.md`
- record representative inputs and outputs from the source of truth
- identify at most two directly relevant current-stack insertion points
- if clarity is still missing after this evidence budget is exhausted, return `blocked on contract`

### 3. Architect: Produce The Stored Handoff Artifact

- fill out `docs/migration/handoffs/<slice-id>/architect.md` using `docs/agents/architect-handoff-template.md`
- identify required legacy IDs and mapping-table needs
- identify auth, profile, aircraft, totals, geography, media, import, or worker dependencies
- confirm whether the row is backend-only, web-facing, or worker-backed
- choose the right local environment from `docs/infrastructure/local-dev.md`
- if the template cannot be completed truthfully, escalate instead of widening the search

### 4. Feature Scaffolder: Prepare Structure And Seed TODOs

- create the minimum structural changes needed across `apps/api`, `apps/web`, `apps/worker`, or `packages/api-client`
- write precise inline `TODO (Codex):` items next to the exact implementation points
- store the scaffold handoff at `docs/migration/handoffs/<slice-id>/feature.md`
- if the live scanner is empty but the row is not actually done, seed the next TODO batch instead of treating the backlog as complete

### 5. Coder: Implement Backend Compatibility First

- add or extend models, schemas, services, and `api/routes` in `apps/api`
- keep compatibility behavior in the backend even when the eventual consumer is a web UI
- keep route handlers thin and push calculations into services

### 6. Coder: Update The Shared Client

- update `packages/api-client` only after the backend contract is stable
- regenerate OpenAPI types when the API surface changed
- keep the generated client aligned with the actual FastAPI contract

### 7. Coder: Add UI Only If The Row Needs It

- update `apps/web` only when the selected row has a real user-facing flow in the new stack
- do not invent UI work for a backend-only compatibility row

### 8. Coder: Add Worker Behavior Only If The Row Needs Async Execution

- use `apps/worker` for telemetry, media, or retryable background work
- do not push synchronous parity logic into the worker prematurely

### 9. Coder: Verify, Persist, And Advance

- run the row-specific parity gates from `docs/testing.md`
- remove completed `TODO (Codex):` comments
- store the batch report in `docs/migration/handoffs/<slice-id>/coder.md`
- set the completion state defined in the autonomous execution protocol
- update `parity-status-ledger.md` with the new row status, owner, and blocker or note field
- re-run the live scanner and either continue the next TODO batch or hand off to the next role

If the scanner fails or returns malformed output:

- run the raw `rg` fallback documented in `docs/migration/contract-inventory.md`
- if the fallback also fails, report `blocked on environment`

## Acceptance Checklist

Before closing a row, confirm:

1. the ledger row was named explicitly
2. the legacy source of truth was named explicitly
3. the stored Architect handoff matches the fixed template and covers exactly one concrete surface
4. fixtures or comparison evidence were captured before implementation
5. backend behavior matches the expected contract
6. the typed client was updated only if the API changed
7. UI work was added only if required
8. worker work was added only if required
9. the parity tests or fixtures that prove the row now exist
10. the row state in the ledger matches the stored handoff or report

## Sample Row Patterns

### Legacy Mobile Auth Compatibility

- source of truth: `MyFlightbook.Web/AppCode/WebService.cs`
- likely work: auth compatibility services, request and response schemas, route wiring, token issuance behavior, parity tests
- expected proof: compatibility tests covering success, invalid credentials, expired state, and any legacy-specific response fields

### Telemetry Parser Addition

- source of truth: legacy telemetry parser behavior and supported import format
- likely work: parser implementation, registry update, upload status handling, fixtures, and parser tests
- expected proof: parser fixture coverage plus registry tests confirming the new format is wired correctly

### MVC Parity Slice

- source of truth: a controller flow under `MyFlightbook.Web/Areas/mvc/Controllers`
- likely work: backend service behavior first, then typed client updates, then any required `apps/web` route or component work
- expected proof: service and route tests, UI coverage only for the new-stack flow that replaces the controller behavior
