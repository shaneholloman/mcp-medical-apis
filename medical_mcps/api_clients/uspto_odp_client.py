"""USPTO Open Data Portal (ODP) client.

Provides access to patent/application metadata, continuity (patent family),
assignments, prosecution history, and transactions via api.uspto.gov.

Requires an ODP API key obtained from https://data.uspto.gov ("My ODP" menu).
Without a key, requests return 403. Pass the key as `api_key` to each method
(stateless — not stored on the instance).

ODP application number format: digits only, no slashes (e.g., "14412875").

BACKGROUND: Alternatives considered (2026-04-24 scout report)
- patent_client (https://github.com/parkerhancock/patent_client): covers ODP
  (USApplication, Assignment, GlobalDossier, PTABDecision) in one ORM-style lib —
  could replace this client and uspto_ppubs_client in one swap. ~6h estimate.
  Caveat: archived 2026-04-24 (v5.0.19); successor patent-client-agents.
- openpharma-org/patents-mcp (https://github.com/openpharma-org/patents-mcp):
  bundles ODP + Google Patents BigQuery into an MCP. Needs USPTO key + GCP creds.
- riemannzeta/patent_mcp_server (https://github.com/riemannzeta/patent_mcp_server):
  FastMCP USPTO server (PPUBS + ODP + PTAB + Litigation). Last updated May 2025;
  several of its target APIs (PatentsView, Office Action) died after that.
- EPO OPS via python-epo-ops-client (https://github.com/ip-tools/python-epo-ops-client):
  Apache 2.0, 4 GB/mo free, INPADOC families across WIPO + national offices.
  Closes the worldwide-family gap our US-only ODP coverage doesn't reach.
- Docket Alarm (https://www.docketalarm.com/api): comprehensive prosecution + dockets,
  but PACER passthrough costs make it pay-per-use. Skip unless customer-billed.
- NOT: PatentsView API — shut down 2026-03-20.
"""

import logging
import re
from typing import Any

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

ODP_BASE_URL = "https://api.uspto.gov"


def _normalize_app_number(app_num: str) -> str:
    """Strip non-digit characters from an application number."""
    digits = re.sub(r"\D", "", app_num)
    if not digits:
        raise ValueError(f"Invalid application number: {app_num!r}")
    return digits


class USPTOOdpClient(BaseAPIClient):
    """Client for the USPTO Open Data Portal API (api.uspto.gov).

    All methods accept an optional `api_key` parameter. When provided, it is
    sent as the X-API-KEY header. ODP requires a key for production use.
    """

    def __init__(self, enable_cache: bool | None = None):
        super().__init__(
            base_url=ODP_BASE_URL,
            api_name="uspto_odp",
            timeout=30.0,
            enable_cache=enable_cache,
        )

    def _headers(self, api_key: str | None) -> dict[str, str]:
        headers: dict[str, str] = {"User-Agent": "medical-mcps/1.0"}
        if api_key:
            headers["X-API-KEY"] = api_key
        return headers

    async def _get(self, path: str, api_key: str | None) -> dict[str, Any]:
        import httpx
        url = f"{ODP_BASE_URL}{path}"
        logger.info("GET %s", url)
        try:
            response = await self.client.get(url, headers=self._headers(api_key))
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(self._extract_error_message(e)) from e
        except httpx.HTTPError as e:
            raise Exception(f"USPTO_ODP API error: {e!s}") from e

    async def get_application(self, app_num: str, api_key: str | None = None) -> dict[str, Any]:
        """Get application status and basic metadata."""
        num = _normalize_app_number(app_num)
        data = await self._get(f"/api/v1/patent/applications/{num}", api_key)
        return {"api_source": "USPTO_ODP", "data": data, "application_number": num}

    async def get_continuity(self, app_num: str, api_key: str | None = None) -> dict[str, Any]:
        """Get patent family continuity data (parent/child applications)."""
        num = _normalize_app_number(app_num)
        data = await self._get(f"/api/v1/patent/applications/{num}/continuity", api_key)
        return {"api_source": "USPTO_ODP", "data": data, "application_number": num}

    async def get_assignment(self, app_num: str, api_key: str | None = None) -> dict[str, Any]:
        """Get patent assignment / ownership records."""
        num = _normalize_app_number(app_num)
        data = await self._get(f"/api/v1/patent/applications/{num}/assignment", api_key)
        return {"api_source": "USPTO_ODP", "data": data, "application_number": num}

    async def get_transactions(self, app_num: str, api_key: str | None = None) -> dict[str, Any]:
        """Get prosecution history / transaction records."""
        num = _normalize_app_number(app_num)
        data = await self._get(f"/api/v1/patent/applications/{num}/transactions", api_key)
        return {"api_source": "USPTO_ODP", "data": data, "application_number": num}

    async def search_applications(
        self,
        *,
        assignee_name: str | None = None,
        inventor_name: str | None = None,
        patent_number: str | None = None,
        application_number: str | None = None,
        filing_date_from: str | None = None,
        filing_date_to: str | None = None,
        offset: int = 0,
        limit: int = 25,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Search patent applications by metadata filters."""
        params: dict[str, Any] = {"start": offset, "limit": limit}
        if assignee_name:
            params["assigneeName"] = assignee_name
        if inventor_name:
            params["inventorName"] = inventor_name
        if patent_number:
            params["patentNumber"] = patent_number
        if application_number:
            params["applicationNumberText"] = _normalize_app_number(application_number)
        if filing_date_from or filing_date_to:
            params["appFilingDate"] = f"{filing_date_from or '*'},{filing_date_to or '*'}"

        import urllib.parse
        qs = "&".join(
            f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()
        )
        data = await self._get(f"/api/v1/patent/applications/search?{qs}", api_key)
        return {
            "api_source": "USPTO_ODP",
            "data": data,
            "metadata": {"offset": offset, "limit": limit},
        }
