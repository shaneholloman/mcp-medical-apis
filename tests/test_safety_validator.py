"""Unit tests for safety_validator module.

Tests the safety validation logic for preventing path explosion in
Everycure KG queries without requiring actual database connection.
"""

import logging
from unittest.mock import AsyncMock

import pytest

from medical_mcps.api_clients.safety_validator import (
    AVERAGE_BRANCHING_FACTOR,
    DEGREE_BLOCK_THRESHOLD,
    DEGREE_WARN_THRESHOLD,
    ESTIMATED_PATHS_BLOCK_THRESHOLD,
    check_metapath_safety,
    check_node_degree,
    estimate_path_complexity,
)

# Disable logging during tests
logging.getLogger("medical_mcps.api_clients.safety_validator").setLevel(logging.CRITICAL)


class TestEstimatePathComplexity:
    """Test path complexity estimation"""

    @pytest.mark.asyncio
    async def test_1_hop_direct_connection(self):
        """Test 1-hop path complexity estimation"""
        result = await estimate_path_complexity(source_degree=100, target_degree=50, hops=1)

        assert result["estimated_paths"] == 50  # min(100, 50)
        assert result["safe"] is True
        assert result["blocked"] is False
        assert result["risk_level"] == "low"
        assert result["warning"] is None

    @pytest.mark.asyncio
    async def test_2_hop_medium_risk(self):
        """Test 2-hop path with medium risk"""
        result = await estimate_path_complexity(source_degree=10, target_degree=100, hops=2)

        # 10 × 440^1 = 4,400 paths (medium risk)
        assert result["estimated_paths"] == 10 * AVERAGE_BRANCHING_FACTOR
        assert result["safe"] is True  # Below block threshold
        assert result["blocked"] is False
        assert result["risk_level"] == "medium"
        assert result["warning"] is not None

    @pytest.mark.asyncio
    async def test_2_hop_high_risk(self):
        """Test 2-hop path with high risk"""
        result = await estimate_path_complexity(source_degree=100, target_degree=1000, hops=2)

        # 100 × 440 = 44,000 paths (high risk)
        assert result["estimated_paths"] == 100 * AVERAGE_BRANCHING_FACTOR
        assert result["safe"] is True  # Below block threshold
        assert result["blocked"] is False
        assert result["risk_level"] == "high"
        assert "WARNING" in result["warning"]

    @pytest.mark.asyncio
    async def test_3_hop_critical_blocked(self):
        """Test 3-hop path that should be blocked"""
        result = await estimate_path_complexity(source_degree=1000, target_degree=1000, hops=3)

        # 1000 × 440^2 = 193,600,000 paths (critical!)
        expected_paths = 1000 * (AVERAGE_BRANCHING_FACTOR**2)
        assert result["estimated_paths"] == int(expected_paths)
        assert result["safe"] is False
        assert result["blocked"] is True
        assert result["risk_level"] == "critical"
        assert "BLOCKED" in result["warning"]
        assert "path explosion" in result["warning"].lower()

    @pytest.mark.asyncio
    async def test_block_threshold_boundary(self):
        """Test behavior at block threshold boundary"""
        # Just below threshold
        source_degree = ESTIMATED_PATHS_BLOCK_THRESHOLD // AVERAGE_BRANCHING_FACTOR - 1
        result_below = await estimate_path_complexity(
            source_degree=source_degree, target_degree=1000, hops=2
        )
        assert result_below["blocked"] is False

        # Just above threshold
        source_degree = ESTIMATED_PATHS_BLOCK_THRESHOLD // AVERAGE_BRANCHING_FACTOR + 1
        result_above = await estimate_path_complexity(
            source_degree=source_degree, target_degree=1000, hops=2
        )
        assert result_above["blocked"] is True


