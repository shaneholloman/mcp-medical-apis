"""Tests for FDA Orphan Drug client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import medical_mcps.api_clients.patent_client as pc
from medical_mcps.api_clients.fda_orphan_client import FDAOrphanClient

_EMPTY_OOPD = {"api_source": "FDA_OOPD", "data": [], "metadata": {"total": 0}}


@pytest.fixture(autouse=True)
def _reset_ob_caches():
    """Reset Orange Book caches between tests."""
    pc._patents = None
    pc._exclusivities = None
    pc._products = None
    yield
    pc._patents = None
    pc._exclusivities = None
    pc._products = None


@pytest.fixture(autouse=True)
def _mock_oopd(monkeypatch):
    """Suppress live OOPD HTTP scraping in unit tests.

    Tests that want real OOPD behavior can override search_oopd_designations
    themselves via patch.object or by not relying on autouse.
    """
    monkeypatch.setattr(
        FDAOrphanClient,
        "search_oopd_designations",
        AsyncMock(return_value=_EMPTY_OOPD),
    )


@pytest.fixture()
def _ob_with_orphan():
    """Inject Orange Book data that includes an ODE exclusivity record."""
    pc._products = [
        {
            "Ingredient": "IMATINIB MESYLATE",
            "DF;Route": "TABLET;ORAL",
            "Trade_Name": "GLEEVEC",
            "Applicant": "NOVARTIS",
            "Applicant_Full_Name": "NOVARTIS PHARMACEUTICALS",
            "Strength": "100MG",
            "Appl_Type": "N",
            "Appl_No": "021588",
            "Product_No": "001",
            "TE_Code": "",
            "Approval_Date": "May 10, 2001",
            "RLD": "Yes",
            "RS": "Yes",
            "Type": "RX",
        },
        {
            "Ingredient": "LOSARTAN POTASSIUM",
            "DF;Route": "TABLET;ORAL",
            "Trade_Name": "COZAAR",
            "Applicant": "MERCK",
            "Applicant_Full_Name": "MERCK SHARP & DOHME",
            "Strength": "50MG",
            "Appl_Type": "N",
            "Appl_No": "020386",
            "Product_No": "001",
            "TE_Code": "",
            "Approval_Date": "Apr 14, 1995",
            "RLD": "Yes",
            "RS": "Yes",
            "Type": "RX",
        },
    ]
    pc._patents = []
    pc._exclusivities = [
        # ODE for Gleevec (future expiry — active)
        {
            "Appl_Type": "N",
            "Appl_No": "021588",
            "Product_No": "001",
            "Exclusivity_Code": "ODE",
            "Exclusivity_Date": "2099-01-01",
        },
        # NCE for Gleevec (expired)
        {
            "Appl_Type": "N",
            "Appl_No": "021588",
            "Product_No": "001",
            "Exclusivity_Code": "NCE",
            "Exclusivity_Date": "2006-05-10",
        },
        # No ODE for Cozaar
        {
            "Appl_Type": "N",
            "Appl_No": "020386",
            "Product_No": "001",
            "Exclusivity_Code": "NCE",
            "Exclusivity_Date": "2000-04-14",
        },
    ]


@pytest.mark.asyncio
@pytest.mark.usefixtures("_ob_with_orphan")
async def test_search_finds_ode_by_drug_name():
    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(drug_name="gleevec")

    assert result["api_source"] == "FDA_orange_book"
    # Only OB records (OOPD is mocked empty)
    ob_records = [r for r in result["data"] if r.get("source") == "Orange_Book_ODE"]
    assert len(ob_records) == 1
    gleevec = ob_records[0]
    assert gleevec["drug_name"] == "GLEEVEC"
    assert gleevec["application_number"] == "N021588"
    assert gleevec["has_active_orphan_exclusivity"] is True
    codes = {r["code"] for r in gleevec["orphan_exclusivities"]}
    assert "ODE" in codes


@pytest.mark.asyncio
@pytest.mark.usefixtures("_ob_with_orphan")
async def test_search_finds_ode_by_ingredient():
    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(active_ingredient="imatinib")

    ob_records = [r for r in result["data"] if r.get("source") == "Orange_Book_ODE"]
    assert len(ob_records) >= 1
    codes = {r["code"] for r in ob_records[0]["orphan_exclusivities"]}
    assert "ODE" in codes


@pytest.mark.asyncio
@pytest.mark.usefixtures("_ob_with_orphan")
async def test_non_orphan_drug_not_returned():
    """Drugs without ODE/ODD should not appear in OB results."""
    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(drug_name="cozaar")

    # Cozaar has no ODE code — should produce 0 records
    assert result["data"] == []


@pytest.mark.asyncio
@pytest.mark.usefixtures("_ob_with_orphan")
async def test_search_by_application_number():
    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(application_number="NDA021588")

    ob_records = [r for r in result["data"] if r.get("source") == "Orange_Book_ODE"]
    assert len(ob_records) == 1
    assert ob_records[0]["application_number"] == "N021588"


@pytest.mark.asyncio
async def test_empty_when_no_ob_data():
    pc._products = []
    pc._exclusivities = []
    pc._patents = []

    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(drug_name="gleevec")
    assert result["data"] == []


@pytest.mark.asyncio
async def test_missing_params_returns_error():
    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity()

    assert result["data"] == []
    assert "error" in result["metadata"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("_ob_with_orphan")
async def test_active_ode_flag_set_correctly():
    """ODE with future expiry should have is_active=True."""
    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(drug_name="gleevec")

    ob_records = [r for r in result["data"] if r.get("source") == "Orange_Book_ODE"]
    gleevec = ob_records[0]
    ode_record = next(r for r in gleevec["orphan_exclusivities"] if r["code"] == "ODE")
    assert ode_record["is_active"] is True
    assert gleevec["has_active_orphan_exclusivity"] is True


@pytest.mark.asyncio
async def test_oopd_records_included_when_drug_name_given(monkeypatch):
    """When OOPD returns records, they appear in search_orphan_exclusivity output."""
    pc._products = []
    pc._exclusivities = []
    pc._patents = []

    sample_oopd_records = [
        {
            "generic_name": "IVACAFTOR",
            "trade_name": "KALYDECO",
            "date_designated": "2007-04-01",
            "designation": "Treatment of cystic fibrosis",
            "sponsor": "VERTEX PHARMACEUTICALS",
            "designation_status": "Designated",
            "date_approved": "2012-01-31",
            "exclusivity_end_date": "2019-01-31",
            "designation_number": "DRU-2006-0123",
        }
    ]
    monkeypatch.setattr(
        FDAOrphanClient,
        "search_oopd_designations",
        AsyncMock(
            return_value={
                "api_source": "FDA_OOPD",
                "data": sample_oopd_records,
                "metadata": {"total": 1},
            }
        ),
    )

    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(drug_name="ivacaftor")

    oopd_records = [r for r in result["data"] if r.get("source") == "OOPD"]
    assert len(oopd_records) == 1
    assert oopd_records[0]["drug_name"] == "KALYDECO"
    assert oopd_records[0]["designation_number"] == "DRU-2006-0123"


@pytest.mark.asyncio
async def test_oopd_failure_falls_back_to_ob(monkeypatch):
    """If OOPD scrape raises, OB data is still returned and error is noted in metadata."""
    pc._products = [
        {
            "Ingredient": "GLEEVEC INGREDIENT",
            "Trade_Name": "GLEEVEC",
            "Appl_Type": "N",
            "Appl_No": "021588",
            "Product_No": "001",
            "Applicant": "NOVARTIS",
            "Applicant_Full_Name": "NOVARTIS PHARMACEUTICALS",
        }
    ]
    pc._patents = []
    pc._exclusivities = [
        {
            "Appl_Type": "N",
            "Appl_No": "021588",
            "Product_No": "001",
            "Exclusivity_Code": "ODE",
            "Exclusivity_Date": "2099-01-01",
        }
    ]

    monkeypatch.setattr(
        FDAOrphanClient,
        "search_oopd_designations",
        AsyncMock(side_effect=Exception("OOPD timeout")),
    )

    client = FDAOrphanClient()
    result = await client.search_orphan_exclusivity(drug_name="gleevec")

    assert "oopd_error" in result["metadata"]
    ob_records = [r for r in result["data"] if r.get("source") == "Orange_Book_ODE"]
    assert len(ob_records) == 1


@pytest.mark.asyncio
async def test_get_application_details_makes_api_call():
    """get_application_details should call the FDA API and return formatted data."""
    client = FDAOrphanClient(enable_cache=False)

    mock_resp_data = {
        "meta": {"results": {"total": 1}},
        "results": [
            {
                "application_number": "NDA021588",
                "sponsor_name": "NOVARTIS PHARMACEUTICALS CORP",
                "openfda": {
                    "brand_name": ["GLEEVEC"],
                    "generic_name": ["IMATINIB MESYLATE"],
                },
                "products": [
                    {
                        "product_number": "001",
                        "brand_name": "GLEEVEC",
                        "active_ingredients": [{"name": "IMATINIB MESYLATE", "strength": "100MG"}],
                        "dosage_form": "TABLET",
                        "route": "ORAL",
                        "marketing_status": "Prescription",
                        "reference_drug": "Yes",
                    }
                ],
            }
        ],
    }

    with patch.object(
        client,
        "_request",
        new=AsyncMock(return_value=mock_resp_data),
    ):
        result = await client.get_application_details(drug_name="gleevec")

    assert result["api_source"] == "FDA_drugsfda"
    assert len(result["data"]) == 1
    assert result["data"][0]["application_number"] == "NDA021588"
    assert result["data"][0]["sponsor_name"] == "NOVARTIS PHARMACEUTICALS CORP"


@pytest.mark.asyncio
async def test_server_tool_error_handling():
    """Server tool returns error dict on unexpected exceptions."""
    from medical_mcps.servers import fda_orphan_server

    with patch.object(
        FDAOrphanClient,
        "search_orphan_exclusivity",
        new=AsyncMock(side_effect=Exception("disk error")),
    ):
        result = await fda_orphan_server.fda_orphan_search_exclusivity(drug_name="gleevec")
        assert "error" in result


# ---------------------------------------------------------------------------
# OOPD form-payload assembly (disease + drug + combined)
# ---------------------------------------------------------------------------


def _patch_oopd_http(monkeypatch):
    """Replace httpx.AsyncClient with a mock that captures form data and returns
    a response whose URL contains 'OOPD_Results' (the success-path branch)."""
    captured: dict = {}

    get_resp = MagicMock()
    get_resp.cookies = {}

    post_resp = MagicMock()
    post_resp.url = "https://accessdata.fda.gov/scripts/opdlisting/oopd/OOPD_Results.cfm?ok"
    post_resp.text = "<html></html>"

    async def _get(url, *a, **kw):
        return get_resp

    async def _post(url, data=None, cookies=None, headers=None):
        captured["data"] = data
        return post_resp

    fake = MagicMock()
    fake.get = AsyncMock(side_effect=_get)
    fake.post = AsyncMock(side_effect=_post)
    fake.__aenter__ = AsyncMock(return_value=fake)
    fake.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("httpx.AsyncClient", lambda *a, **kw: fake)
    return captured


@pytest.mark.asyncio
async def test_oopd_drug_only_sends_product_name(monkeypatch):
    """drug_name → form field 'Product_name'; 'Designation' empty."""
    monkeypatch.undo()
    captured = _patch_oopd_http(monkeypatch)

    client = FDAOrphanClient()
    out = await client.search_oopd_designations(drug_name="ivacaftor")
    assert captured["data"]["Product_name"] == "ivacaftor"
    assert captured["data"]["Designation"] == ""
    assert out["api_source"] == "FDA_OOPD"


@pytest.mark.asyncio
async def test_oopd_disease_only_sends_designation(monkeypatch):
    """disease_name → form field 'Designation'; 'Product_name' empty."""
    monkeypatch.undo()
    captured = _patch_oopd_http(monkeypatch)

    client = FDAOrphanClient()
    await client.search_oopd_designations(disease_name="cystinuria")
    assert captured["data"]["Product_name"] == ""
    assert captured["data"]["Designation"] == "cystinuria"


@pytest.mark.asyncio
async def test_oopd_combined_sends_both(monkeypatch):
    """Both → both form fields populated (AND-filter)."""
    monkeypatch.undo()
    captured = _patch_oopd_http(monkeypatch)

    client = FDAOrphanClient()
    await client.search_oopd_designations(drug_name="apremilast", disease_name="behcet")
    assert captured["data"]["Product_name"] == "apremilast"
    assert captured["data"]["Designation"] == "behcet"


@pytest.mark.asyncio
async def test_oopd_server_requires_one_param():
    """Server tool returns documented error envelope when neither param given."""
    from medical_mcps.servers import fda_orphan_server

    out = await fda_orphan_server.fda_orphan_search_oopd()
    assert out["data"] == []
    assert "drug_name" in out["metadata"]["error"]
    assert "disease_name" in out["metadata"]["error"]
