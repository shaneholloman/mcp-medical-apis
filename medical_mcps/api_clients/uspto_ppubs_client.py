"""USPTO Patent Public Search (PPUBS) client.

Searches granted patents and published applications via ppubs.uspto.gov.
No API key required. Establishes a session cookie before querying.

Search syntax examples:
  "machine learning"           - full-text phrase
  TTL/"drug delivery"          - title search
  ABST/"gene therapy"          - abstract search
  IN/Smith AND AN/Pfizer       - inventor + assignee
  CPC/A61K31                   - CPC classification
  PN/10000000                  - patent number

BACKGROUND: Alternatives considered (2026-04-24 scout report)
- patent_client (https://github.com/parkerhancock/patent_client): Python ORM-style lib
  wrapping USPTO PPUBS + ODP + Assignments + EPO Inpadoc; uses httpx + hishel like us.
  Strong drop-in candidate. Caveat: archived 2026-04-24 (v5.0.19); successor is
  patent-client-agents — spike before adopting v5 long-term.
- openpharma-org/patents-mcp (https://github.com/openpharma-org/patents-mcp): MCP combining
  USPTO ODP + Google Patents BigQuery for 11+ jurisdictions. Heavier (needs GCP creds);
  better for cross-jurisdiction batch landscaping than per-tool calls.
- Google Patents BigQuery (https://github.com/google/patents-public-data): ~90M docs,
  17 countries, US full-text. First 1 TB/mo free. Best for batch analytics, not RPC.
- Lens.org Patent API (https://about.lens.org/lens-apis/): free for non-commercial /
  academic use but tokens expire after 14 days — not viable for production MCP.
- PQAI (https://search.projectpq.ai/): open-source semantic prior-art search.
  Free tier = 20 results/query, web only; PQAI+ $20/mo with limited API.
- NOT: PatentsView API (https://patentsview.org/) — shut down 2026-03-20, data
  migrated to USPTO ODP bulk. Anything pointing here is dead.
- NOT: USPTO Office Action / Enriched Citation APIs — decommissioned early 2026.
"""

import logging
from typing import Any

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

PPUBS_BASE_URL = "https://ppubs.uspto.gov"
PPUBS_SESSION_URL = f"{PPUBS_BASE_URL}/api/users/me/session"
PPUBS_SEARCH_URL = f"{PPUBS_BASE_URL}/api/searches/searchWithBeFamily"

SOURCE_GRANTED = "USPAT"
SOURCE_APPLICATIONS = "US-PGPUB"


