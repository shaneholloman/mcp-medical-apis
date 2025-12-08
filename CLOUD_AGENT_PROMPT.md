# Cloud Agent Task: Complete Pydantic Validation for Remaining APIs

## Context

We're implementing Pydantic validation for all API clients to ensure upstream API responses are
structurally validated at runtime. This follows an 80/20 principle: capture main structure while
allowing flexibility.

**Status**: 4 APIs completed (Reactome, Node Normalization, GWAS, PubMed). 10 APIs remaining.

## Completed Work (Reference)

### Pattern Established

1. **Validation Utility** (`medical_mcps/servers/validation.py`):

    - `validate_response()` - Validates single object responses
    - `validate_list_response()` - Validates list responses (validates first item)

2. **Model Structure** (`medical_mcps/models/{api}.py`):

    - Create Pydantic models for each API's response structures
    - Models inherit from `BaseModel` with `extra = "allow"`
    - Key identifying fields are required (e.g., `stId` for Reactome, `rsId` for GWAS)

3. **Server Integration**:

    ```python
    from .validation import validate_response, validate_list_response
    from ..models.{api} import {ModelClass}

    result = await client.method(...)
    result = validate_response(
        result,
        ModelClass,
        key_field="field_name",
        api_name="API Name",
        context=identifier,
    )
    ```

4. **Models `__init__.py`**: Only exports base models, not provider-specific models

## Remaining APIs to Implement

### 1. KEGG (`models/kegg.py`, `servers/kegg_server.py`)

-   **Note**: KEGG returns text/plain format, not JSON. Skip validation for text responses.
-   Only validate JSON responses if any endpoints return JSON
-   Check `medical_mcps/api_clients/kegg_client.py` for response formats
-   Key fields: Check what KEGG returns in JSON format (if any)

### 2. ChEMBL (`models/chembl.py`, `servers/chembl_server.py`)

-   Models needed: `ChEMBLMolecule`, `ChEMBLTarget`, `ChEMBLActivity`
-   Check `medical_mcps/api_clients/chembl_client.py` for response structures
-   Key fields: Likely `molecule_chembl_id`, `target_chembl_id`, `activity_id`
-   Update tools: `get_molecule()`, `get_target()`, `get_activities()`

### 3. Pathway Commons (`models/pathwaycommons.py`, `servers/pathwaycommons_server.py`)

-   Models needed: `PathwayCommonsPathway`, `PathwayCommonsSearchResult`
-   Check `medical_mcps/api_clients/pathwaycommons_client.py`
-   Key fields: Check response structure
-   **Note**: This is marked as `slow` in tests

### 4. OMIM (`models/omim.py`, `servers/omim_server.py`)

-   Models needed: `OMIMEntry`, `OMIMSearchResult`
-   Check `medical_mcps/api_clients/omim_client.py`
-   Key fields: Likely `mimNumber` or `omim_id`
-   **Note**: Requires API key

### 5. OpenFDA (`models/openfda.py`, `servers/openfda_server.py`)

-   Models needed: `OpenFDAAdverseEvent`, `OpenFDADrugLabel`
-   Check `medical_mcps/api_clients/openfda_client.py`
-   Key fields: Check response structure
-   Update tools: `search_adverse_events()`, `get_adverse_event()`, `search_drug_labels()`,
    `get_drug_label()`

### 6. ClinicalTrials.gov (`models/ctg.py`, `servers/ctg_server.py`)

-   Models needed: `CTGStudy`, `CTGSearchResult`
-   Check `medical_mcps/api_clients/ctg_client.py`
-   **Note**: Client mentions OpenAPI spec at `notes/ctg-oas-v2.yaml` (check if exists)
-   Key fields: Likely `nctId` or `study_id`

### 7. MyVariant (`models/myvariant.py`, `servers/myvariant_server.py`)

-   Models needed: `MyVariantVariant`, `MyVariantSearchResult`
-   Check `medical_mcps/api_clients/myvariant_client.py`
-   Key fields: Likely `_id` or variant identifier

### 8. BioThings Suite (`models/biothings.py`, `servers/biothings_server.py`)

-   Models needed: `MyGeneGene`, `MyDiseaseDisease`, `MyChemDrug`
-   Check `medical_mcps/api_clients/mygene_client.py`, `mydisease_client.py`, `mychem_client.py`
-   Key fields: Check each service's response structure
-   Update tools for all three services

### 9. NCI Clinical Trials (`models/nci.py`, `servers/nci_server.py`)

-   Models needed: `NCITrial`, `NCISearchResult`
-   Check `medical_mcps/api_clients/nci_client.py`
-   Key fields: Check response structure
-   **Note**: Requires API key

### 10. OpenTargets (`models/opentargets.py`, `servers/opentargets_server.py`)

