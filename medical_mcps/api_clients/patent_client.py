"""Patent and exclusivity lookup from FDA Orange Book flat files.

The FDA publishes Orange Book data as tilde-delimited text files (updated monthly):
  https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files

Files (~8 MB total):
  patent.txt       - 20K rows, patent listings per product
  exclusivity.txt  - 2K rows, exclusivity grants per product
  products.txt     - 48K rows, all approved drug products

These are loaded lazily into memory on first call and searched with plain Python.

BACKGROUND: Alternatives considered (2026-04-24 scout report)
- The Orange Book flat-file ingestion is the canonical and fastest path for
  US patent/exclusivity-linked-to-NDA data. No better public source found.
- OpenFDA drug endpoints expose Drugs@FDA but NOT the patent.txt / exclusivity.txt
  joins; the flat files remain the right substrate for this client.
- Augmented-Nature/OpenFDA-MCP-Server (https://github.com/Augmented-Nature/OpenFDA-MCP-Server):
  covers drugs@FDA + adverse events + labels + recalls but NOT Orange Book patent
  listings. Not a replacement.
- For chemistry-bearing patents (formulation, process), see SureChEMBL —
  Augmented-Nature/SureChEMBL-MCP-Server (https://github.com/Augmented-Nature/SureChEMBL-MCP-Server),
  free, ~140M chemical patent docs. Complementary to Orange Book, not a replacement.
"""

import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Orange Book directory: env var > local data/ dir > fallback
_OB_DIR = Path(
    os.environ.get(
        "ORANGE_BOOK_DIR", Path(__file__).resolve().parent.parent.parent / "data" / "orangebook"
    )
)

# Lazy-loaded file contents (list of dicts per file)
_patents: list[dict[str, str]] | None = None
_exclusivities: list[dict[str, str]] | None = None
_products: list[dict[str, str]] | None = None


def _load_tilde_file(path: Path) -> list[dict[str, str]]:
    """Parse a tilde-delimited file with a header row into a list of dicts."""
    if not path.exists():
        logger.warning("Orange Book file not found: %s", path)
        return []
    with open(path) as f:
        lines = f.readlines()
    if not lines:
        return []
    headers = lines[0].strip().split("~")
    rows = []
    for line in lines[1:]:
        values = line.strip().split("~")
        rows.append(dict(zip(headers, values)))
    return rows


def _get_patents() -> list[dict[str, str]]:
    global _patents
    if _patents is None:
        _patents = _load_tilde_file(_OB_DIR / "patent.txt")
        logger.info("Loaded %d Orange Book patent records", len(_patents))
    return _patents


def _get_exclusivities() -> list[dict[str, str]]:
    global _exclusivities
    if _exclusivities is None:
        _exclusivities = _load_tilde_file(_OB_DIR / "exclusivity.txt")
        logger.info("Loaded %d Orange Book exclusivity records", len(_exclusivities))
    return _exclusivities


def _get_products() -> list[dict[str, str]]:
    global _products
    if _products is None:
        _products = _load_tilde_file(_OB_DIR / "products.txt")
        logger.info("Loaded %d Orange Book product records", len(_products))
    return _products


def _parse_date(value: str | None) -> str | None:
    """Parse Orange Book date formats into ISO date string."""
    if not value:
        return None
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _is_expired(date_str: str | None) -> bool | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).date() < datetime.now(UTC).date()
    except ValueError:
        return None


def _normalize_app_number(raw: str) -> tuple[str | None, str]:
    """Normalize 'NDA020386' -> ('N', '020386'), 'ANDA091624' -> ('A', '091624'), 'BLA125057' -> ('B', '125057').

    Also handles already-split forms like 'N020386' or bare '020386'.
    Returns (type_prefix_or_None, numeric_part).
    """
    s = raw.strip().upper()
    for prefix, code in [("NDA", "N"), ("ANDA", "A"), ("BLA", "B")]:
        if s.startswith(prefix):
            return code, s[len(prefix) :]
    # Already short form: "N020386"
    if s and s[0] in ("N", "A", "B") and s[1:].isdigit():
        return s[0], s[1:]
    # Bare number
    return None, s


