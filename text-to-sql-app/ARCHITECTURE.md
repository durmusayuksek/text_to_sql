# Architecture

## Overview

Text-to-SQL App is a single Question & Answer analytical prototype.

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI
- Query engine: DuckDB
- Local data format: Parquet
- Metadata source: central data catalog
- Intelligence layer: Analysis Planner, Query Agent, and Response Agent with `mock` and `openai` modes

The app accepts a natural-language question, plans the analysis, asks the Query Agent for one or more DuckDB SQL queries, validates every query, executes validated queries against catalog-backed Parquet files through DuckDB, and asks the Response Agent to produce the final business answer.

Pax Forecast and Special Cruise / Entertainment Profit Calculation are no longer active modules. Their sample datasets can remain in the catalog as ordinary analytical tables.

## System Flow

1. The user enters a business question in the frontend.
2. The frontend sends `POST /api/ask` with `{ "question": "..." }`.
3. The backend validates the question and blocks destructive intent.
4. The Analysis Planner receives the question and catalog metadata, then returns structured planning JSON.
5. The Query Agent receives the question, catalog metadata, and planner output, then returns a `queries` array.
6. The DuckDB query runner validates every SQL query against catalog table names.
7. The query runner registers catalog Parquet files as DuckDB views.
8. DuckDB executes validated SQL with maximum row protection.
9. The Response Agent receives the question, planner output, generated queries, and query results, then returns final answer JSON.
10. The API returns:
   - answer
   - key findings
   - assumptions
   - limitations
   - generated SQL queries
   - query results only when debug mode is enabled
   - Query Agent mode

## Analysis Planner Flow

The Analysis Planner never generates SQL. It identifies question type, likely tables, relationships, metrics, dimensions, filters, date logic, analysis steps, assumptions, and whether multiple queries may be needed.

It returns JSON with:

```json
{
  "question_type": "summary | comparison | trend | ranking | lookup | diagnostic | unknown",
  "required_tables": [],
  "required_relationships": [],
  "metrics": [],
  "dimensions": [],
  "filters": [],
  "time_period": null,
  "requires_multiple_queries": false,
  "analysis_steps": [],
  "assumptions": [],
  "confidence": "high | medium | low"
}
```

## Query Agent Flow

The Query Agent supports two modes:

- `mock`: deterministic SQL generation with no network calls.
- `openai`: OpenAI-backed SQL generation using catalog metadata only.

The prompt template is `backend/app/prompts/query_agent.md`. The parser in `backend/app/agents/query_agent.py` expects JSON:

```json
{
  "queries": [
    {
      "query_id": "main",
      "purpose": "Explain what this query calculates.",
      "sql": "SELECT * FROM sales_figures_since_2025 LIMIT 10"
    }
  ],
  "assumptions": [],
  "confidence": "high | medium | low"
}
```

OpenAI mode sends only the user question, catalog metadata, and Analysis Planner output. It must never receive raw Parquet rows. Low-confidence Query Agent responses are rejected before DuckDB execution.

## Environment Modes

The backend reads environment variables with `python-dotenv` in `backend/app/config.py`.

- `AGENT_MODE`: `mock` or `openai`
- `QUERY_AGENT_MODE`: backward-compatible fallback if `AGENT_MODE` is not set
- `OPENAI_API_KEY`: required only when `AGENT_MODE=openai`
- `OPENAI_MODEL`: defaults to `gpt-4.1-mini`
- `RESPONSE_AGENT_MAX_SAMPLE_ROWS`: defaults to `5`
- `ENABLE_ASK_EVENT_LOGGING`: defaults to `true` in development
- `ASK_EVENT_LOG_PATH`: defaults to `logs/ask_events.jsonl`
- `LOG_QUERY_RESULT_ROWS`: defaults to `false`

If `AGENT_MODE=openai` and `OPENAI_API_KEY` is missing, the backend raises a clear configuration error.

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
- optional `sensitive`
- optional `redaction_strategy`: `omit`, `mask`, or `hash`

Relationships describe join paths between tables. This keeps the architecture extensible for future data sources without reintroducing selectable modules.

## Response Agent Flow

The Response Agent does not generate SQL and does not execute SQL. It converts the original question, planner output, generated query metadata, and minimized validated DuckDB result summaries into a business-friendly answer.

In OpenAI mode, the backend does not send full raw query rows to the Response Agent. It sends query id, purpose, SQL, row count, column names, warnings, simple numeric summaries, and up to `RESPONSE_AGENT_MAX_SAMPLE_ROWS` sample rows.

Before the Response Agent OpenAI payload is built, catalog sensitivity controls are applied:

- `omit`: remove the sensitive column from sample rows and summaries.
- `mask`: include the column but replace values with `***REDACTED***`.
- `hash`: include the column with a deterministic SHA-256 hash value.

Numeric summaries are never calculated for sensitive columns.

It returns JSON with:

```json
{
  "answer": "Business-friendly answer.",
  "key_findings": [],
  "assumptions": [],
  "limitations": [],
  "confidence": "high | medium | low"
}
```

Raw query rows are included in `/api/ask` responses only when `DEBUG_QUERY_RESULTS=true`. This API debug flag is separate from Response Agent minimization.

## Ask Event Logging

`/api/ask` writes one best-effort JSONL event per request when `ENABLE_ASK_EVENT_LOGGING=true`.

Each event includes:

- request id and UTC timestamp
- user question
- agent mode
- planner output
- Query Agent output
- validated queries
- query result summaries
- Response Agent output
- final answer, findings, assumptions, limitations, warnings, and errors
- latency and success flag

Query result summaries include query id, purpose, SQL, row count, columns, and warnings. Raw rows are omitted unless `LOG_QUERY_RESULT_ROWS=true`.

Logging failures are swallowed so they do not break the API. Logs help improve prompts, SQL quality, catalog metadata, and safety behavior over time.
