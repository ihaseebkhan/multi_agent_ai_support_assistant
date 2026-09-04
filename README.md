# Multi-Agent AI Support Assistant

A FastAPI customer-support assistant powered by the OpenAI Agents SDK and the Pagila PostgreSQL sample database.

## Prerequisites

- Python 3.12
- PostgreSQL running locally
- A local Pagila database
- An OpenAI API key

## Quick Start

### 1. Create and activate a virtual environment

From the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, run this once for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Install dependencies

Install the project's Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://<postgres-user>:<password>@localhost:5432/pagila
OPENAI_API_KEY=your_openai_api_key
MODEL_CHOICE=gpt-4o-mini
```

### 4. Load the Pagila sample database

Create the local database:

```powershell
createdb -U postgres pagila
```

Load the Pagila schema and sample data. Replace the paths with the location of the downloaded Pagila SQL files:

```powershell
psql -U postgres -d pagila -f path\to\pagila-schema.sql
psql -U postgres -d pagila -f path\to\pagila-data.sql
```

### 5. Apply application migrations

Ensure `sqlalchemy.url` in `alembic.ini` points to the same database as `DATABASE_URL` in `.env`.

```powershell
python -m alembic upgrade head
```

This applies the project's additional schema changes, including streaming availability and subscription data.

### 6. Start the API server

```powershell
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Run the MCP smoke test

```powershell
python -m app.mcp.run_server
```

This lists the available MCP-shaped tools and runs database-backed checks.

### 8. Run the evaluation suite

```powershell
python -m app.evals.run_evals
```

## Project Commands

| Purpose | Command |
| --- | --- |
| Apply database migrations | `python -m alembic upgrade head` |
| Start the FastAPI application | `python -m uvicorn app.main:app --reload` |
| Run the MCP smoke test | `python -m app.mcp.run_server` |
| Run evaluations | `python -m app.evals.run_evals` |

## Documentation

- [Architecture and design](docs/design.md)
- [Implementation plan](docs/implementation_plan.md)
- [AI usage disclosure](docs/ai_usage.md)