class PatentClient:
    """Client for FDA Orange Book patent/exclusivity lookups from flat files."""

    async def patent_search_orange_book(
        self,
        drug_name: str | None = None,
        active_ingredient: str | None = None,
        application_number: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Search Orange Book for patents and product info.

        Joins products.txt with patent.txt on (Appl_Type, Appl_No, Product_No).
        """
        if not any([drug_name, active_ingredient, application_number]):
            return {
                "api_source": "FDA_orange_book",
                "data": [],
                "metadata": {
                    "error": "Provide drug_name, active_ingredient, or application_number."
                },
            }

        products = _get_products()
        patents = _get_patents()

        # Filter products
        matched = products
        if active_ingredient:
            q = active_ingredient.casefold()
            matched = [p for p in matched if q in p.get("Ingredient", "").casefold()]
        if drug_name:
            q = drug_name.casefold()
            matched = [
                p
                for p in matched
                if q in p.get("Trade_Name", "").casefold()
                or q in p.get("Ingredient", "").casefold()
            ]
        if application_number:
            app_type, app_no = _normalize_app_number(application_number)
            matched = [
                p
                for p in matched
                if p.get("Appl_No", "") == app_no
                and (app_type is None or p.get("Appl_Type", "") == app_type)
            ]

        # Build patent index keyed by (Appl_Type, Appl_No, Product_No)
        patent_index: dict[tuple[str, str, str], list[dict]] = {}
        for pat in patents:
            key = (pat.get("Appl_Type", ""), pat.get("Appl_No", ""), pat.get("Product_No", ""))
            patent_index.setdefault(key, []).append(pat)

        # Deduplicate matched products by (Appl_Type, Appl_No, Product_No)
        seen: set[tuple[str, str, str]] = set()
        output = []
        for prod in matched[: limit * 3]:  # over-fetch then trim
            key = (prod.get("Appl_Type", ""), prod.get("Appl_No", ""), prod.get("Product_No", ""))
            if key in seen:
                continue
            seen.add(key)

            app_number = prod.get("Appl_Type", "") + prod.get("Appl_No", "")
            prod_patents = []
            for pat in patent_index.get(key, []):
                exp = _parse_date(pat.get("Patent_Expire_Date_Text"))
                prod_patents.append(
                    {
                        "patent_number": pat.get("Patent_No", ""),
                        "expiry_date": exp,
                        "patent_use_code": pat.get("Patent_Use_Code", ""),
                        "drug_substance_flag": pat.get("Drug_Substance_Flag", ""),
                        "drug_product_flag": pat.get("Drug_Product_Flag", ""),
                        "delist_flag": pat.get("Delist_Flag", ""),
                        "is_expired": _is_expired(exp),
                    }
                )

            output.append(
                {
                    "application_number": app_number,
                    "product_name": prod.get("Trade_Name", ""),
                    "active_ingredient": prod.get("Ingredient", ""),
                    "applicant": prod.get("Applicant_Full_Name") or prod.get("Applicant", ""),
                    "strength": prod.get("Strength", ""),
                    "dosage_form_route": prod.get("DF;Route", ""),
                    "te_code": prod.get("TE_Code", ""),
                    "approval_date": _parse_date(prod.get("Approval_Date")),
                    "rld": prod.get("RLD", ""),
                    "patents": prod_patents,
                }
            )
            if len(output) >= limit:
                break

        return {
            "api_source": "FDA_orange_book",
            "data": output,
            "metadata": {
                "total": len(output),
                "query": {
                    "drug_name": drug_name,
                    "active_ingredient": active_ingredient,
                    "application_number": application_number,
                },
                "suggested_next_steps": [
                    "Use patent_get_exclusivities to see non-patent exclusivity grants (NCE, ODE, etc.)",
                    "Cross-reference with fda_orphan_search_exclusivity for orphan drug status",
                ],
            },
        }

    async def patent_get_exclusivities(
        self,
        application_number: str | None = None,
        active_ingredient: str | None = None,
    ) -> dict[str, Any]:
        """Get non-patent exclusivity records from Orange Book."""
        if not application_number and not active_ingredient:
            return {
                "api_source": "FDA_orange_book",
                "data": [],
                "metadata": {"error": "Provide application_number or active_ingredient."},
            }

        exclusivities = _get_exclusivities()
        products = _get_products()

        # If searching by active_ingredient, first resolve to app numbers
        target_apps: set[tuple[str, str]] | None = None
        if active_ingredient:
            q = active_ingredient.casefold()
            target_apps = {
                (p.get("Appl_Type", ""), p.get("Appl_No", ""))
                for p in products
                if q in p.get("Ingredient", "").casefold()
            }

        if application_number:
            app_type, app_no = _normalize_app_number(application_number)
            target_apps_by_num = {
                (excl.get("Appl_Type", ""), excl.get("Appl_No", ""))
                for excl in exclusivities
                if excl.get("Appl_No", "") == app_no
                and (app_type is None or excl.get("Appl_Type", "") == app_type)
            }
            target_apps = (
                target_apps_by_num if target_apps is None else target_apps & target_apps_by_num
            )

        records = []
        if target_apps is None:
            return {
                "api_source": "FDA_orange_book",
                "data": [],
                "metadata": {
                    "total": 0,
                    "note": (
                        "No active exclusivities found. The Orange Book exclusivity.txt "
                        "file lists only currently-in-force exclusivities — FDA removes "
                        "records at expiry. An empty result means either (a) the application "
                        "has no exclusivities, or (b) all exclusivities have already expired. "
                        "For historical/expired exclusivity data, check Drugs@FDA approval "
                        "letters or pharsight.greyb.com via web search."
                    ),
                },
            }

        # Build product name lookup
        product_names: dict[tuple[str, str, str], str] = {
            (p.get("Appl_Type", ""), p.get("Appl_No", ""), p.get("Product_No", "")): p.get(
                "Trade_Name", ""
            )
            for p in products
        }

        for excl in exclusivities:
            key = (excl.get("Appl_Type", ""), excl.get("Appl_No", ""))
            if key not in target_apps:
                continue
            exp = _parse_date(excl.get("Exclusivity_Date"))
            records.append(
                {
                    "application_number": key[0] + key[1],
                    "product_number": excl.get("Product_No", ""),
                    "product_name": product_names.get((*key, excl.get("Product_No", "")), ""),
                    "code": excl.get("Exclusivity_Code", ""),
                    "expiry_date": exp,
                    "is_active": not _is_expired(exp) if exp else None,
                }
            )

        meta: dict[str, Any] = {
            "total": len(records),
            "query": {
                "application_number": application_number,
                "active_ingredient": active_ingredient,
            },
            "suggested_next_steps": [
                "Use fda_orphan_search_exclusivity to check orphan drug exclusivity (ODE codes)",
                "Use fda_orphan_search_oopd for full orphan designation history including pre-approval",
            ],
        }
        if not records:
            meta["note"] = (
                "No active exclusivities found. The Orange Book exclusivity.txt file lists "
                "only currently-in-force exclusivities — FDA removes records at expiry. An "
                "empty result means either (a) the application has no exclusivities, or "
                "(b) all exclusivities have already expired. For historical/expired data, "
                "check Drugs@FDA approval letters or pharsight.greyb.com via web search."
            )
        return {
            "api_source": "FDA_orange_book",
            "data": records,
            "metadata": meta,
        }
