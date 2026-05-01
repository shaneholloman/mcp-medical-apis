# Patent MCP Tools (FDA-focused v1)

## Overview

The patent MCP server exposes two initial tools backed by `api.fda.gov/drug/drugsfda.json`:

1. `patent_search_orange_book`
2. `patent_get_exclusivities`

This v1 surface is designed for Level 1 IP screening workflows where fast public-data checks are needed.

## Tool: `patent_search_orange_book`

Searches FDA drugs@FDA records for application/product entries and returns parsed patent fields where available.

**Inputs**
- `drug_name` (optional)
- `active_ingredient` (optional)
- `application_number` (optional)
- `limit` (default 25)

At least one of the first three identifiers is required.

**Outputs**
- Patent listing objects with:
  - `patent_number`
  - `expiry_date` (normalized ISO date where parseable)
  - `patent_use_code`
  - `patent_use_description`
  - `is_expired` (pre-computed boolean when possible)
- `suggested_next_steps` for LLM orchestration.

## Tool: `patent_get_exclusivities`

Returns non-patent exclusivity records from drugs@FDA product fields.

**Inputs**
- `application_number` (optional)
- `active_ingredient` (optional)

At least one input is required.

**Outputs**
- Exclusivity records with:
  - `code`
  - `description`
  - `expiry_date`
  - `is_active`
- `suggested_next_steps` for follow-up checks.

## Notes

- This is intentionally FDA-first and does not provide litigation analysis.
- Results are public-data signals, not legal conclusions.
- Downstream skills should treat missing fields as `Insufficient data` rather than inferring certainty.
