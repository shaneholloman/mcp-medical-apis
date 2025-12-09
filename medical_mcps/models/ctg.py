"""
Pydantic models for ClinicalTrials.gov API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class CTGStudy(BaseModel):
    """ClinicalTrials.gov study model"""

    nctId: str | None = None
    protocolSection: dict[str, Any] | None = None
    derivedSection: dict[str, Any] | None = None
    hasResults: bool | None = None

    class Config:
        extra = "allow"


class CTGSearchResult(BaseModel):
    """ClinicalTrials.gov search result model"""

    studies: list[CTGStudy] | None = None
    nextPageToken: str | None = None
    totalCount: int | None = None

    class Config:
        extra = "allow"


class CTGToolResult(MCPToolResult[CTGStudy]):
    """ClinicalTrials.gov-specific MCP tool result"""

    pass
