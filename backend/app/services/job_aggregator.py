from __future__ import annotations

import asyncio
import logging

from app.config import Settings
from app.schemas.job import NormalizedJob
from app.schemas.profile import ProfileRead
from app.services.job_adapters import handshake, indeed, linkedin, usajobs

logger = logging.getLogger(__name__)

_MAX_KEYWORDS = 10


def _build_keywords(profile: ProfileRead) -> str:
    """Build a deduplicated keyword string from profile major, skills, and interests.

    Returns up to _MAX_KEYWORDS unique terms joined by spaces.
    """
    seen: set[str] = set()
    terms: list[str] = []
    for raw in [profile.major] + list(profile.skills) + list(profile.interests):
        word = raw.strip()
        if word and word.lower() not in seen:
            seen.add(word.lower())
            terms.append(word)
            if len(terms) >= _MAX_KEYWORDS:
                break
    return " ".join(terms)


async def fetch_jobs(profile: ProfileRead, settings: Settings) -> list[NormalizedJob]:
    """Fetch and aggregate job listings from all four sources concurrently.

    Each adapter is called in parallel via asyncio.gather.  Failures in
    individual adapters are logged but do not prevent results from other
    sources from being returned.

    Args:
        profile: The user's profile providing keywords for the search.
        settings: Application settings containing API keys.

    Returns:
        Deduplicated list of NormalizedJob instances across all sources.
    """
    keywords = _build_keywords(profile)
    location = "United States"

    results = await asyncio.gather(
        linkedin.search(keywords, location, settings.linkedin_client_secret),
        handshake.search(keywords, location, settings.handshake_api_key),
        indeed.search(keywords, location, settings.indeed_publisher_id),
        usajobs.search(keywords, location, settings.usajobs_api_key),
        return_exceptions=True,
    )

    all_jobs: list[NormalizedJob] = []
    source_names = ["linkedin", "handshake", "indeed", "usajobs"]
    for source_name, result in zip(source_names, results):
        if isinstance(result, BaseException):
            logger.error("Adapter %s raised an exception: %s", source_name, result)
        else:
            all_jobs.extend(result)

    # Deduplicate by (title.lower(), company.lower() if company else "")
    seen_keys: set[tuple[str, str]] = set()
    deduplicated: list[NormalizedJob] = []
    for job in all_jobs:
        key = (job.title.lower(), job.company.lower() if job.company else "")
        if key not in seen_keys:
            seen_keys.add(key)
            deduplicated.append(job)

    return deduplicated
