# Pull Request Guide: Contributing Medical MCPs to Life Sciences Marketplace

## Pre-Submission Checklist

✅ **Plugin Configuration**
- [x] Created `.claude-plugin/plugin.json` with all 14 MCP endpoints
- [x] Validated JSON syntax
- [x] Tested unified endpoint (84 tools available)
- [x] Tested individual endpoints (e.g., Reactome: 4 tools)
- [x] Production URLs confirmed working: `https://mcp.cloud.curiloo.com`

✅ **Marketplace Entry**
- [x] Created marketplace entry JSON with proper tags and category
- [x] Validated JSON syntax
- [x] Included comprehensive description

✅ **Documentation**
- [x] Prepared contribution README
- [x] Documented all 13+ databases
- [x] Listed unique vs. overlapping APIs
- [x] Included installation instructions

## Step-by-Step Contribution Process

### 1. Fork the Repository

```bash
# Navigate to: https://github.com/anthropics/life-sciences
# Click "Fork" button
# Clone your fork:
git clone https://github.com/[YOUR-USERNAME]/life-sciences.git
cd life-sciences
```

### 2. Create Feature Branch

```bash
git checkout -b add-medical-mcps
```

### 3. Create Directory Structure

```bash
mkdir -p medical-mcps/.claude-plugin
```

### 4. Copy Plugin Configuration

Copy the `plugin.json` file:

```bash
# From your medical-mcps repo:
cp /Users/pascal/Code/business/medical-mcps/.claude-plugin/plugin.json medical-mcps/.claude-plugin/
```

Or manually create `medical-mcps/.claude-plugin/plugin.json` with the following content:

```json
{
  "name": "medical-mcps",
  "version": "0.1.17",
  "description": "Comprehensive biological and medical research data integration server providing unified access to 13+ specialized databases including Reactome (pathways), KEGG (pathways/diseases), UniProt (proteins), ChEMBL (drug discovery), PubMed (literature), GWAS Catalog (genetic associations), ClinicalTrials.gov (clinical trials), OpenFDA (drug safety), Pathway Commons (pathway data), Gene Ontology (gene functions), OMIM (genetic disorders), NCI Thesaurus (cancer terminology), OpenTargets (disease-target associations), and CTG (gene-disease). Offers 100+ tools through both a unified endpoint (all databases via single connection) and individual API endpoints. Features RFC 9111 compliant HTTP caching with 30-day TTL for optimal performance.",
  "author": {
    "name": "Curiloo",
    "url": "https://curiloo.com"
  },
  "mcpServers": {
    "Medical MCPs (Unified)": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/unified/mcp"
    },
    "Reactome": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/reactome/mcp"
    },
    "KEGG": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/kegg/mcp"
    },
    "UniProt": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/uniprot/mcp"
    },
    "ChEMBL": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/chembl/mcp"
    },
    "PubMed": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/pubmed/mcp"
    },
    "GWAS Catalog": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/gwas/mcp"
    },
    "ClinicalTrials.gov": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/clinical_trials/mcp"
    },
    "OpenFDA": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/openfda/mcp"
    },
    "Pathway Commons": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/pathway_commons/mcp"
    },
    "Gene Ontology": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/gene_ontology/mcp"
    },
    "OMIM": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/omim/mcp"
    },
    "NCI Thesaurus": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/nci/mcp"
    },
    "OpenTargets": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/opentargets/mcp"
    },
    "CTG (CTD Gene)": {
      "type": "http",
      "url": "https://mcp.cloud.curiloo.com/tools/ctg/mcp"
    }
  }
}
```

### 5. Update Marketplace Configuration

Edit `.claude-plugin/marketplace.json` and add the following entry to the `plugins` array:

```json
{
  "name": "medical-mcps",
  "source": "./medical-mcps",
  "description": "Unified access to 13+ biological and medical databases (Reactome, KEGG, UniProt, ChEMBL, PubMed, GWAS, ClinicalTrials.gov, OpenFDA, Pathway Commons, Gene Ontology, OMIM, NCI Thesaurus, OpenTargets, CTG) with 100+ tools, HTTP caching, and flexible endpoint options",
  "category": "life-sciences",
  "tags": [
    "biology",
    "medicine",
    "research",
    "pathways",
    "proteins",
    "genomics",
    "drug-discovery",
    "clinical-trials",
    "literature",
    "genetics",
    "diseases",
    "biomedical",
    "pharmaceutical",
    "cancer"
  ]
}
```

**Position:** Add it alphabetically or at the end of the plugins array, before the closing `]`.

### 6. Commit Changes

```bash
git add medical-mcps/
git add .claude-plugin/marketplace.json
git commit -m "Add Medical MCPs: Unified access to 13+ biological databases

- Adds comprehensive MCP server with 84 tools across 14 databases
- Provides unified endpoint for all databases (single connection)
- Includes individual endpoints for each API
- Features RFC 9111 HTTP caching with 30-day TTL
- No authentication required (except OMIM which uses user-provided API keys)

Unique databases not in marketplace:
- Reactome (pathways)
- KEGG (pathways/diseases)
- UniProt (proteins)
- GWAS Catalog (genetic associations)
- OpenFDA (drug safety)
- Pathway Commons
- Gene Ontology
- OMIM (genetic disorders)
- NCI Thesaurus (cancer)
- CTG (gene-disease)

Also includes ChEMBL, PubMed, ClinicalTrials.gov, and OpenTargets
through both unified and individual endpoints for user flexibility."
```

