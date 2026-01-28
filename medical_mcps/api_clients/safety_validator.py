"""
Safety validation for Everycure KG queries to prevent path explosion.

The Everycure KG is highly connected (~9.2M nodes, 77M edges) with
average branching factor of ~440 per hop. This module provides safety
checks to prevent accidental query explosions that could overwhelm the
database or return millions of results.

Key thresholds (based on graph analysis):
- Warn: Node degree > 1,000 (high branching)
- Block: Node degree > 10,000 (extreme branching)
- Block: Estimated paths > 100,000 (likely explosion)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Safety thresholds
DEGREE_WARN_THRESHOLD = 1_000
DEGREE_BLOCK_THRESHOLD = 10_000
ESTIMATED_PATHS_BLOCK_THRESHOLD = 100_000

# Average branching factor from graph analysis
AVERAGE_BRANCHING_FACTOR = 440


async def check_node_degree(
    client: Any,  # Neo4jClient
    node_id: str,
    database: str,
    max_hops: int = 1,
) -> dict[str, Any]:
    """
    Check node degree before traversal to prevent path explosion.

    Args:
        client: Neo4jClient instance
        node_id: Node identifier (e.g., "MONDO:0007113")
        database: Database name
        max_hops: Number of hops planned (affects risk assessment)

    Returns:
        Dict with:
        - safe: bool - True if safe to proceed
        - degree: int - Node's total degree (incoming + outgoing edges)
        - warning: str|None - Warning message if degree is high
        - blocked: bool - True if query should be blocked
        - risk_level: str - "low", "medium", "high", "critical"
    """
    logger.info(f"Checking degree for node '{node_id}' (max_hops={max_hops})")

    try:
        # Query to get node degree (both incoming and outgoing)
        query = """
        MATCH (n {id: $node_id})
        OPTIONAL MATCH (n)-[r]-()
        RETURN
            n.id as node_id,
            n.name as node_name,
            labels(n) as labels,
            count(r) as degree
        """

        result = await client.execute_cypher(query, {"node_id": node_id}, database)

        if result.get("data") is None or not result["data"]:
            # Node not found - this will fail later, but not a safety issue
            return {
                "safe": True,
                "degree": 0,
                "warning": None,
                "blocked": False,
                "risk_level": "unknown",
                "error": f"Node not found: {node_id}",
            }

        record = result["data"][0]
        degree = record.get("degree", 0)
        node_name = record.get("node_name", node_id)
        labels = record.get("labels", [])

        # Assess risk based on degree and hops
        risk_level = "low"
        warning = None
        blocked = False
        safe = True

        if degree >= DEGREE_BLOCK_THRESHOLD:
            # Critical: Block queries on super-hubs
            risk_level = "critical"
            blocked = True
            safe = False
            warning = (
                f"BLOCKED: Node '{node_name}' ({node_id}) has extremely high degree "
                f"({degree:,} edges). Multi-hop queries on this node would cause path explosion. "
                f"Consider using get_neighborhood() with limit parameter instead."
            )
        elif degree >= DEGREE_WARN_THRESHOLD:
            # High risk: Warn but allow
            risk_level = "high"
            safe = True  # Allow but warn
            if max_hops > 1:
                estimated_paths = degree * (AVERAGE_BRANCHING_FACTOR ** (max_hops - 1))
                warning = (
                    f"WARNING: Node '{node_name}' ({node_id}) has high degree ({degree:,} edges). "
                    f"A {max_hops}-hop query could return ~{estimated_paths:,.0f} paths. "
                    f"Consider reducing max_hops or using more specific filters."
                )
            else:
                warning = (
                    f"INFO: Node '{node_name}' ({node_id}) has high degree ({degree:,} edges). "
                    f"Results will be limited by your limit parameter."
                )
        elif degree > 100:
            # Medium risk: Just log info
            risk_level = "medium"
            if max_hops > 2:
                estimated_paths = degree * (AVERAGE_BRANCHING_FACTOR ** (max_hops - 1))
                warning = (
                    f"INFO: Node '{node_name}' ({node_id}) has moderate degree ({degree:,} edges). "
                    f"A {max_hops}-hop query could return ~{estimated_paths:,.0f} paths."
                )

        if warning:
            logger.warning(warning)

        return {
            "safe": safe,
            "degree": degree,
            "warning": warning,
            "blocked": blocked,
            "risk_level": risk_level,
            "node_id": node_id,
            "node_name": node_name,
            "labels": labels,
        }

    except Exception as e:
        logger.error(f"Error checking node degree: {e}", exc_info=True)
        # On error, allow query (don't block on safety check failures)
        return {
            "safe": True,
            "degree": -1,
            "warning": None,
            "blocked": False,
            "risk_level": "unknown",
            "error": str(e),
        }


async def estimate_path_complexity(
    source_degree: int,
    target_degree: int,
    hops: int,
) -> dict[str, Any]:
    """
    Estimate if query will explode based on degrees and hops.

    Uses heuristic: estimated_paths ≈ source_degree × (avg_branching)^(hops-1)

    This is a rough estimate because:
    - Not all paths lead to target
    - Graph structure varies
    - But it's conservative enough to prevent disasters

    Args:
        source_degree: Degree of source node
        target_degree: Degree of target node
        hops: Number of hops in the path

    Returns:
        Dict with:
        - estimated_paths: int - Rough estimate of path count
        - safe: bool - True if query is likely safe
        - warning: str|None - Warning message if risky
        - blocked: bool - True if should block query
        - risk_level: str - "low", "medium", "high", "critical"
    """
    # Estimate paths using geometric growth
    if hops == 1:
        # Direct connection: at most min(source_degree, target_degree)
        estimated_paths = min(source_degree, target_degree)
    else:
        # Multi-hop: exponential growth
        # Conservative estimate: source_degree × (avg_branching)^(hops-1)
        estimated_paths = source_degree * (AVERAGE_BRANCHING_FACTOR ** (hops - 1))

    # Assess risk
    risk_level = "low"
    warning = None
    blocked = False
    safe = True

    if estimated_paths >= ESTIMATED_PATHS_BLOCK_THRESHOLD:
        # Critical: Block
        risk_level = "critical"
        blocked = True
        safe = False
        warning = (
            f"BLOCKED: Query would likely return ~{estimated_paths:,.0f} paths "
            f"(source degree: {source_degree:,}, {hops} hops). "
            f"This would cause path explosion. Consider using a more specific metapath "
            f"or reducing the number of hops."
        )
    elif estimated_paths >= 10_000:
        # High risk: Warn
        risk_level = "high"
        warning = (
            f"WARNING: Query could return ~{estimated_paths:,.0f} paths "
            f"(source degree: {source_degree:,}, {hops} hops). "
            f"Results will be limited by max_paths parameter, but query may be slow."
        )
    elif estimated_paths >= 1_000:
        # Medium risk: Info
        risk_level = "medium"
        warning = (
            f"INFO: Query could return ~{estimated_paths:,.0f} paths "
            f"(source degree: {source_degree:,}, {hops} hops)."
        )

    if warning:
        logger.info(f"Path complexity estimate: {warning}")

    return {
        "estimated_paths": int(estimated_paths),
        "safe": safe,
        "warning": warning,
        "blocked": blocked,
        "risk_level": risk_level,
        "source_degree": source_degree,
        "target_degree": target_degree,
        "hops": hops,
    }


async def check_metapath_safety(
    client: Any,  # Neo4jClient
    source_id: str,
    target_id: str,
    hops: int,
    database: str,
) -> dict[str, Any]:
    """
    Combined safety check for metapath queries.

    Checks both source and target node degrees, estimates path complexity,
    and returns comprehensive safety assessment.

    Args:
        client: Neo4jClient instance
        source_id: Source node identifier
        target_id: Target node identifier
        hops: Number of hops in metapath
        database: Database name

    Returns:
        Dict with:
        - safe: bool - True if safe to proceed
        - blocked: bool - True if query should be blocked
        - warning: str|None - Combined warning message
        - source_safety: dict - Source node safety check
        - target_safety: dict - Target node safety check
        - complexity: dict - Path complexity estimate
        - risk_level: str - Overall risk level
    """
    # Check source node
    source_safety = await check_node_degree(client, source_id, database, hops)

    # Check target node
    target_safety = await check_node_degree(client, target_id, database, hops)

    # If either node is blocked, block the query
    if source_safety["blocked"] or target_safety["blocked"]:
        blocked_node = "source" if source_safety["blocked"] else "target"
        return {
            "safe": False,
            "blocked": True,
            "warning": source_safety["warning"] or target_safety["warning"],
            "source_safety": source_safety,
            "target_safety": target_safety,
            "complexity": None,
            "risk_level": "critical",
            "blocked_node": blocked_node,
        }

    # Estimate path complexity
    complexity = await estimate_path_complexity(
        source_safety["degree"],
        target_safety["degree"],
        hops,
    )

    # Determine overall safety
    safe = not complexity["blocked"]
    blocked = complexity["blocked"]

    # Combine warnings
    warnings = []
    if source_safety["warning"]:
        warnings.append(f"Source: {source_safety['warning']}")
    if target_safety["warning"]:
        warnings.append(f"Target: {target_safety['warning']}")
    if complexity["warning"]:
        warnings.append(complexity["warning"])

    combined_warning = " | ".join(warnings) if warnings else None

    # Overall risk level (max of all risks)
    risk_levels = ["low", "medium", "high", "critical"]
    max_risk_idx = max(
        risk_levels.index(source_safety["risk_level"]),
        risk_levels.index(target_safety["risk_level"]),
        risk_levels.index(complexity["risk_level"]),
    )
    overall_risk = risk_levels[max_risk_idx]

    return {
        "safe": safe,
        "blocked": blocked,
        "warning": combined_warning,
        "source_safety": source_safety,
        "target_safety": target_safety,
        "complexity": complexity,
        "risk_level": overall_risk,
    }
