"""
Pydantic models for NCI Clinical Trials API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class NCITrial(BaseModel):
    """NCI trial model"""

    nct_id: str | None = None
    protocol_id: str | None = None
    nci_id: str | None = None
    official_title: str | None = None
    brief_title: str | None = None
    current_trial_status: str | None = None
    lead_org: dict[str, Any] | None = None
    primary_disease_names: list[str] | None = None
    intervention_names: list[str] | None = None
    phase: list[str] | None = None

    class Config:
        extra = "allow"


class NCISearchResult(BaseModel):
    """NCI search result model"""

    data: list[NCITrial] | None = None
    total: int | None = None

    class Config:
        extra = "allow"


class NCIToolResult(MCPToolResult[NCITrial]):
    """NCI-specific MCP tool result"""

    pass
