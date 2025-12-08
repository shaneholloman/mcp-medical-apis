"""
Pydantic models for Reactome API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional
from pydantic import BaseModel

from .base import MCPToolResult


class ReactomeGOBiologicalProcess(BaseModel):
    """GO Biological Process information"""
    dbId: Optional[int] = None
    displayName: Optional[str] = None
    accession: Optional[str] = None
    databaseName: Optional[str] = None
    definition: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    className: Optional[str] = None
    schemaClass: Optional[str] = None


class ReactomeFigure(BaseModel):
    """Figure information"""
    dbId: Optional[int] = None
    displayName: Optional[str] = None
    url: Optional[str] = None
    className: Optional[str] = None
    schemaClass: Optional[str] = None


class ReactomeSpecies(BaseModel):
    """Species information"""
    dbId: Optional[int] = None
    displayName: Optional[str] = None
    name: Optional[list[str]] = None
    taxId: Optional[str] = None
    abbreviation: Optional[str] = None
    className: Optional[str] = None
    schemaClass: Optional[str] = None


class ReactomeSummation(BaseModel):
    """Summation information"""
    dbId: Optional[int] = None
    displayName: Optional[str] = None
    text: Optional[str] = None
    className: Optional[str] = None
    schemaClass: Optional[str] = None


class ReactomeReviewStatus(BaseModel):
    """Review status information"""
    dbId: Optional[int] = None
    displayName: Optional[str] = None
    definition: Optional[str] = None
    name: Optional[list[str]] = None
    className: Optional[str] = None
    schemaClass: Optional[str] = None


class ReactomeOrthologousEvent(BaseModel):
    """Orthologous event information"""
    dbId: Optional[int] = None
    displayName: Optional[str] = None
    stId: Optional[str] = None
    stIdVersion: Optional[str] = None
    isInDisease: Optional[bool] = None
    isInferred: Optional[bool] = None
    maxDepth: Optional[int] = None
    name: Optional[list[str]] = None
    releaseDate: Optional[str] = None
    speciesName: Optional[str] = None
    inferredFrom: Optional[list[int]] = None
    hasDiagram: Optional[bool] = None
    hasEHLD: Optional[bool] = None
    schemaClass: Optional[str] = None
    className: Optional[str] = None


class ReactomePathway(BaseModel):
    """
    Main Reactome pathway model.
    
    Captures the core structure of Reactome pathway entries.
    Supports both detailed pathway responses and query/search results.
    """
    dbId: Optional[int | str] = None  # Can be int or string depending on endpoint
    displayName: Optional[str] = None  # Not present in query results
    stId: str  # Stable identifier (e.g., "R-HSA-1640170")
    stIdVersion: Optional[str] = None
    isInDisease: Optional[bool] = None
    isInferred: Optional[bool] = None
    maxDepth: Optional[int] = None
    name: Optional[list[str] | str] = None  # Can be list[str] or str (with HTML in query results)
    releaseDate: Optional[str] = None
    releaseStatus: Optional[str] = None
    speciesName: Optional[str] = None
    species: Optional[list[ReactomeSpecies] | list[str]] = None  # Can be list of objects or strings
    figure: Optional[list[ReactomeFigure]] = None
    goBiologicalProcess: Optional[ReactomeGOBiologicalProcess] = None
    orthologousEvent: Optional[list[ReactomeOrthologousEvent]] = None
    summation: Optional[list[ReactomeSummation] | str] = None  # Can be list of objects or string
    className: Optional[str] = None
    schemaClass: Optional[str] = None
    type: Optional[str] = None  # Present in query results (e.g., "Pathway")
    exactType: Optional[str] = None  # Present in query results
    id: Optional[str] = None  # Present in query results (duplicate of stId)
    reviewStatus: Optional[ReactomeReviewStatus | str] = None  # Can be object or string
    hasDiagram: Optional[bool] = None
    hasEHLD: Optional[bool] = None
    lastUpdatedDate: Optional[str] = None
    
    class Config:
        extra = "allow"


class ReactomePathwayQueryResult(BaseModel):
    """Search/query results structure"""
    results: Optional[list[ReactomePathway]] = None
    totalResults: Optional[int] = None
    
    class Config:
        extra = "allow"


class ReactomeToolResult(MCPToolResult[ReactomePathway]):
    """Reactome-specific MCP tool result"""
    pass

