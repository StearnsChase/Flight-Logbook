from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from myflightbook_api.models.flight import Flight
from myflightbook_api.models.user import User
from myflightbook_api.services.printing.pdf_generator import LogbookPDFGenerator, PrintOptions


def _flight(*, flight_date: date, total_time: str, pic_time: str, cross_country: str = "0.0") -> Flight:
    return Flight(
        user_id=str(uuid4()),
        aircraft_id=str(uuid4()),
        flight_date=flight_date,
        route="KAPA-KBJC",
        total_time=Decimal(total_time),
        pic_time=Decimal(pic_time),
        cross_country=Decimal(cross_country),
        landings=1,
    )


def test_calculate_page_subtotals_tracks_amount_forward() -> None:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()
    generator = LogbookPDFGenerator(
        user=user,
        flights=[
            _flight(flight_date=date(2026, 4, 20), total_time="1.2", pic_time="1.2", cross_country="0.8"),
            _flight(flight_date=date(2026, 4, 21), total_time="2.0", pic_time="1.8", cross_country="1.2"),
        ],
        options=PrintOptions(flights_per_page=1),
    )

    subtotals = generator._calculate_page_subtotals()

    assert len(subtotals) == 2
    assert subtotals[0]["total_time"] == 1.2
    assert subtotals[1]["amount_forward_total_time"] == 1.2


@pytest.mark.asyncio
async def test_render_pdf_to_bytes_returns_pdf_document() -> None:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()
    generator = LogbookPDFGenerator(
        user=user,
        flights=[_flight(flight_date=date(2026, 4, 20), total_time="1.2", pic_time="1.2", cross_country="0.8")],
        options=PrintOptions(),
    )

    html_template = generator.generate_html_template()
    pdf_bytes = await generator.render_pdf_to_bytes()

    assert "KAPA-KBJC" in html_template
    assert pdf_bytes.startswith(b"%PDF")

