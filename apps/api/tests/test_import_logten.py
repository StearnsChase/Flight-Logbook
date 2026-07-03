from __future__ import annotations

from uuid import uuid4

from myflightbook_api.models.user import User
from myflightbook_api.services.importers.flights import LogTenProImporter


def test_logten_importer_parses_tsv_rows_and_creates_aircraft() -> None:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()
    importer = LogTenProImporter(user)
    file_content = """Flight_Date\tAircraft_ID\tFrom_Airport\tTo_Airport\tFlight_Total_Time\tFlight_PIC\tNight\tCross_Country\tNotes
04/20/2026\tN5LT\tKAPA\tKBJC\t1:30\t1.2\t0.2\t0.6\tLogTen import
"""

    result = importer.parse_file(file_content)

    assert result.success is True
    assert len(result.imported_flights) == 1
    flight = result.imported_flights[0]
    assert flight.aircraft.tail_number == "N5LT"
    assert flight.route == "KAPA-KBJC"
    assert float(flight.total_time) == 1.5
    assert flight.remarks == "LogTen import"
