# Career & Debt Planner

A web application that helps US-based students find relevant job opportunities and
understand how long it will take to pay off their **student/academic loans** based on the
salaries those jobs offer.

---

## Ways to Run

There are **two independent ways** to run this project — pick whichever fits your situation:

| Mode | What runs | When to use |
|---|---|---|
| **Standalone `index.html`** | Browser only — no server needed | Quickest start; everything runs in the browser with `localStorage` |
| **Full stack (Docker / manual)** | React frontend + FastAPI backend + PostgreSQL | Full backend with real API calls and a database |

---

## Standalone Mode (no install required)

Open `index.html` (the file at the root of the repo) directly in any modern browser:

```
# macOS / Linux
open index.html

# Windows — double-click the file, or:
start index.html
```

The app is entirely self-contained:
- Auth, profiles, loans, and results are stored in **`localStorage`**.
- Job listings are mock-generated in the browser; no external API keys are needed.
- Job listings stay stable between sessions and only refresh when your **major, interests, skills, or resume** change — or when you click **Regenerate →**.

> **Note:** Do not serve this file from a web server using path-based routing (e.g. `python -m http.server`) — the router is hash-based (`#/login`, `#/profile`, etc.) and works correctly only when opened as a local `file://` URL or from the root path `/`.

---

## Full-Stack Mode

### Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS + Axios |
| Backend | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT (access + refresh tokens, bcrypt passwords) |
| Job Data | LinkedIn, Handshake, Indeed, USAJobs |
| Salary Fallback | BLS Occupational Employment & Wage Statistics API |

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended), **or**
- Node.js 20+ and Python 3.11+ for a manual setup.

---

### Quick Start — Docker Compose (recommended)

```bash
# 1. Clone the repo
git clone <repo-url>
cd career-debt-planner

# 2. Copy the env template and fill in your API keys
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY

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

### Manual Setup (no Docker)

#### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies (includes dev tools)
pip install -e ".[dev]"

# Copy env file and adjust DATABASE_URL to point to your local Postgres
cp ../.env.example ../.env

# Run database migrations
alembic upgrade head

# Start the dev server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

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
| `DATABASE_URL` | PostgreSQL connection string (default in docker-compose: `postgresql://postgres:postgres@db:5432/careerplanner`) |
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
├── index.html                  # Standalone single-file app (no build needed)
├── backend/
│   ├── app/
│   │   ├── config.py           # Settings loaded from .env via pydantic-settings
│   │   ├── database.py         # SQLAlchemy engine & session factory
│   │   ├── dependencies.py     # FastAPI dependency injection helpers
│   │   ├── main.py             # FastAPI app, CORS middleware, router registration
│   │   ├── models/             # SQLAlchemy ORM models (user, profile, loan, job, projection)
│   │   ├── routers/            # API route handlers (auth, profile, loans, resume, results, projections)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic (auth, debt projection, job adapters, scoring, salary)
│   │       └── job_adapters/   # Per-source adapters: linkedin, handshake, indeed, usajobs
│   ├── migrations/
│   │   └── versions/
│   │       └── 0001_initial_schema.py   # Creates all tables and enum types
│   ├── tests/                  # pytest test suite
│   ├── alembic.ini
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx             # React Router + page wiring
│   │   ├── index.css           # Tailwind directives
│   │   ├── api/                # Axios API client modules (auth, profile, loans, resume, results)
│   │   ├── components/         # Shared UI components (Navbar, JobCard, LoanCard, charts, etc.)
│   │   ├── context/            # AuthContext (JWT token storage + React context)
│   │   ├── pages/              # Page components (Login, Register, Profile, Results)
│   │   └── types/              # Shared TypeScript type definitions
│   ├── index.html
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.ts
│   └── tsconfig.json
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
