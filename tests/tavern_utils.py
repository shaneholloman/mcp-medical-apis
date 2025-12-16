"""
Utility functions for Tavern tests to handle JSON strings in MCP responses.

PROBLEM:
--------
MCP (Model Context Protocol) responses return JSON as strings in the `text` field:
  result.content[0].text = '{"api_source": "...", "data": {...}}'

Tavern's built-in JSON validation expects parsed JSON objects, not strings. This creates
a gap when testing MCP servers.

SOLUTION:
---------
These utilities parse JSON strings embedded in responses and make them available for
validation. Two approaches:

1. **Save parsed JSON** for use in later stages or validation
2. **Validate directly** by parsing and checking structure in one step

USAGE EXAMPLES:
---------------
# Option 1: Save parsed JSON (for use in later stages)
response:
  save:
    $ext:
      function: tests.tavern_utils:parse_mcp_json
      extra_kwargs:
        json_path: "result.content[0].text"  # Optional, defaults to MCP standard path

# Option 2: Save + Validate in one step (recommended for most cases)
response:
  save:
    $ext:
      function: tests.tavern_utils:parse_and_validate_mcp_json
      extra_kwargs:
        json_path: "result.content[0].text"  # Optional
        expected_api_source: "Every Cure Matrix Knowledge Graph"  # Optional

# Option 3: Validate only (if you don't need to save)
response:
  verify_response_with:
    function: tests.tavern_utils:validate_mcp_json
    extra_kwargs:
      json_path: "result.content[0].text"  # Optional
      expected_api_source: "Every Cure Matrix Knowledge Graph"  # Optional

The parsed JSON is saved as `parsed_json` in test variables and can be validated
using Tavern's standard JSON validation in subsequent stages.

WHY NOT NATIVE TAVERN SUPPORT?
-------------------------------
This is a common pattern (MCP, GraphQL, some REST APIs) that could benefit from
native Tavern support. Potential improvements:
- Auto-parse JSON strings when validating
- Built-in `json_string_path` option in save/validate blocks
- Native support for nested JSON string parsing

See this file for reference implementation that Tavern could adopt.
"""

import json
from typing import Any

# Standard MCP JSON string path
_MCP_JSON_PATH = "result.content[0].text"


def _extract_and_parse_json(response: Any, json_path: str) -> dict[str, Any]:
    """
    Internal helper to extract and parse JSON string from response.

    Args:
        response: Response object from Tavern
        json_path: Path to JSON string in response body

    Returns:
        Parsed JSON object

    Raises:
        ValueError: If extraction or parsing fails
    """
    from tavern._core.dict_util import recurse_access_key

    # Get the response body (parsed JSON)
    if hasattr(response, "json"):
        body = response.json()
    elif isinstance(response, dict):
        body = response
    else:
        raise ValueError(f"Unexpected response type: {type(response)}")

    # Access the JSON string using the path
    json_str = recurse_access_key(body, json_path)

    if not isinstance(json_str, str):
        raise ValueError(f"Expected string at '{json_path}', got {type(json_str)}: {json_str}")

    # Parse the JSON string
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON string at '{json_path}': {e}") from e

    return parsed


def parse_mcp_json(response: Any, json_path: str = _MCP_JSON_PATH) -> dict[str, Any]:
    """
    Parse a JSON string from MCP response and save it for later use.

    Use this when you need to save the parsed JSON for use in later stages.

    Args:
        response: The response object from Tavern
        json_path: Path to JSON string (defaults to MCP standard: "result.content[0].text")

    Returns:
        Dict with 'parsed_json' key containing the parsed JSON object
    """
    parsed = _extract_and_parse_json(response, json_path)
    return {"parsed_json": parsed}


def parse_and_validate_mcp_json(
    response: Any,
    json_path: str = _MCP_JSON_PATH,
    expected_api_source: str | None = None,
) -> dict[str, Any]:
    """
    Parse MCP JSON response and optionally validate api_source.

    This function parses the JSON string and saves it for use in Tavern YAML assertions.
    Use Tavern's native YAML syntax to assert on the parsed_json structure.

    Args:
        response: The response object from Tavern
        json_path: Path to JSON string (defaults to MCP standard)
        expected_api_source: If provided, validates that api_source matches

    Returns:
        Dict with 'parsed_json' key containing the parsed JSON object

    Raises:
        ValueError: If parsing fails or api_source doesn't match
    """
    parsed = _extract_and_parse_json(response, json_path)

    # Basic type check
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected parsed JSON to be a dict, got {type(parsed)}")

    # Optional api_source validation
    if expected_api_source:
        if parsed.get("api_source") != expected_api_source:
            raise ValueError(
                f"Expected api_source '{expected_api_source}', got '{parsed.get('api_source')}'"
            )

    return {"parsed_json": parsed}


# Backward compatibility aliases
parse_mcp_json_text_from_response = parse_mcp_json


