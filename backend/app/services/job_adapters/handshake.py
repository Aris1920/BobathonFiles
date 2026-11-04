from __future__ import annotations

import logging

import httpx

from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)

_BASE_URL = "https://app.joinhandshake.com/api/v1/jobs"


async def search(keywords: str, location: str, api_key: str) -> list[NormalizedJob]:
    """Search Handshake partner API and return normalized job listings.

    Args:
        keywords: Search query string.
        location: Location string (informational; sent as-is to API).
        api_key: Handshake partner API token.

    Returns:
        List of NormalizedJob objects, or [] on error / missing key.
    """
    if not api_key:
        return []

    params = {
        "query": keywords,
        "per_page": 25,
    }
    headers = {"Authorization": f"Token token={api_key}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Handshake adapter error: %s", exc)
        return []

    jobs: list[NormalizedJob] = []
    for result in data.get("results", []):
        title = result.get("title", "") or ""
        employer = result.get("employer", {}) or {}
        company = employer.get("name") if isinstance(employer, dict) else None
        location_val = result.get("city") or result.get("location") or None
        description = result.get("description") or None
        apply_url = result.get("apply_url") or result.get("url") or None
        posted_at_raw = result.get("created_at") or result.get("posted_at") or None
        posted_at = None
        if posted_at_raw:
            try:
                from datetime import datetime, timezone
                posted_at = datetime.fromisoformat(str(posted_at_raw).replace("Z", "+00:00"))
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        salary_min: float | None = None
        salary_max: float | None = None
        try:
            if result.get("salary_min") is not None:
                salary_min = float(result["salary_min"])
            if result.get("salary_max") is not None:
                salary_max = float(result["salary_max"])
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
                    source="handshake",
                    url=apply_url,
                    posted_at=posted_at,
                )
            )

    return jobs