### 7. Push to Your Fork

```bash
git push origin add-medical-mcps
```

### 8. Create Pull Request

1. Navigate to your fork on GitHub
2. Click "Compare & pull request" button
3. Fill in the PR template:

---

**PR Title:**
```
Add Medical MCPs: Unified access to 13+ biological databases
```

**PR Description:**
```markdown
## Overview

Adds Medical MCPs plugin providing unified access to 13+ biological and medical research databases through a single MCP server with 84 tools.

## Features

- **Unified endpoint**: Access all databases through single connection (`/tools/unified/mcp`)
- **Individual endpoints**: Connect to specific APIs separately (e.g., `/tools/reactome/mcp`)
- **100+ tools** across 14 databases
- **HTTP caching**: RFC 9111 compliant with 30-day TTL for optimal performance
- **No authentication required** (except OMIM which accepts user API keys as parameters)
- **Production-ready**: Deployed on Railway with Sentry monitoring

## Databases Included

### Unique (Not Currently in Marketplace)
1. ✨ **Reactome** - Pathway analysis and biological networks
2. ✨ **KEGG** - Pathway and disease databases
3. ✨ **UniProt** - Protein sequences and functional information
4. ✨ **GWAS Catalog** - Genetic associations with diseases
5. ✨ **OpenFDA** - FDA drug and adverse event data
6. ✨ **Pathway Commons** - Integrated pathway databases
7. ✨ **Gene Ontology** - Gene function classification
8. ✨ **OMIM** - Genetic disorders database
9. ✨ **NCI Thesaurus** - Cancer terminology
10. ✨ **CTG (CTD Gene)** - Gene-disease associations

### Also Included (Overlap with Existing Plugins)
- ChEMBL - Drug discovery and bioactive molecules
- PubMed - Biomedical literature search
- ClinicalTrials.gov - Clinical trial data
- OpenTargets - Disease-target associations

**Note on overlap:** While some databases exist as individual plugins, Medical MCPs provides unique value by offering:
1. Unified access to all databases through a single connection
2. Additional 10 databases not available in the marketplace
3. Consistent API interface across all databases
4. Integrated caching for better performance

## Technical Details

- **Protocol**: MCP (Model Context Protocol)
- **Transport**: HTTP (Starlette ASGI)
- **Server Framework**: FastMCP 0.7.2
- **Deployment**: https://mcp.cloud.curiloo.com
- **Endpoints tested**: ✅ Unified (84 tools), ✅ Individual APIs
- **Repository**: https://github.com/curiloo/medical-mcps

## Example Use Cases

1. **Pathway Analysis**: Search Reactome pathways → Map to KEGG diseases → Find proteins in UniProt
2. **Drug Discovery**: Search ChEMBL molecules → Check FDA adverse events → Review clinical trials
3. **Genetic Research**: GWAS variants → Gene functions (GO) → Genetic disorders (OMIM)
4. **Literature Review**: PubMed search → ClinicalTrials.gov data → Target validation (OpenTargets)

## Testing

All endpoints have been tested and validated:
- ✅ JSON configuration validated
- ✅ Unified endpoint: 84 tools available
- ✅ Individual endpoints tested (e.g., Reactome: 4 tools)
- ✅ Production URLs accessible: https://mcp.cloud.curiloo.com

## Licensing

Individual APIs are licensed by their respective providers. See provider terms of service:
- Reactome: CC0 (public domain)
- KEGG: Academic use free, commercial license required
- UniProt: CC BY 4.0
- ChEMBL: CC BY-SA 3.0
- PubMed, GWAS, ClinicalTrials, OpenFDA: Public domain

## Maintenance

- **Repository**: https://github.com/curiloo/medical-mcps
- **Issues**: Report at https://github.com/curiloo/medical-mcps/issues
- **Contact**: support@curiloo.com
- **Version**: 0.1.17 (actively maintained)
```

---

### 9. Address Review Feedback

Be prepared to discuss:

1. **Overlap with existing plugins**: Explain unified access value proposition
2. **Authentication**: Confirm OMIM uses user-provided API keys (stateless)
3. **Maintenance**: Commit to maintaining the plugin
4. **Testing**: Provide evidence of testing (endpoint validation)

## Post-Merge Actions

Once the PR is merged:

1. **Update your repository README** with marketplace installation instructions
2. **Monitor issues** from users installing via marketplace
3. **Keep plugin.json version** in sync with your server releases
4. **Submit marketplace updates** when adding new databases

## Verification Commands

To verify the plugin works after installation:

```bash
# In Claude Code
/plugin marketplace add https://github.com/anthropics/life-sciences.git
/plugin install medical-mcps@life-sciences

# Restart Claude Code

# Test commands
"List all available Medical MCPs tools"
"Search Reactome for pathways related to apoptosis"
"Find UniProt proteins associated with TP53"
```

## Expected Timeline

- **PR Review**: 1-2 weeks
- **Feedback/Changes**: 2-5 days per round
- **Merge**: 1-3 weeks total

## Rollback Plan

If issues arise post-merge:

1. Plugin can be disabled by users via `/plugin uninstall medical-mcps@life-sciences`
2. Critical issues: Submit hotfix PR to update plugin.json
3. Server issues: Update deployment and maintain backward compatibility

## Contact for PR

**GitHub**: [@[YOUR_GITHUB_USERNAME]]
**Email**: [your-email]
**Project**: https://github.com/curiloo/medical-mcps
