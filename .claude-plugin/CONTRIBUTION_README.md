# Medical MCPs Contribution to Life Sciences Marketplace

This document outlines how to contribute the Medical MCPs server to the anthropics/life-sciences marketplace.

## Overview

**Medical MCPs** is a comprehensive biological and medical research data integration server that provides unified access to 13+ specialized databases through a single MCP interface.

### Databases Included

1. **Reactome** - Pathway analysis and biological networks
2. **KEGG** - Pathway and disease databases
3. **UniProt** - Protein sequences and functional information
4. **ChEMBL** - Drug discovery and bioactive molecules
5. **PubMed** - Biomedical literature search
6. **GWAS Catalog** - Genetic associations with diseases
7. **ClinicalTrials.gov** - Clinical trial data
8. **OpenFDA** - FDA drug and adverse event data
9. **Pathway Commons** - Integrated pathway databases
10. **Gene Ontology** - Gene function classification
11. **OMIM** - Genetic disorders database (requires API key)
12. **NCI Thesaurus** - Cancer terminology
13. **OpenTargets** - Disease-target associations
14. **CTG (CTD Gene)** - Gene-disease associations

### Key Features

- **100+ tools** across all databases
- **Unified endpoint** - Access all databases through single connection
- **Individual endpoints** - Connect to specific APIs separately
- **HTTP caching** - RFC 9111 compliant with 30-day TTL
- **No authentication required** (except OMIM which requires user-provided API key)
- **Production-ready** - Deployed on Railway with monitoring

## Architecture Highlights

