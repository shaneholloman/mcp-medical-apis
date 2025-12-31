# OpenTargets Platform API Server

This server provides access to the OpenTargets Platform, a comprehensive resource for target-disease associations and evidence.

## Server Details

- **Name:** `opentargets-api-server`
- **Path:** `/tools/opentargets/mcp`
- **Base URL:** `https://mcp.cloud.curiloo.com/tools/opentargets/mcp`
- **API:** OpenTargets Platform v4 GraphQL API

## Tools

### 1. `opentargets_search`

Searches across targets, diseases, and drugs in the OpenTargets platform.

- **Parameters:**
    - `query` (string, required): Search term (e.g., `TP53`, `multiple sclerosis`, `imatinib`).
    - `entity` (string, optional): Filter by entity type. Valid values: `target`, `disease`, `drug` (or plural forms).
    - `size` (integer, optional): Maximum number of results to return (default: 10).

- **Returns:** List of matching entities with IDs, names, descriptions, entity types, and relevance scores.

### 2. `opentargets_get_associations`

Retrieves target-disease associations from OpenTargets.

- **Parameters:**
    - `target_id` (string, optional): Ensembl gene ID (e.g., `ENSG00000141510` for TP53).
    - `disease_id` (string, optional): EFO disease ID (e.g., `EFO_0003767` for multiple sclerosis).
    - `size` (integer, optional): Maximum number of results (default: 50).
    - **Note:** At least one of `target_id` or `disease_id` must be provided.

- **Returns:** List of associations with target/disease information, overall association scores, and datatype-specific scores (genetic association, literature, etc.).

### 3. `opentargets_get_evidence`

Fetches evidence linking a specific target to a disease.

- **Parameters:**
    - `target_id` (string, required): Ensembl gene ID (e.g., `ENSG00000157764` for BRAF).
    - `disease_id` (string, required): EFO disease ID (e.g., `EFO_0000756` for melanoma).
    - `size` (integer, optional): Maximum number of evidence entries (default: 25).

- **Returns:** List of evidence entries with association scores and datatype scores (genetic association, known drug, literature, etc.).

## ID Formats

- **Target IDs:** Ensembl gene IDs (e.g., `ENSG00000141510` for TP53, `ENSG00000157764` for BRAF)
- **Disease IDs:** EFO (Experimental Factor Ontology) IDs (e.g., `EFO_0003767` for multiple sclerosis, `EFO_0000756` for melanoma)

## Example Usage

1. **Search for a target:**
   ```
   opentargets_search(query="TP53", entity="target", size=10)
   ```

2. **Get diseases associated with a target:**
   ```
   opentargets_get_associations(target_id="ENSG00000141510", size=20)
   ```

3. **Get targets associated with a disease:**
   ```
   opentargets_get_associations(disease_id="EFO_0003767", size=20)
   ```

4. **Get evidence for a target-disease pair:**
   ```
   opentargets_get_evidence(target_id="ENSG00000157764", disease_id="EFO_0000756")
   ```

## Notes

- The OpenTargets Platform uses GraphQL API v4 for all queries.
- Empty search queries return empty results (not an error).
- Association scores range from 0 to 1, with higher scores indicating stronger associations.
- Evidence includes multiple datatype scores (genetic association, literature, known drug, etc.).

