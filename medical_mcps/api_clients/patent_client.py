"""Patent and exclusivity retrieval client (FDA-focused v1)."""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)

OPENFDA_BASE_URL = "https://api.fda.gov"
OPENFDA_DRUGSFDA_URL = f"{OPENFDA_BASE_URL}/drug/drugsfda.json"
DEFAULT_LIMIT = 25
MAX_LIMIT = 100


class PatentClient(BaseAPIClient):
    """Client for public patent/exclusivity signals used by IP screening."""

    def __init__(self):
        super().__init__(
            base_url=OPENFDA_BASE_URL,
            api_name="Patent",
            timeout=60.0,
            rate_limit_delay=1.5,
        )

    @staticmethod
    def _sanitize(text: str, max_length: int = 100) -> str:
        sanitized = re.sub(r'[<>"\';\\]', "", text)
        return sanitized[:max_length].strip()

    @staticmethod
    def _parse_date(value: str | None) -> str | None:
        if not value:
            return None
        for fmt in ["%b %d, %Y", "%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"]:
            try:
                return datetime.strptime(value.strip(), fmt).date().isoformat()
            except ValueError:
                continue
        return None

    @staticmethod
    def _is_expired(date_str: str | None) -> bool | None:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str).date() < datetime.now(UTC).date()
        except ValueError:
            return None

    @staticmethod
    def _extract_active_ingredient_names(product: dict[str, Any]) -> list[str]:
        return [
            ingredient.get("name")
            for ingredient in product.get("active_ingredients", [])
            if ingredient.get("name")
        ]

    @staticmethod
    def _select_active_ingredient(
        ingredient_names: list[str], active_ingredient: str | None
    ) -> str | None:
        if not ingredient_names:
            return None
        if not active_ingredient:
            return ingredient_names[0]

        normalized_query = active_ingredient.casefold()
        for ingredient_name in ingredient_names:
            if normalized_query in ingredient_name.casefold():
                return ingredient_name

        return ingredient_names[0]

    async def patent_search_orange_book(
        self,
        drug_name: str | None = None,
        active_ingredient: str | None = None,
        application_number: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> dict[str, Any]:
        """Search FDA drugs@FDA records for patents/exclusivity fields."""
        if not any([drug_name, active_ingredient, application_number]):
            return {
                "api_source": "FDA_drugsfda",
                "data": [],
                "metadata": {
                    "error": "Provide drug_name, active_ingredient, or application_number.",
                    "suggested_next_steps": [
                        "Retry with active_ingredient (e.g., 'losartan potassium')."
                    ],
                },
            }

        search_parts: list[str] = []
        if application_number:
            app = self._sanitize(application_number, 32)
            search_parts.append(
                f'(products.application_number:"{app}" OR submissions.application_number:"{app}")'
            )
        if drug_name:
            dn = self._sanitize(drug_name)
            search_parts.append(
                f'(openfda.brand_name:"{dn}" OR products.brand_name:"{dn}" OR products.generic_name:"{dn}")'
            )
        if active_ingredient:
            ai = self._sanitize(active_ingredient)
            search_parts.append(f'products.active_ingredients.name:"{ai}"')

        params = {
            "search": " AND ".join(search_parts),
            "limit": min(limit, MAX_LIMIT),
        }

        response_txt = await self._request(
            "GET", url=OPENFDA_DRUGSFDA_URL, params=params, return_json=False
        )
        payload = json.loads(response_txt)
        results = payload.get("results", [])

        output = []
        for item in results:
            products = item.get("products", [])
            submissions = item.get("submissions", [])
            openfda = item.get("openfda", {})

            for product in products[:5]:
                ingredient_names = self._extract_active_ingredient_names(product)
                app_number = (
                    product.get("application_number")
                    or item.get("application_number")
                    or (submissions[0].get("application_number") if submissions else None)
                )
                patents = []
                for patent in product.get("patents", [])[:10]:
                    exp = self._parse_date(patent.get("patent_expire_date"))
                    patents.append(
                        {
                            "patent_number": patent.get("patent_number"),
                            "expiry_date": exp,
                            "patent_use_code": patent.get("patent_use_code"),
                            "patent_use_description": patent.get("patent_use_description"),
                            "is_expired": self._is_expired(exp),
                        }
                    )

                output.append(
                    {
                        "application_number": app_number,
                        "product_name": product.get("brand_name"),
                        "active_ingredient": self._select_active_ingredient(
                            ingredient_names, active_ingredient
                        ),
                        "active_ingredients": ingredient_names,
                        "applicant": item.get("sponsor_name") or item.get("openfda", {}).get("manufacturer_name"),
                        "te_code": product.get("te_code"),
                        "approval_date": self._parse_date(
                            submissions[0].get("submission_status_date") if submissions else None
                        ),
                        "patents": patents,
                        "exclusivities": product.get("exclusivity", []),
                        "source_id": item.get("application_number"),
                        "openfda_generic_names": openfda.get("generic_name", []),
                    }
                )

        suggestions = [
            "Call patent_get_exclusivities with application_number to evaluate non-patent barriers.",
            "If no patents returned, retry with a salt/form synonym or brand name.",
        ]

        if not output:
            suggestions.insert(0, "No drugs@FDA matches found. Verify spelling and indication context.")

        return {
            "api_source": "FDA_drugsfda",
            "data": output,
            "metadata": {
                "total": len(output),
                "query": {
                    "drug_name": drug_name,
                    "active_ingredient": active_ingredient,
                    "application_number": application_number,
                },
                "suggested_next_steps": suggestions,
            },
        }

    async def patent_get_exclusivities(
        self,
        application_number: str | None = None,
        active_ingredient: str | None = None,
    ) -> dict[str, Any]:
        """Get non-patent exclusivity signals from FDA drugs@FDA fields."""
        if not application_number and not active_ingredient:
            return {
                "api_source": "FDA_drugsfda",
                "data": [],
                "metadata": {"error": "Provide application_number or active_ingredient."},
            }

        search_parts: list[str] = []
        if application_number:
            app = self._sanitize(application_number, 32)
            search_parts.append(
                f'(products.application_number:"{app}" OR submissions.application_number:"{app}")'
            )
        if active_ingredient:
            ai = self._sanitize(active_ingredient)
            search_parts.append(f'products.active_ingredients.name:"{ai}"')

        params = {"search": " AND ".join(search_parts), "limit": MAX_LIMIT}
        response_txt = await self._request(
            "GET", url=OPENFDA_DRUGSFDA_URL, params=params, return_json=False
        )
        payload = json.loads(response_txt)

        records: list[dict[str, Any]] = []
        for item in payload.get("results", []):
            for product in item.get("products", []):
                app_number = product.get("application_number") or item.get("application_number")
                for excl in product.get("exclusivity", []):
                    exp = self._parse_date(excl.get("expiration_date"))
                    records.append(
                        {
                            "application_number": app_number,
                            "product_name": product.get("brand_name"),
                            "code": excl.get("code"),
                            "description": excl.get("description"),
                            "expiry_date": exp,
                            "is_active": not self._is_expired(exp) if exp else None,
                        }
                    )

        return {
            "api_source": "FDA_drugsfda",
            "data": records,
            "metadata": {
                "total": len(records),
                "query": {
                    "application_number": application_number,
                    "active_ingredient": active_ingredient,
                },
                "suggested_next_steps": [
                    "Cross-check with Orange Book listings for route/form-specific context.",
                    "Escalate to counsel if exclusivity scope is material and ambiguous.",
                ],
            },
        }
