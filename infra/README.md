# Local Runtime Helpers

`docker-compose.yml` remains available, but this workspace is now designed to run without Docker on this machine.

## MinIO

1. Place the official Windows `minio.exe` binary at `.tools/minio/minio.exe`.
2. Run `infra/start-minio.ps1`.
3. The script serves data from `infra/minio-data` and uses the credentials already defined in the API and web `.env` files.

## PostgreSQL/PostGIS

Install PostgreSQL 16 locally with PostGIS enabled, then create:

- database: `myflightbook`
- user: `myflightbook`
- password: `myflightbook`

After installation, use the API `.env` and Alembic commands from `apps/api`.
