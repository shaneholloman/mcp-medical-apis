"""
Pydantic models for GWAS Catalog API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Optional

from pydantic import BaseModel

from .base import MCPToolResult


class GWASAssociation(BaseModel):
    """GWAS association data structure"""

    id: Optional[int] = None
    pvalue: Optional[float] = None
    pvalueText: Optional[str] = None
    riskFrequency: Optional[str] = None
    orPerCopyNum: Optional[float] = None
    betaNum: Optional[float] = None
    betaUnit: Optional[str] = None
    betaDirection: Optional[str] = None
    standardError: Optional[float] = None

    class Config:
        extra = "allow"


class GWASVariant(BaseModel):
    """GWAS variant/SNP data structure"""

    id: Optional[int] = None
    rsId: Optional[str] = None
    functionalClass: Optional[str] = None
    chromosomeName: Optional[str] = None
    chromosomePosition: Optional[int] = None

    class Config:
        extra = "allow"


class GWASStudy(BaseModel):
    """GWAS study data structure"""

    id: Optional[int] = None
    initialSampleSize: Optional[str] = None
    replicationSampleSize: Optional[str] = None
    publicationDate: Optional[str] = None
    pubmedId: Optional[str] = None

    class Config:
        extra = "allow"


class GWASTrait(BaseModel):
    """GWAS trait data structure"""

    id: Optional[int] = None
    trait: Optional[str] = None
    efoTrait: Optional[str] = None

    class Config:
        extra = "allow"


class GWASToolResult(MCPToolResult[GWASAssociation]):
    """GWAS-specific MCP tool result"""

    pass
