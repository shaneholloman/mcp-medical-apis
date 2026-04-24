import json

import pytest

from medical_mcps.api_clients.patent_client import PatentClient


@pytest.mark.asyncio
async def test_patent_search_orange_book_parses_patents():
    client = PatentClient()

    async def fake_request(*args, **kwargs):
        return json.dumps(
            {
                "results": [
                    {
                        "sponsor_name": "Merck",
                        "products": [
                            {
                                "application_number": "NDA020386",
                                "brand_name": "COZAAR",
                                "active_ingredients": [{"name": "LOSARTAN POTASSIUM"}],
                                "patents": [
                                    {
                                        "patent_number": "5608075",
                                        "patent_expire_date": "Apr 06, 2010",
                                        "patent_use_code": "U-546",
                                        "patent_use_description": "Method of treatment",
                                    }
                                ],
                            }
                        ],
                        "submissions": [{"submission_status_date": "1995-04-14"}],
                    }
                ]
            }
        )

    client._request = fake_request
    resp = await client.patent_search_orange_book(active_ingredient="losartan")

    assert resp["api_source"] == "FDA_drugsfda"
    assert resp["data"][0]["application_number"] == "NDA020386"
    assert resp["data"][0]["patents"][0]["patent_number"] == "5608075"
    assert resp["data"][0]["patents"][0]["is_expired"] is True


@pytest.mark.asyncio
async def test_patent_search_orange_book_prefers_matching_active_ingredient_and_item_level_application_number():
    client = PatentClient()

    async def fake_request(*args, **kwargs):
        return json.dumps(
            {
                "results": [
                    {
                        "application_number": "ANDA218015",
                        "sponsor_name": "Granules",
                        "products": [
                            {
                                "brand_name": "LOSARTAN POTASSIUM AND HYDROCHLOROTHIAZIDE",
                                "active_ingredients": [
                                    {"name": "HYDROCHLOROTHIAZIDE"},
                                    {"name": "LOSARTAN POTASSIUM"},
                                ],
                                "patents": [],
                            }
                        ],
                        "submissions": [{"submission_status_date": "2023-09-29"}],
                    }
                ]
            }
        )

    client._request = fake_request
    resp = await client.patent_search_orange_book(active_ingredient="losartan")

    assert resp["data"][0]["application_number"] == "ANDA218015"
    assert resp["data"][0]["active_ingredient"] == "LOSARTAN POTASSIUM"
    assert resp["data"][0]["active_ingredients"] == [
        "HYDROCHLOROTHIAZIDE",
        "LOSARTAN POTASSIUM",
    ]


@pytest.mark.asyncio
async def test_patent_get_exclusivities_parses_activity_flag():
    client = PatentClient()

    async def fake_request(*args, **kwargs):
        return json.dumps(
            {
                "results": [
                    {
                        "products": [
                            {
                                "application_number": "NDA999999",
                                "brand_name": "EXAMPLE",
                                "exclusivity": [
                                    {
                                        "code": "NCE",
                                        "description": "NEW CHEMICAL ENTITY",
                                        "expiration_date": "2099-01-01",
                                    }
                                ],
                            }
                        ]
                    }
                ]
            }
        )

    client._request = fake_request
    resp = await client.patent_get_exclusivities(application_number="NDA999999")

    assert resp["data"][0]["code"] == "NCE"
    assert resp["data"][0]["is_active"] is True


@pytest.mark.asyncio
async def test_patent_get_exclusivities_falls_back_to_item_level_application_number():
    client = PatentClient()

    async def fake_request(*args, **kwargs):
        return json.dumps(
            {
                "results": [
                    {
                        "application_number": "NDA123456",
                        "products": [
                            {
                                "brand_name": "EXAMPLE",
                                "exclusivity": [
                                    {
                                        "code": "ODE",
                                        "description": "ORPHAN DRUG EXCLUSIVITY",
                                        "expiration_date": "2030-01-01",
                                    }
                                ],
                            }
                        ]
                    }
                ]
            }
        )

    client._request = fake_request
    resp = await client.patent_get_exclusivities(active_ingredient="example")

    assert resp["data"][0]["application_number"] == "NDA123456"
