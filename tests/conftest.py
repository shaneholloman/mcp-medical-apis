"""Pytest configuration and fixtures for MCP server tests"""

import logging
import os
import socket
import subprocess
import time
from collections.abc import Generator

import pytest

logger = logging.getLogger(__name__)


def _wait_for_server_ready(
    process: subprocess.Popen,
    host: str,
    port: int,
    server_url: str,
    max_wait_seconds: int = 10,
    check_interval: float = 0.5,
) -> None:
    """Wait for server to be ready by checking if port is accessible."""
    deadline = time.time() + max_wait_seconds

    while time.time() < deadline:
        # Check if process has died
        if process.poll() is not None:
            stdout, _ = process.communicate(timeout=1)
            logger.error(f"Server process died. Output: {stdout}")
            raise RuntimeError(f"MCP server process terminated unexpectedly: {stdout}")

        # Check if port is accessible
        if _is_port_open(host, port):
            logger.info(f"MCP server is ready at {server_url}")
            time.sleep(1)  # Give server a moment to fully initialize
            return

        time.sleep(check_interval)

    # Timeout reached
    process.terminate()
    raise RuntimeError(f"MCP server failed to start within {max_wait_seconds} seconds")


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is open and accepting connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def server_url() -> str:
    """Get the server URL from environment or use default"""
    return os.getenv("MCP_SERVER_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def server_process(server_url: str) -> Generator[subprocess.Popen, None, None]:
    """
    Start the MCP server as a subprocess for the entire test session.
    The server will be available at the server_url.

    The server is stateless HTTP and can handle concurrent requests.
    """
    # Extract host and port from URL
    if server_url.startswith("http://"):
        url_part = server_url[7:]
    elif server_url.startswith("https://"):
        url_part = server_url[8:]
    else:
        url_part = server_url

    if ":" in url_part:
        host, port_str = url_part.split(":", 1)
        port = int(port_str)
    else:
        host = "localhost"
        port = 8000

    # Set environment variables for the server
    env = os.environ.copy()
    env["MCP_HOST"] = host
    env["MCP_PORT"] = str(port)
    # Suppress pkg_resources deprecation warning from chembl_webresource_client
    # This warning is harmless but causes CI failures when captured by subprocess
    pythonwarnings = env.get("PYTHONWARNINGS", "")
    if pythonwarnings:
        env["PYTHONWARNINGS"] = f"{pythonwarnings},ignore:pkg_resources:UserWarning"
    else:
        env["PYTHONWARNINGS"] = "ignore:pkg_resources:UserWarning"

    # Start the server process
    logger.info(f"Starting MCP server at {server_url}")
    process = subprocess.Popen(
        ["uv", "run", "medical-mcps"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Wait for server to be ready
    _wait_for_server_ready(process, host, port, server_url, max_wait_seconds=10)

    yield process

    # Cleanup: terminate the server
    logger.info("Stopping MCP server")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope="session")
def mcp_base_url(server_url: str) -> str:
    """Base URL for MCP endpoint"""
    return f"{server_url}/mcp"


@pytest.fixture(scope="session")
def omim_api_key() -> str:
    """Get OMIM API key from environment variable"""
    return os.getenv("OMIM_API_KEY", "")


def pytest_collection_modifyitems(config, items):
    """Skip OMIM tests if API key is not set, and skip NCI tests if API key is not set"""
    # Skip OMIM tests if API key is not set
    omim_api_key = os.getenv("OMIM_API_KEY", "")
    if not omim_api_key:
        skip_omim = pytest.mark.skip(reason="OMIM_API_KEY environment variable not set")
        for item in items:
            if "omim" in item.name.lower():
                item.add_marker(skip_omim)

    # Skip NCI tests if API key is not set
    nci_api_key = os.getenv("NCI_API_KEY", "")
    if not nci_api_key:
        skip_nci = pytest.mark.skip(reason="NCI_API_KEY environment variable not set")
        for item in items:
            if "nci" in item.name.lower():
                item.add_marker(skip_nci)
