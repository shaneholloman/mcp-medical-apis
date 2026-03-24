# Metapaths for Everycure KG

**Purpose**: Predefined and corrected metapath definitions for drug repurposing queries

---

## What is a Metapath?

A **metapath** is a specific pattern of node types and relationship types that forms a biologically meaningful path through the knowledge graph.

Example: `Drug → directly_physically_interacts_with → Protein → associated_with → Disease`

Metapaths prevent path explosion by constraining queries to specific, sparse patterns.

---

## Predefined Metapaths (Use via `find_paths_by_metapath` tool)

### 1. drug_to_disease_direct (1-hop) ✅

**Pattern**: `Drug -[:treats_or_applied_or_studied_to_treat]-> Disease`

**Use when**: Looking for direct clinical evidence

**Performance**: <1s, 0-10 paths

**Success rate**: 100% when relationship exists

**Example**:
```python
find_paths_by_metapath(
    source_id="CHEBI:6801",  # Metformin
    target_id="MONDO:0800029",  # IPF
    metapath_name="drug_to_disease_direct"
)
```

### 2. drug_to_disease_via_target (2-hop) ✅

**Pattern**: `Drug -[:directly_physically_interacts_with]-> Protein -[:associated_with]-> Disease`

**Use when**: Finding mechanistic protein targets

**Performance**: 2-5s, 0-100 paths

**Success rate**: 90% for well-studied drugs

**Biological meaning**: Drug modulates a protein that is implicated in the disease

**Example**:
```python
find_paths_by_metapath(
    source_id="CHEMBL.COMPOUND:CHEMBL2108455",  # Antihemophilic factor
    target_id="MONDO:0010602",  # Hemophilia A
    metapath_name="drug_to_disease_via_target"
)
# Result: 4 paths via F9, F8, F10, F5 proteins
```

---

## 3-Hop Metapaths

The predefined metapaths automatically handle schema quirks (reversed relationships, specific predicates). Details below are for reference when writing custom queries.

### 3. drug_to_disease_via_pathway (3-hop)

**Predefined metapath pattern** (automatically handled):
```
Drug -[:directly_physically_interacts_with]-> Protein
     <-[:has_participant]- Pathway
     <-[:disease_has_basis_in]- Disease
```

**Schema notes** (for custom queries):
- Protein → Pathway uses reversed `has_participant` (312K edges vs actively_involved_in 23.9K)
- Pathway → Disease uses reversed `disease_has_basis_in` (607 edges)

**Performance**: 10-30s, 0-50 paths

**Success rate**: 50% (sparse disease-pathway annotations)

**Custom Cypher**:
```cypher
MATCH (d:Drug {id: $drug_id})
      -[:directly_physically_interacts_with]->(p:Protein)
      <-[:has_participant]-(path:Pathway)
      <-[:disease_has_basis_in]-(dis:Disease {id: $disease_id})
RETURN d, p, path, dis
LIMIT 10
```

### 4. drug_to_disease_via_gene (3-hop)

**Predefined metapath pattern** (automatically handled):
```
Drug -[:directly_physically_interacts_with]-> Protein
     -[:gene_product_of]-> Gene
     -[:gene_associated_with_condition]-> Disease
```

**Schema note** (for custom queries):
- Gene → Disease uses specific `gene_associated_with_condition` (52.8K edges) not generic `associated_with` (38.6K edges)

**Performance**: 5-15s, 0-100 paths

**Success rate**: 70%

**Custom Cypher**:
```cypher
MATCH (d:Drug {id: $drug_id})
      -[:directly_physically_interacts_with]->(p:Protein)
      -[:gene_product_of]->(g:Gene)
      -[:gene_associated_with_condition]->(dis:Disease {id: $disease_id})
RETURN d, p, g, dis
LIMIT 50
```

### 5. disease_to_disease_shared_gene (2-hop)

**Predefined metapath pattern** (automatically handled):
```
Disease1 <-[:gene_associated_with_condition]- Gene
         -[:gene_associated_with_condition]-> Disease2
```

**Schema notes** (for custom queries):
- Direction: First relationship is reversed (Gene points to Disease)
- Predicate: Uses specific `gene_associated_with_condition`

