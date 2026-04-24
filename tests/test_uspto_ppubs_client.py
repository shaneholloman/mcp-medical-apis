"""Tests for USPTO PPUBS client."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from medical_mcps.api_clients.uspto_ppubs_client import USPTOPpubsClient


def _make_mock_client(case_id="12345", access_token="tok123"):
    """Return a USPTOPpubsClient with a mocked httpx client and pre-seeded session."""
    client = USPTOPpubsClient(enable_cache=False)
    mock_http = AsyncMock()
    client._client = mock_http
    client._case_id = case_id
    client._access_token = access_token
    mock_http.headers = {"X-Access-Token": access_token}
    return client, mock_http


def _make_search_response(docs: list[dict], total: int | None = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "numFound": total if total is not None else len(docs),
        "patents": docs,
    }
    resp.raise_for_status = MagicMock()
    return resp


SAMPLE_DOC = {
    "guid": "US10000001",
    "patentNumber": "10000001",
    "inventionTitle": "Method of treating cancer using compound X",
    # Actual PPUBS API keys (BLOCKER-3 fix verification)
    "datePublished": "20180101",
    "applicationFilingDate": "20150101",
    "inventorsShort": "Smith, John",
    "assigneeName": "Pharma Corp",
    "type": "USPAT",
    "cpcInventiveFlattened": ["A61K31/00"],
}


@pytest.mark.asyncio
async def test_search_patents_returns_formatted_results():
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([SAMPLE_DOC], total=1))

    result = await client.search_patents(query="TTL/cancer")

    assert result["api_source"] == "USPTO_PPUBS"
    assert len(result["data"]) == 1
    doc = result["data"][0]
    assert doc["guid"] == "US10000001"
    assert doc["patent_number"] == "10000001"
    assert "cancer" in doc["title"].lower()
    assert result["metadata"]["total"] == 1
    assert result["metadata"]["query"] == "TTL/cancer"
    # BLOCKER-3: verify actual PPUBS field keys are mapped correctly
    assert doc["publication_date"] == "20180101"
    assert doc["filing_date"] == "20150101"
    assert doc["inventors"] == "Smith, John"
    assert doc["assignee"] == "Pharma Corp"
    assert doc["cpc_codes"] == ["A61K31/00"]
    # abstract field must NOT be present (doesn't exist at search level)
    assert "abstract" not in doc


@pytest.mark.asyncio
async def test_pn_query_prefers_uspat_family_member():
    """PN/ bare-number queries set familyIdFirstPreferred=USPAT so the granted patent is
    returned instead of being collapsed to its pre-grant application (US-PGPUB)."""
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([SAMPLE_DOC], total=1))

    await client.search_patents(query="PN/10183988")

    call_args = mock_http.post.call_args
    payload = call_args[1].get("json") or call_args[1]["json"]
    assert payload["docFamilyFiltering"] == "familyIdFiltering"
    assert payload["familyIdFirstPreferred"] == "USPAT", (
        f"PN/ query should prefer USPAT family member, got: {payload['familyIdFirstPreferred']}"
    )


@pytest.mark.asyncio
async def test_fulltext_query_uses_family_filtering():
    """Full-text queries use familyIdFiltering with US-PGPUB preferred (default)."""
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([], total=0))

    await client.search_patents(query="pembrolizumab")

    call_args = mock_http.post.call_args
    payload = call_args[1].get("json") or call_args[1]["json"]
    assert payload["docFamilyFiltering"] == "familyIdFiltering"
    assert payload["familyIdFirstPreferred"] == "US-PGPUB"


@pytest.mark.asyncio
async def test_ttl_parenthesized_query_uses_pgpub_preferred():
    """TTL/(term) content searches use familyIdFiltering with default US-PGPUB preference."""
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([], total=0))

    await client.search_patents(query="TTL/(aspirin)")

    call_args = mock_http.post.call_args
    payload = call_args[1].get("json") or call_args[1]["json"]
    assert payload["docFamilyFiltering"] == "familyIdFiltering"
    assert payload["familyIdFirstPreferred"] == "US-PGPUB"


@pytest.mark.asyncio
async def test_an_bare_query_prefers_uspat():
    """AN/number direct lookup (no parentheses) also sets familyIdFirstPreferred=USPAT."""
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([SAMPLE_DOC], total=1))

    await client.search_patents(query="AN/14412875")

    call_args = mock_http.post.call_args
    payload = call_args[1].get("json") or call_args[1]["json"]
    assert payload["familyIdFirstPreferred"] == "USPAT"


@pytest.mark.asyncio
async def test_search_applications_uses_pgpub_source():
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([], total=0))

    result = await client.search_applications(query="ABST/gleevec")

    assert result["api_source"] == "USPTO_PPUBS"
    # Verify the request included the US-PGPUB source
    call_args = mock_http.post.call_args
    payload = call_args[1].get("json") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1]["json"]
    db_filters = payload["query"]["databaseFilters"]
    sources = [f["databaseName"] for f in db_filters]
    assert "US-PGPUB" in sources
    assert "USPAT" not in sources


@pytest.mark.asyncio
async def test_search_patents_uses_uspat_source():
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([], total=0))

    await client.search_patents(query="TTL/drug")

    call_args = mock_http.post.call_args
    payload = call_args[1].get("json") or call_args[1]["json"]
    db_filters = payload["query"]["databaseFilters"]
    sources = [f["databaseName"] for f in db_filters]
    assert "USPAT" in sources
    assert "US-PGPUB" not in sources


@pytest.mark.asyncio
async def test_session_refresh_on_403():
    """On 403, client clears cached session, re-establishes it, and retries search."""
    client = USPTOPpubsClient(enable_cache=False)
    mock_http = AsyncMock()
    client._client = mock_http
    mock_http.headers = {}

    page_response = MagicMock(spec=httpx.Response)
    page_response.status_code = 200

    session_response = MagicMock(spec=httpx.Response)
    session_response.status_code = 200
    session_response.json.return_value = {"userCase": {"caseId": "99999"}}
    session_response.headers = {"X-Access-Token": "newtoken"}
    session_response.raise_for_status = MagicMock()

    forbidden_response = MagicMock(spec=httpx.Response)
    forbidden_response.status_code = 403

    success_response = _make_search_response([SAMPLE_DOC], total=1)

    mock_http.get = AsyncMock(return_value=page_response)
    # sequence: initial session POST, first search POST → 403,
    # refresh session (page GET + session POST), second search POST → 200
    mock_http.post = AsyncMock(side_effect=[
        session_response,   # _ensure_session: POST /api/users/me/session
        forbidden_response, # search: POST searchWithBeFamily → 403
        session_response,   # session refresh: POST /api/users/me/session again
        success_response,   # retry search: POST searchWithBeFamily → 200
    ])

    client._case_id = None
    client._access_token = None

    result = await client.search_patents("TTL/cancer")
    assert result["api_source"] == "USPTO_PPUBS"
    assert result["metadata"]["total"] == 1
    # Verify session was refreshed: POST was called 4 times (session + search + session + search)
    assert mock_http.post.call_count == 4


@pytest.mark.asyncio
async def test_session_refresh_on_400():
    """On 400 (invalid caseId from evicted server-side session), client refreshes and retries."""
    client = USPTOPpubsClient(enable_cache=False)
    mock_http = AsyncMock()
    client._client = mock_http
    mock_http.headers = {}

    page_response = MagicMock(spec=httpx.Response)
    page_response.status_code = 200

    session_response = MagicMock(spec=httpx.Response)
    session_response.status_code = 200
    session_response.json.return_value = {"userCase": {"caseId": "77777"}}
    session_response.headers = {"X-Access-Token": "freshtoken"}
    session_response.raise_for_status = MagicMock()

    bad_request_response = MagicMock(spec=httpx.Response)
    bad_request_response.status_code = 400

    success_response = _make_search_response([SAMPLE_DOC], total=1)

    mock_http.get = AsyncMock(return_value=page_response)
    # sequence: session creation, search → 400, session refresh, search → 200
    mock_http.post = AsyncMock(side_effect=[
        session_response,
        bad_request_response,
        session_response,
        success_response,
    ])

    client._case_id = None
    client._access_token = None

    result = await client.search_patents("TTL/(cancer) AND AN/(Novartis)")
    assert result["api_source"] == "USPTO_PPUBS"
    assert result["metadata"]["total"] == 1


@pytest.mark.asyncio
async def test_session_refresh_on_401():
    """On 401 (unauthorized), client refreshes session and retries."""
    client = USPTOPpubsClient(enable_cache=False)
    mock_http = AsyncMock()
    client._client = mock_http
    mock_http.headers = {}

    page_response = MagicMock(spec=httpx.Response)
    page_response.status_code = 200

    session_response = MagicMock(spec=httpx.Response)
    session_response.status_code = 200
    session_response.json.return_value = {"userCase": {"caseId": "88888"}}
    session_response.headers = {"X-Access-Token": "newtoken2"}
    session_response.raise_for_status = MagicMock()

    unauthorized_response = MagicMock(spec=httpx.Response)
    unauthorized_response.status_code = 401

    success_response = _make_search_response([SAMPLE_DOC], total=1)

    mock_http.get = AsyncMock(return_value=page_response)
    mock_http.post = AsyncMock(side_effect=[
        session_response,
        unauthorized_response,
        session_response,
        success_response,
    ])

    client._case_id = None
    client._access_token = None

    result = await client.search_patents("pembrolizumab")
    assert result["api_source"] == "USPTO_PPUBS"
    assert result["metadata"]["total"] == 1


@pytest.mark.asyncio
async def test_empty_results():
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([], total=0))

    result = await client.search_patents(query="TTL/nonexistentdrug12345xyz")

    assert result["data"] == []
    assert result["metadata"]["total"] == 0


@pytest.mark.asyncio
async def test_pagination_params_passed():
    client, mock_http = _make_mock_client()
    mock_http.post = AsyncMock(return_value=_make_search_response([], total=100))

    await client.search_patents(query="CPC/A61K31", offset=50, limit=10)

    call_args = mock_http.post.call_args
    payload = call_args[1].get("json") or call_args[1]["json"]
    assert payload["start"] == 50
    assert payload["pageCount"] == 10


@pytest.mark.asyncio
async def test_error_handling_http_error():
    """When HTTP request fails, return error dict instead of raising."""
    from medical_mcps.servers import uspto_ppubs_server

    with patch.object(
        USPTOPpubsClient, "search_patents", new=AsyncMock(side_effect=Exception("network error"))
    ):
        result = await uspto_ppubs_server.uspto_ppubs_search_patents(query="test")
        assert "error" in result
        assert "network error" in result["error"]
