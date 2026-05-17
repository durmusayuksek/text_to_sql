# Roadmap

## Completed Milestones

- Created full-stack project structure.
- Added React, TypeScript, Vite, and Tailwind frontend.
- Added FastAPI backend.
- Added `/health` endpoint.
- Added `POST /api/ask`.
- Added DuckDB query layer.
- Added local Parquet sample data.
- Added SQL validation with `sqlglot`.
- Added table allow-listing against catalog metadata.
- Added central data catalog metadata.
- Added relationship metadata for joins.
- Added Query Agent prompt template and JSON response parser.
- Added Query Agent `mock` and `openai` modes.
- Simplified the product to one Question & Answer workflow.
- Removed selectable frontend modules and module-specific processors.
- Added controlled Analysis Planner -> Query Agent -> Validator -> DuckDB -> Response Agent pipeline.
- Added multi-query SQL generation and execution support.

## Current State

- Frontend asks one natural-language question and renders loading, error, empty, and response states.
- `/api/ask` accepts only `{ "question": "..." }`.
- Analysis Planner and Query Agent use central catalog metadata only.
- Response Agent formats validated query results into a final answer.
- DuckDB returns real rows from local Parquet files.
- SQL is validated before execution.
- `/api/ask` can hide raw query results unless `DEBUG_QUERY_RESULTS=true`.
- Mock mode is deterministic and remains the default.
- OpenAI mode is available behind `QUERY_AGENT_MODE=openai`.

## Next Planned Milestones

- Add stricter SQL validation tests for aliases, joins, CTEs, nested queries, and aggregate queries.
- Improve frontend answer display for tabular query results.
- Add backend formatting and linting configuration.
- Add frontend tests for submit flow and error states.
- Expand catalog metadata with stronger business definitions.
- Add query audit logging.

## Future Planned Features

- Improve Response Agent answer quality and result summarization.
- Add more Parquet-backed catalog tables.
- Add schema/catalog versioning.
- Add query result pagination.
- Add saved questions and saved SQL examples.
- Add export options for query results.
- Add authentication and user-level access controls.
- Add deployment configuration for frontend and backend.
- Add production-safe observability and structured logging.
