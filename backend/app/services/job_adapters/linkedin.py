from __future__ import annotations

import logging

import httpx

from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.linkedin.com/v2/jobSearch"


async def search(keywords: str, location: str, api_key: str) -> list[NormalizedJob]:
    """Search LinkedIn Jobs API and return normalized job listings.

    Args:
        keywords: Space-separated search terms.
        location: Location string (not used directly; LinkedIn uses locationId).
        api_key: OAuth2 Bearer token / client secret used as bearer token.

    Returns:
        List of NormalizedJob objects, or [] on error / missing key.
    """
    if not api_key:
        return []

    params = {
        "keywords": keywords,
        "locationId": "us:0",
        "count": 25,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("LinkedIn adapter error: %s", exc)
        return []

    jobs: list[NormalizedJob] = []
    for element in data.get("elements", []):
        title = element.get("title", "") or ""
        company_detail = element.get("companyDetails", {}) or {}
        company = (
            company_detail.get("company", {}).get("name")
            if isinstance(company_detail.get("company"), dict)
            else None
        )
        location_detail = element.get("formattedLocation") or None
        description = element.get("description", {}).get("text") if isinstance(element.get("description"), dict) else None
        apply_url = element.get("applyMethod", {}).get("companyApplyUrl") if isinstance(element.get("applyMethod"), dict) else None
        posted_at_raw = element.get("listedAt")
        posted_at = None
        if posted_at_raw:
            try:
                from datetime import datetime, timezone
                # LinkedIn returns epoch milliseconds
                posted_at = datetime.fromtimestamp(int(posted_at_raw) / 1000, tz=timezone.utc)
            except (ValueError, TypeError):
                pass

        if title:
            jobs.append(
                NormalizedJob(
                    title=title,
                    company=company,
                    location=location_detail,
                    description=description,
                    salary_min=None,
                    salary_max=None,
                    source="linkedin",
                    url=apply_url,
                    posted_at=posted_at,
                )
            )

    return jobs
