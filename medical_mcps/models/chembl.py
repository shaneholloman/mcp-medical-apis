"""
Pydantic models for ChEMBL API responses.

Models derived from sample API responses.
Following 80/20 principle: capture main structure, allow flexibility for edge cases.
"""

from typing import Any

from pydantic import BaseModel

from .base import MCPToolResult


class ChEMBLMolecule(BaseModel):
    """ChEMBL molecule model"""

    molecule_chembl_id: str
    pref_name: str | None = None
    molecule_type: str | None = None
    max_phase: int | None = None
    first_approval: int | None = None
    molecular_weight: float | None = None
    alogp: float | None = None

    class Config:
        extra = "allow"


class ChEMBLTarget(BaseModel):
    """ChEMBL target model"""

    target_chembl_id: str
    pref_name: str | None = None
    target_type: str | None = None
    organism: str | None = None

    class Config:
        extra = "allow"


class ChEMBLActivity(BaseModel):
    """ChEMBL activity model"""

    activity_id: int | None = None
    molecule_chembl_id: str | None = None
    target_chembl_id: str | None = None
    standard_value: float | None = None
    standard_type: str | None = None
    standard_units: str | None = None
    assay_chembl_id: str | None = None

    class Config:
        extra = "allow"


class ChEMBLMechanism(BaseModel):
    """ChEMBL mechanism model"""

    mechanism_id: int | None = None
    molecule_chembl_id: str | None = None
    target_chembl_id: str | None = None
    mechanism_of_action: str | None = None
    action_type: str | None = None

    class Config:
        extra = "allow"


class ChEMBLDrugIndication(BaseModel):
    """ChEMBL drug indication model"""

    drug_chembl_id: str | None = None
    molecule_chembl_id: str | None = None
    parent_molecule_chembl_id: str | None = None
    mesh_heading: str | None = None
    mesh_id: str | None = None
    efo_id: str | None = None
    efo_term: str | None = None
    max_phase_for_ind: int | None = None
    indication_refs: list[Any] | None = None

    class Config:
        extra = "allow"


class ChEMBLToolResult(MCPToolResult[ChEMBLMolecule]):
    """ChEMBL-specific MCP tool result"""

    pass