class TestCheckNodeDegree:
    """Test node degree checking"""

    @pytest.mark.asyncio
    async def test_low_degree_node_safe(self):
        """Test low-degree node is safe"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.return_value = {
            "data": [
                {
                    "node_id": "TEST:123",
                    "node_name": "Test Node",
                    "labels": ["biolink:Gene"],
                    "degree": 50,
                }
            ]
        }

        result = await check_node_degree(mock_client, "TEST:123", "everycure-v0.13.0", max_hops=1)

        assert result["safe"] is True
        assert result["blocked"] is False
        assert result["degree"] == 50
        assert result["risk_level"] == "low"
        assert result["warning"] is None

    @pytest.mark.asyncio
    async def test_medium_degree_node_safe_1_hop(self):
        """Test medium-degree node safe for 1-hop"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.return_value = {
            "data": [
                {
                    "node_id": "TEST:456",
                    "node_name": "Medium Hub",
                    "labels": ["biolink:Protein"],
                    "degree": 500,
                }
            ]
        }

        result = await check_node_degree(mock_client, "TEST:456", "everycure-v0.13.0", max_hops=1)

        assert result["safe"] is True
        assert result["blocked"] is False
        assert result["degree"] == 500
        assert result["risk_level"] == "medium"
        # May or may not have warning for 1-hop

    @pytest.mark.asyncio
    async def test_high_degree_node_warns(self):
        """Test high-degree node triggers warning"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.return_value = {
            "data": [
                {
                    "node_id": "TEST:789",
                    "node_name": "High Degree Hub",
                    "labels": ["biolink:Gene"],
                    "degree": DEGREE_WARN_THRESHOLD + 100,
                }
            ]
        }

        result = await check_node_degree(mock_client, "TEST:789", "everycure-v0.13.0", max_hops=2)

        assert result["safe"] is True  # Warns but allows
        assert result["blocked"] is False
        assert result["degree"] == DEGREE_WARN_THRESHOLD + 100
        assert result["risk_level"] == "high"
        assert result["warning"] is not None
        assert "WARNING" in result["warning"]

    @pytest.mark.asyncio
    async def test_super_hub_blocked(self):
        """Test super-hub node is blocked"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.return_value = {
            "data": [
                {
                    "node_id": "TEST:SUPERHUB",
                    "node_name": "Super Hub",
                    "labels": ["biolink:Gene"],
                    "degree": DEGREE_BLOCK_THRESHOLD + 1000,
                }
            ]
        }

        result = await check_node_degree(
            mock_client, "TEST:SUPERHUB", "everycure-v0.13.0", max_hops=2
        )

        assert result["safe"] is False
        assert result["blocked"] is True
        assert result["degree"] == DEGREE_BLOCK_THRESHOLD + 1000
        assert result["risk_level"] == "critical"
        assert "BLOCKED" in result["warning"]
        assert "extremely high degree" in result["warning"].lower()

    @pytest.mark.asyncio
    async def test_node_not_found(self):
        """Test behavior when node not found"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.return_value = {"data": []}

        result = await check_node_degree(
            mock_client, "NONEXISTENT:999", "everycure-v0.13.0", max_hops=1
        )

        assert result["safe"] is True  # Don't block on missing nodes
        assert result["blocked"] is False
        assert result["degree"] == 0
        assert result["risk_level"] == "unknown"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_error_allows_through(self):
        """Test that query errors don't block (fail open)"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.side_effect = Exception("Database connection failed")

        result = await check_node_degree(mock_client, "TEST:123", "everycure-v0.13.0", max_hops=1)

        # Should fail open (allow query despite check failure)
        assert result["safe"] is True
        assert result["blocked"] is False
        assert result["risk_level"] == "unknown"
        assert "error" in result


