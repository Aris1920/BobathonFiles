# Career & Debt Planner — Technical Plan

## Top-Level Overview

Build a full-stack web application that helps US-based students find relevant job opportunities and understand how long it will take to pay off their **student/academic loan debt** based on the salaries those jobs offer.

**Scope constraints:**
- **Geography:** US-only job listings and US tax/financial assumptions throughout.
- **Debt types:** Student and academic loans only (federal and private). No credit cards, mortgages, or other debt types.

**User flow:**
1. User registers / logs in.
2. User fills in a structured profile: major, interests, skills, experience level, current savings, and one or more **student/academic loan** records (balance + interest rate + minimum payment).
3. User optionally uploads a resume (PDF/DOCX) — the text is extracted and used to boost job matching quality.
4. The backend queries multiple US job board APIs (LinkedIn, Handshake, Indeed, and USAJobs) using the profile data.
5. Matched jobs are scored for fit and bucketed into **High / Mid / Low** tiers. Each tier displays its salary range and median.
6. For each tier the app runs a student loan payoff projection: given the tier's median salary, a configurable savings rate, and each loan's balance + interest rate + minimum payment, how many months until debt-free?
7. Results (profile + job matches + projections) are persisted to the user's account and can be revisited.

**Recommended stack:**
- **Frontend:** React (Vite) + TypeScript + Tailwind CSS
- **Backend:** Python / FastAPI — excellent async support for parallel job-board API calls, strong ecosystem for text processing (resume parsing), and clean Pydantic data models
- **Database:** PostgreSQL — relational structure fits users, debts, saved results
- **Auth:** JWT-based authentication (access + refresh tokens)
- **Job data:** Aggregated from LinkedIn Jobs API, Handshake API (campus jobs), Indeed Publisher API, and USAJobs REST API — US listings only
- **Salary data:** Extracted from live job listings; supplemented by BLS Occupational Employment & Wage Statistics (OEWS) API for median salary fallback when listings lack salary data

---

## Architecture Diagram (described in text)

```
Browser (React)
    |
    |  HTTPS REST
    v
FastAPI Backend
    |-- Auth Service (JWT)
    |-- Profile Service
    |-- Job Aggregation Service  -->  LinkedIn API
    |                            -->  Handshake API
    |                            -->  Indeed API
    |                            -->  USAJobs API
    |-- Scoring Engine (fit score + tier bucketing)
    |-- Salary Estimation Service  --> BLS OEWS API (fallback)
    |-- Debt Projection Engine
    |-- Results Persistence Service
    v
PostgreSQL Database
```

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding & Repository Structure

**Status:** `[ ] pending`

**Intent:**
Set up the monorepo with a `frontend/` and `backend/` directory, initialize tooling, and establish the development environment so all subsequent sub-tasks have a consistent foundation.

**Expected Outcomes:**
- `frontend/` contains a working Vite + React + TypeScript + Tailwind project that renders a placeholder page.
- `backend/` contains a working FastAPI app with a `/health` endpoint.
- A root `docker-compose.yml` spins up the backend, frontend (dev server), and a PostgreSQL instance.
- A `.env.example` lists every required secret/config key.
- A root `README.md` describes how to run the project locally.

**Todo List:**
1. Initialize `frontend/` with `npm create vite@latest` (React + TypeScript template).
2. Install and configure Tailwind CSS in the frontend.
3. Initialize `backend/` as a Python project with `pyproject.toml` (use `uv` or `poetry`). Add FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, python-dotenv, httpx, pdfplumber, python-docx as dependencies.
4. Create `backend/app/main.py` with a FastAPI instance and a `GET /health` route.
5. Write `docker-compose.yml` with services: `db` (postgres:16), `backend`, `frontend`.
6. Write `.env.example` with placeholder keys for: DATABASE_URL, SECRET_KEY, LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, HANDSHAKE_API_KEY, INDEED_PUBLISHER_ID, USAJOBS_API_KEY, BLS_API_KEY.
7. Write `README.md` with local setup instructions.

