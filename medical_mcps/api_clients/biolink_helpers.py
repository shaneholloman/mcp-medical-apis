"""
Biolink Model helpers for node labels and relationship types.
Handles biolink: prefix intelligently for agent convenience.
Uses the bmt (Biolink Model Toolkit) library to access Biolink Model definitions.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bmt import Toolkit  # type: ignore[import-untyped]

# Whitelist of meaningful node types for biomedical pathway discovery
# Excludes ontology noise, procedures, and non-meaningful entities
MEANINGFUL_NODE_TYPES = {
    # Core biomedical entities
    "Drug",
    "Disease",
    "DiseaseOrPhenotypicFeature",
    "Gene",
    "GeneFamily",
    "GeneProduct",
    "Protein",
    "Polypeptide",
    "Pathway",
    "BiologicalProcess",
    "MolecularActivity",
    "CellularComponent",
    # Chemical entities
    "ChemicalEntity",
    "SmallMolecule",
    "MolecularMixture",
    "ChemicalMixture",
    # Phenotypic features
    "PhenotypicFeature",
    "BehavioralFeature",
    "ClinicalFinding",
    # Anatomical entities
    "AnatomicalEntity",
    "Cell",
    "CellLine",
    "GrossAnatomicalStructure",
    # Organism
    "OrganismTaxon",
    # Information content
    "Publication",
    "InformationContentEntity",
}

# Whitelist of meaningful relationship types for biomedical pathway discovery
# Excludes generic/ontology relationships that don't add value for pathway discovery
MEANINGFUL_RELATIONSHIP_TYPES = {
    # Treatment relationships
    "treats",
    "treats_or_applied_or_studied_to_treat",
    "applied_to_treat",
    "prevents",
    "contraindicated_in",
    # Causal relationships
    "causes",
    "predisposes_to_condition",
    "contributes_to",
    # Association relationships
    "associated_with",
    "genetically_associated_with",
    "gene_associated_with_condition",
    "disease_has_basis_in",
    # Interaction relationships
    "interacts_with",
    "directly_physically_interacts_with",
    "physically_interacts_with",
    "molecularly_interacts_with",
    "regulates",
    "affects",
    "disrupts",
    # Targeting relationships
    "targets",
    "has_target",
    # Side effects and adverse events
    "has_side_effect",
    "has_adverse_event",
    # Pathway relationships
    "part_of",
    "actively_involved_in",
    "has_participant",
    "located_in",
    # Gene product relationships
    "gene_product_of",
    # Regulatory relationships
    "acts_upstream_of",
    "acts_upstream_of_or_within",
    "acts_upstream_of_positive_effect",
    "acts_upstream_of_or_within_positive_effect",
    # Related relationships (keep as it's commonly used)
    "related_to",
}

# Cache for bmt Toolkit instance
_toolkit: "Toolkit | None" = None


def _get_toolkit() -> "Toolkit":
    """Get or create bmt Toolkit instance."""
    global _toolkit
    if _toolkit is None:
        try:
            import bmt

            _toolkit = bmt.Toolkit()
        except ImportError:
            raise ImportError("bmt library is required. Install it with: pip install bmt")
    return _toolkit


def normalize_node_label(label: str) -> str:
    """
    Normalize node label - add biolink: prefix if missing.
    Allows agents to use 'Drug' or 'biolink:Drug' interchangeably.

    Special case: 'Entity' doesn't use biolink: prefix in the database.

    Args:
        label: Node label (with or without biolink: prefix)

    Returns:
        Normalized label with biolink: prefix (except for 'Entity')
    """
    if not label:
        return label

    # Entity is special - doesn't use biolink: prefix
    if label == "Entity" or label == "biolink:Entity":
        return "Entity"

    # If already has biolink: prefix, return as-is
    if label.startswith("biolink:"):
        return label

    # Add biolink: prefix
    return f"biolink:{label}"


def normalize_relationship_type(rel_type: str) -> str:
    """
    Normalize relationship type.
    Relationship types typically don't use biolink: prefix.

    Args:
        rel_type: Relationship type name

    Returns:
        Normalized relationship type (unchanged, as they don't use prefix)
    """
    # Relationship types don't use biolink: prefix in Neo4j
    return rel_type


def validate_node_type(node_type: str) -> tuple[bool, str | None]:
    """Validate node type exists in Biolink Model and whitelist. Returns (is_valid, normalized_class_uri)."""
    # Check whitelist first (fast)
    base_name = node_type.replace("biolink:", "")
    if base_name not in MEANINGFUL_NODE_TYPES:
        return False, None

    # Validate with BMT
    try:
        toolkit = _get_toolkit()
        elem = toolkit.get_element(base_name.lower())
        if hasattr(elem, "class_uri") and elem.class_uri:
            return True, normalize_node_label(base_name)
    except Exception:
        pass
    return False, None


def validate_relationship_type(rel_type: str) -> tuple[bool, str | None]:
    """Validate relationship type exists in Biolink Model and whitelist. Returns (is_valid, normalized_rel_type)."""
    # Check whitelist first (fast)
    if rel_type not in MEANINGFUL_RELATIONSHIP_TYPES:
        return False, None

    # Validate with BMT (try direct lookup first)
    try:
        toolkit = _get_toolkit()
        # Try as-is, with spaces, and with underscores
        for variant in [rel_type, rel_type.replace("_", " "), rel_type.replace("_", "-")]:
            try:
                elem = toolkit.get_element(variant)
                if hasattr(elem, "slot_uri") and elem.slot_uri:
                    normalized = elem.slot_uri.replace("biolink:", "")
                    if normalized in MEANINGFUL_RELATIONSHIP_TYPES:
                        return True, normalized
            except Exception:
                continue
    except Exception:
        pass
    return False, None


def get_common_node_types() -> list[str]:
    """
    Return list of meaningful Biolink node types for biomedical pathway discovery.
    Uses bmt library to get all Biolink classes, then filters by whitelist.
    All returned labels include biolink: prefix.

    Returns:
        List of meaningful node type labels with biolink: prefix
    """
    try:
        toolkit = _get_toolkit()
        # Get all entities from Biolink Model
        all_entities = toolkit.get_all_entities()
        meaningful_classes = []

        for entity_name in all_entities:
            try:
                # Get the ClassDefinition for this entity
                elem = toolkit.get_element(entity_name)
                if hasattr(elem, "class_uri") and elem.class_uri:
                    # Extract class name from CURIE (e.g., "biolink:Drug" -> "Drug")
                    class_name = elem.class_uri.replace("biolink:", "")
                    # Check if it's in our whitelist
                    if class_name in MEANINGFUL_NODE_TYPES:
                        meaningful_classes.append(elem.class_uri)
            except Exception:
                # Skip entities that can't be retrieved
                continue

        # Ensure all have biolink: prefix and normalize
        return [normalize_node_label(cls.replace("biolink:", "")) for cls in meaningful_classes]
    except Exception:
        # Fallback to hardcoded list if bmt fails
        return [normalize_node_label(label) for label in MEANINGFUL_NODE_TYPES]


def get_common_relationship_types() -> list[str]:
    """
    Return list of meaningful relationship types for biomedical pathway discovery.
    Uses bmt library to get all Biolink slots (relationships), then filters by whitelist.

    Returns:
        List of meaningful relationship type names (with underscores, matching database format)
    """
    try:
        toolkit = _get_toolkit()
        # Get all slots (relationships) from Biolink Model
        all_slots = toolkit.get_all_slots()
        meaningful_slots = []

        for slot_name in all_slots:
            try:
                # Get the SlotDefinition for this slot
                slot_elem = toolkit.get_element(slot_name)
                if hasattr(slot_elem, "slot_uri") and slot_elem.slot_uri:
                    # Extract slot name from CURIE (e.g., "biolink:has_side_effect" -> "has_side_effect")
                    slot_normalized = slot_elem.slot_uri.replace("biolink:", "")
                    # Check if it's in our whitelist
                    if slot_normalized in MEANINGFUL_RELATIONSHIP_TYPES:
                        meaningful_slots.append(slot_normalized)
            except Exception:
                # Skip slots that can't be retrieved
                continue

        return meaningful_slots
    except Exception:
        # Fallback to hardcoded list if bmt fails
        return list(MEANINGFUL_RELATIONSHIP_TYPES)
