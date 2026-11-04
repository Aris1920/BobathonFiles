"""Unit tests for backend/app/services/salary_service.py."""
from __future__ import annotations

import pytest
import httpx
import respx

from app.services.salary_service import estimate_salary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_BLS_KEY = "test-bls-key-12345"

# Minimal BLS API v2 response with a single data point
def _bls_response(value: str = "95000") -> dict:
    return {
        "status": "REQUEST_SUCCEEDED",
        "responseTime": 123,
        "message": [],
        "Results": {
            "series": [
                {
                    "seriesID": "OES000000151252",
                    "data": [
                        {
                            "year": "2023",
                            "period": "A01",
                            "periodName": "Annual",
                            "value": value,
                            "footnotes": [{}],
                        }
                    ],
                }
            ]
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_estimate_salary_known_title():
    """A known job title should call BLS and return the parsed float value."""
    respx.post("https://api.bls.gov/publicAPI/v2/timeseries/data/").mock(
        return_value=httpx.Response(200, json=_bls_response("95000"))
    )

    result = await estimate_salary("software engineer", _FAKE_BLS_KEY)

    assert result == 95000.0


@pytest.mark.asyncio
async def test_estimate_salary_unknown_title():
    """A title with no SOC mapping should return None without making any HTTP call."""
    # No respx mock is set up — if a request were made, it would raise an error.
    result = await estimate_salary("underwater basket weaver", _FAKE_BLS_KEY)
    assert result is None


@pytest.mark.asyncio
async def test_estimate_salary_empty_key():
    """An empty BLS API key should return None immediately, before any HTTP call."""
    result = await estimate_salary("software engineer", "")
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_estimate_salary_api_failure():
    """When the BLS API raises an exception, estimate_salary should return None."""
    respx.post("https://api.bls.gov/publicAPI/v2/timeseries/data/").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    result = await estimate_salary("software engineer", _FAKE_BLS_KEY)
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_estimate_salary_http_error():
    """A non-200 HTTP status code should cause estimate_salary to return None."""
    respx.post("https://api.bls.gov/publicAPI/v2/timeseries/data/").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    result = await estimate_salary("data analyst", _FAKE_BLS_KEY)
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_estimate_salary_empty_series():
    """BLS response with empty series list should return None."""
    respx.post("https://api.bls.gov/publicAPI/v2/timeseries/data/").mock(
        return_value=httpx.Response(
            200, json={"status": "REQUEST_SUCCEEDED", "Results": {"series": []}}
        )
    )

    result = await estimate_salary("nurse", _FAKE_BLS_KEY)
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_estimate_salary_case_insensitive_title():
    """Title matching should be case-insensitive (e.g. 'Software Engineer' matches 'software engineer')."""
    respx.post("https://api.bls.gov/publicAPI/v2/timeseries/data/").mock(
        return_value=httpx.Response(200, json=_bls_response("110000"))
    )

    result = await estimate_salary("Software Engineer", _FAKE_BLS_KEY)
    assert result == 110000.0