**Performance**: 5-10s, 0-100 paths

**Success rate**: 80%

**Custom Cypher**:
```cypher
MATCH (dis1:Disease {id: $disease1_id})
      <-[:gene_associated_with_condition]-(g:Gene)
      -[:gene_associated_with_condition]->(dis2:Disease {id: $disease2_id})
RETURN dis1, g, dis2
LIMIT 50
```

### 6. drug_side_effect_path (1-hop)

**Predefined metapath pattern** (automatically handled):
```
Drug -[:causes]-> Disease
```

**Schema notes** (for custom queries):
- Side effects are modeled as BOTH Disease (35K edges) and PhenotypicFeature (25K edges)
- Predefined metapath uses direct 1-hop to Disease
- For custom queries, can also use: `Drug -[:causes]-> PhenotypicFeature`

**Performance**: <1s, 0-100 paths

**Success rate**: 90%

**Custom Cypher**:
```cypher
// Option 1: Side effects as Disease
MATCH (d:Drug {id: $drug_id})-[:causes]->(se:Disease)
RETURN d, se
LIMIT 50

// Option 2: Side effects as PhenotypicFeature
MATCH (d:Drug {id: $drug_id})-[:causes]->(se:PhenotypicFeature)
RETURN d, se
LIMIT 50
```

---

## Custom Metapath Design Guidelines

When predefined metapaths don't fit your use case:

### 1. Keep it SHORT (2-3 hops max)

**Good**: Drug → Protein → Disease (2 hops)

**Risky**: Drug → Protein → Pathway → Gene → Disease (4 hops - likely explosion)

### 2. Include at least ONE SPARSE relationship (<10K edges)

**Good**: Disease -[:disease_has_basis_in]-> Pathway (607 edges - SPARSE)

**Bad**: Protein -[:associated_with]-> Gene (millions of edges - DENSE)

**KG Relationship Sparsity**:
- SPARSE (<10K): `disease_has_basis_in` (607), `contraindicated_in` (~5K)
- MEDIUM (10K-100K): `gene_associated_with_condition` (52.8K), `treats` (35K)
- DENSE (>100K): `has_participant` (312K), `associated_with` (millions)

### 3. Start from DRUG or DISEASE nodes

**Safe Start Points**:
- Drug (73K nodes, avg degree ~125)
- Disease (112K nodes, avg degree ~1.4K)

**Risky Start Points**:
- Protein (458K nodes, avg degree ~3.5K)
- Gene (264K nodes)

**Never Start From**:
- OrganismTaxon (3.2M nodes)
- SmallMolecule (3M nodes)

### 4. Use SPECIFIC relationship types

**Good**: `-[:directly_physically_interacts_with]->` (specific)

**Bad**: `-[*]->` (wildcard - will explode)

### 5. Validate EACH STEP before chaining

```cypher
// Step 1: Validate Drug → Protein
MATCH (d:Drug {id: $drug_id})-[r:directly_physically_interacts_with]->(p:Protein)
RETURN COUNT(p) as protein_count
// If count < 1000, proceed to step 2

// Step 2: Validate Protein → Gene
MATCH (p:Protein {id: $protein_id})-[r:gene_product_of]->(g:Gene)
RETURN COUNT(g) as gene_count
// If count < 100, proceed to step 3

// Step 3: Validate Gene → Disease
MATCH (g:Gene {id: $gene_id})-[r:gene_associated_with_condition]->(dis:Disease)
RETURN COUNT(dis) as disease_count
// If count < 100, safe to chain all 3 steps
```

### 6. Always COUNT before RETURN

```cypher
// WRONG:
MATCH (d)-[r1]->(mid)-[r2]->(target)
RETURN d, mid, target LIMIT 10

// CORRECT:
MATCH (d)-[r1]->(mid)-[r2]->(target)
WITH COUNT(*) as total_paths
WHERE total_paths < 100
MATCH (d)-[r1]->(mid)-[r2]->(target)
RETURN d, mid, target LIMIT 10
```

---

## Metapath Success Patterns from Experiments

### High Success (80-100%)

