# AGENTS.md

This file defines project rules for Codex and future contributors.

## Coding Rules

- Keep functions small, typed, and testable.
- Prefer explicit data models over loose dictionaries when data crosses module boundaries.
- Keep business logic in `backend/app/modules`.
- Keep API routes thin. Routes should validate request flow, call service/module functions, and return typed responses.
- Do not place SQL generation logic directly inside API routes.
- Do not add unrelated refactors while implementing a focused feature.
- Update tests when changing validation, registry behavior, query execution, or API contracts.

## Architectural Constraints

- Backend framework: FastAPI with async endpoints.
- Frontend framework: React, TypeScript, Vite, Tailwind CSS.
- Backend module metadata lives in `backend/app/modules/registry.py`.
- Module processors live in `backend/app/modules/*.py` and expose:

```python
process(data, question, context)
```

- DuckDB execution belongs in `backend/app/duckdb_layer/query_runner.py`.
- SQL validation belongs in `backend/app/duckdb_layer/sql_validator.py`.
- Local analytical data lives under `data/` as Parquet files.
- Future SQL Agent prompts should receive registry metadata only, never full Parquet data.

## SQL Safety Rules

- Every query executed by DuckDB must pass through `sql_validator.py`.
- Only read-only analytical SQL is allowed.
- Allowed queries must be single-statement `SELECT` queries.
- `WITH` queries are allowed only when the final expression is a `SELECT`.
- Block destructive or modifying commands including:
  - `DELETE`
  - `UPDATE`
  - `DROP`
  - `ALTER`
  - `INSERT`
  - `CREATE`
  - `REPLACE`
  - `TRUNCATE`
  - `MERGE`
  - `COPY`
  - `ATTACH`
  - `DETACH`
  - `PRAGMA`
  - `EXPORT`
  - `INSTALL`
  - `LOAD`
- Block multiple SQL statements in one input.
- Block table access outside the selected module registry metadata.
- Block direct file-reading functions such as `read_csv`, `read_parquet`, `read_json`, and `glob`.
- The query runner enforces a maximum returned row count.

## Modularity Rules

- Adding a new module should require:
  - one processor file in `backend/app/modules`
  - one registry entry in `backend/app/modules/registry.py`
  - Parquet data under `data/<module>/`
- Module registry entries should define:
  - `module_id`
  - `label`
  - `description`
  - `tables`
  - `relationships`
  - `processor_function`
  - `example_questions`
  - `example_sql`
- Registry metadata should describe tables, columns, relationships, and examples clearly enough for a future SQL Agent.

## Frontend Standards

- Use TypeScript interfaces for API payloads.
- Keep UI components reusable and modular.
- Keep backend API calls in `frontend/src/api`.
- Keep shared frontend types in `frontend/src/types`.
- Maintain loading, empty, and error states for backend interactions.
- Avoid embedding backend business rules in frontend components.

## Backend Standards

- Use Pydantic models for API request and response contracts.
- Use async FastAPI endpoints.
- Keep validation errors clear and user-readable.
- Keep DuckDB-specific concerns inside `backend/app/duckdb_layer`.
- Keep module-specific behavior inside module processors and registry metadata.
- Do not add OpenAI or LLM logic until the registry, validation, and query layers are stable.