**Relevant Context:**
- Greenfield project — no existing files.
- All environment secrets must never be committed; use `.env` (git-ignored) derived from `.env.example`.

---

### Sub-Task 2 — Database Schema & Migrations

**Status:** `[ ] pending`

**Intent:**
Define the PostgreSQL schema using SQLAlchemy ORM models and wire up Alembic for migrations. This schema underpins auth, profile storage, job results, and debt records.

**Expected Outcomes:**
- Alembic initial migration creates all tables cleanly from a fresh database.
- All relationships (foreign keys, cascades) are correct.
- The schema can store everything needed for auth, profiles, debts, and saved job results.

**Todo List:**
1. Create `backend/app/models/` with the following SQLAlchemy models:
   - `User` — id, email, hashed_password, created_at
   - `Profile` — id, user_id (FK), major, interests (text array), skills (text array), experience_level (enum: entry/mid/senior), savings, updated_at
   - `StudentLoan` — id, user_id (FK), label (e.g. "Federal Direct Subsidized"), loan_type (enum: federal_subsidized/federal_unsubsidized/federal_grad_plus/private), balance, annual_interest_rate, minimum_monthly_payment
   - `JobResult` — id, user_id (FK), created_at, tier (enum: high/mid/low), job_title, company, location, salary_min, salary_max, salary_median_est, source (linkedin/handshake/indeed/usajobs), job_url, fit_score
   - `DebtProjection` — id, user_id (FK), created_at, tier (enum), median_salary_used, savings_rate_pct, months_to_payoff, total_interest_paid
2. Create `backend/app/database.py` with SQLAlchemy engine and session factory.
3. Run `alembic init` and configure `env.py` to use the app's models.
4. Generate and verify the initial migration.

**Relevant Context:**
- `backend/app/models/` (to be created in Sub-Task 1 scaffolding).
- `interests` and `skills` stored as PostgreSQL `ARRAY(Text)`.
- `DebtProjection` stores a snapshot result so the user can see how projections changed over time.
- `loan_type` enum distinguishes federal vs. private loans — relevant for future features (e.g. income-driven repayment) but used as a display label for MVP.

---

### Sub-Task 3 — Authentication Service (Register / Login / JWT)

**Status:** `[ ] pending`

**Intent:**
Implement user registration and login endpoints with JWT access + refresh token flow. This gates all profile and results endpoints.

**Expected Outcomes:**
- `POST /auth/register` creates a new user and returns tokens.
- `POST /auth/login` validates credentials and returns tokens.
- `POST /auth/refresh` exchanges a valid refresh token for a new access token.
- All protected routes reject requests without a valid access token with a 401.
- Passwords are hashed with bcrypt.

**Todo List:**
1. Add `passlib[bcrypt]` and `python-jose[cryptography]` to backend dependencies.
2. Create `backend/app/services/auth_service.py` with functions: `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`.
3. Create `backend/app/routers/auth.py` with `POST /auth/register` and `POST /auth/login` routes.
4. Create a FastAPI dependency `get_current_user` that validates the Bearer token from the `Authorization` header.
5. Add `POST /auth/refresh` route.
6. Register the auth router in `main.py`.
7. Write at least one happy-path and one failure test per endpoint using `pytest` + `httpx`.

**Relevant Context:**
- `backend/app/models/User` (Sub-Task 2).
- Access token TTL: 30 minutes. Refresh token TTL: 7 days.

---

### Sub-Task 4 — Profile & Debt Management API

**Status:** `[ ] pending`

**Intent:**
Expose CRUD endpoints so users can create and update their profile (major, interests, skills, experience level, savings) and manage their **student loan** records. This data drives the job search and debt projection.

**Expected Outcomes:**
- `GET/PUT /profile` — read and update the current user's profile.
- `GET/POST /loans` — list and add student loan records.
- `PUT/DELETE /loans/{id}` — update or remove a specific loan.
- All endpoints require authentication (use `get_current_user` dependency).
- Profile and loan data is validated with Pydantic schemas.

