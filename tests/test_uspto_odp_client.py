"""Tests for USPTO ODP client."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from medical_mcps.api_clients.uspto_odp_client import USPTOOdpClient, _normalize_app_number


# ---------------------------------------------------------------------------
# Unit tests for _normalize_app_number helper
# ---------------------------------------------------------------------------

def test_normalize_strips_slashes():
    assert _normalize_app_number("14/412,875") == "14412875"


def test_normalize_digits_only():
    assert _normalize_app_number("14412875") == "14412875"


def test_normalize_raises_on_empty():
    with pytest.raises(ValueError):
        _normalize_app_number("abc")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_client() -> tuple[USPTOOdpClient, AsyncMock]:
    client = USPTOOdpClient(enable_cache=False)
    mock_http = AsyncMock()
    client._client = mock_http
    return client, mock_http


def _ok_response(data: dict) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


SAMPLE_APP = {
    "applicationNumber": "14412875",
    "filingDate": "2015-01-06",
    "applicationStatus": "Patented Case",
    "patentNumber": "10000001",
    "inventorName": "Smith, John",
    "assigneeName": "Pharma Corp",
}

SAMPLE_CONTINUITY = {
    "parentApplications": [],
    "childApplications": [{"applicationNumber": "16000000", "relationshipType": "Continuation"}],
}

SAMPLE_ASSIGNMENTS = {
    "assignments": [{"assigneeName": "Pharma Corp", "assignorName": "Smith, John"}]
}

SAMPLE_TRANSACTIONS = {
    "transactions": [{"date": "2018-01-01", "description": "Patent Granted"}]
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_application_returns_data():
    client, mock_http = _make_client()
    mock_http.get = AsyncMock(return_value=_ok_response(SAMPLE_APP))

    result = await client.get_application("14412875", api_key="testkey")

    assert result["api_source"] == "USPTO_ODP"
    assert result["data"] == SAMPLE_APP
    assert result["application_number"] == "14412875"
    # Verify X-API-KEY header was sent
    call_headers = mock_http.get.call_args[1]["headers"]
    assert call_headers["X-API-KEY"] == "testkey"


@pytest.mark.asyncio
async def test_get_application_normalizes_number():
    client, mock_http = _make_client()
    mock_http.get = AsyncMock(return_value=_ok_response(SAMPLE_APP))

    result = await client.get_application("14/412,875", api_key="key")
    # URL should contain normalized number
    url_called = mock_http.get.call_args[0][0]
    assert "14412875" in url_called


@pytest.mark.asyncio
async def test_get_continuity_returns_family_data():
    client, mock_http = _make_client()
    mock_http.get = AsyncMock(return_value=_ok_response(SAMPLE_CONTINUITY))

    result = await client.get_continuity("14412875", api_key="key")

    assert result["api_source"] == "USPTO_ODP"
    assert "childApplications" in result["data"]


@pytest.mark.asyncio
async def test_get_assignment_returns_ownership():
    client, mock_http = _make_client()
    mock_http.get = AsyncMock(return_value=_ok_response(SAMPLE_ASSIGNMENTS))

    result = await client.get_assignment("14412875", api_key="key")

    assert result["api_source"] == "USPTO_ODP"
    assert "assignments" in result["data"]
    # BLOCKER-1: endpoint must be singular /assignment not /assignments
    url_called = mock_http.get.call_args[0][0]
    assert url_called.endswith("/assignment"), f"Expected singular /assignment, got: {url_called}"


@pytest.mark.asyncio
async def test_get_transactions_returns_history():
    client, mock_http = _make_client()
    mock_http.get = AsyncMock(return_value=_ok_response(SAMPLE_TRANSACTIONS))

    result = await client.get_transactions("14412875", api_key="key")

    assert result["api_source"] == "USPTO_ODP"
    assert "transactions" in result["data"]


@pytest.mark.asyncio
async def test_search_applications_builds_correct_url():
    client, mock_http = _make_client()
    search_result = {"results": [], "totalCount": 0}
    mock_http.get = AsyncMock(return_value=_ok_response(search_result))

    result = await client.search_applications(
        assignee_name="Pharma Corp",
        filing_date_from="2020-01-01",
        filing_date_to="2023-12-31",
        api_key="key",
    )

    assert result["api_source"] == "USPTO_ODP"
    url_called = mock_http.get.call_args[0][0]
    assert "assigneeName" in url_called
    assert "appFilingDate" in url_called
    # MAJOR-6: ODP Swagger uses `limit` not `rows`
    assert "limit=" in url_called, f"Expected 'limit=' in URL, got: {url_called}"
    assert "rows=" not in url_called, f"Unexpected 'rows=' in URL (must use 'limit='): {url_called}"


@pytest.mark.asyncio
async def test_missing_api_key_returns_error():
    """Tools should return error dict when api_key is missing."""
    from medical_mcps.servers import uspto_odp_server

    result = await uspto_odp_server.uspto_odp_get_application(app_num="14412875", api_key="")
    assert "error" in result
    assert "api_key" in result["error"].lower() or "required" in result["error"].lower()


@pytest.mark.asyncio
async def test_get_application_error_handling():
    """When the HTTP call fails, server tool returns error dict."""
    from medical_mcps.servers import uspto_odp_server

    with patch.object(
        USPTOOdpClient, "get_application", new=AsyncMock(side_effect=Exception("connection refused"))
    ):
        result = await uspto_odp_server.uspto_odp_get_application(
            app_num="14412875", api_key="testkey"
        )
        assert "error" in result
        assert "connection refused" in result["error"]


@pytest.mark.asyncio
async def test_http_error_does_not_leak_raw_httpx():
    """Raw httpx.HTTPStatusError must not reach the caller — MAJOR-1."""
    client, mock_http = _make_client()

    raw_err = httpx.HTTPStatusError(
        "403 Forbidden",
        request=MagicMock(),
        response=MagicMock(
            status_code=403,
            reason_phrase="Forbidden",
            json=MagicMock(return_value={"error": "invalid key"}),
        ),
    )
    mock_http.get = AsyncMock(side_effect=raw_err)

    # The client._get must convert HTTPStatusError to a plain Exception
    with pytest.raises(Exception) as exc_info:
        await client.get_application("14412875", api_key="bad_key")

    err_str = str(exc_info.value)
    assert "developer.mozilla.org" not in err_str, "Raw httpx error leaked to user"
    assert "HTTP" in err_str or "403" in err_str or "USPTO_ODP" in err_str
