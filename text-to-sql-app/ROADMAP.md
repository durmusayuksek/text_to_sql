# Roadmap

## Completed Milestones

- Created full-stack project structure.
- Added React, TypeScript, Vite, and Tailwind frontend.
- Added FastAPI backend.
- Added `/health` endpoint.
- Added frontend module-selection UI.
- Added backend API contract:
  - `GET /api/modules`
  - `POST /api/ask`
- Added module registry architecture.
- Added module processors for:
  - Pax Forecast
  - Special Cruise / Entertainment Profit Calculation
  - Questions / Answers
- Added DuckDB query layer.
- Added local Parquet sample data.
- Added SQL validation with `sqlglot`.
- Added module-scoped table allow-listing.
- Added multi-table registry metadata.
- Added relationship metadata for joins.
- Added `build_agent_schema_context(module_id)`.
- Added mocked Query Agent SQL generation.
- Added Query Agent prompt template and JSON response parser.
- Added tests for SQL validation and registry query behavior.

## Current State

- Frontend communicates with the backend.
- Backend responses still use mocked business answers.
- DuckDB returns real rows from local Parquet files.
- Pax Forecast supports a real join between two registered Parquet tables.
- Query Agent is responsible for deterministic mocked SQL generation.
- Query Agent prompt and parser are ready for future LLM integration.
- SQL is validated before execution.
- No OpenAI, real LLM, or Response Agent logic is connected yet.

## Next Planned Milestones

- Add prompt templates for SQL generation using registry metadata only.
- Add Query Agent prompt assembly without connecting an external model yet.
- Add stricter SQL validation tests for aliases, joins, CTEs, nested queries, and aggregate queries.
- Add API endpoint tests for `/api/modules` and `/api/ask`.
- Add backend formatting and linting configuration.
- Add frontend tests for module loading, submit flow, and error states.
- Improve frontend answer display for tabular query results.
- Add loading and error boundaries around module metadata loading.

## Future Planned Features

- Connect a real SQL Agent after validation and registry context are stable.
- Connect a Response Agent for business-friendly answer generation.
- Add module-specific business logic in processors.
- Add richer Parquet datasets for each module.
- Add schema versioning for module metadata.
- Add query audit logging.
- Add query result pagination.
- Add saved questions and saved SQL examples.
- Add export options for query results.
- Add authentication and user-level access controls.
- Add deployment configuration for frontend and backend.
- Add production-safe observability and structured logging.
