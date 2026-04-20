from __future__ import annotations

from dataclasses import dataclass
from time import sleep

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MFB_", env_file=".env", case_sensitive=False)

    worker_queue: str = "telemetry"
    api_base_url: str = "http://127.0.0.1:8000"


@dataclass(slots=True, frozen=True)
class TelemetryParseJob:
    upload_id: str
    source_format: str
    storage_key: str


def run_once(settings: WorkerSettings) -> None:
    print(f"Polling queue '{settings.worker_queue}' against {settings.api_base_url} (stub)")


def main() -> None:
    settings = WorkerSettings()
    while True:
        run_once(settings)
        sleep(30)


if __name__ == "__main__":
    main()
