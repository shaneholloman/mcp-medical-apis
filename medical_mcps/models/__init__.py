"""
Pydantic models for API response validation.

Models are organized by provider in submodules:
- base: Universal MCP response structure models
- uniprot: UniProt protein database models
- reactome: Reactome pathway database models
- gwas: GWAS Catalog models
- nodenorm: Node Normalization models
- etc.

Import specific models directly: `from medical_mcps.models.uniprot import UniProtProtein`
"""

from .base import (
    APIResponseData,
    MCPContentItem,
    MCPResponse,
    MCPToolResult,
)

__all__ = [
    "APIResponseData",
    "MCPContentItem",
    "MCPResponse",
    "MCPToolResult",
]
