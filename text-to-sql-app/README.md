# Text to SQL App

A clean full-stack starter for a text-to-SQL application.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI
- Data layer placeholder: DuckDB

## Project Structure

```text
text-to-sql-app/
├── frontend/
├── backend/
├── data/
└── tests/
```

Business logic belongs in `backend/app/modules`. API routes should stay thin, and SQL generation or validation must go through `backend/app/duckdb_layer/sql_validator.py`.

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

