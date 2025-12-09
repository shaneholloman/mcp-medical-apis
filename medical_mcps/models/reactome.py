"""
Pydantic models for Reactome API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from pydantic import BaseModel

from .base import MCPToolResult


class ReactomeGOBiologicalProcess(BaseModel):
    """GO Biological Process information"""

    dbId: int | None = None
    displayName: str | None = None
    accession: str | None = None
    databaseName: str | None = None
    definition: str | None = None
    name: str | None = None
    url: str | None = None
    className: str | None = None
    schemaClass: str | None = None


class ReactomeFigure(BaseModel):
    """Figure information"""

    dbId: int | None = None
    displayName: str | None = None
    url: str | None = None
    className: str | None = None
    schemaClass: str | None = None


class ReactomeSpecies(BaseModel):
    """Species information"""

    dbId: int | None = None
    displayName: str | None = None
    name: list[str] | None = None
    taxId: str | None = None
    abbreviation: str | None = None
    className: str | None = None
    schemaClass: str | None = None


class ReactomeSummation(BaseModel):
    """Summation information"""

    dbId: int | None = None
    displayName: str | None = None
    text: str | None = None
    className: str | None = None
    schemaClass: str | None = None


class ReactomeReviewStatus(BaseModel):
    """Review status information"""

    dbId: int | None = None
    displayName: str | None = None
    definition: str | None = None
    name: list[str] | None = None
    className: str | None = None
    schemaClass: str | None = None


class ReactomeOrthologousEvent(BaseModel):
    """Orthologous event information"""

    dbId: int | None = None
    displayName: str | None = None
    stId: str | None = None
    stIdVersion: str | None = None
    isInDisease: bool | None = None
    isInferred: bool | None = None
    maxDepth: int | None = None
    name: list[str] | None = None
    releaseDate: str | None = None
    speciesName: str | None = None
    inferredFrom: list[int] | None = None
    hasDiagram: bool | None = None
    hasEHLD: bool | None = None
    schemaClass: str | None = None
    className: str | None = None


class ReactomePathway(BaseModel):
    """
    Main Reactome pathway model.

    Captures the core structure of Reactome pathway entries.
    Supports both detailed pathway responses and query/search results.
    """

    dbId: int | str | None = None  # Can be int or string depending on endpoint
    displayName: str | None = None  # Not present in query results
    stId: str  # Stable identifier (e.g., "R-HSA-1640170")
    stIdVersion: str | None = None
    isInDisease: bool | None = None
    isInferred: bool | None = None
    maxDepth: int | None = None
    name: list[str] | str | None = None  # Can be list[str] or str (with HTML in query results)
    releaseDate: str | None = None
    releaseStatus: str | None = None
    speciesName: str | None = None
    species: list[ReactomeSpecies] | list[str] | None = None  # Can be list of objects or strings
    figure: list[ReactomeFigure] | None = None
    goBiologicalProcess: ReactomeGOBiologicalProcess | None = None
    orthologousEvent: list[ReactomeOrthologousEvent] | None = None
    summation: list[ReactomeSummation] | str | None = None  # Can be list of objects or string
    className: str | None = None
    schemaClass: str | None = None
    type: str | None = None  # Present in query results (e.g., "Pathway")
    exactType: str | None = None  # Present in query results
    id: str | None = None  # Present in query results (duplicate of stId)
    reviewStatus: ReactomeReviewStatus | str | None = None  # Can be object or string
    hasDiagram: bool | None = None
    hasEHLD: bool | None = None
    lastUpdatedDate: str | None = None

    class Config:
        extra = "allow"


class ReactomePathwayQueryResult(BaseModel):
    """Search/query results structure"""

    results: list[ReactomePathway] | None = None
    totalResults: int | None = None

    class Config:
        extra = "allow"


class ReactomeToolResult(MCPToolResult[ReactomePathway]):
    """Reactome-specific MCP tool result"""

    pass