class TestCheckMetapathSafety:
    """Test combined metapath safety checking"""

    @pytest.mark.asyncio
    async def test_both_nodes_safe(self):
        """Test when both source and target nodes are safe"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.side_effect = [
            # Source node
            {
                "data": [
                    {
                        "node_id": "SOURCE:1",
                        "node_name": "Source",
                        "labels": ["biolink:Drug"],
                        "degree": 100,
                    }
                ]
            },
            # Target node
            {
                "data": [
                    {
                        "node_id": "TARGET:1",
                        "node_name": "Target",
                        "labels": ["biolink:Disease"],
                        "degree": 50,
                    }
                ]
            },
        ]

        result = await check_metapath_safety(
            mock_client, "SOURCE:1", "TARGET:1", hops=2, database="everycure-v0.13.0"
        )

        assert result["safe"] is True
        assert result["blocked"] is False
        assert result["source_safety"]["degree"] == 100
        assert result["target_safety"]["degree"] == 50
        assert result["complexity"] is not None

    @pytest.mark.asyncio
    async def test_source_blocked(self):
        """Test when source node is blocked"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.side_effect = [
            # Source node (super-hub)
            {
                "data": [
                    {
                        "node_id": "SUPERHUB:1",
                        "node_name": "Super Hub",
                        "labels": ["biolink:Gene"],
                        "degree": DEGREE_BLOCK_THRESHOLD + 1000,
                    }
                ]
            },
            # Target node (won't be checked if source blocks)
            {
                "data": [
                    {
                        "node_id": "TARGET:1",
                        "node_name": "Target",
                        "labels": ["biolink:Disease"],
                        "degree": 50,
                    }
                ]
            },
        ]

        result = await check_metapath_safety(
            mock_client, "SUPERHUB:1", "TARGET:1", hops=3, database="everycure-v0.13.0"
        )

        assert result["safe"] is False
        assert result["blocked"] is True
        assert result["blocked_node"] == "source"
        assert result["risk_level"] == "critical"
        assert "BLOCKED" in result["warning"]

    @pytest.mark.asyncio
    async def test_target_blocked(self):
        """Test when target node is blocked"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.side_effect = [
            # Source node (safe)
            {
                "data": [
                    {
                        "node_id": "SOURCE:1",
                        "node_name": "Source",
                        "labels": ["biolink:Drug"],
                        "degree": 100,
                    }
                ]
            },
            # Target node (super-hub)
            {
                "data": [
                    {
                        "node_id": "SUPERHUB:2",
                        "node_name": "Target Super Hub",
                        "labels": ["biolink:Gene"],
                        "degree": DEGREE_BLOCK_THRESHOLD + 5000,
                    }
                ]
            },
        ]

        result = await check_metapath_safety(
            mock_client, "SOURCE:1", "SUPERHUB:2", hops=3, database="everycure-v0.13.0"
        )

        assert result["safe"] is False
        assert result["blocked"] is True
        assert result["blocked_node"] == "target"
        assert result["risk_level"] == "critical"

    @pytest.mark.asyncio
    async def test_complexity_blocked(self):
        """Test when complexity estimate blocks query"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.side_effect = [
            # Source node (high degree but not blocked individually)
            {
                "data": [
                    {
                        "node_id": "SOURCE:1",
                        "node_name": "Source",
                        "labels": ["biolink:Drug"],
                        "degree": 1000,
                    }
                ]
            },
            # Target node (high degree but not blocked individually)
            {
                "data": [
                    {
                        "node_id": "TARGET:1",
                        "node_name": "Target",
                        "labels": ["biolink:Disease"],
                        "degree": 1000,
                    }
                ]
            },
        ]

        result = await check_metapath_safety(
            mock_client, "SOURCE:1", "TARGET:1", hops=3, database="everycure-v0.13.0"
        )

        # Nodes individually OK, but combined complexity too high
        assert result["source_safety"]["blocked"] is False
        assert result["target_safety"]["blocked"] is False
        # But overall query is blocked by complexity
        assert result["blocked"] is True
        assert result["safe"] is False
        assert result["risk_level"] == "critical"

    @pytest.mark.asyncio
    async def test_warning_combination(self):
        """Test that warnings are properly combined"""
        mock_client = AsyncMock()
        mock_client.execute_cypher.side_effect = [
            # Source node (medium risk, warns but not blocked)
            {
                "data": [
                    {
                        "node_id": "SOURCE:1",
                        "node_name": "Source",
                        "labels": ["biolink:Drug"],
                        "degree": 200,  # Moderate degree
                    }
                ]
            },
            # Target node (medium risk, warns but not blocked)
            {
                "data": [
                    {
                        "node_id": "TARGET:1",
                        "node_name": "Target",
                        "labels": ["biolink:Disease"],
                        "degree": 150,  # Moderate degree
                    }
                ]
            },
        ]

        result = await check_metapath_safety(
            mock_client, "SOURCE:1", "TARGET:1", hops=2, database="everycure-v0.13.0"
        )

        # Both nodes are medium risk but complexity is OK
        # 200 × 440 = 88,000 paths (below 100K block threshold)
        assert result["safe"] is True
        assert result["blocked"] is False
        assert result["warning"] is not None
        assert result["risk_level"] in ["medium", "high"]


class TestThresholdConstants:
    """Test that safety thresholds are reasonable"""

    def test_thresholds_are_ordered(self):
        """Test that thresholds are in correct order"""
        assert DEGREE_WARN_THRESHOLD < DEGREE_BLOCK_THRESHOLD
        assert DEGREE_WARN_THRESHOLD == 1_000
        assert DEGREE_BLOCK_THRESHOLD == 10_000
        assert ESTIMATED_PATHS_BLOCK_THRESHOLD == 100_000

    def test_branching_factor_reasonable(self):
        """Test branching factor is reasonable"""
        assert AVERAGE_BRANCHING_FACTOR > 0
        assert AVERAGE_BRANCHING_FACTOR == 440  # From graph analysis
