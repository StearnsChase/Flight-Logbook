# System Overview

This document outlines the high-level architecture of the new Flight Logbook platform, which replaces the legacy .NET monolithic application.

## High-Level Architecture

The new system is a distributed application consisting of the following core components:

### 1. Frontend (`apps/web`)
- **Technology:** Next.js (TypeScript, React).
- **Responsibility:** Serves the user interface for pilots to log flights, view telemetry, and manage their aircraft. It communicates exclusively with the API component.

### 2. Backend API (`apps/api`)
- **Technology:** Python, FastAPI, SQLAlchemy, Alembic.
- **Responsibility:** The core business logic and RESTful API layer. Handles authentication, data validation, database interactions, and orchestrates background jobs.

### 3. Background Worker (`apps/worker`)
- **Technology:** Python.
- **Responsibility:** Handles asynchronous and resource-intensive tasks such as processing flight telemetry (GPX, KML, CSV) and media transcoding (images, video).

### 4. Shared API Client (`packages/api-client`)
- **Technology:** TypeScript.
- **Responsibility:** A shared library that provides strongly typed API client methods and data contracts used by the Frontend to communicate with the Backend API.

### 5. Infrastructure Services
- **Database:** PostgreSQL with PostGIS extensions for spatial data queries.
- **Object Storage:** MinIO (S3-compatible) for storing user-uploaded media, documents, and telemetry files.
