# Slice Artifact Store

This directory is the canonical persisted handoff store for repo-completion work.

## Layout

Every row uses this layout:

- `docs/migration/handoffs/<slice-id>/architect.md`
- `docs/migration/handoffs/<slice-id>/feature.md`
- `docs/migration/handoffs/<slice-id>/coder.md`

## Rules

- The parity status ledger is the source of truth for which `slice_id` is active.
- The `_template/` folder is the materialization source for new rows that do not yet have a slice folder.
- `slice_id` must match the atomic row naming rule from `parity-status-ledger.md`.
- Seeded example folders must remain valid one-surface rows. Remove or replace them when a seeded `slice_id` is no longer valid.
- Architect owns `architect.md`.
- Feature Scaffolder owns `feature.md`.
- Coder owns `coder.md`.
- Downstream roles must read the stored artifact, not chat history, as the upstream contract.

## Seeded Example Rows

- `ws-auth-token-for-user-new`
- `mvc-auth-sign-in`
- `telemetry-parser-gpx`
- `import-foreflight-conversion`
- `background-image-derivative-generation`
