# Deployment Guide

This document defines the minimum deployment contract for the new Flight Logbook stack. It is intentionally concrete enough for rollout planning, even though the repo is still in migration.

## Target Runtime Topology

- **Frontend (`apps/web`)**
  - Next.js App Router deployment
  - serves the user-facing web surface
  - consumes the typed API client generated from the FastAPI contract
- **Backend (`apps/api`)**
  - FastAPI application
  - owns HTTP API behavior, OIDC-backed auth integration, and canonical business services
- **Worker (`apps/worker`)**
  - long-running `arq` worker process
  - owns retryable telemetry, media, and other background jobs
- **Database**
  - managed PostgreSQL instance for canonical entities and legacy mapping tables
- **Redis**
  - required for `arq` queues, worker scheduling, and Redis-backed async flows
- **Object storage**
  - S3-compatible object storage in production
  - replaces local MinIO used in development

## Required Services

Every non-local deployment must provide:

- one web runtime for `apps/web`
- one API runtime for `apps/api`
- one worker runtime for `apps/worker`
- PostgreSQL
- Redis
- S3-compatible object storage

The deployment is incomplete if any row that depends on worker-backed behavior is promoted without Redis and the worker runtime available.

## Environment Ownership

Environment variables must be owned by subsystem:

- **Web**
  - frontend-safe public variables only
  - API base URL and browser-facing runtime configuration
- **API**
  - database URL
  - OIDC and auth configuration
  - Redis URL when API behavior enqueues background work
  - S3 or MinIO endpoint, bucket, and credentials
- **Worker**
  - database URL
  - Redis URL
  - S3 or MinIO endpoint, bucket, and credentials
  - any task-specific processing configuration

Rules:

- the worker and API must point at the same PostgreSQL, Redis, and object-storage environment
- the web app must never own secrets that belong only to API or worker
- production credentials must not be shared through development `.env` defaults

## CI/CD Gates

The minimum release contract is:

- install dependencies successfully
- build `packages/api-client`
- build `apps/web`
- run the smallest relevant API and web test suites for changed scope
- run worker tests when the change touches async behavior
- reject releases that leave contract-shape drift between API and generated client

Recommended release stages:

1. validate dependencies and environment
2. run targeted tests
3. build API image or artifact
4. build worker image or artifact
5. build web artifact
6. promote only after required checks pass

## Deploy-Time Verification Expectations

After deployment, verify at minimum:

- the web app serves and can reach the API
- the API can connect to PostgreSQL
- the API can reach Redis when queue-backed behavior exists
- the worker can consume queued jobs
- object storage is writable for telemetry and media flows
- auth flows use the expected OIDC configuration

Parity-sensitive releases should also verify the smallest row-specific proof that matches the changed scope.

## Coordination Rules

- Do not deploy `apps/worker` independently of Redis availability.
- Do not deploy API changes that alter the contract without regenerating and deploying the matching `packages/api-client` consumer.
- Do not mark worker-backed rows `verified complete` in production planning unless API, worker, Redis, and object storage are all represented in the target environment.
- Treat the full deployment as a coordinated web + API + worker system, not as three unrelated services.

## Current Local-To-Deployment Mapping

- local PostgreSQL service or container -> managed PostgreSQL
- local MinIO -> production S3-compatible storage
- local Redis container -> production Redis
- local FastAPI dev server -> API runtime
- local Next.js dev server -> web runtime
- local `arq` worker process -> worker runtime
