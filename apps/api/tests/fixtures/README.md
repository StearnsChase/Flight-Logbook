# Parity Fixtures

Store deterministic fixtures here for golden comparisons against the legacy implementation.

Recommended layout:

- `telemetry/airbly/*`
- `telemetry/baju/*`
- `telemetry/csv/*`
- `telemetry/gpx/*`
- `telemetry/igc/*`
- `telemetry/kml/*`
- `telemetry/nmea/*`
- `totals/*`
- `airports/*`
- `validation/*`

Each fixture set should include:

1. the original legacy input payload
2. the observed legacy output snapshot
3. any notes about intentional behavior changes in the new platform
