from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings  # noqa: F401  — imported to validate env early
from app.routers import auth as auth_router
from app.routers import loans as loans_router
from app.routers import profile as profile_router
from app.routers import projections as projections_router
from app.routers import resume as resume_router
from app.routers import results as results_router

app = FastAPI(
    title="Career & Debt Planner API",
    version="0.1.0",
    description="Match US job listings to your profile and project student loan payoff timelines.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(loans_router.router)
app.include_router(projections_router.router)
app.include_router(resume_router.router)
app.include_router(results_router.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Liveness probe — returns 200 when the service is up."""
    return {"status": "ok"}
