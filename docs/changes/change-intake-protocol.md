# Change Intake Protocol

This document is the canonical workflow for feature conversations and contract changes. It sits upstream of the Architect, Feature Scaffolder, and Coder roles.

## Mission

Turn feature discussions into decision-complete, approval-gated change proposals that can safely alter the contract and feed the execution system.

Core rule:

- discussion does not mutate execution state
- only explicitly approved changes may alter `contract-inventory.md`, `parity-status-ledger.md`, or in-flight row definitions

## Canonical Sources

- `change-proposal-template.md`: required proposal shape
- `approved-change-register.md`: record of explicitly approved changes
- `proposals/<change-id>/proposal.md`: working proposal artifact
- `../migration/contract-inventory.md`: current contract families and census source
- `../migration/parity-status-ledger.md`: current execution rows and live execution state
- `../migration/repo-completion-protocol.md`: rowization and execution loop after approval

## Change Types

Every proposal must classify the change as one of:

- `parity correction`
- `net-new feature`
- `hybrid`

## Naming Rules

- `change_id` must use `chg-<kebab-case>`
- `slice_id` must use `<family>-<single-workflow-kebab-case>`
- one change may link to multiple `slice_id` values after rowization, but every linked slice must be recorded explicitly

## Change Lifecycle

Use this lifecycle for every change:

`discussion` -> `proposed` -> `approved` -> `rowized` -> `closed`

Available non-terminal exceptions:

- `needs clarification`
- `rejected`
- `superseded`

State meanings:

- `discussion`: the request is still being shaped
- `proposed`: the proposal is decision-complete and waiting for explicit human approval
- `approved`: explicit human approval was given and the change was recorded in the approved change register
- `rowized`: the Architect decomposed the approved change into exact execution rows and recorded the resulting `slice_id` values
- `closed`: all resulting execution rows reached `verified complete`, or the approved change was otherwise fully resolved

Lifecycle ownership:

- Discussion owns `discussion -> proposed -> approved`
- Architect owns `approved -> rowized`
- the role that lands the final linked row at `verified complete` closes the change to `closed`

## Required Change Fields

Every change must have at least:

- `change_id`
- title
- change type
- problem statement and user value
- affected contract families or current rows
- approval state
- contract delta summary
- ledger impact summary
- artifact path
- blocker or note field

## Discussion Workflow

1. Ground the request in the current repo state.
   Read the contract inventory, parity ledger, and repo-completion protocol before making claims.
2. Create or update `docs/changes/proposals/<change-id>/proposal.md`.
3. Classify the request as parity correction, net-new feature, or hybrid.
4. Produce a decision-complete proposal using the fixed template.
5. Stop at `proposed` until explicit human approval is given.

Discussion-phase rules:

- do not update `contract-inventory.md`
- do not update `parity-status-ledger.md`
- do not create or alter `docs/migration/handoffs/<slice-id>/` except to append `## Contract Resolution` notes to existing blocked slice artifacts
- do not let downstream execution roles infer the change from chat

## Run-To-Completion Readiness

Some PM requests are not asking for a single feature discussion. They are asking for a scoped autonomous pass: talk to Discussion once, then let `Architect -> Feature Scaffolder -> Coder` continue until the scoped work is complete.

Before Discussion hands off a run-to-completion scope to the Architect:

1. inspect `../migration/parity-status-ledger.md` for `blocked on contract` rows in the requested scope
2. read the matching blocked slice artifacts
3. get explicit human decisions for each blocking ambiguity
4. append those decisions under `## Contract Resolution` in the blocked slice artifacts
5. persist any resulting contract change through the approved change register and approved proposal artifacts when required
6. confirm that no known contract blocker remains unresolved in the requested scope

Rules:

- known blocked rows must be resolved in Discussion before a run-to-completion handoff starts
- Discussion may append contract-resolution notes to blocked slice artifacts, but it still must not create Architect handoffs
- if the PM declines to resolve a blocked row, the run-to-completion handoff must stop short of that scope instead of implying autonomous completion

## Approval And Persistence Workflow

Once a change is explicitly approved:

1. update the proposal approval state to `approved`
2. add or update the change in `approved-change-register.md`
3. update `contract-inventory.md` only if family scope, ordering, or contract surface changes
4. hand the approved change to the Architect for rowization
5. stop discussion work after the approved state is persisted

Approval rules:

- approval must be explicit
- conversational agreement is not approval
- unapproved proposals must not mutate contract or ledger state

## Rowization Rules

Approved changes do not go straight to coding.

The Architect must:

- decompose approved changes into one-surface execution rows
- create or alter rows in `parity-status-ledger.md`
- create or update `docs/migration/handoffs/<slice-id>/` only after the change is rowized into exact execution rows
- write the `change_id` back into the proposal, the approved change register, the ledger note field for every affected row, and the slice artifact for rows created from the change

Rowization behavior by change type:

- `net-new feature`: create new ledger rows
- `parity correction`: modify existing rows or add missing rows
- `hybrid`: modify existing rows and add new rows as needed

If an approved change alters an in-progress row:

- return that row to Architect ownership
- do not let Feature or Coder silently reinterpret the row
- record the originating `change_id` in the ledger note field or matching slice artifact note

If an approved change resolves a previously blocked row:

- append the explicit resolution under `## Contract Resolution` in the blocked slice artifact
- keep the row blocked until the resolution note exists
- hand the row back to Architect only after the resolution is persisted

## Completion Rules

A change may move to `closed` only when:

- every row created or altered by that change reaches `verified complete`, or
- the approved change is intentionally resolved by explicit rejection or supersession handling

Anything short of that remains active change work.
