"""
Pydantic models for Pathway Commons API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from pydantic import BaseModel

from .base import MCPToolResult


class PathwayCommonsPathway(BaseModel):
    """Pathway Commons pathway model"""

    uri: str | None = None
    name: str | None = None
    displayName: str | None = None
    datasource: str | None = None
    organism: str | None = None
    pathwayType: str | None = None

    class Config:
        extra = "allow"


class PathwayCommonsSearchResult(BaseModel):
    """Pathway Commons search result model"""

    hits: list[PathwayCommonsPathway] | None = None
    total: int | None = None

    class Config:
        extra = "allow"


class PathwayCommonsToolResult(MCPToolResult[PathwayCommonsPathway]):
    """Pathway Commons-specific MCP tool result"""

    pass
