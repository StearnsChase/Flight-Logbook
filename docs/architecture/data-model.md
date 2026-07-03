# Data Model Overview

This document describes the core entities of the Flight Logbook application, the most important legacy-to-new mappings, and the mapping-table concept the Architect must reason about when planning parity rows.

## Core Entities

### Users

- `users` stores the canonical pilot profile in the new stack.
- Key fields include email identity, display and profile fields, locale, and the optional `legacy_username`.
- One user owns many:
  - `identities`
  - `aircraft`
  - `flights`
  - `telemetry_uploads`
  - `image_assets`

### Identities

- `identities` attaches OIDC or external login subjects to a canonical user.
- The current model supports provider-scoped identities instead of legacy forms-auth membership.
- This is the main bridge from modern auth to legacy-compatible user behavior.

### Aircraft

- `aircraft` stores user-owned aircraft records.
- Key fields include tail number, display/model naming, category/class, configuration flags, maintenance timestamps, and notes.
- One aircraft belongs to one owner and can appear on many flights.

### Flights

- `flights` is the central logbook-entry table.
- Each flight belongs to one user and one aircraft.
- Key fields include route, remarks, totals, landings, approaches, and the telemetry-upload link when telemetry is attached.
- Many parity rows depend on this table because legacy behavior often computes totals, currency, printing, ratings, and exports from flight data.

### Telemetry Uploads

- `telemetry_uploads` stores the raw uploaded track reference and parse lifecycle.
- Key fields include source format, storage key, parse status, detected departure and arrival codes, and parser metadata.
- One telemetry upload can be linked to many flights over time.

### Image Assets

- `image_assets` stores user-uploaded media references.
- Each asset belongs to one user and may be attached to one flight.
- Key fields include storage key, original filename, media type, and metadata JSON.

### Airports

- `airports` stores canonical airport data and user-sourced airport records.
- Key fields include code, facility type, name, country/admin metadata, lat/long, and the optional PostGIS point geometry.

### Legacy Entity Mappings

- `legacy_entity_mappings` is the durable bridge from legacy identifiers to canonical UUID-backed entities.
- Each mapping records:
  - legacy system
  - legacy table
  - legacy identifier
  - canonical entity type
  - canonical entity ID
  - optional metadata about the mapping
- Architects should assume this table is the default place to preserve legacy IDs rather than leaking legacy identifiers into canonical tables.

## High-Value Relationships

- one `User` -> many `Aircraft`
- one `User` -> many `Flights`
- one `Aircraft` -> many `Flights`
- one `User` -> many `TelemetryUpload`
- one `TelemetryUpload` -> many `Flights`
- one `User` -> many `ImageAsset`
- one `Flight` -> many `ImageAsset`
- one legacy identifier -> one canonical entity mapping row in `legacy_entity_mappings`

## Legacy-To-New Mapping Concepts

The migration is not a table-for-table rewrite. It is a canonical-model migration with explicit legacy mapping.

### Identity Mapping

- Legacy forms-auth and MySQL membership do not move forward directly.
- The new canonical user lives in `users`.
- External login identities live in `identities`.
- Legacy usernames and legacy account references should be traced through `legacy_username` and `legacy_entity_mappings`, not through parallel auth tables.

### Logbook Entry Mapping

- Legacy logbook-entry records map into `flights`.
- Flight totals, derived status, currency impact, printing output, and export behavior may still depend on legacy field semantics even after the row is imported.
- Architects should plan parity rows assuming the table shape alone is not enough; fixture evidence is still required for observable outputs.

### Aircraft Mapping

- Legacy aircraft tables and IDs map into canonical `aircraft` records.
- Aircraft configuration flags and maintenance timestamps are part of parity behavior because they affect totals, currency, and maintenance workflows.

### Media And Telemetry Mapping

- Legacy image and telemetry references should map to `image_assets` and `telemetry_uploads`.
- Storage keys replace local filesystem assumptions, but legacy annotations, metadata, and parse-state behavior still need parity coverage.

### Airport And Geography Mapping

- Legacy airport and route-calculation behavior maps into `airports` plus service-layer logic.
- Architects should treat geography parity as a mix of canonical airport rows plus derived calculations, not as data import only.

## What The Architect Should Assume

- Canonical UUID entities live in the new tables.
- Legacy IDs belong in `legacy_entity_mappings` unless there is a clearly documented exception.
- `import-legacy.ps1` and the import jobs seed canonical entities, but they do not remove the need for row-specific parity proof.
- A parity row may depend on both:
  - table shape and relationships
  - service-layer rules that reproduce legacy calculations or formatting

## Current Sources Of Truth

- ORM models under `apps/api/src/myflightbook_api/models/`
- Alembic model imports in `apps/api/alembic/env.py`
- legacy import entrypoint in `scripts/import-legacy.ps1`
