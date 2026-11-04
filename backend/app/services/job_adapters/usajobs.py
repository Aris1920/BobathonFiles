from __future__ import annotations

import logging

import httpx

from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)

_BASE_URL = "https://data.usajobs.gov/api/Search"


async def search(keywords: str, location: str, api_key: str) -> list[NormalizedJob]:
    """Search USAJobs REST API and return normalized job listings.

    Args:
        keywords: Search query string.
        location: Location string (informational; API targets United States).
        api_key: USAJobs API key (Authorization-Key header).

    Returns:
        List of NormalizedJob objects, or [] on error / missing key.
    """
    if not api_key:
        return []

    params = {
        "Keyword": keywords,
        "LocationName": "United+States",
        "ResultsPerPage": 25,
    }
    headers = {
        "Authorization-Key": api_key,
        "User-Agent": "career-debt-planner",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("USAJobs adapter error: %s", exc)
        return []

    search_result = data.get("SearchResult", {}) or {}
    items = search_result.get("SearchResultItems", []) or []

    jobs: list[NormalizedJob] = []
    for item in items:
        descriptor = item.get("MatchedObjectDescriptor", {}) or {}
        title = descriptor.get("PositionTitle", "") or ""
        company = descriptor.get("OrganizationName") or None
        location_val = descriptor.get("PositionLocationDisplay") or None
        user_area = descriptor.get("UserArea", {}) or {}
        details = user_area.get("Details", {}) or {}
        description = details.get("JobSummary") or None
        apply_url = descriptor.get("PositionURI") or None
        posted_at_raw = descriptor.get("PublicationStartDate") or None
        posted_at = None
        if posted_at_raw:
            try:
                from datetime import datetime, timezone
                # USAJobs format: "2025-01-01" or "2025-01-01T00:00:00.0000000"
                posted_at = datetime.fromisoformat(str(posted_at_raw).split("T")[0])
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        salary_min: float | None = None
        salary_max: float | None = None
        remunerations = descriptor.get("PositionRemuneration", []) or []
        if remunerations:
            first = remunerations[0]
            try:
                min_raw = first.get("MinimumRange")
                if min_raw is not None:
                    salary_min = float(min_raw)
            except (ValueError, TypeError):
                pass
            try:
                max_raw = first.get("MaximumRange")
                if max_raw is not None:
                    salary_max = float(max_raw)
            except (ValueError, TypeError):
                pass

        if title:
            jobs.append(
                NormalizedJob(
                    title=title,
                    company=company,
                    location=location_val,
                    description=description,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    source="usajobs",
                    url=apply_url,
                    posted_at=posted_at,
                )
            )

    return jobs