**Todo List:**
1. Create Pydantic schemas in `backend/app/schemas/` for `ProfileRead`, `ProfileUpdate`, `LoanRead`, `LoanCreate`, `LoanUpdate`.
2. Create `backend/app/routers/profile.py` with `GET /profile` and `PUT /profile`.
3. Create `backend/app/routers/loans.py` with `GET /loans`, `POST /loans`, `PUT /loans/{id}`, `DELETE /loans/{id}`.
4. Register both routers in `main.py`.
5. Write tests covering create, read, update, delete for loans.

**Relevant Context:**
- `backend/app/models/Profile` and `backend/app/models/StudentLoan` (Sub-Task 2).
- `experience_level` must be validated as one of: `entry`, `mid`, `senior`.
- `loan_type` must be validated as one of: `federal_subsidized`, `federal_unsubsidized`, `federal_grad_plus`, `private`.

---

### Sub-Task 5 — Job Board API Integration Layer

**Status:** `[ ] pending`

**Intent:**
Build an async aggregation service that queries LinkedIn, Handshake, Indeed, and USAJobs in parallel, normalizes results into a common schema, and returns a unified list of job listings.

**Expected Outcomes:**
- `backend/app/services/job_aggregator.py` exposes a single async function `fetch_jobs(profile: ProfileRead) -> list[NormalizedJob]` that fans out to all four sources concurrently.
- Each source adapter handles auth, pagination (first page only for MVP), and error isolation — one failing source does not block the others.
- The `NormalizedJob` Pydantic model contains: `title`, `company`, `location`, `description`, `salary_min`, `salary_max`, `source`, `url`, `posted_at`.
- Salary fields are `None` when a listing does not provide them.

**Todo List:**
1. Create `backend/app/services/job_adapters/` package with one module per source: `linkedin.py`, `handshake.py`, `indeed.py`, `usajobs.py`.
2. Each adapter implements an async function `search(keywords: str, location: str) -> list[NormalizedJob]` using `httpx.AsyncClient`.
3. Build the query keywords string from `profile.major + profile.skills + profile.interests`.
4. In `job_aggregator.py`, use `asyncio.gather(*[adapter.search(...) for adapter in adapters], return_exceptions=True)` and filter out exceptions with logging.
5. Deduplicate results by `(title, company)` to avoid cross-source duplicates.
6. Write unit tests with mocked HTTP responses for each adapter.

**Relevant Context:**
- LinkedIn Jobs API requires OAuth 2.0 app credentials.
- Handshake requires a campus/partner API key.
- Indeed Publisher API uses a publisher ID + REST calls.
- USAJobs REST API uses an API key in the `Authorization-Key` header.
- API keys come from environment variables defined in `.env.example` (Sub-Task 1).

---

### Sub-Task 6 — Job Scoring Engine & Tier Bucketing

**Status:** `[ ] pending`

**Intent:**
Score each normalized job listing against the user's profile for fit, compute a salary estimate for listings that lack salary data, and bucket jobs into High / Mid / Low tiers.

**Expected Outcomes:**
- Each `NormalizedJob` is annotated with a `fit_score` (0–100) and a `salary_median_est`.
- Jobs are split into three tiers based on fit score thresholds (High ≥ 70, Mid 40–69, Low < 40).
- Each tier object also carries `salary_range_min`, `salary_range_max`, and `salary_median` computed across all jobs in that tier.
- The BLS OEWS API is called as a fallback to fill in `salary_median_est` when a listing's `salary_min` and `salary_max` are both `None`.

**Todo List:**
1. Create `backend/app/services/scoring_engine.py`.
2. Implement `compute_fit_score(job: NormalizedJob, profile: ProfileRead) -> int`:
   - Keyword overlap between job description and profile skills/interests: up to 50 points.
   - Major-to-job-title relevance (simple keyword match): up to 30 points.
   - Experience level alignment (entry jobs for entry profiles, etc.): up to 20 points.
