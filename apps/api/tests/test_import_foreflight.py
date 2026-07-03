from __future__ import annotations

from uuid import uuid4

from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.user import User
from myflightbook_api.services.importers.flights import ForeFlightImporter


def test_foreflight_importer_parses_csv_rows() -> None:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()
    aircraft = Aircraft(owner_user_id=user.id, tail_number="N123FF", display_name="N123FF")
    aircraft.id = uuid4()
    importer = ForeFlightImporter(user, existing_aircraft=[aircraft])
    file_content = """Date,AircraftID,From,To,TotalTime,PIC,SIC,Night,CrossCountry,AllLandings,DayLandingsFullStop,NightLandingsFullStop,Approaches,TextCFINotes
2026-04-20,N123FF,KDEN,KAPA,1.5,1.2,0.3,0.1,0.8,2,2,0,1,ForeFlight import
"""

    result = importer.parse_file(file_content)

    assert result.success is True
    assert result.skipped_rows == 0
    assert len(result.imported_flights) == 1
    flight = result.imported_flights[0]
    assert flight.aircraft_id == aircraft.id
    assert flight.route == "KDEN-KAPA"
    assert float(flight.total_time) == 1.5
    assert flight.remarks == "ForeFlight import"
