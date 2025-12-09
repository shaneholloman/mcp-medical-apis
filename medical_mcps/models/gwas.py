"""
Pydantic models for GWAS Catalog API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from pydantic import BaseModel

from .base import MCPToolResult


class GWASAssociation(BaseModel):
    """GWAS association data structure"""

    id: int | None = None
    pvalue: float | None = None
    pvalueText: str | None = None
    riskFrequency: str | None = None
    orPerCopyNum: float | None = None
    betaNum: float | None = None
    betaUnit: str | None = None
    betaDirection: str | None = None
    standardError: float | None = None

    class Config:
        extra = "allow"


class GWASVariant(BaseModel):
    """GWAS variant/SNP data structure"""

    id: int | None = None
    rsId: str | None = None
    functionalClass: str | None = None
    chromosomeName: str | None = None
    chromosomePosition: int | None = None

    class Config:
        extra = "allow"


class GWASStudy(BaseModel):
    """GWAS study data structure"""

    id: int | None = None
    initialSampleSize: str | None = None
    replicationSampleSize: str | None = None
    publicationDate: str | None = None
    pubmedId: str | None = None

    class Config:
        extra = "allow"


class GWASTrait(BaseModel):
    """GWAS trait data structure"""

    id: int | None = None
    trait: str | None = None
    efoTrait: str | None = None

    class Config:
        extra = "allow"


class GWASToolResult(MCPToolResult[GWASAssociation]):
    """GWAS-specific MCP tool result"""

    pass
