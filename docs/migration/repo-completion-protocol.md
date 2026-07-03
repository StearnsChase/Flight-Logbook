# Repo Completion Protocol

This document is the canonical coordination layer above the Architect, Feature Scaffolder, and Coder. It tells the repo how to move from current state to full contract completion without relying on chat history or ad hoc reseeding.

## Mission

Drive the repo from a seeded parity census to `verified complete` across every tracked row.

Strict repo rule:

- the repo is complete only when every row in `parity-status-ledger.md` reaches `verified complete`
- blocked rows remain visible and keep the repo incomplete
- only approved and rowized changes may enter or alter the execution ledger

## Canonical Sources

- `../changes/change-intake-protocol.md`: upstream change discussion, approval, and rowization rules
- `../changes/approved-change-register.md`: explicitly approved changes awaiting or already past rowization
- `contract-inventory.md`: family-order source and census source
- `parity-status-ledger.md`: live execution state
- `execution-playbook.md`: exact workflow for one row
- `docs/agents/autonomous-execution-protocol.md`: role-specific execution, validation, escalation, and completion-state rules
- `docs/migration/handoffs/<slice-id>/`: persisted slice artifacts for the active or previously advanced rows

## Approved Change Gate

Before selecting the next ledger row, check the approved change register.

Rules:

- proposed or discussion-state changes must not mutate execution state
- approved changes may update the contract inventory and approved change register
- only rowized changes may create or alter ledger rows
- the Architect owns rowization of approved changes
- rowization must write `change_id` back into the proposal, approved change register, ledger note field, and slice artifact for every affected row

If an approved change alters an in-progress row:

- return that row to Architect ownership
- do not let Feature or Coder silently reinterpret the row
- record the originating `change_id` in the ledger note field or matching slice artifact note

## Autonomous Run Readiness Gate

The normal row loop can continue while the repo still has future work. A run-to-completion handoff is stricter.

A scoped autonomous pass is valid only when all of these are true inside the requested scope:

- no approved changes remain unrowized
- no row remains `blocked on contract`
- every previously blocked row has an explicit `## Contract Resolution` note in its slice artifact, or has been explicitly removed or reshaped through an approved change path
- the requested scope is clear enough that `verified complete` has an objective meaning at the end of the pass

Rules:

- known contract blockers are Discussion work before the run begins, not active Architect work during the run
- Architect may still discover a new ambiguity while planning a row; that removes autonomy-ready status for the scope until Discussion resolves it
- if the PM wants repo-wide completion, the gate applies to the whole ledger, not just the next row

## Repo-Wide Execution Loop

1. Run the non-optional census first.
   Use `contract-inventory.md`, the legacy source tree, and the current repo layout to seed `parity-status-ledger.md`.
2. Check for approved unrowized changes.
   If the approved change register contains a change that is not yet rowized, the Architect rowizes that change before normal row execution continues.
3. Check run scope readiness when autonomous completion is expected.
   If the requested scope still contains `blocked on contract` rows or unresolved contract-resolution notes, route back to Discussion instead of starting another triad pass that cannot reach terminal completion.
4. Select the next incomplete row.
   Prefer the highest-priority incomplete row in the current family order unless the ledger explicitly points to an already-active row.
5. Materialize or open the slice folder.
   The canonical path is `docs/migration/handoffs/<slice-id>/`.
6. Run the triad.
   Architect -> Feature Scaffolder -> Coder.
7. Re-scan live code state.
   Use `powershell -ExecutionPolicy Bypass -File .\scripts\find-codex-todos.ps1`.
8. Update persisted state.
   Update the slice folder artifact and the matching ledger row.
9. Decide the next owner.
   Continue the same row if live TODOs remain, route back to Architect or Feature if the row needs new planning or reseeding, or advance to the next incomplete row if the current row is `verified complete`.
10. Continue until no incomplete rows remain.

## Non-Optional Census Phase

Before normal autonomous execution can claim repo-wide progress, the repo must have a seeded ledger.

The census must:

- enumerate every `WebService.cs` method into its own row
- enumerate MVC replacement work as user-observable action-flow rows rather than whole-controller blobs
- enumerate telemetry parsers and import/export/background surfaces into atomic parity rows
- attach an initial proof class to every row
- leave rows `unplanned` until the Architect writes a valid stored handoff

Hard validity rules during recensus:

- any row naming multiple controllers is invalid and must be split
- any row naming multiple workflows joined by `and` is invalid and must be split
- any row that cannot map cleanly to one slice folder is invalid and must be split

## Ledger Rules

`parity-status-ledger.md` is the live source of truth for repo progress.

Each row must carry at least:

- `slice_id`
- contract family
- exact legacy source
- current status
- current owner
- environment path
- proof target
- handoff artifact path
- blocker or note field

Naming rules:

- `slice_id` must use `<family>-<single-workflow-kebab-case>`
- every row sourced from an approved change must record the originating `change_id` in its note field and slice artifact

The fixed status pipeline is:

`unplanned` -> `architecting` -> `architected` -> `scaffolding` -> `scaffolded` -> `coding` -> `implemented pending verification` -> `verified complete`

Available non-terminal blocked states:

- `blocked on environment`
- `blocked on contract`
- `blocked on conflicting workspace state`

## Slice Artifact Store

The canonical storage convention is:

- `docs/migration/handoffs/<slice-id>/architect.md`
- `docs/migration/handoffs/<slice-id>/feature.md`
- `docs/migration/handoffs/<slice-id>/coder.md`

Rules:

- every active row must have a materialized slice folder
- the `_template/` folder under `docs/migration/handoffs/` is the materialization source for newly selected rows
- the ledger must point directly to the slice folder path
- downstream roles must use the stored artifact, not chat history, as their upstream contract

## Repo-Level Ownership Rules

- Discussion shapes changes and stops at `proposed` until explicit human approval
- Discussion also clears known contract blockers before a run-to-completion handoff by appending explicit `## Contract Resolution` notes to blocked slice artifacts when the human makes the decision
- Architect rowizes approved changes, selects or confirms the next ledger row, creates or updates `architect.md`, and moves the row into `architected` when the handoff is valid
- Feature Scaffolder reads `architect.md`, produces `feature.md`, seeds code-adjacent TODOs, and moves the row into `scaffolded` when the handoff is valid
- Coder reads the slice folder, closes one TODO batch at a time, produces or updates `coder.md`, and advances the row through coding and verification states

## Scanner-Empty Rule

Empty scanner output does not mean the repo is done.

If the scanner fails or returns malformed output:

- use the raw `rg` fallback documented in `docs/migration/contract-inventory.md`
- if the fallback also fails, report `blocked on environment`

When the scanner is empty:

- if the current row is not `verified complete`, route back to Architect or Feature and reseed that row
- if the current row is `verified complete` but the ledger still has incomplete rows, move to the next incomplete row
- if the ledger has no incomplete rows but the approved change register still has approved unrowized changes, route back to Architect
- only treat the scanner as a terminal signal when the ledger itself has no incomplete rows and the approved change register has no approved unrowized changes

## Repo Terminal Conditions

The repo is complete only when:

- every ledger row is present
- every ledger row has a materialized or historically stored slice artifact path
- every ledger row is `verified complete`
- no blocked rows remain
- no approved changes remain unrowized

Anything short of that is in-progress work, even if the scanner is empty.
