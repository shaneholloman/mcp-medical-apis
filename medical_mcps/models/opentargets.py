"""
Pydantic models for OpenTargets API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class OpenTargetsAssociation(BaseModel):
    """OpenTargets association model"""

    target: dict[str, Any] | None = None
    disease: dict[str, Any] | None = None
    association_score: dict[str, Any] | None = None
    datatype_scores: dict[str, Any] | None = None

    class Config:
        extra = "allow"


class OpenTargetsSearchResult(BaseModel):
    """OpenTargets search result model"""

    data: list[dict[str, Any]] | None = None
    total: int | None = None

    class Config:
        extra = "allow"


class OpenTargetsToolResult(MCPToolResult[OpenTargetsAssociation]):
    """OpenTargets-specific MCP tool result"""

    pass
