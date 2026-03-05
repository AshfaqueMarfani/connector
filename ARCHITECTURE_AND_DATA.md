# 🏗 Architecture & Data Flow

## 1. The Database & Geospatial Engine
* **PostGIS:** All user and entity locations must be stored as `Point` fields in PostGIS.
* **Radius Queries:** Backend searches must utilize PostGIS `ST_DWithin` for highly efficient radius lookups (e.g., scanning the 100m or 500m boundary) rather than standard math calculations.

## 2. Data Ingestion & Seeding
* **Dynamic Database:** The architecture must support bulk ingestion of third-party data to solve the "cold start" problem.
* **Upload Pipeline:** Implement Django management commands and secure API endpoints to ingest external datasets (e.g., scraping local NGO directories or business registries) and map them to Public Profiles.

## 3. AI Agent Layer
* **Profile Analysis:** An asynchronous Celery task runs incoming profiles and statuses through an LLM/AI agent.
* **Intelligent Matching:** If User A posts a status "Need emergency food assistance," the AI agent parses the intent, queries PostGIS for nearby NGOs with the tag "Food," and pushes a smart notification to both parties.