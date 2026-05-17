# Text to SQL App

A clean full-stack starter for a single Question & Answer text-to-SQL application.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI
- Query engine: DuckDB
- Local data format: Parquet

## Project Structure

```text
text-to-sql-app/
|-- frontend/
|-- backend/
|-- data/
`-- tests/
```

The central data catalog lives in `backend/app/catalog.py`. API routes should stay thin, and every executable SQL query must go through `backend/app/duckdb_layer/sql_validator.py`.

## Environment

Copy `.env.example` to `.env` and adjust values locally.

```bash
cp .env.example .env
```

Query Agent modes:

- `QUERY_AGENT_MODE=mock`: default mode. Uses deterministic mocked SQL and does not call OpenAI.
- `QUERY_AGENT_MODE=openai`: uses OpenAI to generate SQL from catalog metadata only.

Required OpenAI settings for `openai` mode:

```text
OPENAI_API_KEY=
QUERY_AGENT_MODE=mock
OPENAI_MODEL=gpt-4.1-mini
```

Do not commit `.env`. It is ignored by git.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend runs at `http://localhost:8000`.

Visit `http://localhost:8000/health` to verify the API is running.
