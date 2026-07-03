# Local Development Infrastructure

This document is the source of truth for how local environments behave in this repo. Use it to decide which startup mode to use, what each command actually starts, and how to shut it back down safely.

## Environment Matrix

| Mode | Command | Requires | Starts | Does not start |
| --- | --- | --- | --- | --- |
| Windows fast path | `powershell -ExecutionPolicy Bypass -File .\scripts\dev-up.ps1 -Seed` | `apps/api/.venv`, `npm.cmd`, valid `apps/api/.env`, PostgreSQL 16 service or external DB | Alembic migration, local Postgres service if present, MinIO, API, web, demo seed | Redis, worker, Docker services |
| Full container/parity path | `docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker` | Docker runtime, valid environment values for API and worker | Postgres, Redis, MinIO, worker | API, web, demo seed |

## Windows Fast Path

Use this mode for normal API and web iteration on Windows.

### What `dev-up.ps1` Does

- ensures `apps/api/.env` and `apps/web/.env.local` exist by copying from examples when needed
- starts the PostgreSQL 16 Windows service if it exists and is stopped
- runs `alembic upgrade head` from `apps/api`
- starts MinIO through `infra/start-minio.ps1`
- starts the FastAPI app on `http://127.0.0.1:8000`
- starts the Next.js app on `http://127.0.0.1:3000`
- optionally runs `dev-seed.ps1` when `-Seed` is supplied

### What It Does Not Do

- it does not start Redis
- it does not start the worker
- it does not start Docker services

### Shutdown

Use:

`powershell -ExecutionPolicy Bypass -File .\scripts\dev-down.ps1`

This stops only the API, web, and MinIO processes launched from this repo. It does not stop the PostgreSQL Windows service.

## Full Container/Parity Path

Use this mode when the slice touches Redis-backed worker behavior or you need the full backing-service set for parity work.

### Bring Up Backing Services And Worker

Use:

`docker compose -f .\infra\docker-compose.yml up -d postgres redis minio worker`

This starts:

- Postgres on `localhost:5432`
- Redis on `localhost:6379`
- MinIO on `localhost:9000` and `localhost:9001`
- the worker process using `python -m myflightbook_worker.main`

### Start API And Web Separately

The compose file does not start the API or the web app. Start them separately:

- API:
  `.\apps\api\.venv\Scripts\python.exe -m uvicorn myflightbook_api.main:app --host 127.0.0.1 --port 8000`
- Web:
  `npm run dev --workspace @myflightbook/web -- --hostname 127.0.0.1`

### Shutdown

Use:

`docker compose -f .\infra\docker-compose.yml down`

## Common Issues

### Database Connection Failures

- Ensure `apps/api/.env` points at the database you actually started.
- When using the Windows fast path, ensure PostgreSQL 16 is installed or that `apps/api/.env` targets an already running external database.
- When using the full container path, confirm port `5432` is available and the `postgres` container is healthy.

### Redis And Worker Issues

- The worker expects `MFB_REDIS_URL` to resolve to a reachable Redis instance.
- If a task depends on Redis-backed behavior, do not use the Windows fast path alone.
- Check `infra/docker-compose.yml` for the expected queue and environment values when validating worker flows.

### MinIO Issues

- In the Windows fast path, `infra/start-minio.ps1` is responsible for starting MinIO and creating the expected buckets.
- In the full container path, MinIO is provided by Docker compose and does not need the PowerShell bootstrap.

### Re-Seeding Data

If your database gets into a bad state, re-run:

`powershell -ExecutionPolicy Bypass -File .\scripts\dev-seed.ps1`
