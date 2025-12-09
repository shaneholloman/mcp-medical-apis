"""
Pydantic models for MyVariant API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class MyVariantVariant(BaseModel):
    """MyVariant variant model"""

    _id: str | None = None
    query: str | None = None
    dbsnp: dict[str, Any] | None = None
    clinvar: dict[str, Any] | None = None
    gnomad_exome: dict[str, Any] | None = None
    gnomad_genome: dict[str, Any] | None = None
    cadd: dict[str, Any] | None = None
    dbnsfp: dict[str, Any] | None = None

    class Config:
        extra = "allow"


class MyVariantSearchResult(BaseModel):
    """MyVariant search result model"""

    hits: list[MyVariantVariant] | None = None
    total: int | None = None

    class Config:
        extra = "allow"


class MyVariantToolResult(MCPToolResult[MyVariantVariant]):
    """MyVariant-specific MCP tool result"""

    pass
