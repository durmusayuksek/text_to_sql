# Architecture

## Overview

Text-to-SQL App is a full-stack analytical prototype.

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI
- Query engine: DuckDB
- Local data format: Parquet
- Module system: registry-driven metadata and processors
- Current intelligence layer: Query Agent with `mock` and `openai` modes, plus mocked processor responses

The current system accepts a module and a natural-language question, asks the Query Agent for SQL, validates the SQL, executes it against local Parquet files through DuckDB, calls the module processor for a mocked business answer, and returns real queried rows.

OpenAI mode is available behind `QUERY_AGENT_MODE=openai`. Mock mode remains the default.

## System Flow

1. The frontend loads modules from `GET /api/modules`.
2. The user selects a module and submits a question.
3. The frontend sends `POST /api/ask` with `module_id` and `question`.
4. The backend validates the module and question.
5. The Query Agent builds schema context from registry metadata.
6. The Query Agent returns SQL and an explanation. In `mock` mode this is deterministic; in `openai` mode this comes from OpenAI and is parsed as JSON.
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

The Query Agent supports two modes:

- `mock`: deterministic SQL generation with no network calls.
- `openai`: OpenAI-backed SQL generation using registry metadata only.

A real prompt template exists at `backend/app/prompts/query_agent.md`, and a response parser exists in `backend/app/agents/query_agent.py`. The parser expects JSON with `sql`, `explanation`, `confidence`, and `assumptions`.

The current flow is:

1. Build module schema context with `build_agent_schema_context(module_id)`.
2. Use only metadata from the registry:
   - module description
   - table names
   - column names, types, descriptions, examples, and business terms
   - relationships
   - example questions
   - example SQL
3. Return SQL, explanation, confidence, and assumptions.
4. The query is validated by `sql_validator.py`.
5. The validated query runs through `query_runner.py`.

OpenAI mode sends only the user question, selected module id, and schema context from `build_agent_schema_context(module_id)`. It must never receive raw Parquet rows.

Every OpenAI raw response passes through `parse_query_agent_response(raw_response)` before validation and execution. Low-confidence responses are rejected before DuckDB execution.

## Environment Modes

The backend reads environment variables with `python-dotenv` in `backend/app/config.py`.

Required values:

- `QUERY_AGENT_MODE`: `mock` or `openai`
- `OPENAI_API_KEY`: required only when `QUERY_AGENT_MODE=openai`
- `OPENAI_MODEL`: defaults to `gpt-4.1-mini`

If `QUERY_AGENT_MODE=openai` and `OPENAI_API_KEY` is missing, the backend raises a clear configuration error.

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
