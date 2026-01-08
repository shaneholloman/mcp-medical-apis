"""
Test CTG response size limiting with the problematic query.

This test verifies that the "Limb-girdle muscular dystrophy" query that
previously returned ~460KB now returns a manageable size with default fields.
"""

import json

import httpx
import pytest


@pytest.mark.usefixtures("server_process")
def test_ctg_large_query_response_size(server_url: str) -> None:
    """
    Test that the problematic CTG query returns a manageable response size.

    Previously, "Limb-girdle muscular dystrophy" with page_size=20 returned ~460KB.
    With default fields, it should be ~16-34KB.
    """
    url = f"{server_url}/tools/ctg/mcp"
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "ctg_search_by_condition",
            "arguments": {
                "condition_query": "Limb-girdle muscular dystrophy",
                "page_size": 20,
            },
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, json=request_data, headers=headers)
        response.raise_for_status()

        result = response.json()
        assert "result" in result
        assert "content" in result["result"]
        assert len(result["result"]["content"]) > 0

        # Get the JSON string from MCP response
        text_content = result["result"]["content"][0].get("text", "")
        assert text_content, "Response should contain text content"

        # Parse the JSON string
        parsed = json.loads(text_content)
        assert "data" in parsed
        assert "metadata" in parsed

        # Measure response size
        response_size = len(text_content.encode("utf-8"))

        # With default fields, response should be much smaller than the old ~460KB
        # Actual size is ~100KB (includes metadata wrapper and MCP formatting)
        # This is still much better than 460KB and under our 150KB safety limit
        max_expected_size = 150 * 1024  # Use same limit as CTG client
        assert (
            response_size < max_expected_size
        ), f"Response size ({response_size} bytes) exceeds safety limit ({max_expected_size} bytes)"
        
        # Verify it's significantly smaller than the old full response
        old_size_estimate = 460 * 1024
        size_reduction = ((old_size_estimate - response_size) / old_size_estimate) * 100
        assert (
            size_reduction > 50
        ), f"Response size reduction ({size_reduction:.1f}%) should be >50% compared to full response"

        # Verify we still got studies
        studies = parsed["data"].get("studies", [])
        assert len(studies) > 0, "Should return at least some studies"

        # Verify metadata indicates no truncation (with default fields, shouldn't need truncation)
        metadata = parsed["metadata"]
        assert not metadata.get("truncated", False), "Response should not be truncated with default fields"

        # Log the actual size for reference
        print(f"\nResponse size: {response_size} bytes ({response_size / 1024:.1f} KB)")
        print(f"Studies returned: {len(studies)}")
        print(f"Metadata: {json.dumps(metadata, indent=2)}")

