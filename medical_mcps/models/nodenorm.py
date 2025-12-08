"""
Pydantic models for Node Normalization API responses.

Models derived from OpenAPI spec: https://nodenormalization-sri.renci.org/1.5/openapi.json
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Optional

from pydantic import BaseModel

from .base import MCPToolResult


class NodeNormalizationIdentifier(BaseModel):
    """Identifier information"""

    identifier: str
    label: Optional[str] = None
    taxa: Optional[list[str]] = None


class NodeNormalizationNode(BaseModel):
    """Normalized node information"""

    id: NodeNormalizationIdentifier
    equivalent_identifiers: Optional[list[NodeNormalizationIdentifier]] = None
    type: Optional[list[str]] = None  # Semantic types
    taxa: Optional[list[str]] = None  # Taxa associated with the node
    information_content: Optional[float] = (
        None  # Information content metric (float value)
    )

    class Config:
        extra = "allow"


class NodeNormalizationResult(BaseModel):
    """
    Node Normalization response structure.

    This represents the full response from get_normalized_nodes, which is a dict
    where keys are input CURIEs and values are normalized node objects.
    Since the keys are dynamic (CURIE strings), we validate the structure differently.
    """

    # The actual response is a dict[str, NodeNormalizationNode]
    # We'll validate individual nodes in the server code

    class Config:
        extra = "allow"  # Allow dynamic CURIE keys


class NodeNormalizationToolResult(MCPToolResult[NodeNormalizationResult]):
    """Node Normalization-specific MCP tool result"""

    pass
