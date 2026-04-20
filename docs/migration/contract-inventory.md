# Legacy Contract Inventory

This document captures the high-risk legacy surfaces that the new platform must either replace or explicitly retire.

## Legacy surfaces discovered in the current repo

- SOAP/mobile API: `MyFlightbook.Web/AppCode/WebService.cs`
  - Current implementation exposes `38` `[WebMethod]` operations.
- MVC UI layer: `MyFlightbook.Web/Areas/mvc/Controllers`
  - Current implementation includes `30` controller files.
- Embedded domain model inside the web application:
  - `MyFlightbook.Web/AppCode/Flights/LogbookEntry.cs`
  - `MyFlightbook.Web/AppCode/Flights/FlightQuery.cs`
  - `MyFlightbook.Web/AppCode/Flights/PendingFlight.cs`
  - `MyFlightbook.Web/AppCode/UserAccounts/Profile.cs`
- Direct SQL coupling:
  - sampled non-web libraries contain at least `84` direct `DBHelper` usages.
- Legacy database baseline:
  - `MyFlightbook.Web/Support/MinimalDB-2026-01-29.sql` defines `54` `CREATE TABLE` statements.

## Replacement strategy

- Do not preserve the SOAP contract in v1.
- Replace legacy Forms Authentication and MySQL membership with OIDC-backed identity in the new stack.
- Extract behavior parity using deterministic fixtures and shadow comparisons rather than route-for-route rewrites.
- Keep legacy IDs only in dedicated mapping tables in the new database.

## Core parity tracks

- Telemetry parsers: `Airbly`, `Baju`, `CSV`, `GPX`, `IGC`, `KML`, `NMEA`
- Geography and route calculations
- Flight validation and totals/currency behavior
- Airport matching and visited-airport derivation
- Image and telemetry metadata handling

## Fixture collection expectations

- Store new golden fixtures under `apps/api/tests/fixtures` by domain area.
- Track legacy source file and observed output for every fixture.
- Record known intentional behavior changes in the fixture metadata, not only in prose.
