"""
Default metapaths for path finding in EveryCure Knowledge Graph.
These are biochemically sound patterns that limit path explosion.
"""

from .biolink_helpers import normalize_node_label

# Default metapaths - biochemically sound patterns
DEFAULT_METAPATHS = {
    "drug_to_disease_direct": {
        "name": "Drug → Disease (Direct)",
        "description": "Direct treatment relationship",
        "pattern": ["Drug", "treats_or_applied_or_studied_to_treat", "Disease"],
        "hops": 1,
    },
    "drug_to_disease_via_target": {
        "name": "Drug → Disease (Via Target)",
        "description": "Drug interacts with protein associated with disease",
        "pattern": [
            "Drug",
            "directly_physically_interacts_with",
            "Protein",
            "associated_with",
            "Disease",
        ],
        "hops": 2,
    },
    "drug_to_disease_via_pathway": {
        "name": "Drug → Disease (Via Pathway)",
        "description": "Drug interacts with protein in pathway associated with disease",
        "pattern": [
            "Drug",
            "directly_physically_interacts_with",
            "Protein",
            "actively_involved_in",
            "Pathway",
            "associated_with",
            "Disease",
        ],
        "hops": 3,
    },
    "disease_to_disease_shared_gene": {
        "name": "Disease → Disease (Shared Gene)",
        "description": "Two diseases associated with same gene",
        "pattern": ["Disease1", "associated_with", "Gene", "associated_with", "Disease2"],
        "hops": 2,
    },
    "drug_side_effect_path": {
        "name": "Drug → Side Effect → Disease",
        "description": "Drug causes side effect (phenotypic feature) associated with disease",
        "pattern": ["Drug", "causes", "PhenotypicFeature", "associated_with", "Disease"],
        "hops": 2,
    },
    "drug_to_disease_via_gene": {
        "name": "Drug → Disease (Via Gene)",
        "description": "Drug interacts with protein that is product of gene associated with disease",
        "pattern": [
            "Drug",
            "directly_physically_interacts_with",
            "Protein",
            "gene_product_of",
            "Gene",
            "associated_with",
            "Disease",
        ],
        "hops": 3,
    },
}


def get_metapath_by_name(name: str) -> dict | None:
    """
    Get metapath definition by name.

    Args:
        name: Metapath name (e.g., "drug_to_disease_direct")

    Returns:
        Metapath definition dict or None if not found
    """
    return DEFAULT_METAPATHS.get(name)


def list_metapaths() -> list[dict]:
    """
    List all available metapaths.

    Returns:
        List of metapath definition dicts
    """
    return list(DEFAULT_METAPATHS.values())


def parse_metapath_pattern(pattern: list[str]) -> tuple[list[str], list[str]]:
    """
    Parse metapath pattern into node labels and relationship types.
    Uses biolink_helpers to normalize labels.

    Args:
        pattern: Metapath pattern list (e.g., ["Drug", "treats", "Disease"])

    Returns:
        Tuple of (node_labels, relationship_types)
        Example: (["biolink:Drug", "biolink:Disease"], ["treats"])
    """
    node_labels = []
    relationship_types = []

    # Pattern alternates: NodeType, RelType, NodeType, RelType, ...
    for i, item in enumerate(pattern):
        if i % 2 == 0:
            # Even indices are node labels
            node_labels.append(normalize_node_label(item))
        else:
            # Odd indices are relationship types
            relationship_types.append(item)

    return node_labels, relationship_types


def parse_metapath_string(metapath_str: str) -> tuple[list[str], list[str], int]:
    """
    Parse a metapath string into node labels and relationship types.

    Supports formats:
    - "Drug->directly_physically_interacts_with->Protein->gene_product_of->Gene"
    - "Drug -> directly_physically_interacts_with -> Protein -> gene_product_of -> Gene"

    Args:
        metapath_str: Metapath string with arrows separating components

    Returns:
        Tuple of (node_labels, relationship_types, hops)

    Raises:
        ValueError: If metapath string is invalid
    """
    # Split by arrow (-> or -> with spaces)
    parts = [p.strip() for p in metapath_str.replace("->", "->").split("->")]

    if len(parts) < 2:
        raise ValueError("Metapath must have at least 2 components (source and target)")

    # Pattern should alternate: NodeType, RelType, NodeType, RelType, ...
    if len(parts) % 2 == 0:
        raise ValueError(
            "Metapath must alternate between node types and relationship types. "
            "Format: NodeType->RelType->NodeType->RelType->NodeType"
        )

    node_labels = []
    relationship_types = []

    for i, part in enumerate(parts):
        if i % 2 == 0:
            node_labels.append(part)
        else:
            relationship_types.append(part)

    hops = len(relationship_types)

    return node_labels, relationship_types, hops
