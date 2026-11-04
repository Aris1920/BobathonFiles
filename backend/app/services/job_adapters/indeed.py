from __future__ import annotations

import logging

import httpx

from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.indeed.com/ads/apisearch"


async def search(keywords: str, location: str, publisher_id: str) -> list[NormalizedJob]:
    """Search Indeed Publisher API and return normalized job listings.

    Args:
        keywords: Search query string.
        location: Location string (informational; API always targets United States).
        publisher_id: Indeed Publisher ID.

    Returns:
        List of NormalizedJob objects, or [] on error / missing publisher_id.
    """
    if not publisher_id:
        return []

    params = {
        "publisher": publisher_id,
        "q": keywords,
        "l": "United+States",
        "v": "2",
        "format": "json",
        "limit": 25,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Indeed adapter error: %s", exc)
        return []

    jobs: list[NormalizedJob] = []
    for result in data.get("results", []):
        title = result.get("jobtitle", "") or ""
        company = result.get("company") or None
        location_val = result.get("formattedLocation") or result.get("city") or None
        description = result.get("snippet") or None
        apply_url = result.get("url") or None
        posted_at_raw = result.get("date") or None
        posted_at = None
        if posted_at_raw:
            try:
                from datetime import datetime, timezone
                # Indeed returns dates like "Wed, 01 Jan 2025 12:00:00 GMT"
                posted_at = datetime.strptime(str(posted_at_raw), "%a, %d %b %Y %H:%M:%S %Z")
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        if title:
            jobs.append(
                NormalizedJob(
                    title=title,
                    company=company,
                    location=location_val,
                    description=description,
                    salary_min=None,
                    salary_max=None,
                    source="indeed",
                    url=apply_url,
                    posted_at=posted_at,
                )
            )

    return jobs
