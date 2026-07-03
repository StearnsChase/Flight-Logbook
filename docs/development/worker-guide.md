# Worker Development Guide

This guide covers the actual background worker implementation in `apps/worker`.

## Current Runtime

- language: Python
- queue runtime: `arq`
- broker: Redis
- default queue name: `telemetry`
- entrypoint: `python -m myflightbook_worker.main`

The worker is responsible for long-running or retriable tasks that should not block request handling, such as telemetry parsing and media processing.

## When To Use The Worker

Use the worker only when the selected parity slice requires async processing or external I/O that should be retried. Do not move behavior into the worker just because the repo has a worker package.

Typical uses:

- telemetry parsing that should run out of band
- image resizing or thumbnail generation
- import replay or shadow-run batches that are operationally expensive

## Running Locally

### Full Parity Path

This is the normal worker environment:

`docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker`

This starts Redis, MinIO, Postgres, and the worker.

### Manual Worker Start

If the backing services are already running, start the worker manually with:

`.\apps\api\.venv\Scripts\python.exe -m myflightbook_worker.main`

or from the worker package environment:

`python -m myflightbook_worker.main`

The Windows fast path in `dev-up.ps1` does not start Redis or the worker.

## Defining New Tasks

1. Add the task function under `src/myflightbook_worker/`.
2. Keep the task idempotent so retries are safe.
3. Ensure the API or service layer enqueues the task intentionally rather than hiding contract logic inside background execution.
4. If the task updates persisted state, define the state transitions explicitly and test failure handling.

## Testing

- keep unit tests in `apps/worker/tests/`
- mock Redis, storage, and database dependencies where possible
- add slice-specific verification when a task is part of parity behavior
- if the task is tied to a telemetry or media parity slice, ensure the backend parity tests and worker tests agree on the expected state transitions