class USPTOPpubsClient(BaseAPIClient):
    """Client for the USPTO Patent Public Search API (ppubs.uspto.gov).

    Requires a session cookie obtained by POST to /api/users/me/session.
    The session and access token are cached per instance.
    """

    def __init__(self, enable_cache: bool | None = None):
        super().__init__(
            base_url=PPUBS_BASE_URL,
            api_name="uspto_ppubs",
            timeout=45.0,
            enable_cache=enable_cache,
        )
        self._case_id: str | None = None
        self._access_token: str | None = None

    def _create_client(self):
        import httpx
        from hishel import AsyncSqliteStorage
        from hishel.httpx import AsyncCacheClient

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "medical-mcps/1.0",
            "Origin": PPUBS_BASE_URL,
            "Referer": f"{PPUBS_BASE_URL}/pubwebapp/",
        }
        if self.enable_cache:
            try:
                storage = AsyncSqliteStorage(
                    database_path=str(self.cache_dir / "uspto_ppubs.db"),
                    default_ttl=3600,  # 1 hour - search results change
                )
                return AsyncCacheClient(
                    storage=storage,
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers=headers,
                )
            except Exception:
                pass
        return httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers,
        )

    async def _ensure_session(self) -> None:
        """Establish or refresh a PPUBS session."""
        if self._case_id is not None:
            return

        logger.info("Establishing USPTO PPUBS session")
        # Hit the webapp page first to get cookies; bypass cache so Set-Cookie headers are live
        await self.client.get(
            f"{PPUBS_BASE_URL}/pubwebapp/",
            headers={"Cache-Control": "no-store"},
        )

        response = await self.client.post(
            PPUBS_SESSION_URL,
            json=-1,
            headers={"X-Access-Token": "null", "Cache-Control": "no-store"},
        )
        response.raise_for_status()

        data = response.json()
        self._case_id = data["userCase"]["caseId"]
        self._access_token = response.headers.get("X-Access-Token", "")
        self.client.headers["X-Access-Token"] = self._access_token
        logger.info("PPUBS session established, case_id=%s", self._case_id)

    def _build_query_payload(
        self,
        query: str,
        sources: list[str],
        offset: int,
        limit: int,
        sort: str,
    ) -> dict[str, Any]:
        import re as _re

        # PPUBS BRS rejects `PN/<digits>` (prefix syntax for patent numbers) and
        # returns 0 results. The canonical form is the suffix-dot syntax
        # `<digits>.PN.`, which yields the exact patent. Rewrite transparently so
        # callers can use either spelling.
        m = _re.fullmatch(r"\s*PN/(\d+)\s*", query, _re.IGNORECASE)
        if m:
            query = f"{m.group(1)}.PN."

        # For bare PN/ or AN/ lookups (no parentheses after the slash), prefer USPAT as
        # the family representative — the default preference (US-PGPUB first) would collapse
        # a granted-patent query to its pre-grant application and return 0 results.
        is_pn_an_lookup = bool(_re.search(r"\b(PN|AN)/[^\s(]", query, _re.IGNORECASE))
        first_preferred = "USPAT" if is_pn_an_lookup else "US-PGPUB"
        second_preferred = "US-PGPUB" if is_pn_an_lookup else "USPAT"

        return {
            "start": offset,
            "pageCount": min(limit, 500),
            "sort": sort,
            "docFamilyFiltering": "familyIdFiltering",
            "searchType": 1,
            "familyIdEnglishOnly": True,
            "familyIdFirstPreferred": first_preferred,
            "familyIdSecondPreferred": second_preferred,
            "familyIdThirdPreferred": "FPRS",
            "showDocPerFamilyPref": "showEnglish",
            "queryId": 0,
            "tagDocSearch": False,
            "query": {
                "caseId": self._case_id,
                "hl_snippets": "2",
                "op": "OR",
                "q": query,
                "queryName": query,
                "highlights": "1",
                "qt": "brs",
                "spellCheck": False,
                "viewName": "tile",
                "plurals": True,
                "britishEquivalents": True,
                "databaseFilters": [
                    {"databaseName": s, "countryCodes": []} for s in sources
                ],
                "searchType": 1,
                "ignorePersist": True,
                "userEnteredQuery": query,
            },
        }

    def _format_patent(self, doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "guid": doc.get("guid"),
            "patent_number": doc.get("patentNumber") or doc.get("guid"),
            "title": doc.get("inventionTitle") or doc.get("title"),
            "publication_date": doc.get("datePublished") or doc.get("datePubl"),
            "filing_date": doc.get("applicationFilingDate") or doc.get("filingDate"),
            "inventors": doc.get("inventorsShort") or doc.get("inventorNames"),
            "assignee": doc.get("assigneeName") or doc.get("assigneeNames"),
            "source_type": doc.get("type") or doc.get("sourceType"),
            "cpc_codes": doc.get("cpcInventiveFlattened") or doc.get("cpcCodes"),
        }

    async def search(
        self,
        query: str,
        sources: list[str],
        offset: int = 0,
        limit: int = 25,
        sort: str = "date_publ desc",
    ) -> dict[str, Any]:
        await self._ensure_session()

        payload = self._build_query_payload(query, sources, offset, limit, sort)

        response = await self.client.post(PPUBS_SEARCH_URL, json=payload)

        # 400 = invalid caseId in payload (session evicted server-side)
        # 401/403 = token expired; refresh session and retry once
        if response.status_code in (400, 401, 403):
            self._case_id = None
            self._access_token = None
            await self._ensure_session()
            payload["query"]["caseId"] = self._case_id
            response = await self.client.post(PPUBS_SEARCH_URL, json=payload)

        import httpx as _httpx
        try:
            response.raise_for_status()
        except _httpx.HTTPStatusError as e:
            raise Exception(self._extract_error_message(e)) from e
        result = response.json()

        docs = result.get("patents") or result.get("docs") or []
        total = result.get("numFound") or result.get("total") or len(docs)

        return {
            "api_source": "USPTO_PPUBS",
            "data": [self._format_patent(d) for d in docs],
            "metadata": {
                "total": total,
                "offset": offset,
                "limit": limit,
                "query": query,
                "sources": sources,
            },
        }

    async def search_patents(
        self,
        query: str,
        offset: int = 0,
        limit: int = 25,
        sort: str = "date_publ desc",
    ) -> dict[str, Any]:
        """Search granted US patents."""
        return await self.search(
            query=query,
            sources=[SOURCE_GRANTED],
            offset=offset,
            limit=limit,
            sort=sort,
        )

    async def search_applications(
        self,
        query: str,
        offset: int = 0,
        limit: int = 25,
        sort: str = "date_publ desc",
    ) -> dict[str, Any]:
        """Search published US patent applications (pre-grant)."""
        return await self.search(
            query=query,
            sources=[SOURCE_APPLICATIONS],
            offset=offset,
            limit=limit,
            sort=sort,
        )
