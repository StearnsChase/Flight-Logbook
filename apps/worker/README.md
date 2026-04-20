# MyFlightbook Worker

This package is the background-processing home for work that does not belong in the request path.

## Intended responsibilities

- telemetry parsing jobs
- media transcoding and thumbnail jobs
- legacy import replay batches
- parity-comparison and shadow-run orchestration

## Current state

The foundational scaffold uses `arq` with Redis as the broker:

- async worker runtime that matches the FastAPI/SQLAlchemy stack
- Redis-backed queue for telemetry and media jobs
- a dummy `process_telemetry` task that marks an upload `processing`, sleeps for two seconds, and then marks it `processed`
- a `generate_thumbnails` media task that downloads an image from S3-compatible storage, writes `_thumb.jpg` and `_web.jpg` variants, and uploads them back to the bucket

## Running locally

1. Install the package in a virtualenv with `pip install -e .`.
2. Ensure PostgreSQL, Redis, and the S3-compatible bucket are reachable using the values in `.env`.
3. Start the worker with `python -m myflightbook_worker.main`.
