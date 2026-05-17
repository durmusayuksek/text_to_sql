# Architecture

## Overview

Text-to-SQL App is a single Question & Answer analytical prototype.

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI
- Query engine: DuckDB
- Local data format: Parquet
- Metadata source: central data catalog
- Intelligence layer: Query Agent with `mock` and `openai` modes

The app accepts a natural-language question, asks the Query Agent for DuckDB SQL, validates the SQL, executes it against catalog-backed Parquet files through DuckDB, and returns an answer, SQL explanation, and result rows.

Pax Forecast and Special Cruise / Entertainment Profit Calculation are no longer active modules. Their sample datasets can remain in the catalog as ordinary analytical tables.

## System Flow

1. The user enters a business question in the frontend.
2. The frontend sends `POST /api/ask` with `{ "question": "..." }`.
3. The backend validates the question and blocks destructive intent.
4. The Query Agent builds context from `backend/app/catalog.py`.
5. The Query Agent returns JSON with `sql`, `explanation`, `confidence`, and `assumptions`.
6. The DuckDB query runner validates SQL against catalog table names.
7. The query runner registers catalog Parquet files as DuckDB views.
8. DuckDB executes the validated SQL with maximum row protection.
9. The API returns:
   - answer
   - generated SQL
   - explanation
   - result rows
   - Query Agent mode

## Query Agent Flow

The Query Agent supports two modes:

- `mock`: deterministic SQL generation with no network calls.
- `openai`: OpenAI-backed SQL generation using catalog metadata only.

The prompt template is `backend/app/prompts/query_agent.md`. The parser in `backend/app/agents/query_agent.py` expects JSON:

```json
{
  "sql": "SELECT * FROM qa LIMIT 10",
  "explanation": "Briefly explain what the query does.",
  "confidence": "high | medium | low",
  "assumptions": []
}
```

OpenAI mode sends only the user question and catalog metadata. It must never receive raw Parquet rows. Low-confidence responses are rejected before DuckDB execution.

## Environment Modes

The backend reads environment variables with `python-dotenv` in `backend/app/config.py`.

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
- no table access outside the central data catalog

`query_runner.py` applies the validator before DuckDB execution and wraps the validated query with an outer maximum `LIMIT`.

## DuckDB And Parquet Setup

Local data is stored under `data/`. Each catalog table points to a Parquet file. The query runner:

1. Resolves each table `data_path`.
2. Registers each Parquet file as a DuckDB view using trusted internal `read_parquet()`.
3. Executes the validated SQL.
4. Returns rows as `list[dict]`.

Direct user SQL cannot call `read_parquet()`. Only the trusted query runner uses it internally.

## Data Catalog

The central data catalog lives in `backend/app/catalog.py`.

It defines:

- catalog description
- tables
- relationships
- example questions
- example SQL

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

Relationships describe join paths between tables. This keeps the architecture extensible for future data sources without reintroducing selectable modules.

## Response Formatting

There is no Response Agent yet. The current backend returns a minimal answer string plus the generated SQL, explanation, and result rows.

A future Response Agent may be added later, but it should receive only the original question, validated SQL, catalog summaries, and query result rows needed for formatting.