3. Create `backend/app/services/salary_service.py` with `estimate_salary(job_title: str) -> float` that calls the BLS OEWS API.
4. Implement `bucket_jobs(scored_jobs: list[ScoredJob]) -> TieredResults` that produces the three-tier structure with per-tier salary stats.
5. Write unit tests for fit scoring with mock profiles and jobs.

**Relevant Context:**
- BLS OEWS API endpoint: `https://api.bls.gov/publicAPI/v2/timeseries/data/` with series IDs for occupational wages.
- BLS API key from environment variable `BLS_API_KEY`.
- Fit scoring is intentionally simple for MVP — no ML, pure keyword overlap and heuristics.

---

### Sub-Task 7 — Student Loan Payoff Projection Engine

**Status:** `[ ] pending`

**Intent:**
Given a user's student loans and a salary figure, calculate month-by-month how long it takes to pay off all loans, accounting for compound interest and minimum payments. All logic and assumptions are anchored to US student loan conventions.

**Expected Outcomes:**
- `backend/app/services/debt_projection.py` exposes `project_payoff(loans: list[LoanRead], annual_salary: float, savings_rate_pct: float) -> ProjectionResult`.
- `ProjectionResult` contains: `months_to_payoff`, `total_interest_paid`, `monthly_breakdown` (list of month snapshots with remaining balance per loan).
- The function is called once per tier (using that tier's `salary_median`) to produce three projections shown side-by-side.
- Savings rate defaults to 20% of after-tax take-home but is configurable by the user.

**Expected Calculation Logic:**
1. Compute monthly after-tax income using the US 2024 federal income tax brackets (single filer). Apply the correct marginal rates across the brackets; do NOT use a flat rate.
   - 10% on income $0–$11,600
   - 12% on income $11,601–$47,150
   - 22% on income $47,151–$100,525
   - 24% on income $100,526–$191,950
   - 32% on income $191,951–$243,725
   - 35% on income $243,726–$609,350
   - 37% above $609,350
   - Also apply 7.65% FICA (Social Security + Medicare) on gross income.
2. `monthly_loan_payment = monthly_after_tax_income * (savings_rate_pct / 100)`.
3. Apply the **avalanche method** (pay minimum on all loans, put any surplus toward the highest-interest loan). This is optimal for student loans which often have varying rates across federal/private loans.
4. Each month: accrue interest on each loan (`balance * (annual_rate / 12)`), apply minimum payments, then apply surplus to the highest-interest loan.
5. Stop when all loan balances reach zero.
6. Cap simulation at 600 months (50 years) to avoid infinite loops for unrealistic inputs.

**Todo List:**
1. Create `backend/app/services/debt_projection.py` with the `project_payoff` function and `ProjectionResult` Pydantic model.
2. Implement a `compute_monthly_take_home(annual_salary: float) -> float` helper using the 2024 US federal tax brackets and FICA deductions.
3. Implement the month-by-month avalanche loop.
4. Create a `POST /projections/calculate` endpoint in `backend/app/routers/projections.py` that accepts the user's loans + salary + savings rate and returns results for all three tiers.
5. Persist the projection results to `DebtProjection` table after calculation.
6. Create a `GET /projections` endpoint to retrieve saved projections for the current user.
7. Write unit tests for `compute_monthly_take_home` with known salary inputs and expected after-tax outputs. Write unit tests for the avalanche loop with known inputs and expected payoff months.

**Relevant Context:**
- `backend/app/models/DebtProjection` and `backend/app/models/StudentLoan` (Sub-Task 2).
- Monthly interest rate = `annual_rate / 12`.
- Tax brackets above are for 2024 (single filer, standard deduction of $14,600 already applied to taxable income). Update bracket thresholds if the year changes.
- FICA rate: 6.2% Social Security (on wages up to $168,600) + 1.45% Medicare = 7.65% total for the employee share.

---

### Sub-Task 8 — Main Results Endpoint (Orchestration)

**Status:** `[ ] pending`

**Intent:**
Wire Sub-Tasks 5, 6, and 7 together into a single `POST /results/generate` endpoint that a user calls to kick off the full pipeline: fetch jobs → score → tier → project debt payoff → persist → return.

**Expected Outcomes:**
- `POST /results/generate` returns a fully populated `ResultsResponse` with three tiers, each containing job listings, salary stats, and debt projection.
- Results are saved to the `JobResult` and `DebtProjection` tables.
- `GET /results/latest` returns the most recently generated results for the current user.
- The endpoint handles the case where a job board API key is missing gracefully (skip that source, still return results from others).

**Todo List:**
1. Create `backend/app/routers/results.py` with `POST /results/generate` and `GET /results/latest`.
2. In the generate handler: load user profile and debts → call `job_aggregator.fetch_jobs` → call `scoring_engine.bucket_jobs` → call `debt_projection.project_payoff` for each tier → persist → return response.
3. Define `ResultsResponse` Pydantic schema with `high_tier`, `mid_tier`, `low_tier` each containing `jobs`, `salary_stats`, and `debt_projection`.
4. Register the results router in `main.py`.
5. Write an integration test that mocks all external APIs and validates the full pipeline end-to-end.

**Relevant Context:**
- `job_aggregator.py`, `scoring_engine.py`, `debt_projection.py` (Sub-Tasks 5, 6, 7).
- All external HTTP calls must be mocked in tests.

---

### Sub-Task 9 — Frontend: Profile & Debt Input Forms

**Status:** `[ ] pending`

**Intent:**
Build the React UI for user registration/login and the structured profile + debt input forms.

**Expected Outcomes:**
- `/register` and `/login` pages with form validation and error display.
- `/profile` page with fields: major (text), interests (tag input), skills (tag input), experience level (dropdown), savings (currency input).
- `/loans` section on the same page: list of student loan cards, each with label, loan type (dropdown: Federal Subsidized / Federal Unsubsidized / Federal Grad PLUS / Private), balance, annual interest rate, minimum monthly payment. Users can add and remove loans.
- On submit, the frontend calls `PUT /profile` and the debts CRUD endpoints.
- A resume upload field (PDF/DOCX) on the profile page — the file is sent to the backend for text extraction but is not persisted as a file; extracted text is stored in the session for use during job matching.
- JWT stored in `localStorage`; attached as `Authorization: Bearer <token>` header on all API calls.

**Todo List:**
1. Set up React Router with routes for `/login`, `/register`, `/profile`, `/results`.
2. Create an `api/` utility module (axios or fetch wrapper) that auto-attaches the auth token.
3. Build `LoginPage` and `RegisterPage` components with form validation.
4. Build `ProfileForm` component with tag-input for skills and interests.
5. Build `LoanList` component with add/edit/delete student loan cards (label, loan type dropdown, balance, rate, minimum payment fields).
6. Build `ResumeUpload` component that sends the file to `POST /resume/extract` and stores extracted text in React state.
7. Wire all form submissions to the backend API.

**Relevant Context:**
- Tailwind CSS for styling.
- No external form library required for MVP — use React controlled components.
- Resume text from the upload is passed as part of the `POST /results/generate` request body to supplement job matching.
- Loan type dropdown values must exactly match the `loan_type` enum: `federal_subsidized`, `federal_unsubsidized`, `federal_grad_plus`, `private`.

---

### Sub-Task 10 — Frontend: Results Dashboard

**Status:** `[ ] pending`

**Intent:**
Build the results dashboard that displays the three job tiers, salary ranges, and debt payoff projections in a clear, scannable layout.

**Expected Outcomes:**
- `/results` page shows three columns or tabs: High Fit, Mid Fit, Low Fit.
- Each tier shows: job count, salary range (min–max), median salary, and a list of job cards (title, company, location, source badge, link to listing).
- Below the tiers, a "Student Loan Payoff Projection" section shows a side-by-side comparison: for each tier's median salary, how many months to pay off all loans and total interest paid.
- A simple bar or line chart visualizes months-to-payoff across the three tiers.
- A "Regenerate" button re-calls `POST /results/generate`.
- A "Saved Results" section shows past result snapshots.

**Todo List:**
1. Build `TierColumn` component (job count, salary stats, job card list).
2. Build `JobCard` component (title, company, location, fit score badge, source badge, external link).
3. Build `LoanProjectionComparison` component showing the three-tier side-by-side numbers (months to payoff, total interest paid, estimated monthly payment required).
4. Integrate a lightweight chart library (e.g. Recharts) to show months-to-payoff as a bar chart.
5. Build `SavedResultsList` component that calls `GET /results/latest`.
6. Wire the "Regenerate" button to `POST /results/generate` and refresh the page state.

**Relevant Context:**
- React state for current results; no global state manager needed for MVP.
- Recharts is the recommended chart library — lightweight and React-native.

---

### Sub-Task 11 — Resume Text Extraction Endpoint

**Status:** `[ ] pending`

**Intent:**
Add a lightweight backend endpoint that accepts a PDF or DOCX file, extracts plain text, and returns it. The text is used by the job scoring engine to improve match quality.

**Expected Outcomes:**
- `POST /resume/extract` accepts a multipart file upload (PDF or DOCX, max 5 MB).
- Returns `{ "text": "..." }` with the extracted plain text.
- Endpoint is authenticated.
- The extracted text is NOT stored in the database — it is used only at request time.

**Todo List:**
1. Add `pdfplumber` (PDF) and `python-docx` (DOCX) to backend dependencies (should already be in Sub-Task 1).
2. Create `backend/app/routers/resume.py` with `POST /resume/extract`.
3. Detect file type by MIME type or extension; route to the correct parser.
4. Return extracted text, stripped of excessive whitespace.
5. Modify the scoring engine to optionally accept `resume_text: str | None` and use it as an additional keyword source in `compute_fit_score`.
6. Register the resume router in `main.py`.

**Relevant Context:**
- `backend/app/services/scoring_engine.py` (Sub-Task 6).
- File size limit enforced in FastAPI via `UploadFile` max-size validation.

---

## Key Design Decisions & Trade-offs

| Decision | Choice | Rationale |
|---|---|---|
| Backend language | Python / FastAPI | Async HTTP fan-out, strong text-processing libs, Pydantic fits data-heavy validation |
| Job scope | US listings only (LinkedIn, Handshake, Indeed, USAJobs) | User confirmed US-only scope |
| Debt scope | Student and academic loans only | User confirmed; keeps the debt model focused and avoids over-engineering |
| Loan types supported | Federal Subsidized, Federal Unsubsidized, Federal Grad PLUS, Private | Covers all major US student loan categories |
| Job scoring | Keyword heuristics | Simple, explainable, no ML infrastructure needed for MVP |
| Salary fallback | BLS OEWS API | Free, authoritative, covers most US occupations |
| Loan payoff method | Avalanche (highest interest first) | Minimizes total interest paid; particularly effective with mixed federal/private rates |
| Tax calculation | 2024 US federal marginal tax brackets + FICA | Accurate for US single filers; much more precise than a flat rate |
| Auth | JWT access + refresh | Stateless, standard, avoids session storage complexity |
| File storage | No persistent file storage | Resume text extracted and discarded — reduces storage complexity and privacy risk |

---

## Environment Variables Required

```
DATABASE_URL=postgresql://user:pass@localhost:5432/careerplanner
SECRET_KEY=<random 64-char hex>
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
HANDSHAKE_API_KEY=
INDEED_PUBLISHER_ID=
USAJOBS_API_KEY=
BLS_API_KEY=
```
