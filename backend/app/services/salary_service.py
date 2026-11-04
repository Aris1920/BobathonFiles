from __future__ import annotations

import httpx

# Mapping of lowercased job title keywords to SOC codes (BLS OEWS series suffix)
_SOC_MAP: dict[str, str] = {
    "software engineer": "151252",
    "data analyst": "151211",
    "nurse": "291141",
    "teacher": "252021",
    "accountant": "132011",
    "marketing manager": "112021",
    "civil engineer": "172051",
    "mechanical engineer": "172141",
    "lawyer": "231011",
    "financial analyst": "132051",
    "data scientist": "152051",
    "product manager": "113021",
    "web developer": "151254",
    "graphic designer": "271024",
    "human resources": "131071",
    "registered nurse": "291141",
    "physician": "291215",
    "electrician": "472111",
    "plumber": "472152",
    "pharmacist": "291051",
}

_BLS_ENDPOINT = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def _match_soc_code(job_title: str) -> str | None:
    """Return the SOC code for the first keyword in _SOC_MAP that appears in job_title."""
    title_lower = job_title.lower()
    for keyword, soc_code in _SOC_MAP.items():
        if keyword in title_lower:
            return soc_code
    return None


async def estimate_salary(job_title: str, bls_api_key: str) -> float | None:
    """Estimate annual median salary via the BLS Public Data API v2.

    Returns the most recent annual median wage as a float, or None if:
    - the job title has no SOC code mapping,
    - the API key is empty,
    - the HTTP request fails, or
    - the response cannot be parsed.
    """
    if not bls_api_key:
        return None

    soc_code = _match_soc_code(job_title)
    if soc_code is None:
        return None

    series_id = f"OES000000{soc_code}"
    payload = {
        "seriesid": [series_id],
        "registrationkey": bls_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(_BLS_ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()

        # BLS API v2 response structure:
        # { "Results": { "series": [ { "seriesID": "...", "data": [ { "year": "2023", "period": "A01", "value": "120000", ... } ] } ] } }
        series_list = data.get("Results", {}).get("series", [])
        if not series_list:
            return None

        series_data = series_list[0].get("data", [])
        if not series_data:
            return None

        # The first entry is the most recent period
        latest = series_data[0]
        value_str = latest.get("value", "")
        if not value_str or value_str == "-":
            return None

        return float(value_str)

    except Exception:
        return None
