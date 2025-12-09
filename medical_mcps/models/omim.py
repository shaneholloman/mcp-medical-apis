"""
Pydantic models for OMIM API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class OMIMEntry(BaseModel):
    """OMIM entry model"""

    mimNumber: str | None = None
    preferredTitle: str | None = None
    allelicVariantList: list[dict[str, Any]] | None = None
    geneMap: dict[str, Any] | None = None
    text: list[dict[str, Any]] | None = None

    class Config:
        extra = "allow"


class OMIMSearchResult(BaseModel):
    """OMIM search result model"""

    omim: dict[str, Any] | None = None
    searchResponse: dict[str, Any] | None = None

    class Config:
        extra = "allow"


class OMIMToolResult(MCPToolResult[OMIMEntry]):
    """OMIM-specific MCP tool result"""

    pass
