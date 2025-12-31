"""OpenTargets Platform API client - GraphQL API."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class OpenTargetsClient(BaseAPIClient):
    """Client for the OpenTargets Platform GraphQL API (v4)."""

    def __init__(self, enable_cache: bool | None = None) -> None:
        super().__init__(
            base_url="https://api.platform.opentargets.org/api/v4/graphql",
            api_name="OpenTargets",
            timeout=30.0,
            rate_limit_delay=0.2,
            enable_cache=enable_cache,
        )

    async def _graphql_query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query."""
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        
        # Use a custom request to capture error details
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as e:
            # Try to extract GraphQL error from response
            try:
                error_body = e.response.json()
                if "errors" in error_body:
                    error_messages = [err.get("message", str(err)) for err in error_body.get("errors", [])]
                    logger.error(f"GraphQL errors: {'; '.join(error_messages)}")
                    raise Exception(f"OpenTargets GraphQL error: {'; '.join(error_messages)}")
            except Exception:
                pass
            # Fall back to base client error handling
            raise Exception(self._extract_error_message(e)) from e
        except Exception as e:
            logger.error(f"GraphQL query failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Variables: {variables}")
            raise
        
        # GraphQL responses have "data" and potentially "errors" fields
        if isinstance(result, dict) and "errors" in result:
            error_messages = [err.get("message", str(err)) for err in result.get("errors", [])]
            error_details = [json.dumps(err, indent=2) for err in result.get("errors", [])]
            logger.error(f"GraphQL errors: {'; '.join(error_messages)}")
            logger.debug(f"Error details: {error_details}")
            raise Exception(f"OpenTargets GraphQL error: {'; '.join(error_messages)}")
        
        return result

    async def search(self, query: str, entity: str | None = None, size: int = 10) -> dict[str, Any]:
        """Search across targets, diseases, and drugs."""
        # Map entity names to GraphQL entityNames format
        entity_names = None
        if entity:
            # OpenTargets GraphQL uses lowercase entity names: ["target", "disease", "drug"]
            entity_map = {
                "target": "target",
                "disease": "disease", 
                "drug": "drug",
                "targets": "target",
                "diseases": "disease",
                "drugs": "drug",
            }
            mapped_entity = entity_map.get(entity.lower(), entity.lower())
            entity_names = [mapped_entity]
        
        # Build GraphQL query
        graphql_query = """
        query Search($queryString: String!, $entityNames: [String!], $size: Int!) {
          search(queryString: $queryString, entityNames: $entityNames, page: { index: 0, size: $size }) {
            hits {
              id
              name
              description
              entity
              score
            }
          }
        }
        """
        
        variables: dict[str, Any] = {
            "queryString": query,
            "size": size,
        }
        if entity_names:
            variables["entityNames"] = entity_names
        
        result = await self._graphql_query(graphql_query, variables)
        
        # Transform GraphQL response to match expected format
        if "data" in result and "search" in result["data"]:
            hits = result["data"]["search"].get("hits", [])
            return {"data": hits}
        
        return {"data": []}

    async def get_associations(
        self,
        target_id: str | None = None,
        disease_id: str | None = None,
        size: int = 50,
    ) -> dict[str, Any]:
        """Fetch target-disease associations."""
        if not target_id and not disease_id:
            raise ValueError("Provide at least one of target_id or disease_id")
        
        # Build GraphQL query - OpenTargets uses ensemblId for targets and efoId for diseases
        if target_id:
            # Query target associations
            graphql_query = """
            query GetTargetAssociations($targetId: String!, $size: Int!) {
              target(ensemblId: $targetId) {
                id
                approvedName
                associatedDiseases(page: { index: 0, size: $size }) {
                  rows {
                    disease {
                      id
                      name
                    }
                    score
                    datatypeScores {
                      id
                      score
                    }
                  }
                }
              }
            }
            """
            variables: dict[str, Any] = {"targetId": target_id, "size": size}
        else:
            # Query disease associations
            graphql_query = """
            query GetDiseaseAssociations($diseaseId: String!, $size: Int!) {
              disease(efoId: $diseaseId) {
                id
                name
                associatedTargets(page: { index: 0, size: $size }) {
                  rows {
                    target {
                      id
                      approvedName
                    }
                    score
                    datatypeScores {
                      id
                      score
                    }
                  }
                }
              }
            }
            """
            variables = {"diseaseId": disease_id, "size": size}
        
        result = await self._graphql_query(graphql_query, variables)
        
        # Transform GraphQL response
        if "data" in result:
            if target_id and "target" in result["data"]:
                target_data = result["data"]["target"]
                if target_data and "associatedDiseases" in target_data:
                    rows = target_data["associatedDiseases"].get("rows", [])
                    return {"data": rows}
            elif disease_id and "disease" in result["data"]:
                disease_data = result["data"]["disease"]
                if disease_data and "associatedTargets" in disease_data:
                    rows = disease_data["associatedTargets"].get("rows", [])
                    return {"data": rows}
        
        return {"data": []}

    async def get_evidence(
        self,
        target_id: str,
        disease_id: str,
        size: int = 25,
    ) -> dict[str, Any]:
        """Retrieve evidence linking a target to a disease."""
        # Build GraphQL query - fetch associations and filter client-side for the specific disease
        # Note: OpenTargets GraphQL doesn't support filtering associatedDiseases by efoId directly
        # We fetch a larger set and filter, or use a reasonable size limit
        graphql_query = """
        query GetEvidence($targetId: String!, $size: Int!) {
          target(ensemblId: $targetId) {
            id
            approvedName
            associatedDiseases(page: { index: 0, size: $size }) {
              rows {
                disease {
                  id
                  name
                }
                score
                datatypeScores {
                  id
                  score
                }
              }
            }
          }
        }
        """
        
        variables = {
            "targetId": target_id,
            "size": size * 2,  # Fetch more to increase chance of finding the disease
        }
        
        result = await self._graphql_query(graphql_query, variables)
        
        # Transform GraphQL response and filter for the specific disease
        if "data" in result and "target" in result["data"]:
            target_data = result["data"]["target"]
            if target_data and "associatedDiseases" in target_data:
                rows = target_data["associatedDiseases"].get("rows", [])
                # Filter for the specific disease
                filtered_rows = [
                    row for row in rows
                    if row.get("disease", {}).get("id") == disease_id
                ]
                return {"data": filtered_rows[:size]}
        
        return {"data": []}
