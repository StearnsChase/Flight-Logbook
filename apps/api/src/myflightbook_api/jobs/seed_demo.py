from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from typing import Any

from sqlalchemy import select

from myflightbook_api.core.config import get_settings
from myflightbook_api.db.session import SessionLocal
from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.flight import Flight
from myflightbook_api.models.media import ImageAsset, MediaType, ParseStatus, TelemetryFormat, TelemetryUpload
from myflightbook_api.models.user import Identity, IdentityProvider, User

DEMO_IDENTITY_SUBJECT = "demo-google-subject"
DEMO_AIRCRAFT_TAIL = "N123MFB"
DEMO_TELEMETRY_KEY = "telemetry/demo-track.gpx"
DEMO_IMAGE_KEY = "images/demo-flight.jpg"
DEMO_FLIGHT_DATE = date(2026, 4, 17)
DEMO_ROUTE = "KAPA KBJC"


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


async def seed_demo_data(email: str) -> dict[str, Any]:
    async with SessionLocal() as session:
        user_result = await session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                display_name="Demo Pilot",
                given_name="Demo",
                family_name="Pilot",
                locale="en-US"
            )
            session.add(user)
            await session.flush()
        else:
            user.display_name = "Demo Pilot"
            user.given_name = "Demo"
            user.family_name = "Pilot"
            user.locale = "en-US"

        identity_result = await session.execute(
            select(Identity).where(
                Identity.provider == IdentityProvider.GOOGLE,
                Identity.provider_subject == DEMO_IDENTITY_SUBJECT
            )
        )
        identity = identity_result.scalar_one_or_none()
        if identity is None:
            identity = Identity(
                user=user,
                provider=IdentityProvider.GOOGLE,
                provider_subject=DEMO_IDENTITY_SUBJECT,
                email_verified=True
            )
            session.add(identity)
        else:
            identity.user = user
            identity.email_verified = True

        aircraft_result = await session.execute(
            select(Aircraft).where(
                Aircraft.owner_user_id == user.id,
                Aircraft.tail_number == DEMO_AIRCRAFT_TAIL
            )
        )
        aircraft = aircraft_result.scalar_one_or_none()
        if aircraft is None:
            aircraft = Aircraft(
                owner_user_id=user.id,
                tail_number=DEMO_AIRCRAFT_TAIL,
                display_name="MyFlightbook Demo 172",
                model_name="Cessna 172S",
                category_class="ASEL",
                engine_type="Piston",
                is_complex=False,
                is_high_performance=False,
                is_retractable=False
            )
            session.add(aircraft)
        else:
            aircraft.display_name = "MyFlightbook Demo 172"
            aircraft.model_name = "Cessna 172S"
            aircraft.category_class = "ASEL"
            aircraft.engine_type = "Piston"
            aircraft.is_complex = False
            aircraft.is_high_performance = False
            aircraft.is_retractable = False

        await session.flush()

        telemetry_result = await session.execute(
            select(TelemetryUpload).where(
                TelemetryUpload.user_id == user.id,
                TelemetryUpload.storage_key == DEMO_TELEMETRY_KEY
            )
        )
        telemetry = telemetry_result.scalar_one_or_none()
        telemetry_metadata = {"note": "demo seed upload"}
        if telemetry is None:
            telemetry = TelemetryUpload(
                user_id=user.id,
                source_format=TelemetryFormat.GPX,
                original_filename="demo-track.gpx",
                storage_key=DEMO_TELEMETRY_KEY,
                parse_status=ParseStatus.QUEUED,
                detected_departure_code="KAPA",
                detected_arrival_code="KBJC",
                metadata_json=telemetry_metadata
            )
            session.add(telemetry)
        else:
            telemetry.source_format = TelemetryFormat.GPX
            telemetry.original_filename = "demo-track.gpx"
            telemetry.parse_status = ParseStatus.QUEUED
            telemetry.detected_departure_code = "KAPA"
            telemetry.detected_arrival_code = "KBJC"
            telemetry.metadata_json = telemetry_metadata

        await session.flush()

        flight_result = await session.execute(
            select(Flight).where(
                Flight.user_id == user.id,
                Flight.aircraft_id == aircraft.id,
                Flight.flight_date == DEMO_FLIGHT_DATE,
                Flight.route == DEMO_ROUTE
            )
        )
        flight = flight_result.scalar_one_or_none()
        flight_values = {
            "user_id": user.id,
            "aircraft_id": aircraft.id,
            "telemetry_upload_id": telemetry.id,
            "flight_date": DEMO_FLIGHT_DATE,
            "route": DEMO_ROUTE,
            "remarks": "Seeded verification flight",
            "total_time": 1.4,
            "pic_time": 1.4,
            "sic_time": 0,
            "dual_given": 0,
            "dual_received": 0,
            "cross_country": 0.8,
            "night": 0,
            "imc": 0.1,
            "simulated_instrument": 0.2,
            "landings": 2,
            "full_stop_landings_day": 2,
            "full_stop_landings_night": 0,
            "approaches": 1,
        }
        if flight is None:
            flight = Flight(**flight_values)
            session.add(flight)
        else:
            for field, value in flight_values.items():
                setattr(flight, field, value)

        await session.flush()

        image_result = await session.execute(
            select(ImageAsset).where(
                ImageAsset.user_id == user.id,
                ImageAsset.storage_key == DEMO_IMAGE_KEY
            )
        )
        image = image_result.scalar_one_or_none()
        image_metadata = {"caption": "Seeded demo image"}
        if image is None:
            image = ImageAsset(
                user_id=user.id,
                flight_id=flight.id,
                storage_key=DEMO_IMAGE_KEY,
                original_filename="demo-flight.jpg",
                media_type=MediaType.IMAGE,
                metadata_json=image_metadata
            )
            session.add(image)
        else:
            image.flight_id = flight.id
            image.original_filename = "demo-flight.jpg"
            image.media_type = MediaType.IMAGE
            image.metadata_json = image_metadata

        await session.commit()

        for entity in (user, identity, aircraft, telemetry, flight, image):
            await session.refresh(entity)

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
            },
            "identity": {
                "provider": identity.provider.value,
                "provider_subject": identity.provider_subject,
            },
            "aircraft": {
                "id": aircraft.id,
                "tail_number": aircraft.tail_number,
            },
            "telemetry": {
                "id": telemetry.id,
                "storage_key": telemetry.storage_key,
            },
            "flight": {
                "id": flight.id,
                "route": flight.route,
            },
            "image": {
                "id": image.id,
                "storage_key": image.storage_key,
            },
        }


async def _main_async(email: str) -> None:
    payload = await seed_demo_data(email)
    print(json.dumps(payload, indent=2, default=_json_default))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic demo data into the canonical schema.")
    parser.add_argument("--email", default=get_settings().default_demo_email, help="Demo user email to seed.")
    args = parser.parse_args()
    asyncio.run(_main_async(args.email))


if __name__ == "__main__":
    main()
