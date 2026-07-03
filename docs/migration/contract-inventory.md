# Legacy Contract Inventory

This document is the canonical migration strategy, family-order document, and census source for the new platform. Use it to decide which legacy families still matter, how to stage parity work, and where the highest-risk legacy surfaces still live. For feature discussions and contract changes, use [../changes/change-intake-protocol.md](../changes/change-intake-protocol.md). For the live execution state, use [parity-status-ledger.md](parity-status-ledger.md). For the repo-wide loop that advances rows to completion, use [repo-completion-protocol.md](repo-completion-protocol.md). For the implementation workflow of a single row, use [execution-playbook.md](execution-playbook.md).

## Legacy Surfaces Discovered In The Current Repo

- SOAP/mobile API: `MyFlightbook.Web/AppCode/WebService.cs`
  - Current implementation exposes `38` `[WebMethod]` operations.
- MVC UI layer: `MyFlightbook.Web/Areas/mvc/Controllers`
  - Current implementation includes `30` controller files and a much larger action-flow surface.
- Embedded domain model inside the web application:
  - `MyFlightbook.Web/AppCode/Flights/LogbookEntry.cs`
  - `MyFlightbook.Web/AppCode/Flights/FlightQuery.cs`
  - `MyFlightbook.Web/AppCode/Flights/PendingFlight.cs`
  - `MyFlightbook.Web/AppCode/UserAccounts/Profile.cs`
- Direct SQL coupling:
  - sampled non-web libraries contain at least `84` direct `DBHelper` usages.
- Legacy database baseline:
  - `MyFlightbook.Web/Support/MinimalDB-2026-01-29.sql` defines `54` `CREATE TABLE` statements.

## Replacement Strategy

- Preserve wire-compatible behavior for legacy public and mobile contracts where current clients still depend on them.
- Replace legacy Forms Authentication and MySQL membership with OIDC-backed identity in the new stack.
- Extract behavior parity using deterministic fixtures and shadow comparisons rather than route-for-route rewrites.
- Keep legacy IDs only in dedicated mapping tables in the new database.
- Default to backend compatibility work first; add new web UI or worker behavior only when the selected row requires it.

## Contract Inventory Role In The New Loop

- This document is not the live execution ledger.
- This document defines family order, census source material, and the high-level parity factory rules.
- `parity-status-ledger.md` is the live execution state for exact rows.
- `repo-completion-protocol.md` defines how the repo moves from this family inventory to row-by-row completion.
- `docs/changes/` is the only valid entrypoint for proposing contract changes.
- Chat by itself is not a contract source.

## Contract Change Rules

- Feature discussions and contract changes must start in `docs/changes/change-intake-protocol.md`.
- Only explicitly approved changes may alter this document.
- Approved changes may:
  - add new contract families
  - change family ordering
  - refine or correct existing contract scope
- Unapproved proposals must not change this document.

## Migration Factory Rules

- The executable code backlog lives in `apps/` as inline `TODO (Codex):` comments. Workers do not stop when the current TODO batch is exhausted if the ledger still has incomplete rows.
- In this Windows workspace, the default scan command is:
  `powershell -ExecutionPolicy Bypass -File .\scripts\find-codex-todos.ps1`
- If you need a raw search outside the PowerShell helper, use:
  `rg -uu -g '!**/.venv/**' -g '!**/.next/**' -g '!**/node_modules/**' -g '!**/.pytest_cache/**' -g '!**/pytest-cache-files-*/*' -n "TODO\\s*\\(Codex\\):|TODO\\(Codex\\):" apps`
- After completing a TODO batch, remove the completed TODO comments, update the slice artifact and ledger row, update this document only if parity scope or family ordering changed through an approved change, derive the next parity gaps from the legacy repo, and write the next `TODO (Codex):` comments directly next to the intended implementation code.
- Preserve in-flight dirty work from other workers. Integrate around existing edits instead of resetting the tree.

## Current Family Order

1. Public/mobile compatibility from `MyFlightbook.Web/AppCode/WebService.cs`
   Start with auth token issuance and refresh, aircraft management, totals and currency, flight query and commit flows, telemetry path exports, and named query endpoints.
2. Core domain behavior parity
   Flights, totals and currency, aircraft, airports, geography, ratings, printing, weather, images, and telemetry must match legacy outputs via golden fixtures.
3. MVC/web parity
   Bridge the behavior covered by `MyFlightbook.Web/Areas/mvc/Controllers`, including admin and operational paths, into the new web and API layers.
4. Import/export and background processing
   Complete legacy import replay, media processing, shadow comparisons, and production background execution paths.

## Core Parity Tracks

- Telemetry parsers: `Airbly`, `Baju`, `CSV`, `GPX`, `IGC`, `KML`, `NMEA`
- Geography and route calculations
- Flight validation and totals/currency behavior
- Airport matching and visited-airport derivation
- Image and telemetry metadata handling
- Printing, ratings, and import/export behavior

## Census Expectations

The repo-completion census should:

- enumerate every current `WebService.cs` method into its own ledger row
- enumerate MVC replacement work as user-observable action-flow rows rather than whole-controller blobs
- enumerate telemetry parsers and import/export/background surfaces into atomic parity rows
- attach an initial proof class to every row before implementation starts
- leave rows `unplanned` until the Architect writes a valid stored handoff

## Fixture Collection Expectations

- Store new golden fixtures under `apps/api/tests/fixtures` by domain area.
- Track the legacy source file and observed output for every fixture.
- Record known intentional behavior changes in fixture metadata, not only in prose.
- Use shadow comparisons when a row depends on legacy calculations that are still being ported.
