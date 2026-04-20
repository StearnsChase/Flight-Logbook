# MyFlightbook Worker

This package is the placeholder home for background processing that does not belong in the request path.

## Intended responsibilities

- telemetry parsing jobs
- media transcoding and thumbnail jobs
- legacy import replay batches
- parity-comparison and shadow-run orchestration

## Current state

The worker is intentionally thin in the bootstrap phase. It provides job envelope types and a polling loop stub so
queueing decisions can be made later without reworking the monorepo shape.
