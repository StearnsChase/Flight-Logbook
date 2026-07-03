# Change Proposal Template

Use this exact structure for every feature discussion or contract-change proposal.

## Required Structure

### Change

- stable `change_id`
- short title

### Type

- one of:
  - `parity correction`
  - `net-new feature`
  - `hybrid`

### Problem

- what is wrong, missing, or changing
- what user or business value the change provides

### Desired Behavior

- the observable behavior the repo should support after the change

### In Scope

- exact behavior included in this change

### Out Of Scope

- adjacent behavior explicitly excluded from this change

### Contract Delta

- what contract, expected behavior, or execution assumption is changing
- state `none` only if the discussion produced no contract change and should not proceed

### Affected Rows Or Families

- exact current ledger rows affected, if any
- exact contract families affected, if rowization has not happened yet

### Acceptance Criteria

- decision-complete success conditions written so the Architect does not need to infer intent

### Ledger Impact Summary

- what current rows will be modified
- what new rows are expected after rowization
- state `none` only if the proposal should not proceed into execution

### Artifact Path

- exact path to `docs/changes/proposals/<change-id>/proposal.md`

### Approval State

- one of:
  - `discussion`
  - `proposed`
  - `approved`
  - `rowized`
  - `closed`
  - `needs clarification`
  - `rejected`
  - `superseded`

### Approval Evidence

- exact human approval reference when approval exists
- state `pending explicit approval` when the proposal is still `discussion` or `proposed`

### Rowization Notes

- how the Architect should decompose the approved change into exact execution rows
- note whether the change creates new rows, modifies existing rows, or both

### Resulting Slice IDs

- exact `slice_id` values once rowization happens
- state `pending rowization` before the Architect completes that step

### Blocker Or Note

- unresolved ambiguity, dependency, or tracking note
- state `none` if no blocker or note exists

## Example Skeleton

```md
## Change
- `chg-example`
- Example change title

## Type
- `hybrid`

## Problem
- ...

## Desired Behavior
- ...

## In Scope
- ...

## Out Of Scope
- ...

## Contract Delta
- ...

## Affected Rows Or Families
- ...

## Acceptance Criteria
- ...

## Ledger Impact Summary
- ...

## Artifact Path
- `docs/changes/proposals/chg-example/proposal.md`

## Approval State
- `proposed`

## Approval Evidence
- pending explicit approval

## Rowization Notes
- ...

## Resulting Slice IDs
- pending rowization

## Blocker Or Note
- none
```
