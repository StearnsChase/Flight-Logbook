# MyFlightbook Worker

This package handles background processing that does not belong on the request path.

## Intended Responsibilities

- telemetry parsing jobs
- media transcoding and thumbnail jobs
- legacy import replay batches
- parity-comparison and shadow-run orchestration when a slice needs async execution

## Current Runtime

The current worker implementation uses:

- `arq` as the worker runtime
- Redis as the broker
- Postgres for persisted state transitions
- S3-compatible storage for media and telemetry files

Current tasks include:

- `process_telemetry`, which moves uploads through processing states
- `generate_thumbnails`, which creates `_thumb.jpg` and `_web.jpg` variants and uploads them back to storage

## Local Startup

### Full Parity Path

Use:

`docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker`

This is the normal way to run the worker locally.

### Manual Startup

If backing services are already running, start the worker with:

`python -m myflightbook_worker.main`

The Windows fast path in `dev-up.ps1` does not start Redis or the worker.
