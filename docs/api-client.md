# API Client

`packages/api-client` is the shared TypeScript contract package between the Next.js frontend and the FastAPI backend.

## Purpose

- keep frontend calls aligned with the actual API surface
- generate types from FastAPI OpenAPI where possible
- expose typed helpers that the web app can consume without re-declaring backend contracts

## Usage

Import methods and types from `@myflightbook/api-client`:

```typescript
import { getFlights, type Flight } from "@myflightbook/api-client";

const flights = await getFlights();
```

## Updating The Client

When a migration slice changes the backend contract:

1. stabilize the FastAPI route, schema, and response shape first
2. regenerate or update the client package
3. run the relevant frontend checks so the web app stays aligned

From the repo root:

- generate OpenAPI types:
  `npm run generate:client`

From the package directly:

- generate OpenAPI types:
  `npm run generate`
