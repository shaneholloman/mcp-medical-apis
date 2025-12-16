"""
Cypher query builder helpers for maintainable query construction.
Avoids string concatenation errors and makes queries readable.
"""

from typing import Any

from .biolink_helpers import normalize_node_label, normalize_relationship_type


def build_match_clause(node_var: str, node_id: str, labels: list[str] | None = None) -> str:
    """
    Build MATCH clause for a node with optional labels.
    Uses biolink_helpers to normalize labels.

    Args:
        node_var: Variable name for the node (e.g., "n", "source")
        node_id: Node identifier property value (e.g., "MONDO:0007113")
        labels: Optional list of node labels to filter by

    Returns:
        MATCH clause string (e.g., "MATCH (n:biolink:Drug {id: $node_id})")
    """
    label_str = ""
    if labels:
        normalized_labels = [normalize_node_label(label) for label in labels]
        label_str = ":" + ":".join(normalized_labels)

    return f"MATCH ({node_var}{label_str} {{id: ${node_id}}})"


def build_relationship_pattern(
    start_var: str,
    end_var: str,
    rel_var: str | None = None,
    rel_types: list[str] | None = None,
    direction: str = "both",  # "out", "in", "both"
    min_hops: int = 1,
    max_hops: int = 1,
) -> str:
    """
    Build relationship pattern with optional type filtering.
    Uses biolink_helpers to normalize relationship types.

    Args:
        start_var: Variable name for start node
        end_var: Variable name for end node
        rel_var: Optional variable name for relationship
        rel_types: Optional list of relationship types to filter by
        direction: Direction of relationship ("out", "in", "both")
        min_hops: Minimum number of hops (for variable-length paths)
        max_hops: Maximum number of hops (for variable-length paths)

    Returns:
        Relationship pattern string (e.g., "-[r:treats]->" or "-[*1..2]->")
    """
    # Build relationship type filter
    rel_type_str = ""
    if rel_types:
        normalized_types = [normalize_relationship_type(rt) for rt in rel_types]
        rel_type_str = ":" + "|".join(normalized_types)

    # Build variable-length pattern if needed
    if min_hops != 1 or max_hops != 1:
        if min_hops == max_hops:
            hop_str = f"*{min_hops}"
        else:
            hop_str = f"*{min_hops}..{max_hops}"
    else:
        hop_str = ""

    # Build relationship variable
    rel_var_str = rel_var if rel_var else ""
    if rel_var_str:
        rel_var_str = f"[{rel_var_str}{rel_type_str}{hop_str}]"
    else:
        rel_var_str = f"[{rel_type_str}{hop_str}]" if rel_type_str or hop_str else ""

    # Build direction
    if direction == "out":
        return f"-{rel_var_str}->"
    elif direction == "in":
        return f"<-{rel_var_str}-"
    else:  # both
        return f"-{rel_var_str}-"


def build_where_clause(filters: dict[str, Any]) -> str:
    """
    Build WHERE clause from filter dict.

    Args:
        filters: Dict of filter conditions (e.g., {"labels": ["Drug"], "property": "value"})

    Returns:
        WHERE clause string (e.g., "WHERE 'Drug' IN labels(n) AND n.property = $property")
    """
    if not filters:
        return ""

    conditions = []
    for key, value in filters.items():
        if key == "labels" and isinstance(value, list):
            # Handle label filtering
            normalized_labels = [normalize_node_label(label) for label in value]
            label_conditions = " OR ".join(
                [f"'{label}' IN labels(n)" for label in normalized_labels]
            )
            conditions.append(f"({label_conditions})")
        elif isinstance(value, (str, int, float, bool)):
            # Simple property equality
            conditions.append(f"n.{key} = ${key}")
        elif isinstance(value, list):
            # IN clause
            conditions.append(f"n.{key} IN ${key}")

    if not conditions:
        return ""

    return "WHERE " + " AND ".join(conditions)


def build_return_clause(fields: list[str]) -> str:
    """
    Build RETURN clause.

    Args:
        fields: List of fields to return (e.g., ["n", "r", "count(n)"])

    Returns:
        RETURN clause string (e.g., "RETURN n, r, count(n)")
    """
    if not fields:
        return "RETURN *"
    return "RETURN " + ", ".join(fields)
