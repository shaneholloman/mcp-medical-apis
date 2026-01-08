"""
Regression test to verify all MCP tool responses stay within size limits.

This test ensures that responses from all tavern test endpoints don't exceed
the maximum response size, preventing context window overflow issues.
"""

import json
import logging
from pathlib import Path

import httpx
import pytest
import yaml

logger = logging.getLogger(__name__)


class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
    """YAML loader that ignores unknown tags (like tavern's !re_search)."""

    def ignore_unknown(self, node):
        return None


# Register handler for unknown tags
SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)

# Maximum response size in bytes (150KB) - same as CTG client limit
MAX_RESPONSE_SIZE_BYTES = 150 * 1024


def extract_test_cases_from_tavern_file(tavern_file: Path) -> list[dict]:
    """Extract test cases from a tavern YAML file."""
    with open(tavern_file) as f:
        content = yaml.load(f, Loader=SafeLoaderIgnoreUnknown)

    test_cases = []
    stages = content.get("stages", [])

    for stage in stages:
        if "request" not in stage:
            continue

        request = stage["request"]
        url = request.get("url", "")
        method = request.get("method", "POST")
        json_data = request.get("json", {})

        # Extract tool name and arguments from MCP JSON-RPC request
        tool_name = None
        tool_args = {}
        if method == "POST" and json_data.get("method") == "tools/call":
            params = json_data.get("params", {})
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

        if tool_name:
            test_cases.append(
                {
                    "name": stage.get("name", "unnamed"),
                    "url": url,
                    "method": method,
                    "tool_name": tool_name,
                    "arguments": tool_args,
                }
            )

    return test_cases


@pytest.fixture(scope="session")
def tavern_test_files() -> list[Path]:
    """Find all tavern test YAML files."""
    tests_dir = Path(__file__).parent
    return list(tests_dir.glob("*.tavern.yaml"))


@pytest.fixture(scope="session")
def all_test_cases(tavern_test_files: list[Path]) -> list[dict]:
    """Extract all test cases from tavern files."""
    all_cases = []
    for tavern_file in tavern_test_files:
        cases = extract_test_cases_from_tavern_file(tavern_file)
        for case in cases:
            case["source_file"] = tavern_file.name
        all_cases.extend(cases)
    return all_cases


def test_all_responses_within_size_limit(
    server_process, server_url: str, all_test_cases: list[dict]
) -> None:
    """
    Test that all responses from tavern test endpoints stay within size limit.

    This regression test ensures no response exceeds MAX_RESPONSE_SIZE_BYTES,
    preventing context window overflow issues.
    """
    base_url = server_url
    failures = []

    for test_case in all_test_cases:
        url = test_case["url"]
        method = test_case["method"]
        tool_name = test_case["tool_name"]
        arguments = test_case["arguments"]
        test_name = test_case["name"]
        source_file = test_case["source_file"]

        # Skip error cases (they might return small error messages, but not worth testing)
        if "error" in test_name.lower() or "invalid" in test_name.lower():
            continue

        # Build JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        try:
            # Make request
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=request_data)
                response.raise_for_status()

                # Parse response
                result = response.json()
                if "result" in result and "content" in result["result"]:
                    # MCP responses have JSON string in content[0].text
                    content = result["result"]["content"]
                    if content and len(content) > 0:
                        text_content = content[0].get("text", "")
                        if text_content:
                            # Measure size of the JSON string
                            response_size = len(text_content.encode("utf-8"))

                            if response_size > MAX_RESPONSE_SIZE_BYTES:
                                failures.append(
                                    {
                                        "test": test_name,
                                        "tool": tool_name,
                                        "source_file": source_file,
                                        "size_bytes": response_size,
                                        "limit_bytes": MAX_RESPONSE_SIZE_BYTES,
                                        "excess_bytes": response_size - MAX_RESPONSE_SIZE_BYTES,
                                    }
                                )
                                logger.error(
                                    f"FAIL: {test_name} ({tool_name}) in {source_file}: "
                                    f"{response_size} bytes (exceeds limit by {response_size - MAX_RESPONSE_SIZE_BYTES} bytes)"
                                )
                            else:
                                logger.debug(
                                    f"PASS: {test_name} ({tool_name}) in {source_file}: "
                                    f"{response_size} bytes"
                                )
                else:
                    logger.warning(
                        f"Unexpected response format for {test_name} ({tool_name}) in {source_file}"
                    )

        except Exception as e:
            logger.warning(
                f"Failed to test {test_name} ({tool_name}) in {source_file}: {e}"
            )
            # Don't fail the test for individual request failures - these are covered by tavern tests
            continue

    # Report failures
    if failures:
        failure_report = "\n".join(
            f"  - {f['test']} ({f['tool']}) in {f['source_file']}: "
            f"{f['size_bytes']} bytes (exceeds limit by {f['excess_bytes']} bytes)"
            for f in failures
        )
        pytest.fail(
            f"{len(failures)} test case(s) exceed response size limit:\n{failure_report}\n\n"
            f"Limit: {MAX_RESPONSE_SIZE_BYTES} bytes ({MAX_RESPONSE_SIZE_BYTES / 1024:.1f} KB)"
        )

