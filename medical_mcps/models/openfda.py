"""
Pydantic models for OpenFDA API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class OpenFDAAdverseEvent(BaseModel):
    """OpenFDA adverse event model"""

    safetyreportid: str | None = None
    serious: int | None = None
    receivedate: str | None = None
    drugs: list[dict[str, Any]] | None = None
    reactions: list[str] | None = None
    patient: dict[str, Any] | None = None
    summary: str | None = None

    class Config:
        extra = "allow"


class OpenFDADrugLabel(BaseModel):
    """OpenFDA drug label model"""

    set_id: str | None = None
    brand_name: str | None = None
    generic_name: str | None = None
    indications_and_usage: list[str] | None = None
    boxed_warning: list[str] | None = None
    dosage_and_administration: list[str] | None = None
    contraindications: list[str] | None = None
    warnings_and_precautions: list[str] | None = None
    adverse_reactions: list[str] | None = None
    drug_interactions: list[str] | None = None

    class Config:
        extra = "allow"


class OpenFDAToolResult(MCPToolResult[OpenFDAAdverseEvent]):
    """OpenFDA-specific MCP tool result"""

    pass
