"""
Unit tests for tavern_utils.py helper functions.
Tests the JSON parsing and validation utilities directly.
"""

import pytest

from tests.tavern_utils import (
    parse_and_validate_mcp_json,
    parse_mcp_json,
    validate_mcp_json,
    validate_saved_json,
)


class MockResponse:
    """Mock response object for testing."""

    def __init__(self, json_data: dict):
        self._json_data = json_data

    def json(self):
        return self._json_data


def test_parse_mcp_json():
    """Test parsing MCP JSON from response."""
    json_str = '{"api_source": "Test API", "data": {"key": "value"}, "metadata": {}}'
    response = MockResponse({"result": {"content": [{"type": "text", "text": json_str}]}})

    result = parse_mcp_json(response)
    assert "parsed_json" in result
    assert result["parsed_json"]["api_source"] == "Test API"
    assert result["parsed_json"]["data"]["key"] == "value"


def test_parse_and_validate_mcp_json():
    """Test parsing and validating MCP JSON."""
    json_str = '{"api_source": "Test API", "data": {}, "metadata": {}}'
    response = MockResponse({"result": {"content": [{"type": "text", "text": json_str}]}})

    result = parse_and_validate_mcp_json(response, expected_api_source="Test API")
    assert "parsed_json" in result
    assert result["parsed_json"]["api_source"] == "Test API"

    # Test wrong API source
    with pytest.raises(ValueError, match="Expected api_source"):
        parse_and_validate_mcp_json(response, expected_api_source="Wrong API")


def test_validate_mcp_json():
    """Test validation of MCP JSON structure."""
    json_str = '{"api_source": "Test API", "data": {}, "metadata": {}}'
    response = MockResponse({"result": {"content": [{"type": "text", "text": json_str}]}})

    # Should not raise
    validate_mcp_json(response, expected_api_source="Test API")

    # Test missing data field
    json_str_bad = '{"api_source": "Test API", "metadata": {}}'
    response_bad = MockResponse({"result": {"content": [{"type": "text", "text": json_str_bad}]}})
    with pytest.raises(ValueError, match="missing required 'data' field"):
        validate_mcp_json(response_bad)


def test_validate_saved_json():
    """Test validation of saved JSON with expected structure."""
    json_str = '{"api_source": "Test API", "data": {"items": [1, 2, 3]}, "metadata": {"count": 3}}'
    response = MockResponse({"result": {"content": [{"type": "text", "text": json_str}]}})

    # Test type validation
    expected = {
        "api_source": "Test API",
        "data": {"items": {"type": "list", "min_length": 1}},
        "metadata": {"count": 3},
    }
    validate_saved_json(response, expected_body=expected)

    # Test validation failure
    expected_bad = {
        "api_source": "Test API",
        "data": {"items": {"type": "list", "min_length": 10}},  # Should fail
    }
    with pytest.raises(ValueError, match="Validation failed"):
        validate_saved_json(response, expected_body=expected_bad)
