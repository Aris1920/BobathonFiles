# Career & Debt Planner

A full-stack web application that helps US-based students find relevant job opportunities and
understand how long it will take to pay off their **student/academic loans** based on the
salaries those jobs offer.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| Backend | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT (access + refresh tokens, bcrypt passwords) |
| Job Data | LinkedIn, Handshake, Indeed, USAJobs |
| Salary Fallback | BLS Occupational Employment & Wage Statistics API |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended path), **or**
- Node.js 20+ and Python 3.11+ for a manual setup.

---

## Quick Start — Docker Compose (recommended)

```bash
# 1. Clone the repo
git clone <repo-url>
cd career-debt-planner

# 2. Copy the env template and fill in your API keys
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and any API keys you have

# 3. Spin everything up
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend (Vite dev) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

## Manual Setup (no Docker)

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy env file (adjust DATABASE_URL to point to your local Postgres)
cp ../.env.example ../.env

# Run database migrations (after Sub-Task 2 is complete)
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the Vite dev server
npm run dev
```

The frontend dev server starts at http://localhost:5173.  
The Vite proxy forwards `/api/*` requests to the FastAPI backend at `http://localhost:8000`.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Random 64-char hex used to sign JWTs — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `LINKEDIN_CLIENT_ID` | OAuth 2.0 client ID from [LinkedIn Developer Portal](https://developer.linkedin.com/) |
| `LINKEDIN_CLIENT_SECRET` | OAuth 2.0 client secret |
| `HANDSHAKE_API_KEY` | Campus partner API key from your Handshake institution account |
| `INDEED_PUBLISHER_ID` | Publisher ID from [Indeed Publisher Console](https://publisher.indeed.com/) |
| `USAJOBS_API_KEY` | API key from [USAJobs Developer Portal](https://developer.usajobs.gov/) |
| `BLS_API_KEY` | API key from [BLS Data Registration](https://data.bls.gov/registrationEngine/) |

---

## Project Structure

```
career-debt-planner/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py          # Settings loaded from .env via pydantic-settings
│   │   └── main.py            # FastAPI app + /health endpoint
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx            # React Router + placeholder pages
│   │   └── index.css          # Tailwind directives
│   ├── index.html
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Running Tests

```bash
cd backend
pytest
```

---

## Health Check

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```