- **Built on FastMCP** (Anthropic's MCP SDK)
- **Stateless HTTP transport** - Claude Code compatible
- **Transparent caching** via hishel
- **Error tracking** via Sentry (optional)
- **Multi-endpoint design** - Users can choose unified or per-API access

## Overlap Analysis with Existing Life Sciences Plugins

### Overlapping APIs (4)
These databases already exist as separate plugins in life-sciences:
- ChEMBL ✓
- PubMed ✓
- ClinicalTrials.gov ✓
- OpenTargets ✓

**Note:** Medical MCPs provides these through both unified AND individual endpoints, giving users flexibility to use either the comprehensive suite or specific APIs.

### Unique APIs (9)
Medical MCPs adds these databases not currently in life-sciences:
- Reactome (pathways)
- KEGG (pathways/diseases)
- UniProt (proteins)
- GWAS Catalog (genetic associations)
- OpenFDA (drug safety)
- Pathway Commons (pathway integration)
- Gene Ontology (gene functions)
- OMIM (genetic disorders)
- NCI Thesaurus (cancer)
- CTG (gene-disease)

## Files for Contribution

### 1. Plugin Configuration
**File:** `.claude-plugin/plugin.json`

Defines the MCP server endpoints and metadata. Includes:
- Unified endpoint at `/tools/unified/mcp` (all 100+ tools)
- 14 individual API endpoints (e.g., `/tools/reactome/mcp`)

### 2. Marketplace Entry
**File:** `.claude-plugin/marketplace-entry.json`

Entry to be added to the life-sciences `marketplace.json`:
```json
{
  "name": "medical-mcps",
  "source": "./medical-mcps",
  "description": "Unified access to 13+ biological and medical databases...",
  "category": "life-sciences",
  "tags": ["biology", "medicine", "research", ...]
}
```

## Installation Instructions (for end users)

### Via Life Sciences Marketplace

```bash
# 1. Add the marketplace (if not already added)
/plugin marketplace add https://github.com/anthropics/life-sciences.git

# 2. Install Medical MCPs
/plugin install medical-mcps@life-sciences

# 3. Restart Claude Code
```

### Authentication

Most databases require **no authentication**. The exception is:

- **OMIM**: Requires API key as parameter in tool calls
  - Get free API key: https://omim.org/api
  - Passed per-request: `omim_get_entry(mim_number="123456", api_key="your-key")`

## Example Use Cases

### Pathway Analysis
```
Search Reactome for pathways related to "cell cycle" and get detailed pathway diagrams
```

### Drug Discovery Research
```
Find all ChEMBL molecules targeting EGFR, then cross-reference with FDA adverse events from OpenFDA
```

### Genetic Research
```
Search GWAS Catalog for genetic variants associated with Alzheimer's disease, then look up protein functions in UniProt
```

### Literature Review
```
Search PubMed for recent papers on "CRISPR gene therapy", analyze clinical trials from ClinicalTrials.gov
```

### Disease Research
```
Look up a genetic disorder in OMIM, find associated genes, map to pathways in Reactome and KEGG
```

## Technical Specifications

- **Protocol:** MCP (Model Context Protocol)
- **Transport:** HTTP (Starlette ASGI)
- **Server Framework:** FastMCP 0.7.2
- **Python Version:** 3.12+
- **Deployment:** Railway (https://mcp.cloud.curiloo.com)
- **Cache:** SQLite via hishel (~/.cache/medical-mcps/)
- **Monitoring:** Sentry (optional)

## Endpoint Structure

All endpoints follow the pattern:
```
https://mcp.cloud.curiloo.com/tools/{api_name}/mcp
```

Special endpoints:
- **Unified:** `/tools/unified/mcp` - All 100+ tools in one connection
- **Individual:** `/tools/reactome/mcp`, `/tools/kegg/mcp`, etc.

## Tool Naming Convention

All tools are prefixed with API name:
- `reactome_get_pathway`
- `kegg_search_diseases`
- `uniprot_get_protein`
- `chembl_search_molecules`
- `pubmed_search_articles`
- etc.

## Contributing to Life Sciences Repository

### Step 1: Fork and Clone
```bash
git clone https://github.com/[YOUR-USERNAME]/life-sciences.git
cd life-sciences
```

### Step 2: Create medical-mcps Directory
```bash
mkdir -p medical-mcps/.claude-plugin
```

### Step 3: Copy Plugin Files
```bash
# Copy plugin.json to the new directory
cp /path/to/medical-mcps/.claude-plugin/plugin.json medical-mcps/.claude-plugin/
```

### Step 4: Update marketplace.json
Add the marketplace entry from `.claude-plugin/marketplace-entry.json` to the `plugins` array in `.claude-plugin/marketplace.json`.

### Step 5: Create Pull Request
```bash
git checkout -b add-medical-mcps
git add medical-mcps/
git add .claude-plugin/marketplace.json
git commit -m "Add Medical MCPs: Unified access to 13+ biological databases"
git push origin add-medical-mcps
```

Then create a PR on GitHub with description:

```markdown
# Add Medical MCPs Plugin

Adds unified access to 13+ biological and medical research databases including Reactome, KEGG, UniProt, GWAS Catalog, OpenFDA, Pathway Commons, Gene Ontology, OMIM, NCI Thesaurus, and CTG.

## Features
- 100+ tools across 14 databases
- Unified endpoint (all databases via single connection)
- Individual API endpoints (connect to specific databases)
- HTTP caching with 30-day TTL
- No authentication required (except OMIM)

## Unique Databases (not in life-sciences)
- Reactome (pathways)
- KEGG (pathways/diseases)
- UniProt (proteins)
- GWAS Catalog (genetic associations)
- OpenFDA (drug safety)
- Pathway Commons
- Gene Ontology
- OMIM (genetic disorders)
- NCI Thesaurus
- CTG

## Overlaps
This plugin includes ChEMBL, PubMed, ClinicalTrials.gov, and OpenTargets which exist as separate plugins. Medical MCPs provides access through both unified and individual endpoints for user flexibility.

## Deployment
- Production URL: https://mcp.cloud.curiloo.com
- Uptime: 99.9%
- Monitoring: Sentry
```

## Maintenance and Support

- **Repository:** https://github.com/curiloo/medical-mcps
- **Issues:** https://github.com/curiloo/medical-mcps/issues
- **Documentation:** See README.md in repository
- **Contact:** support@curiloo.com

## Version History

- **v0.1.17** (Current) - Added OpenTargets Platform integration, fixed CTG response size issues
- **v0.1.16** - Improved caching and error handling
- **v0.1.15** - Initial stable release

## License

See individual API providers for their terms of service:
- Reactome: CC0 (public domain)
- KEGG: Academic use free, commercial requires license
- UniProt: CC BY 4.0
- ChEMBL: CC BY-SA 3.0
- PubMed: Public domain
- GWAS Catalog: Public domain
- ClinicalTrials.gov: Public domain
- OpenFDA: Public domain
- etc.

## Notes for Reviewers

1. **Overlap handling:** The plugin includes some databases that exist separately, but provides unique value through unified access and additional unique databases.

2. **API key handling:** OMIM requires user API keys passed as tool parameters (stateless design, no stored credentials).

3. **Production readiness:** Server is deployed and monitored, with caching for performance.

4. **User choice:** Users can install individual existing plugins OR use Medical MCPs for comprehensive coverage - both options work.

5. **Naming:** Tools are prefixed with API names to avoid conflicts (e.g., `chembl_search_molecules` vs potential `search_molecules`).
