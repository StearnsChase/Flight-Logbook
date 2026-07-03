# Frontend Development Guide

This guide covers the Next.js frontend in `apps/web`.

## Role In The Migration

The frontend is not the default first step for every slice. In this repo, backend compatibility and fixture work usually come first. Update the frontend only when the selected legacy surface requires a new-stack user flow.

## Technology Stack

- Next.js App Router
- TypeScript
- shared `@myflightbook/api-client` package for backend calls

## Running Locally

Preferred commands:

- from the repo root:
  `npm run dev:web`
- from `apps/web`:
  `npm run dev`

Ensure the API and required backing services are already running for the slice you are testing.

## Data Fetching

- prefer server components where possible
- use `@myflightbook/api-client` for type-safe API access
- keep domain calculations in the backend rather than duplicating them in the browser

## Testing

- use Vitest for unit and component tests
- run from the repo root with:
  `npm run test --workspace @myflightbook/web`
- add frontend tests only when the slice has genuine UI behavior to verify
