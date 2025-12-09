"""
Shared validation utilities for API responses.
"""

import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def validate_response[T: BaseModel](
    result: dict,
    model_class: type[T],
    key_field: str | None = None,
    api_name: str = "API",
    context: str = "",
) -> dict:
    """
    Validate API response structure using Pydantic model.

    Args:
        result: Response dict from API client
        model_class: Pydantic model class to validate against
        key_field: Optional key field to check for before validating
        api_name: API name for logging (e.g., "Reactome", "GWAS")
        context: Additional context for logging (e.g., pathway_id)

    Returns:
        Validated and normalized result dict

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(result, dict):
        return result

    data_to_validate = result.get("data", result)

    # Skip validation if data is None/null or not a dict
    if data_to_validate is None or not isinstance(data_to_validate, dict):
        return result

    # Check for key field if specified
    if key_field and key_field not in data_to_validate:
        return result

    try:
        validated = model_class(**data_to_validate)
        logger.debug(
            f"Validated {api_name} response structure{f' for {context}' if context else ''}"
        )

        if "data" in result:
            result["data"] = validated.model_dump(exclude_none=False)
        else:
            result = validated.model_dump(exclude_none=False)

        return result
    except ValidationError as ve:
        logger.error(
            f"{api_name} response validation failed{f' for {context}' if context else ''}: {ve}"
        )
        raise ValueError(f"Invalid {api_name} API response structure: {ve}") from ve


def validate_list_response[T: BaseModel](
    result: dict,
    model_class: type[T],
    list_key: str = "results",
    api_name: str = "API",
) -> dict:
    """
    Validate list responses by validating first item.

    Args:
        result: Response dict from API client
        model_class: Pydantic model class to validate against
        list_key: Key containing the list (default: "results")
        api_name: API name for logging

    Returns:
        Original result dict (validation is for structure checking only)

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(result, dict):
        return result

    data = result.get("data", result)

    if not isinstance(data, dict):
        return result

    # Check for list key
    if list_key not in data:
        return result

    items = data[list_key]

    # Validate first item if list is non-empty
    if items and isinstance(items, list) and len(items) > 0:
        if isinstance(items[0], dict):
            try:
                model_class(**items[0])  # Validate first item
                logger.debug(f"Validated {api_name} list response structure")
            except ValidationError as ve:
                logger.error(f"{api_name} list response validation failed: {ve}")
                raise ValueError(f"Invalid {api_name} API response structure: {ve}") from ve

    return result
