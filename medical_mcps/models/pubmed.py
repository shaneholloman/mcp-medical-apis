"""
Pydantic models for PubMed/PubTator3 API responses.

Models integrate existing PubTator models with MCP structure.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

# Import existing models from pubmed_client
from ..api_clients.pubmed_client import (
    PubTatorSearchResult,
)
from .base import MCPToolResult


class PubMedToolResult(MCPToolResult[PubTatorSearchResult]):
    """PubMed-specific MCP tool result"""

    pass
