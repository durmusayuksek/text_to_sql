# AGENTS.md

This file defines project rules for Codex and future contributors.

## Current Direction

This project is now a single Question & Answer Text-to-SQL application.

Users ask natural-language business questions. The backend asks the Query Agent to generate DuckDB SQL from central catalog metadata, validates the SQL, runs it through DuckDB over local Parquet files, and returns the result.

Pax Forecast and Special Cruise / Entertainment Profit Calculation are no longer active frontend or backend modules. Their sample Parquet files may remain available as catalog tables, but they are data sources, not selectable modules.

## Coding Rules

- Keep functions small, typed, and testable.
- Prefer explicit data models over loose dictionaries when data crosses boundaries.
- Keep API routes thin. Routes should validate request flow, call service functions, and return typed responses.
- Do not place SQL generation logic directly inside API routes.
- Do not add unrelated refactors while implementing a focused feature.
- Update tests when changing validation, catalog behavior, query execution, or API contracts.

## Architectural Constraints

- Backend framework: FastAPI with async endpoints.
- Frontend framework: React, TypeScript, Vite, Tailwind CSS.
- Central table metadata lives in `backend/app/catalog.py`.
- The ask workflow lives in `backend/app/ask_service.py`.
- DuckDB execution belongs in `backend/app/duckdb_layer/query_runner.py`.
- SQL validation belongs in `backend/app/duckdb_layer/sql_validator.py`.
- Local analytical data lives under `data/` as Parquet files.
- Query Agent prompts must receive catalog metadata only, never full Parquet data.
- Keep both `mock` and `openai` Query Agent modes.

## SQL Safety Rules

- Every query executed by DuckDB must pass through `sql_validator.py`.
- Only read-only analytical SQL is allowed.
- Allowed queries must be single-statement `SELECT` queries.
- `WITH` queries are allowed only when the final expression is a `SELECT`.
- Block destructive or modifying commands, including `DELETE`, `UPDATE`, `DROP`, `ALTER`, `INSERT`, `CREATE`, `REPLACE`, `TRUNCATE`, `MERGE`, `COPY`, `ATTACH`, `DETACH`, `PRAGMA`, `EXPORT`, `INSTALL`, and `LOAD`.
- Block multiple SQL statements in one input.
- Block table access outside the central data catalog.
- Block direct file-reading functions such as `read_csv`, `read_parquet`, `read_json`, and `glob`.
- The query runner enforces a maximum returned row count.

## Catalog Rules

- Adding a new data source should require:
  - a Parquet file under `data/`
  - one table entry in `backend/app/catalog.py`
  - relationship metadata when joins are useful
  - example questions and example SQL when helpful
- Catalog metadata should describe tables, columns, relationships, and examples clearly enough for the Query Agent.
- Do not expose sensitive raw values to the Query Agent.

## Frontend Standards

- Use TypeScript interfaces for API payloads.
- Keep backend API calls in `frontend/src/api`.
- Keep shared frontend types in `frontend/src/types`.
- Maintain loading, empty, response, and error states.
- Avoid embedding backend SQL or catalog rules in frontend components.

## Backend Standards

- Use Pydantic models for API request and response contracts.
- Use async FastAPI endpoints.
- Keep validation errors clear and user-readable.
- Keep DuckDB-specific concerns inside `backend/app/duckdb_layer`.
- Keep Query Agent logic in `backend/app/agents`.
