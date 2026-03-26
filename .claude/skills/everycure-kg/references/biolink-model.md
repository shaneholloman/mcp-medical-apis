# Biolink Model Reference for Knowledge Graph Queries

## What is Biolink Model?

The [Biolink Model](https://biolink.github.io/biolink-model/) is an open-source, high-level data model designed to standardize types and relationships in biological knowledge graphs. It provides a universal schema for representing biological knowledge across various databases and formats, particularly for translational science and drug discovery applications.

### Why It Exists

The biomedical research community faces critical challenges:

- **Data heterogeneity**: Proliferation of ad-hoc data formats across databases
- **Integration complexity**: Difficulty reconciling data sources for downstream analysis
- **Interoperability gaps**: Lack of universally accepted standards for biomedical knowledge graphs
- **FAIR compliance**: Poor adherence to Findability, Accessibility, Interoperability, and Reusability principles

Biolink Model solves these problems by providing a consistent framework that enables easier integration of biomedical knowledge graphs, bringing together knowledge from multiple sources to support translational science goals like drug repurposing.

**Key Applications**: The [NCATS Biomedical Data Translator Consortium](https://pmc.ncbi.nlm.nih.gov/articles/PMC9372416/), Monarch Initiative, and numerous drug repurposing projects.

---

## Core Concepts

### Node Types (Classes)

Node types represent **entities** in the biological domain - the "things" in a knowledge graph. Examples include genes, diseases, drugs, and proteins. Classes are organized in a hierarchy using inheritance.

**Example hierarchy**:
```
Entity
  └─ NamedThing
      └─ BiologicalEntity
          └─ DiseaseOrPhenotypicFeature
              └─ Disease
```

### Relationship Types (Predicates)

Predicates represent **connections** between nodes - the "edges" that describe how entities interact or relate. Like classes, predicates form a hierarchy.

**Example hierarchy**:
```
related_to
  └─ associated_with
      └─ correlated_with
  └─ affects
      └─ regulates
          ├─ positively_regulates
          └─ negatively_regulates
```

The hierarchical structure is powerful: querying for `biolink:related_to` will return results for all more specific predicates like `biolink:treats` or `biolink:regulates`.

### The biolink: Prefix Convention

The `biolink:` prefix denotes standardized terms from the Biolink Model namespace. It ensures consistent terminology across different knowledge graphs and databases.

**Examples**:
- `biolink:Drug`
- `biolink:treats`
- `biolink:Gene`
- `biolink:interacts_with`

In Cypher queries, this often appears as a node label or relationship type property:
```cypher
MATCH (d:Drug)-[r:treats]->(disease:Disease)
WHERE r.predicate = 'biolink:treats'
```

---

## Common Node Types for Drug Repurposing

### 1. Drug

**Definition**: A substance intended for use in the diagnosis, cure, mitigation, treatment, or prevention of disease.

**Hierarchy**: Entity → NamedThing → ChemicalEntity → ChemicalMixture → MolecularMixture → Drug

**Identifier Prefixes**: RXCUI, CHEBI, DRUGBANK, CHEMBL.COMPOUND, UMLS, MESH

**Key Properties**:
- `routes_of_delivery`
- `highest_FDA_approval_status`
- `drug_regulatory_status_world_wide`
- `available_from`
- `has_chemical_role`

**Common Patterns**:
```cypher
// Find drugs treating a disease
(Drug)-[:treats]->(Disease)

// Find drug-gene interactions
(Drug)-[:affects]->(Gene)

// Find drug mechanisms via proteins
(Drug)-[:interacts_with]->(Protein)
```

---

### 2. Disease

**Definition**: A disorder of structure or function, especially one that produces specific signs, phenotypes or symptoms, affecting a specific location, and not simply a direct result of physical injury.

**Hierarchy**: Entity → NamedThing → BiologicalEntity → DiseaseOrPhenotypicFeature → Disease

**Identifier Prefixes**: MONDO, DOID, OMIM, EFO, UMLS, MESH

**Common Patterns**:
```cypher
// Genes associated with disease
(Gene)-[:associated_with|causes|contributes_to]->(Disease)

// Variants causing disease
(SequenceVariant)-[:causes]->(Disease)

// Phenotypes related to disease
(PhenotypicFeature)-[:associated_with]->(Disease)
```

---

### 3. Gene

**Definition**: A region (or regions) encoding a functional RNA or protein product, including regulatory elements.

**Hierarchy**: Entity → NamedThing → BiologicalEntity → BiologicalEntity → Gene (part of GeneOrGeneProduct)

**Identifier Prefixes**: HGNC, NCBIGene, ENSEMBL, MGI, RGD

**Common Patterns**:
```cypher
// Gene-disease associations
(Gene)-[:associated_with|causes|contributes_to]->(Disease)

// Gene regulation networks
(Gene)-[:regulates|positively_regulates|negatively_regulates]->(Gene)

// Gene-pathway membership
(Gene)-[:participates_in]->(Pathway)

// Gene products
(Gene)-[:has_gene_product]->(Protein)
```

---

### 4. Protein

**Definition**: A gene product composed of amino acid sequences produced by ribosome-mediated translation of mRNA.

**Hierarchy**: Entity → NamedThing → BiologicalEntity → Polypeptide → Protein → ProteinIsoform

**Mixins**: GeneProductMixin, ChemicalEntityOrGeneOrGeneProduct, ChemicalEntityOrProteinOrPolypeptide

**Identifier Prefixes**: UniProtKB (preferred), PR, ENSEMBL

**Common Patterns**:
```cypher
// Drug-protein interactions (targets)
(Drug)-[:interacts_with]->(Protein)

// Protein-protein interactions
(Protein)-[:interacts_with]->(Protein)

// Proteins in pathways
(Protein)-[:participates_in]->(Pathway)

// Gene-protein relationship
(Gene)-[:has_gene_product]->(Protein)
```

---

### 5. Pathway

**Definition**: A biological process involving multiple molecular activities and interactions.

**Hierarchy**: Entity → NamedThing → BiologicalEntity → BiologicalProcessOrActivity → BiologicalProcess → Pathway

**Identifier Prefixes**: REACT, KEGG, GO, WikiPathways

**Common Patterns**:
```cypher
// Genes in pathways
(Gene)-[:participates_in]->(Pathway)

// Proteins in pathways
(Protein)-[:participates_in]->(Pathway)

// Disease-pathway associations
(Disease)-[:associated_with]->(Pathway)

// Pathway hierarchy
(Pathway)-[:part_of]->(Pathway)
```

---

### 6. ChemicalEntity / SmallMolecule

**Definition**: Physical entities pertaining to chemistry (atoms, molecules, ions, molecular entities).

**Hierarchy**: Entity → NamedThing → ChemicalEntity

**Note**: ChemicalSubstance is deprecated; SmallMolecule is the recommended replacement for small chemical compounds.

**Identifier Prefixes**: CHEBI, CHEMBL.COMPOUND, PUBCHEM.COMPOUND, HMDB, DrugBank

**Common Patterns**:
```cypher
// Chemical-protein binding
(ChemicalEntity)-[:interacts_with]->(Protein)

// Chemical effects on genes
(ChemicalEntity)-[:affects]->(Gene)

// Chemical similarity
(ChemicalEntity)-[:similar_to]->(ChemicalEntity)
```

---

### 7. PhenotypicFeature

**Definition**: Observable characteristics resulting from genotype-environment interaction.

**Hierarchy**: Entity → NamedThing → BiologicalEntity → DiseaseOrPhenotypicFeature → PhenotypicFeature

**Identifier Prefixes**: HP (Human Phenotype Ontology), MP (Mammalian Phenotype), UMLS

**Note**: This class reconciles concepts like "side effects," "symptoms," "traits," and "phenotypes."

**Common Patterns**:
```cypher
// Phenotype-disease relationships
(PhenotypicFeature)-[:associated_with]->(Disease)

// Gene-phenotype associations
(Gene)-[:associated_with]->(PhenotypicFeature)

// Variant-phenotype relationships
(SequenceVariant)-[:contributes_to]->(PhenotypicFeature)
```

---

### 8. SequenceVariant

**Definition**: Genomic alterations including SNPs, indels, and structural variants.

**Hierarchy**: Entity → NamedThing → BiologicalEntity → GenomicEntity → SequenceVariant

**Identifier Prefixes**: DBSNP, ClinVar, CAID

**Common Patterns**:
```cypher
// Variants causing disease
(SequenceVariant)-[:causes|contributes_to]->(Disease)

// Variant-gene associations
(SequenceVariant)-[:associated_with]->(Gene)

// Variant effects on protein function
(SequenceVariant)-[:affects]->(Protein)
```

---

### Other Important Node Types

**9. AnatomicalEntity**: Body parts, organs, tissues, cells
- Prefixes: UBERON, CL, FMA

**10. ClinicalFinding**: Observations made during clinical examination
- Prefixes: SNOMEDCT, UMLS

**11. Procedure**: Clinical procedures and interventions
- Prefixes: CPT, SNOMEDCT

**12. OrganismTaxon**: Taxonomic classification
- Prefixes: NCBITaxon

**13. MolecularActivity**: Specific molecular functions
- Prefixes: GO

**14. BiologicalProcess**: Biological processes and functions
- Prefixes: GO

**15. CellularComponent**: Cellular locations and structures
- Prefixes: GO

---

## Common Relationship Types (Predicates)

### 1. treats

**Definition**: An intervention (substance, procedure, or activity) ameliorates, stabilizes, or cures a medical condition, or delays/prevents/reduces the risk of it manifesting.

**Domain**: ChemicalOrDrugOrTreatment (Drug, ChemicalEntity, Procedure, Treatment)
**Range**: DiseaseOrPhenotypicFeature (Disease, PhenotypicFeature)

**Evidence Standard**: Should only be asserted with strong evidence:
- FDA approval for the condition
- Successful Phase 3/4 clinical trials
- Established medical community acceptance (including recognized off-label uses)

**Examples**:
```cypher
(Drug {name: "Aspirin"})-[:treats]->(Disease {name: "Cardiovascular Disease"})
(Procedure {name: "Surgery"})-[:treats]->(Disease {name: "Herniated Disc"})
```

---

### 2. associated_with

**Definition**: A general statistical relationship between entities, without implying causation.

**Domain**: Entity (any node)
**Range**: Entity (any node)

**Use Case**: When there's evidence of a relationship but the mechanism or directionality is unclear.

**Examples**:
```cypher
(Gene)-[:associated_with]->(Disease)
(PhenotypicFeature)-[:associated_with]->(Disease)
```

---

### 3. correlated_with

**Definition**: A statistical correlation exists between two concepts, as demonstrated using correlation analysis methods.

**Parent**: associated_with
**Symmetric**: Yes (bidirectional relationship)

**Note**: More specific than `associated_with`, indicating statistical correlation has been explicitly demonstrated.

**Examples**:
```cypher
(Gene)-[:correlated_with]->(PhenotypicFeature)
(Biomarker)-[:correlated_with]->(Disease)
```

---

### 4. causes

**Definition**: One entity directly generates or brings about the occurrence of another.

**Parent**: contributes_to
**Note**: A stronger form of contribution implying direct causation.

**Examples**:
```cypher
(SequenceVariant)-[:causes]->(Disease)
(Exposure)-[:causes]->(Disease)
```

---

### 5. contributes_to

**Definition**: One entity makes a positive or negative contribution to another's state or quality.

**Parent**: affects
**Children**: causes

**Examples**:
```cypher
(Gene)-[:contributes_to]->(Disease)
(SequenceVariant)-[:contributes_to]->(PhenotypicFeature)
```

---

### 6. affects

**Definition**: One entity impacts another's state, quality, or activity.

**Parent**: related_to
**Children**: regulates, contributes_to

**Note**: Very general predicate; more specific predicates are preferred when known.

**Examples**:
```cypher
(Drug)-[:affects]->(Gene)
(ChemicalEntity)-[:affects]->(BiologicalProcess)
```

---

### 7. regulates

**Definition**: A more specific form of `affects` that implies the effect results from a biologically evolved control mechanism.

**Parent**: affects
**Children**: positively_regulates, negatively_regulates

**Domain & Range**: PhysicalEssenceOrOccurrent (genes, proteins, biological processes)

**Note**: Use for gene-gene relationships (which almost always involve regulation). For exogenous/environmental chemical-gene interactions, use `affects` instead.

**Examples**:
```cypher
(Gene {name: "TP53"})-[:regulates]->(Gene {name: "MDM2"})
(Protein)-[:regulates]->(BiologicalProcess)
```

**Specific Variants**:
```cypher
(Gene)-[:positively_regulates]->(Gene)  // Upregulation
(Gene)-[:negatively_regulates]->(Gene)  // Downregulation
```

---

### 8. interacts_with

**Definition**: A grouping term for interaction predicates describing direct or indirect entity interactions.

**Children**: genetically_interacts_with, physically_interacts_with, molecularly_interacts_with

**Examples**:
```cypher
// Drug-protein binding
(Drug)-[:interacts_with]->(Protein)

// Protein-protein interactions
(Protein)-[:interacts_with]->(Protein)

// Gene-gene interactions
(Gene)-[:genetically_interacts_with]->(Gene)
```

---

### 9. participates_in

**Definition**: An entity is involved in or part of a process, pathway, or activity.

**Examples**:
```cypher
(Gene)-[:participates_in]->(Pathway)
(Protein)-[:participates_in]->(BiologicalProcess)
```

---

### 10. has_gene_product

**Definition**: Links a gene to its product (RNA or protein).

**Domain**: Gene
**Range**: GeneProduct (Protein, RNA)

**Examples**:
```cypher
(Gene {name: "BRCA1"})-[:has_gene_product]->(Protein {name: "BRCA1 protein"})
```

---

### Other Important Predicates

**11. similar_to**: Entities share common features or properties
**12. part_of**: Hierarchical containment (e.g., pathway part_of pathway)
**13. located_in**: Anatomical or cellular location
**14. expressed_in**: Gene/protein expression location
**15. biomarker_for**: Entity serves as indicator for condition
**16. predisposes**: Increases susceptibility
**17. prevents**: Reduces likelihood of occurrence
**18. ameliorates**: Improves condition symptoms
**19. exacerbates**: Worsens condition
**20. contraindicated_for**: Should not be used for condition

---

## Valid Pattern Examples

Understanding which node types connect via which predicates is crucial for writing correct Cypher queries.

### Drug Repurposing Core Patterns

```cypher
// 1. Direct drug-disease relationships
(Drug)-[:treats]->(Disease)

// 2. Drug mechanisms via protein targets
(Drug)-[:interacts_with]->(Protein)-[:participates_in]->(Pathway)
(Pathway)-[:associated_with]->(Disease)

// 3. Drug effects on genes
(Drug)-[:affects|regulates]->(Gene)-[:associated_with]->(Disease)

// 4. Genetic basis of disease
(Gene)-[:causes|contributes_to|associated_with]->(Disease)

// 5. Variant-disease causation
(SequenceVariant)-[:causes|contributes_to]->(Disease)

// 6. Phenotype connections
(Disease)-[:associated_with]->(PhenotypicFeature)
(Gene)-[:associated_with]->(PhenotypicFeature)

// 7. Gene-protein-pathway flow
(Gene)-[:has_gene_product]->(Protein)
(Protein)-[:participates_in]->(Pathway)
(Pathway)-[:associated_with]->(Disease)

// 8. Gene regulation networks
(Gene)-[:regulates|positively_regulates|negatively_regulates]->(Gene)

// 9. Chemical similarity for drug repurposing
(Drug)-[:similar_to]->(ChemicalEntity)
(ChemicalEntity)-[:treats]->(Disease)

// 10. Multi-hop drug repurposing hypothesis
(Drug)-[:interacts_with]->(Protein)
(Protein)-[:participates_in]->(Pathway)
(Gene)-[:participates_in]->(Pathway)
(Gene)-[:associated_with]->(Disease)
```

### Query Strategy Tips

1. **Use predicate hierarchy**: Query for `related_to` to capture all relationship types, or be specific with `treats`, `causes`, etc.

2. **Check directionality**: Some predicates are symmetric (`correlated_with`, `similar_to`), others are directional (`causes`, `treats`).

3. **Leverage class hierarchy**: Querying for `BiologicalEntity` will match `Gene`, `Protein`, `Disease`, etc.

4. **Filter by evidence**: Use edge properties to filter by evidence source, publication count, or confidence scores.

5. **Multi-hop reasoning**: Drug repurposing often requires 2-5 hop paths:
   ```cypher
   MATCH path = (d:Drug)-[*2..5]-(disease:Disease)
   WHERE d.name = "Metformin"
     AND disease.id = "MONDO:0005148"  // Type 2 Diabetes
   RETURN path
   ```

6. **Common patterns**:
   - Gene-Disease: `associated_with`, `causes`, `contributes_to`
   - Drug-Protein: `interacts_with`
   - Drug-Disease: `treats`, `ameliorates`, `contraindicated_for`
   - Gene-Gene: `regulates`, `genetically_interacts_with`
   - Protein-Protein: `interacts_with`, `physically_interacts_with`

---

## Summary for AI Agents

When writing Cypher queries against a Biolink-based knowledge graph:

1. **Always use biolink: prefix** for standardization
2. **Understand hierarchies**: Both classes and predicates are hierarchical
3. **Match domains and ranges**: Not all predicates work with all node types
4. **Leverage common patterns**: Drug repurposing has well-established multi-hop patterns
5. **Check for evidence**: Use edge properties to filter by quality/source
6. **Think in biological flows**: Gene → Protein → Pathway → Disease
7. **Consider directionality**: Some relationships are asymmetric (causes, treats)
8. **Use specific predicates**: Prefer `treats` over `associated_with` when evidence supports it

**Most Important for Drug Repurposing**:
- Node types: Drug, Disease, Gene, Protein, Pathway, PhenotypicFeature
- Predicates: treats, interacts_with, regulates, participates_in, associated_with, causes

---

## References

- [Biolink Model Documentation](https://biolink.github.io/biolink-model/)
- [Biolink Model Paper (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9372416/)
- [Biolink Model GitHub Repository](https://github.com/biolink/biolink-model)
- [DrugMechDB: Curated Drug Mechanisms](https://www.nature.com/articles/s41597-023-02534-z)
- [BioCypher Framework](https://hal.science/hal-04135813/document)
- [Drug Class Documentation](https://biolink.github.io/biolink-model/Drug/)
- [Disease Class Documentation](https://biolink.github.io/biolink-model/Disease/)
- [Protein Class Documentation](https://biolink.github.io/biolink-model/Protein/)
- [Treats Predicate Documentation](https://biolink.github.io/biolink-model/treats/)
- [Regulates Predicate Documentation](https://biolink.github.io/biolink-model/regulates/)

---

*Document Version: 1.0 | Created: 2026-01-28*
