from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@dataclass(slots=True)
class LegacyMySQLConfig:
    username: str
    password: str
    host: str
    database: str
    port: int = 3306

    @property
    def sqlalchemy_url(self) -> str:
        return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"


class LegacyMySQLImporter:
    """
    Thin extraction adapter around the legacy MySQL schema.

    The implementation intentionally starts with read-only extraction methods.
    Write-path reconciliation and canonical upsert orchestration belong in
    separate import jobs once mapping rules are finalized.
    """

    def __init__(self, config: LegacyMySQLConfig) -> None:
        self.config = config
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(self.config.sqlalchemy_url, future=True)
        return self._engine

    def fetch_users(self, limit: int = 1000) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT PKID, Username, Email, FirstName, LastName, timezone, prefs
            FROM users
            ORDER BY CreationDate ASC
            LIMIT :limit
            """
        )
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(query, {"limit": limit}).mappings()]

    def fetch_user(self, username: str) -> dict[str, Any] | None:
        query = text(
            """
            SELECT PKID, Username, Email, FirstName, LastName, timezone, prefs
            FROM users
            WHERE Username = :username
            LIMIT 1
            """
        )
        with self.engine.connect() as connection:
            return connection.execute(query, {"username": username}).mappings().first()

    def fetch_aircraft_for_user(self, username: str) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT ua.userName, ac.idaircraft, ac.tailnumber, ac.version, ac.PublicNotes
            FROM useraircraft ua
            INNER JOIN aircraft ac ON ac.idaircraft = ua.idAircraft
            WHERE ua.userName = :username
            ORDER BY ac.tailnumber ASC, ac.version ASC
            """
        )
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(query, {"username": username}).mappings()]

    def fetch_flights_for_user(self, username: str, limit: int = 5000) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT idFlight, date, idaircraft, Route, Comments, totalFlightTime, PIC, SIC,
                   dualReceived, cfi, crosscountry, night, IMC, simulatedInstrument,
                   cLandings, cFullStopLandings, cNightLandings, cInstrumentApproaches
            FROM flights
            WHERE username = :username
            ORDER BY date ASC, idFlight ASC
            LIMIT :limit
            """
        )
        with self.engine.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(query, {"username": username, "limit": limit}).mappings()
            ]

    def fetch_images_for_user(self, username: str, limit: int = 5000) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT VirtPathID, ImageKey, ThumbFilename, imageType, Comment, Latitude, Longitude, IsLocal
            FROM images
            WHERE ImageKey = :username
            LIMIT :limit
            """
        )
        with self.engine.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(query, {"username": username, "limit": limit}).mappings()
            ]
