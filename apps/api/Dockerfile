FROM python:3.14-slim-bookworm AS builder

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN python -m venv "$VIRTUAL_ENV"

COPY apps/api/pyproject.toml apps/api/README.md /build/apps/api/
COPY apps/api/src /build/apps/api/src

RUN pip install --upgrade pip \
    && pip install --no-cache-dir /build/apps/api


FROM python:3.14-slim-bookworm AS runtime

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /usr/sbin/nologin myflightbook

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY apps/api/alembic /app/alembic
COPY apps/api/alembic.ini /app/alembic.ini

RUN chown -R myflightbook:myflightbook /app /opt/venv

USER myflightbook

EXPOSE 8000

CMD ["gunicorn", "myflightbook_api.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