def validate_mcp_json(
    response: Any, json_path: str = _MCP_JSON_PATH, expected_api_source: str | None = None
) -> None:
    """
    Validate MCP JSON response structure (doesn't save, only validates).

    Use this with `verify_response_with` when you only need validation and don't
    need to save the parsed JSON for later stages.

    Args:
        response: The response object from Tavern
        json_path: Path to JSON string (defaults to MCP standard)
        expected_api_source: If provided, validates that api_source matches

    Raises:
        ValueError: If JSON parsing or validation fails
    """
    parsed = _extract_and_parse_json(response, json_path)

    # Validate structure
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected parsed JSON to be a dict, got {type(parsed)}")

    if expected_api_source:
        if parsed.get("api_source") != expected_api_source:
            raise ValueError(
                f"Expected api_source '{expected_api_source}', got '{parsed.get('api_source')}'"
            )

    # Validate required fields for MCP responses
    if "data" not in parsed:
        raise ValueError("Parsed JSON missing required 'data' field")
    if "metadata" not in parsed:
        raise ValueError("Parsed JSON missing required 'metadata' field")


# Backward compatibility alias
validate_mcp_json_response = validate_mcp_json


def validate_saved_json(
    response: Any,
    variable_name: str = "parsed_json",
    expected_body: dict[str, Any] | None = None,
    json_path: str = _MCP_JSON_PATH,
) -> None:
    """
    Validate a saved JSON variable using Tavern-style validation syntax.

    This function parses the JSON from the response (same way parse_and_validate_mcp_json does)
    and validates it against the expected structure.

    Supports basic Tavern validation patterns:
    - Exact value matching: `key: "value"`
    - Type checking: `key: {type: list}` or `key: {type: dict}`
    - Required fields: `key: {type: dict, required: ["field1", "field2"]}`
    - List constraints: `key: {type: list, min_length: 1}`
    - String contains: `key: {type: str, contains: "substring"}`

    Usage in YAML:
      verify_response_with:
        - function: tests.tavern_utils:validate_saved_json
          extra_kwargs:
            variable_name: "parsed_json"
            expected_body:
              api_source: "Every Cure Matrix Knowledge Graph"
              data:
                paths:
                  type: list

    Args:
        response: Response object from Tavern
        variable_name: Name of the saved variable (for error messages, default: "parsed_json")
        expected_body: Expected structure using Tavern-style validation syntax
        json_path: Path to JSON string in response (defaults to MCP standard)

    Raises:
        ValueError: If validation fails
    """
    # Parse JSON from response (same as parse_and_validate_mcp_json)
    parsed = _extract_and_parse_json(response, json_path)

    if expected_body is None:
        return

    def _validate_value(expected: Any, actual: Any, path: str = "") -> None:
        """Recursively validate expected structure against actual value."""
        if isinstance(expected, dict) and "type" in expected:
            # Type validation
            expected_type = expected["type"]
            if expected_type == "list":
                if not isinstance(actual, list):
                    raise ValueError(f"{path}: Expected list, got {type(actual).__name__}")
                if "min_length" in expected:
                    if len(actual) < expected["min_length"]:
                        raise ValueError(
                            f"{path}: Expected at least {expected['min_length']} items, got {len(actual)}"
                        )
                if "items" in expected and actual:
                    for i, item in enumerate(actual):
                        _validate_value(expected["items"], item, f"{path}[{i}]")
            elif expected_type == "dict":
                if not isinstance(actual, dict):
                    raise ValueError(f"{path}: Expected dict, got {type(actual).__name__}")
                if "required" in expected:
                    for req_field in expected["required"]:
                        if req_field not in actual:
                            raise ValueError(f"{path}: Missing required field '{req_field}'")
                # Validate nested structure
                for key, val in expected.items():
                    if key not in ("type", "required"):
                        if key in actual:
                            _validate_value(val, actual[key], f"{path}.{key}")
            elif expected_type == "str":
                if not isinstance(actual, str):
                    raise ValueError(f"{path}: Expected str, got {type(actual).__name__}")
                if "contains" in expected:
                    if expected["contains"] not in actual:
                        raise ValueError(
                            f"{path}: Expected string to contain '{expected['contains']}', got '{actual}'"
                        )
        elif isinstance(expected, dict):
            # Dict structure validation
            if not isinstance(actual, dict):
                raise ValueError(f"{path}: Expected dict, got {type(actual).__name__}")
            for key, val in expected.items():
                if key not in actual:
                    raise ValueError(f"{path}: Missing key '{key}'")
                _validate_value(val, actual[key], f"{path}.{key}")
        elif isinstance(expected, list):
            # List validation (exact match)
            if not isinstance(actual, list):
                raise ValueError(f"{path}: Expected list, got {type(actual).__name__}")
            if len(expected) != len(actual):
                raise ValueError(f"{path}: Expected {len(expected)} items, got {len(actual)}")
            for i, (exp_item, act_item) in enumerate(zip(expected, actual)):
                _validate_value(exp_item, act_item, f"{path}[{i}]")
        else:
            # Exact value match
            if expected != actual:
                raise ValueError(f"{path}: Expected '{expected}', got '{actual}'")

    try:
        _validate_value(expected_body, parsed, "root")
    except ValueError as e:
        raise ValueError(f"Validation failed: {e}") from e
