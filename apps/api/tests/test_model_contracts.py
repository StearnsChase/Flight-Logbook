from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from myflightbook_api.models.media import ImageAsset, TelemetryUpload
from myflightbook_api.models.user import Identity
from myflightbook_api.schemas.profile import ProfileRead


def test_database_enum_values_use_lowercase_payload_values() -> None:
    assert Identity.__table__.c.provider.type.enums == ["google", "apple"]
    assert TelemetryUpload.__table__.c.source_format.type.enums == [
        "airbly",
        "baju",
        "csv",
        "gpx",
        "igc",
        "kml",
        "nmea",
        "unknown",
    ]
    assert TelemetryUpload.__table__.c.parse_status.type.enums == [
        "queued",
        "processing",
        "parsed",
        "processed",
        "failed",
    ]
    assert ImageAsset.__table__.c.media_type.type.enums == ["image", "pdf", "video"]


def test_profile_read_accepts_uuid_values_from_orm_objects() -> None:
    payload = SimpleNamespace(
        id=uuid4(),
        email="demo@myflightbook.local",
        display_name="Demo Pilot",
        given_name="Demo",
        family_name="Pilot",
        home_airport_code=None,
        locale="en-US",
        legacy_username=None,
    )

    profile = ProfileRead.model_validate(payload)

    assert str(profile.id) == str(payload.id)
