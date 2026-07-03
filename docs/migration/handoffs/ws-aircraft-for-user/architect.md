## Slice
- `AircraftForUser` from `WebService.cs`

## Source Of Truth
- `MyFlightbook.Web/AppCode/WebService.cs`
- Method: `AircraftForUser`
- Additional legacy evidence used:
  - `docs/migration/repo-completion-protocol.md`
  - `docs/migration/parity-status-ledger.md`
  - `docs/migration/contract-inventory.md`
  - `MyFlightbook.AircraftSupport/Aircraft.cs` (`AircraftImages`, `PopulateImages`, `HackDisplayTailnumber`, `DefaultImage`)
  - `MyFlightbook.Image/MFBImageInfo.cs` (public image payload members)

## Originating Change
- none

## Approved Evidence Reviewed
- `docs/migration/repo-completion-protocol.md`
- `docs/migration/parity-status-ledger.md`
- `docs/changes/approved-change-register.md`
- `docs/migration/contract-inventory.md`
- `docs/migration/execution-playbook.md`
- `docs/infrastructure/local-dev.md`
- current scanner output: empty
- current `git status --short`
- legacy file: `MyFlightbook.Web/AppCode/WebService.cs` (`AircraftForUser`)
- user-approved legacy file: `MyFlightbook.AircraftSupport/Aircraft.cs`
- user-approved legacy file: `MyFlightbook.Image/MFBImageInfo.cs`
- current-stack file: `apps/api/src/myflightbook_api/services/compat/legacy_mobile.py`
- current-stack file: `apps/api/src/myflightbook_api/models/media.py`

## Current-Stack Touchpoints
- `apps/api/src/myflightbook_api/services/compat/legacy_mobile.py`: contains `LegacyAircraftContract.aircraft_for_user` and `LegacyAircraftRecord`; this is the compat-layer insertion point for `AircraftForUser` auth behavior, null-versus-empty behavior, UTC maintenance normalization, anonymous tail rewriting, and the legacy `AircraftImages` payload.
- `apps/api/src/myflightbook_api/models/media.py`: the current canonical image model is user- and flight-scoped only, so this is the exact current-stack file that determines whether `AircraftForUser` can read aircraft-scoped image metadata directly or needs the minimum compat-only linkage.

## In Scope
- preserve `GetEncryptedUser` behavior for this method boundary:
  - `null` or empty auth token raises the legacy bad-sign-in error path before any aircraft lookup.
  - a non-empty token that fails decryption returns `null` from `AircraftForUser` because `GetEncryptedUser` returns `string.Empty`.
- return the authenticated user's aircraft list and preserve the legacy `null`-enumeration to empty-array fallback before serialization.
- preserve the compat aircraft fields already modeled in `LegacyAircraftRecord` and add the legacy aircraft image payload populated by `Aircraft.PopulateImages()`.
- normalize `LastAltimeter`, `LastVOR`, `LastStatic`, `LastTransponder`, `LastAnnual`, and `LastELT` to UTC-kind timestamps in the returned payload.
- rewrite the visible tail number for anonymous aircraft to `HackDisplayTailnumber`, which keeps the anonymous prefix while remaining human-readable.
- preserve legacy aircraft-image population semantics:
  - populate `AircraftImages` from aircraft-scoped images using the aircraft id.
  - preserve default-image ordering semantics from `ImageList.Refresh(true, DefaultImage)`, so the first returned image remains the sample image.
  - expose `MFBImageInfo`-compatible members needed by legacy mobile clients: `Width`, `Height`, `WidthThumbnail`, `HeightThumbnail`, `ImageType`, `Comment`, `VirtualPath`, `ThumbnailFile`, `Location`, `URLFullImage`, and `URLThumbnail`.

## Out Of Scope
- `AddAircraftForUser`, `AircraftMatchingPrefix`, aircraft-maintenance update flows, and delete-aircraft flow.
- image deletion or annotation behavior from `DeleteImage` and `UpdateImageAnnotation`.
- broad media-model redesign beyond the minimum aircraft-image read path required for `AircraftForUser`.
- silently expanding this row to cover additional legacy `Aircraft` members beyond the compat fields already modeled in `LegacyAircraftRecord` plus the `AircraftImages` payload captured above.

## Acceptance Criteria
- `AircraftForUser` throws the legacy bad-sign-in error when the auth token is `null` or empty.
- `AircraftForUser` returns `null` when token decryption fails but the token was non-empty.
- `AircraftForUser` returns `[]` rather than `null` when the authenticated aircraft enumeration is absent.
- each returned aircraft preserves the compat-layer aircraft fields already emitted by `LegacyAircraftRecord`, normalizes the six maintenance timestamps to UTC, and rewrites anonymous tails to the human-readable `HackDisplayTailnumber` form.
- each returned aircraft includes a populated `AircraftImages` collection whose entries preserve legacy-compatible image metadata and URL fields, with default-image-first ordering.
- implementation remains backend-only for this row; no web UI or worker work is introduced.

## Fixtures And Proof
- add or extend fixture-backed tests in `apps/api/tests/test_legacy_mobile_compat.py`.
- store new golden fixtures under `apps/api/tests/fixtures/compat/legacy_mobile/aircraft/`.
- proof targets:
  - auth token `null` or empty raises the legacy bad-sign-in path for `AircraftForUser`.
  - malformed but non-empty token returns `None`.
  - empty or absent aircraft collection yields `[]`.
  - anonymous aircraft tail output uses the `#`-prefixed human-readable display form.
  - maintenance timestamps are normalized to UTC.
  - `AircraftImages` entries are populated with legacy-compatible fields and preserve default-image-first ordering.
- if the implementation path reveals additional required aircraft response members outside the modeled compat fields plus `AircraftImages`, stop and return the row to Architect instead of widening inside Coder.

## Environment
- `Windows fast path`: backend-only compatibility planning with a service-test proof target; no Redis-backed worker behavior is implicated by the selected row.

## Escalation Risks
- if another worker changes `apps/api/src/myflightbook_api/services/compat/legacy_mobile.py` or `apps/api/src/myflightbook_api/models/media.py` before scaffolding begins, re-check the slice for conflicting write scope.
- `apps/api/src/myflightbook_api/models/media.py` currently exposes only `user_id` and `flight_id` ownership for `ImageAsset`; if the Coder cannot derive an aircraft-image read path from existing media metadata or the smallest compat linkage, stop with `blocked on contract` rather than redesigning the media domain inside this row.

## Feature Handoff Payload
- Target TODO location: `apps/api/src/myflightbook_api/services/compat/legacy_mobile.py`
- `TODO (Codex): extend LegacyAircraftRecord and LegacyAircraftContract.aircraft_for_user to preserve AircraftForUser auth failure semantics, null-to-empty aircraft fallback, UTC maintenance fields, anonymous tail rewrite, and legacy AircraftImages payload ordering, scope limit to WebService.cs::AircraftForUser only, proof target fixture-backed compatibility tests for malformed auth, empty aircraft list, UTC fields, anonymous tails, and default-image-first AircraftImages`
- Target TODO location: `apps/api/src/myflightbook_api/models/media.py`
- `TODO (Codex): add the minimum aircraft-image lookup support needed for AircraftForUser to read aircraft-scoped image metadata without changing unrelated flight-image behavior, scope limit to the read path required by ws-aircraft-for-user only, proof target compatibility test returning populated legacy AircraftImages entries with URL and thumbnail metadata`
