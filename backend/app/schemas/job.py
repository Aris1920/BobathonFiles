from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NormalizedJob(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    source: Literal["linkedin", "handshake", "indeed", "usajobs"]
    url: str | None = None
    posted_at: datetime | None = None
