"""
Pydantic models for UniProt API responses.

These models provide structure validation and documentation for UniProt API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any, Optional

from pydantic import BaseModel

from .base import MCPToolResult


class UniProtOrganism(BaseModel):
    """Organism information"""

    scientificName: str
    commonName: Optional[str] = None
    taxonId: int
    lineage: Optional[list[str]] = None


class UniProtProteinDescription(BaseModel):
    """Protein description"""

    recommendedName: Optional[dict[str, Any]] = None
    alternativeNames: Optional[list[dict[str, Any]]] = None


class UniProtEntryAudit(BaseModel):
    """Entry audit information"""

    firstPublicDate: Optional[str] = None
    lastAnnotationUpdateDate: Optional[str] = None
    lastSequenceUpdateDate: Optional[str] = None
    entryVersion: Optional[int] = None
    sequenceVersion: Optional[int] = None


class UniProtSequence(BaseModel):
    """Protein sequence information"""

    value: Optional[str] = None
    length: Optional[int] = None
    molWeight: Optional[int] = None
    crc64: Optional[str] = None
    md5: Optional[str] = None


class UniProtProtein(BaseModel):
    """
    Main UniProt protein entry model.

    This model captures the core structure of UniProt protein entries.
    Many fields are optional to handle variations in API responses.
    """

    entryType: Optional[str] = None
    primaryAccession: str
    secondaryAccessions: Optional[list[str]] = None
    uniProtkbId: Optional[str] = None
    entryAudit: Optional[UniProtEntryAudit] = None
    annotationScore: Optional[float] = None
    organism: Optional[UniProtOrganism] = None
    proteinExistence: Optional[str] = None
    proteinDescription: Optional[UniProtProteinDescription] = None
    genes: Optional[list[dict[str, Any]]] = None
    comments: Optional[list[dict[str, Any]]] = None
    features: Optional[list[dict[str, Any]]] = None
    keywords: Optional[list[dict[str, Any]]] = None
    references: Optional[list[dict[str, Any]]] = None
    uniProtKBCrossReferences: Optional[list[dict[str, Any]]] = None
    sequence: Optional[UniProtSequence] = None
    extraAttributes: Optional[dict[str, Any]] = None

    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class UniProtSearchResult(BaseModel):
    """UniProt search results"""

    results: Optional[list[UniProtProtein]] = None
    facets: Optional[list[dict[str, Any]]] = None
    totalResults: Optional[int] = None

    class Config:
        extra = "allow"


class UniProtToolResult(MCPToolResult[UniProtProtein]):
    """
    UniProt-specific MCP tool result.

    Inherits from MCPToolResult and specifies UniProtProtein as the data type.
    """

    pass
