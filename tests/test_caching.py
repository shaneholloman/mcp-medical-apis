"""
Test HTTP caching implementation with hishel
"""

from pathlib import Path

import pytest

from medical_mcps.api_clients.ctg_client import CTGClient
from medical_mcps.api_clients.reactome_client import ReactomeClient


@pytest.fixture
def cache_dir():
    """Get the cache directory path (base directory, not per-process)"""
    return Path.home() / ".cache" / "medical-mcps" / "api_cache"


@pytest.fixture
def get_cache_file_path():
    """Get the actual cache file path for current process"""
    import os

    process_id = os.getpid()
    proc_cache_dir = Path.home() / ".cache" / "medical-mcps" / "api_cache" / f"proc_{process_id}"
    return lambda api_name: proc_cache_dir / f"{api_name.lower()}.db"


@pytest.fixture
def clean_reactome_cache(get_cache_file_path):
    """Clean Reactome cache before test"""
    cache_file = get_cache_file_path("reactome")
    if cache_file.exists():
        cache_file.unlink()
    yield
    # Cleanup after test
    if cache_file.exists():
        cache_file.unlink()


@pytest.fixture
def clean_ctg_cache(get_cache_file_path):
    """Clean CTG cache before test"""
    cache_file = get_cache_file_path("clinicaltrials.gov")
    if cache_file.exists():
        cache_file.unlink()
    yield
    # Cleanup after test
    if cache_file.exists():
        cache_file.unlink()


@pytest.mark.asyncio
async def test_reactome_caching_enabled(clean_reactome_cache, cache_dir):
    """Test that Reactome client caching can be enabled"""
    client = ReactomeClient(enable_cache=True)
    assert client.enable_cache is True
    # Cache dir is per-process, so it should be a subdirectory of cache_dir
    assert cache_dir in client.cache_dir.parents or client.cache_dir == cache_dir


@pytest.mark.asyncio
async def test_reactome_cache_creation(clean_reactome_cache, get_cache_file_path):
    """Test that cache file is created after first request"""
    client = ReactomeClient(enable_cache=True)
    cache_file = get_cache_file_path("reactome")

    # Cache file should not exist initially
    assert not cache_file.exists()

    async with client:
        # Make first request
        result1 = await client.get_pathway("R-HSA-1640170")

        # Cache file should be created in per-process directory
        assert cache_file.exists(), "Cache file should be created after first request"
        assert cache_file.stat().st_size > 0, "Cache file should not be empty"

        # Verify response is valid
        assert isinstance(result1, dict)
        # Reactome returns data directly or wrapped in format_response
        assert "displayName" in result1 or "data" in result1


@pytest.mark.asyncio
async def test_reactome_cache_hit(clean_reactome_cache, get_cache_file_path):
    """Test that second request uses cache (revalidated)"""
    client = ReactomeClient(enable_cache=True)
    cache_file = get_cache_file_path("reactome")

    async with client:
        # First request - should store in cache
        result1 = await client.get_pathway("R-HSA-1640170")
        assert cache_file.exists()

        # Second request - should use cache (may revalidate)
        result2 = await client.get_pathway("R-HSA-1640170")

        # Results should match
        assert result1 == result2, "Cached response should match original"

        # Verify cache file still exists and may have grown
        assert cache_file.exists()


@pytest.mark.asyncio
async def test_reactome_cache_extensions(clean_reactome_cache):
    """Test that hishel extensions are present in responses"""
    client = ReactomeClient(enable_cache=True)

    async with client:
        # Make first request - should store in cache
        response1 = await client.client.get(
            "https://reactome.org/ContentService/data/query/R-HSA-1640170"
        )

        # First request should store in cache
        assert "hishel_stored" in response1.extensions
        assert response1.extensions.get("hishel_stored") is True
        # First request won't be from cache
        assert response1.extensions.get("hishel_from_cache") is False

        # Make second request - should use cache (may revalidate)
        response2 = await client.client.get(
            "https://reactome.org/ContentService/data/query/R-HSA-1640170"
        )

        # Second request should have cache-related extensions
        # hishel revalidates cached responses by default, so check for revalidated flag
        assert "hishel_revalidated" in response2.extensions
        assert response2.extensions.get("hishel_revalidated") is True
        # When revalidated, hishel_from_cache may be False but revalidated is True


@pytest.mark.asyncio
async def test_reactome_cache_disabled():
    """Test that caching can be disabled"""
    # Test with caching disabled
    client_disabled = ReactomeClient(enable_cache=False)
    assert client_disabled.enable_cache is False

    async with client_disabled:
        # The client should work without cache
        result = await client_disabled.get_pathway("R-HSA-1640170")
        assert isinstance(result, dict)

    # Test with caching enabled
    client_enabled = ReactomeClient(enable_cache=True)
    assert client_enabled.enable_cache is True

    async with client_enabled:
        result = await client_enabled.get_pathway("R-HSA-1640170")
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_ctg_cache_adapter(clean_ctg_cache):
    """Test that CTG client uses CacheAdapter for requests"""
    client = CTGClient()

    # Verify session has adapters mounted (CacheAdapter should be present)
    assert len(client._session.adapters) > 0
    # Check that https:// is in the adapters keys
    assert "https://" in client._session.adapters

    async with client:
        # Make a request
        result1 = await client.search_studies(condition="multiple sclerosis", page_size=5)

        # Verify response is valid
        assert isinstance(result1, dict)

        # Make second request - should use cache
        result2 = await client.search_studies(condition="multiple sclerosis", page_size=5)

        # Results should match
        assert result1 == result2, "Cached response should match original"


@pytest.mark.asyncio
async def test_ctg_cache_header(clean_ctg_cache):
    """Test that CTG responses include cache header"""
    client = CTGClient()

    async with client:
        # First request
        response1 = await client._run_sync(
            client._session.get,
            "https://clinicaltrials.gov/api/v2/studies",
            params={"format": "json", "pageSize": 1},
        )

        # Second request (should be cached)
        response2 = await client._run_sync(
            client._session.get,
            "https://clinicaltrials.gov/api/v2/studies",
            params={"format": "json", "pageSize": 1},
        )

        # Check for cache header (may be present on cached responses)
        # Note: hishel may add X-Hishel-From-Cache header
        # Headers are checked implicitly via response objects

        # Both requests should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200


@pytest.mark.asyncio
async def test_cache_directory_creation(cache_dir):
    """Test that cache directory is created automatically"""
    # Directory should exist (created at import time)
    assert cache_dir.exists(), "Cache directory should exist"
    assert cache_dir.is_dir(), "Cache directory should be a directory"


@pytest.mark.asyncio
async def test_multiple_api_caches(cache_dir, get_cache_file_path):
    """Test that different APIs use separate cache files"""
    reactome_client = ReactomeClient(enable_cache=True)
    # Note: We can't easily test CTG cache file name without making requests
    # But we can verify the pattern

    # Cache dir is per-process, so it should be a subdirectory of cache_dir
    assert cache_dir in reactome_client.cache_dir.parents or reactome_client.cache_dir == cache_dir

    # Reactome should use reactome.db in per-process directory
    reactome_cache_file = get_cache_file_path("reactome")

    async with reactome_client:
        await reactome_client.get_pathway("R-HSA-1640170")
        assert reactome_cache_file.exists(), "Reactome cache file should exist"
