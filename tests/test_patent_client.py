import pytest

import medical_mcps.api_clients.patent_client as pc


@pytest.fixture(autouse=True)
def _reset_caches():
    """Reset lazy-loaded caches between tests."""
    pc._patents = None
    pc._exclusivities = None
    pc._products = None
    yield
    pc._patents = None
    pc._exclusivities = None
    pc._products = None


@pytest.fixture()
def _fake_ob_data():
    """Inject fake Orange Book data into the module-level caches."""
    pc._products = [
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
        {
            "Ingredient": "HYDROCHLOROTHIAZIDE; LOSARTAN POTASSIUM",
            "DF;Route": "TABLET;ORAL",
            "Trade_Name": "HYZAAR",
            "Applicant": "MERCK",
            "Applicant_Full_Name": "MERCK SHARP & DOHME",
            "Strength": "12.5MG;50MG",
            "Appl_Type": "N",
            "Appl_No": "020387",
            "Product_No": "001",
            "TE_Code": "",
            "Approval_Date": "Apr 14, 1995",
            "RLD": "Yes",
            "RS": "Yes",
            "Type": "RX",
        },
    ]
    pc._patents = [
        {
            "Appl_Type": "N",
            "Appl_No": "020386",
            "Product_No": "001",
            "Patent_No": "5608075",
            "Patent_Expire_Date_Text": "Apr 06, 2010",
            "Drug_Substance_Flag": "Y",
            "Drug_Product_Flag": "",
            "Patent_Use_Code": "U-546",
            "Delist_Flag": "",
            "Submission_Date": "",
        },
    ]
    pc._exclusivities = [
        {
            "Appl_Type": "N",
            "Appl_No": "020386",
            "Product_No": "001",
            "Exclusivity_Code": "NCE",
            "Exclusivity_Date": "Apr 14, 2000",
        },
        {
            "Appl_Type": "N",
            "Appl_No": "020386",
            "Product_No": "001",
            "Exclusivity_Code": "ODE",
            "Exclusivity_Date": "2099-01-01",
        },
    ]


@pytest.mark.asyncio
@pytest.mark.usefixtures("_fake_ob_data")
async def test_patent_search_finds_patents_by_ingredient():
    client = pc.PatentClient()
    resp = await client.patent_search_orange_book(active_ingredient="losartan")

    assert resp["api_source"] == "FDA_orange_book"
    assert len(resp["data"]) >= 1
    cozaar = next(r for r in resp["data"] if r["product_name"] == "COZAAR")
    assert cozaar["application_number"] == "N020386"
    assert cozaar["patents"][0]["patent_number"] == "5608075"
    assert cozaar["patents"][0]["is_expired"] is True


@pytest.mark.asyncio
@pytest.mark.usefixtures("_fake_ob_data")
async def test_patent_search_finds_by_drug_name():
    client = pc.PatentClient()
    resp = await client.patent_search_orange_book(drug_name="COZAAR")

    assert len(resp["data"]) == 1
    assert resp["data"][0]["product_name"] == "COZAAR"


@pytest.mark.asyncio
@pytest.mark.usefixtures("_fake_ob_data")
async def test_patent_search_finds_by_application_number():
    client = pc.PatentClient()
    resp = await client.patent_search_orange_book(application_number="NDA020386")

    assert len(resp["data"]) >= 1
    assert resp["data"][0]["application_number"] == "N020386"


@pytest.mark.asyncio
@pytest.mark.usefixtures("_fake_ob_data")
async def test_exclusivities_by_ingredient():
    client = pc.PatentClient()
    resp = await client.patent_get_exclusivities(active_ingredient="losartan")

    assert resp["api_source"] == "FDA_orange_book"
    assert len(resp["data"]) == 2
    codes = {r["code"] for r in resp["data"]}
    assert "NCE" in codes
    assert "ODE" in codes

    expired = next(r for r in resp["data"] if r["code"] == "NCE")
    assert expired["is_active"] is False

    future = next(r for r in resp["data"] if r["code"] == "ODE")
    assert future["is_active"] is True


@pytest.mark.asyncio
@pytest.mark.usefixtures("_fake_ob_data")
async def test_exclusivities_by_application_number():
    client = pc.PatentClient()
    resp = await client.patent_get_exclusivities(application_number="NDA020386")

    assert len(resp["data"]) == 2
    assert resp["data"][0]["application_number"] == "N020386"


@pytest.mark.asyncio
async def test_empty_when_no_data():
    """When no Orange Book files are loaded (empty lists), return empty results."""
    pc._patents = []
    pc._exclusivities = []
    pc._products = []

    client = pc.PatentClient()
    resp = await client.patent_search_orange_book(active_ingredient="nonexistent")
    assert resp["data"] == []

    resp = await client.patent_get_exclusivities(active_ingredient="nonexistent")
    assert resp["data"] == []