-   Models needed: `OpenTargetsAssociation`, `OpenTargetsSearchResult`
-   Check `medical_mcps/api_clients/opentargets_client.py`
-   Key fields: Check response structure

## Implementation Steps for Each API

1. **Examine API Client** (`medical_mcps/api_clients/{api}_client.py`):

    - Identify response structures
    - Note key identifying fields
    - Check if responses are wrapped in `format_response()` (has `data` key)

2. **Create Model File** (`medical_mcps/models/{api}.py`):

    ```python
    """
    Pydantic models for {API} API responses.

    Models derived from: {OpenAPI URL or "sample API responses"}
    Following 80/20 principle: capture main structure, allow flexibility.
    """

    from typing import Any, Optional
    from pydantic import BaseModel
    from .base import MCPToolResult

    class {API}Data(BaseModel):
        # Key identifying field (required)
        key_field: str
        # Other important fields (optional)
        field1: Optional[str] = None
        field2: Optional[int] = None
        # ...
        class Config:
            extra = "allow"

    class {API}ToolResult(MCPToolResult[{API}Data]):
        pass
    ```

3. **Update Server** (`medical_mcps/servers/{api}_server.py`):

    ```python
    from .validation import validate_response, validate_list_response
    from ..models.{api} import {ModelClass}

    @medmcps_tool(...)
    async def tool_method(...):
        result = await client.method(...)
        result = validate_response(
            result,
            ModelClass,
            key_field="key_field_name",
            api_name="{API Name}",
            context=identifier_if_available,
        )
        return result
    ```

4. **Update Tests** (`tests/test_{api}_tools.tavern.yaml`):

    - Ensure all response blocks have `strict: [json:off]`
    - Update regex patterns if needed to handle newlines: `(?s)pattern`

5. **Verify**:
    ```bash
    uv run pytest tests/test_{api}_tools.tavern.yaml -v
    ```

## Key Principles

1. **Fail Fast**: Validation errors raise `ValueError`, not warnings
2. **80/20**: Capture main structure, use `extra = "allow"` for flexibility
3. **DRY**: Use `validate_response()` and `validate_list_response()` utilities
4. **Text Responses**: Skip validation for non-JSON formats (fasta, xml, text)
5. **Key Field Detection**: Identify unique key field per API to determine if validation should run

## Testing Strategy

-   Run tests for each API after implementation
-   If tests fail, check:
    -   Response structure matches model
    -   Key field detection is correct
    -   Regex patterns in tests handle newlines
    -   `strict: [json:off]` is present in test responses

## Files to Create/Modify

**New Model Files (10):**

-   `medical_mcps/models/kegg.py`
-   `medical_mcps/models/chembl.py`
-   `medical_mcps/models/pathwaycommons.py`
-   `medical_mcps/models/omim.py`
-   `medical_mcps/models/openfda.py`
-   `medical_mcps/models/ctg.py`
-   `medical_mcps/models/myvariant.py`
-   `medical_mcps/models/biothings.py`
-   `medical_mcps/models/nci.py`
-   `medical_mcps/models/opentargets.py`

**Modified Server Files (10):**

-   `medical_mcps/servers/kegg_server.py`
-   `medical_mcps/servers/chembl_server.py`
-   `medical_mcps/servers/pathwaycommons_server.py`
-   `medical_mcps/servers/omim_server.py`
-   `medical_mcps/servers/openfda_server.py`
-   `medical_mcps/servers/ctg_server.py`
-   `medical_mcps/servers/myvariant_server.py`
-   `medical_mcps/servers/biothings_server.py`
-   `medical_mcps/servers/nci_server.py`
-   `medical_mcps/servers/opentargets_server.py`

**Test Files (10):**

-   Update all `test_*_tools.tavern.yaml` files to ensure `strict: [json:off]` is present

## Example: Completed Implementation (Reactome)

See `medical_mcps/models/reactome.py` and `medical_mcps/servers/reactome_server.py` for reference.

## Notes

-   **OpenAPI Specs**: Check for OpenAPI specs where available (e.g., CTG mentions
    `notes/ctg-oas-v2.yaml`)
-   **Sample Responses**: For APIs without OpenAPI, make actual API calls to get sample responses
-   **Text Formats**: KEGG primarily returns text - only validate if JSON endpoints exist
-   **Error Handling**: Validation errors should propagate as `ValueError` (fail fast)

## Success Criteria

-   All 10 remaining APIs have Pydantic models
-   All servers use `validate_response()` or `validate_list_response()`
-   All tests pass: `uv run pytest tests/ -v`
-   No linter errors: `uv run ruff check medical_mcps/`

## Questions?

If unsure about response structure:

1. Check the API client implementation
2. Look at existing test files for sample responses
3. Make a test API call to see actual response structure
4. Follow the 80/20 principle - capture main fields, allow extras

Good luck! 🚀