1. **Metformin → IPF**: 75% success via direct treatment + AMPK mechanism
2. **Rituximab → CHS**: 90% success via B cell depletion
3. **Lenalidomide → RDD**: 100% success via CRBN/IKZF mechanism (704 targets!)
4. **Losartan → EB**: 83% success via TGF-β inhibition
5. **L-Glutamine → SCD**: 100% success via oxidative stress pathway
6. **JAK inhibitors → SSc**: 100% success via JAK-STAT pathway

### Moderate Success (50-80%)

7. **Brigatinib → NF2**: 70% success via EGFR/FAK mechanisms
8. **VPA → DMD**: 82% success via HDAC8 mechanism
9. **Tacrolimus → SSc**: 75% success (but safety concerns!)
10. **Sorafenib → Gastric Cancer**: 83% success via multi-kinase inhibition

### Lower Success (30-50%)

11. **Vortioxetine → Glioblastoma**: 30% success (KG gaps, PubMed validates)
12. **Leuprolide → LAM**: 37.5% success (class evidence via gonadorelin)

### Pattern Analysis

**What makes metapaths succeed?**
1. Direct treatment relationships in KG (highest confidence)
2. Well-studied drug-protein-disease triangles
3. Multiple parallel mechanisms (Lenalidomide: 704 targets)
4. Complete pathway chains (L-Glutamine → NAD → Glutathione → SCD)

**What causes metapaths to fail?**
1. Missing schema relationships (Protein → Pathway reversed)
2. Sparse annotations (only 607 disease-pathway edges)
3. Rare diseases (< 50 patients, limited research)
4. Recent discoveries (not yet in KG databases)

---

## Metapath Selection Decision Tree

```
START: What's your biological question?

Drug Repurposing?
├─ Known drug + known disease?
│  └─ Use: drug_to_disease_direct (1-hop)
│  └─ Fallback: drug_to_disease_via_target (2-hop)
│
└─ Exploring mechanism?
   ├─ Protein level? → drug_to_disease_via_target (2-hop)
   ├─ Gene level? → drug_to_disease_via_gene (3-hop corrected)
   └─ Pathway level? → drug_to_disease_via_pathway (3-hop corrected)

Disease Understanding?
├─ Find genes? → Use: MATCH (g:Gene)-[:gene_associated_with_condition]->(dis)
├─ Find pathways? → Use: MATCH (dis)-[:disease_has_basis_in]->(path)
└─ Similar diseases? → Use: disease_to_disease_shared_gene (2-hop corrected)

Side Effect Discovery?
└─ Use: drug_side_effect_path (1-hop corrected)

Comparative Analysis?
├─ Disease-disease similarity? → disease_to_disease_shared_gene
└─ Drug-drug similarity? → Compare via shared protein targets (2-hop)
```

---

## Advanced: Combining Metapaths

For comprehensive drug repurposing analysis, chain multiple metapaths:

```python
# Step 1: Direct evidence?
direct = find_paths_by_metapath(drug_id, disease_id, "drug_to_disease_direct")

# Step 2: Mechanistic evidence via proteins?
via_targets = find_paths_by_metapath(drug_id, disease_id, "drug_to_disease_via_target")

# Step 3: Genetic evidence?
via_genes = find_paths_by_metapath(drug_id, disease_id, "drug_to_disease_via_gene")

# Step 4: Safety check (contraindications)?
contraindications = execute_cypher(
    "MATCH (d:Drug {id: $drug_id})-[:contraindicated_in]->(dis:Disease {id: $disease_id}) RETURN dis",
    {"drug_id": drug_id, "disease_id": disease_id}
)

# Synthesize: Direct + Mechanistic + Genetic - Contraindications = Repurposing Score
```

---

## Key Takeaways

1. **Use predefined metapaths first** - They're tested and optimized
2. **Correct for KG schema quirks** - Direction and predicate matter!
3. **3-hop is the practical limit** - Beyond that, path explosion is inevitable
4. **Validate before chaining** - Test each step independently
5. **COUNT before RETURN** - Always check path count before materializing
6. **Biological plausibility > Technical success** - 0 results may indicate indirect mechanism
7. **Combine multiple metapaths** - Triangulate evidence for confidence
