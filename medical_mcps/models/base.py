"""
Base models for MCP server responses.

These models define the universal structure for all MCP tool responses.
Server-specific models should inherit from these base models.
"""

from typing import Any, TypeVar

from pydantic import BaseModel

# Type variable for the actual data type
T = TypeVar("T")


class MCPContentItem(BaseModel):
    """A single content item in an MCP response"""

    type: str  # Usually "text"
    text: str


class MCPToolResult[T](BaseModel):
    """
    Base model for MCP tool result structure.

    This is what FastMCP wraps tool return values in.
    FastMCP adds structuredContent when it detects structured data (dict/list).
    The structure is: {"result": <actual_data>}
    """

    content: list[MCPContentItem]
    isError: bool = False
    structuredContent: dict[str, Any] | None = None  # Usually {"result": T}

    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class MCPResponse[T](BaseModel):
    """
    Base model for complete MCP JSON-RPC response.

    This represents the full HTTP response structure from FastMCP servers.
    """

    jsonrpc: str = "2.0"
    id: int | str
    result: MCPToolResult[T]

    class Config:
        extra = "allow"


class APIResponseData(BaseModel):
    """
    Base model for API response data wrapper.

    Many API clients wrap their data with metadata using format_response().
    """

    data: Any
    metadata: dict[str, Any] | None = None

    class Config:
        extra = "allow"
