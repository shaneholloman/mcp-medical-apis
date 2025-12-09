"""
Pydantic models for UniProt API responses.

These models provide structure validation and documentation for UniProt API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class UniProtOrganism(BaseModel):
    """Organism information"""

    scientificName: str
    commonName: str | None = None
    taxonId: int
    lineage: list[str] | None = None


class UniProtProteinDescription(BaseModel):
    """Protein description"""

    recommendedName: dict[str, Any] | None = None
    alternativeNames: list[dict[str, Any]] | None = None


class UniProtEntryAudit(BaseModel):
    """Entry audit information"""

    firstPublicDate: str | None = None
    lastAnnotationUpdateDate: str | None = None
    lastSequenceUpdateDate: str | None = None
    entryVersion: int | None = None
    sequenceVersion: int | None = None


class UniProtSequence(BaseModel):
    """Protein sequence information"""

    value: str | None = None
    length: int | None = None
    molWeight: int | None = None
    crc64: str | None = None
    md5: str | None = None


class UniProtProtein(BaseModel):
    """
    Main UniProt protein entry model.

    This model captures the core structure of UniProt protein entries.
    Many fields are optional to handle variations in API responses.
    """

    entryType: str | None = None
    primaryAccession: str
    secondaryAccessions: list[str] | None = None
    uniProtkbId: str | None = None
    entryAudit: UniProtEntryAudit | None = None
    annotationScore: float | None = None
    organism: UniProtOrganism | None = None
    proteinExistence: str | None = None
    proteinDescription: UniProtProteinDescription | None = None
    genes: list[dict[str, Any]] | None = None
    comments: list[dict[str, Any]] | None = None
    features: list[dict[str, Any]] | None = None
    keywords: list[dict[str, Any]] | None = None
    references: list[dict[str, Any]] | None = None
    uniProtKBCrossReferences: list[dict[str, Any]] | None = None
    sequence: UniProtSequence | None = None
    extraAttributes: dict[str, Any] | None = None

    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class UniProtSearchResult(BaseModel):
    """UniProt search results"""

    results: list[UniProtProtein] | None = None
    facets: list[dict[str, Any]] | None = None
    totalResults: int | None = None

    class Config:
        extra = "allow"


class UniProtToolResult(MCPToolResult[UniProtProtein]):
    """
    UniProt-specific MCP tool result.

    Inherits from MCPToolResult and specifies UniProtProtein as the data type.
    """

    pass
