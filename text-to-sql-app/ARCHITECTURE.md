# Architecture

## Overview

Text-to-SQL App is a full-stack analytical prototype.

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI
- Query engine: DuckDB
- Local data format: Parquet
- Module system: registry-driven metadata and processors
- Current intelligence layer: mocked Query Agent SQL generation and mocked processor responses

The current system accepts a module and a natural-language question, asks the mocked Query Agent for SQL, validates the SQL, executes it against local Parquet files through DuckDB, calls the module processor for a mocked business answer, and returns real queried rows.

No OpenAI or real LLM logic is connected yet.

## System Flow

1. The frontend loads modules from `GET /api/modules`.
2. The user selects a module and submits a question.
3. The frontend sends `POST /api/ask` with `module_id` and `question`.
4. The backend validates the module and question.
5. The Query Agent builds schema context from registry metadata.
6. The Query Agent returns deterministic mocked SQL and an explanation.
7. The DuckDB query runner validates the SQL against module metadata.
8. The query runner registers all Parquet-backed tables for the selected module.
9. DuckDB executes the validated SQL.
10. The module processor returns a mocked business answer.
11. The API returns:
   - mocked answer
   - SQL
   - explanation
   - real query rows
   - module id

## Query Agent Flow

The Query Agent currently uses deterministic mocked SQL generation.

The current flow is:

1. Build module schema context with `build_agent_schema_context(module_id)`.
2. Use only metadata from the registry:
   - module description
   - table names
   - column names, types, descriptions, examples, and business terms
   - relationships
   - example questions
   - example SQL
3. Return a mocked SQL query and explanation for the selected module.
4. The query is validated by `sql_validator.py`.
5. The validated query runs through `query_runner.py`.

The future real SQL Agent must follow the same boundary: it must never receive raw Parquet data.

## SQL Validation Flow

All executable SQL must pass through `backend/app/duckdb_layer/sql_validator.py`.

The validator uses `sqlglot` and enforces:

- one SQL statement only
- `SELECT` only
- `WITH` only when the final expression is a `SELECT`
- no destructive or modifying statements
- no direct file-reading functions
- no network or external file access
- no table access outside the selected module metadata

`query_runner.py` applies the validator before DuckDB execution and wraps the validated query with an outer maximum `LIMIT`.

## DuckDB And Parquet Setup

Local data is stored under `data/`:

```text
data/
|-- pax_forecast/
|-- special_cruise/
`-- qa/
```

Each registry table points to a Parquet file. The query runner:

1. Looks up the selected module.
2. Resolves each table `data_path`.
3. Registers each Parquet file as a DuckDB view using `read_parquet()`.
4. Executes the validated SQL.
5. Returns rows as `list[dict]`.

Direct user SQL cannot call `read_parquet()`. Only the trusted query runner uses it internally.

## Module Registry

The module registry lives in `backend/app/modules/registry.py`.

Each module defines:

- `module_id`
- `label`
- `description`
- `tables`
- `relationships`
- `processor_function`
- `example_questions`
- `example_sql`

Each table defines:

- `table_name`
- `data_path`
- `description`
- `columns`

Each column defines:

- `name`
- `type`
- `description`
- optional `examples`
- optional `business_terms`

Relationships describe join paths between tables. Pax Forecast currently proves the multi-table design with:

- `pax_forecast`
- `pax_route_targets`

## Processor Flow

Processors live in `backend/app/modules`.

Each processor exposes:

```python
process(data, question, context)
```

Processors currently return mocked:

- answer

The Query Agent owns SQL and SQL explanation. The API fills the final `data` field with real DuckDB query results.

## Future Response Agent Flow

The Response Agent is not implemented yet.

The intended future flow is:

1. Query Agent generates SQL from module metadata.
2. SQL validator approves or rejects the SQL.
3. DuckDB returns result rows.
4. Response Agent receives:
   - original question
   - module metadata summary
   - validated SQL
   - query result rows
5. Response Agent writes a business-friendly answer.

The Response Agent should explain results clearly and avoid inventing data not present in the query output.
