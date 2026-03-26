# Everycure KG Schema Quirks

**Purpose**: Document where the Everycure KG deviates from Biolink Model expectations

---

## Critical Insight

**The Biolink Model documentation ≠ Everycure KG reality**

Always validate actual relationship types and directions before designing queries.

---

## Relationship Direction Mismatches

### 1. Protein ↔ Pathway: REVERSED

**Biolink Model Expectation**:
```
Protein -[:actively_involved_in]-> Pathway
```

**Everycure KG Reality**:
```
Pathway -[:has_participant]-> Protein (312K edges - DOMINANT)
Protein -[:actively_involved_in]-> Pathway (23.9K edges - exists but 13x fewer)
```

**Impact**: Using forward direction misses 93% of protein-pathway connections

**Solution**: Use reverse direction or bidirectional queries
```cypher
// BEST:
MATCH (p:Protein)<-[:has_participant]-(path:Pathway)

// ACCEPTABLE:
MATCH (p:Protein)-[:actively_involved_in]->(path:Pathway)

// COMPREHENSIVE:
MATCH (p:Protein)-[:actively_involved_in|has_participant]-(path:Pathway)
```

### 2. Pathway ↔ Disease: REVERSED + SPARSE

**Biolink Model Expectation**:
```
Pathway -[:associated_with]-> Disease
```

**Everycure KG Reality**:
```
Disease -[:disease_has_basis_in]-> Pathway (607 edges - ONLY option)
Pathway -[:associated_with]-> Disease (2 edges - essentially nonexistent)
```

**Impact**: Forward direction finds almost nothing

**Solution**: Always use reverse direction
```cypher
// CORRECT:
MATCH (dis:Disease)-[:disease_has_basis_in]->(path:Pathway)

// WRONG (only 2 edges!):
MATCH (path:Pathway)-[:associated_with]->(dis:Disease)
```

---

## Relationship Type Preference

### 3. Gene → Disease: Use Specific Predicate

**Generic Predicate**:
```
Gene -[:associated_with]-> Disease (38.6K edges)
```

**Specific Predicate** (PREFERRED):
```
Gene -[:gene_associated_with_condition]-> Disease (52.8K edges)
```

**Impact**: Specific predicate has 37% more edges and higher confidence

**Solution**: Always use `gene_associated_with_condition` when available
```cypher
// BEST:
MATCH (g:Gene)-[:gene_associated_with_condition]->(dis:Disease)

// ACCEPTABLE:
MATCH (g:Gene)-[:associated_with]->(dis:Disease)

// MOST COMPREHENSIVE:
MATCH (g:Gene)-[:gene_associated_with_condition|associated_with]->(dis:Disease)
```

---

## Node Type Ambiguities

### 4. Side Effects: Dual Modeling

**Biolink Model Expectation**:
```
Drug -[:causes]-> PhenotypicFeature
```

**Everycure KG Reality**:
```
Drug -[:causes]-> Disease (35K edges - PRIMARY)
Drug -[:causes]-> PhenotypicFeature (25K edges - SECONDARY)
```

**Example**: Stevens-Johnson syndrome labeled as `Disease`, not `PhenotypicFeature`

**Impact**: Queries expecting only PhenotypicFeature miss 58% of side effects

**Solution**: Support both node types
```cypher
// COMPREHENSIVE:
MATCH (d:Drug)-[:causes]->(se)
WHERE 'biolink:Disease' IN labels(se) OR 'biolink:PhenotypicFeature' IN labels(se)
RETURN se
```

### 5. HBB: Protein vs Gene Label

**Biolink Model Expectation**:
```
HBB labeled as Gene (NCBIGene:3043)
```

**Everycure KG Reality**:
```
HBB labeled as Protein (UniProtKB:P68871), not Gene
```

**Impact**: Gene-based queries miss protein-level annotations

**Solution**: Search both Gene and Protein labels
```cypher
// FLEXIBLE:
MATCH (n) WHERE (n.name = 'HBB' OR n.id CONTAINS 'HBB')
  AND ('biolink:Gene' IN labels(n) OR 'biolink:Protein' IN labels(n))
RETURN n
```

---

## Node Label Inconsistencies

### 6. Drug vs SmallMolecule vs ChemicalEntity

**Issue**: Same drug may have multiple node labels

**Example**: Valproic acid
- `CHEBI:39867` (labeled as `biolink:NamedThing`)
- `CHEBI:60654` (labeled as `biolink:SmallMolecule`)

**Impact**: Treatment relationships on one node, protein interactions on another

**Solution**: Search across related node types
```cypher
// COMPREHENSIVE drug search:
MATCH (d) WHERE d.name CONTAINS 'DrugName'
  AND ('biolink:Drug' IN labels(d)
    OR 'biolink:SmallMolecule' IN labels(d)
    OR 'biolink:ChemicalEntity' IN labels(d))
RETURN d.id, labels(d), d.name
```

### 7. Gene Not in KG (Missing Annotations)

**Issue**: Some clinically important genes absent

**Examples from experiments**:
- DMD gene (NCBIGene:1756) - NOT in KG despite being causative for DMD disease
- LILRB1 - NOT in Everycure KG v0.13.0

**Impact**: Cannot validate direct gene-drug hypotheses

**Solution**: Use protein-level queries as proxy
```cypher
// If gene not found, try protein:
MATCH (p:Protein) WHERE p.name CONTAINS 'GeneName'
MATCH (p)-[:gene_product_of]->(g:Gene)  // Infer gene
RETURN g
```

---

## Relationship Type Quirks

### 8. HDAC Inhibition: Uses "affects" not "directly_physically_interacts_with"

**Biolink Model Expectation**:
```
Drug -[:directly_physically_interacts_with]-> Protein (for all direct targets)
```

**Everycure KG Reality for Inhibitors**:
```
VPA -[:affects]-> HDAC8 (not "directly_physically_interacts_with")
```

**Impact**: Queries limited to `directly_physically_interacts_with` miss inhibitors

**Solution**: Include both relationship types
```cypher
// COMPREHENSIVE:
MATCH (d:Drug)-[r:directly_physically_interacts_with|affects]->(p:Protein)
WHERE d.id = $drug_id
RETURN p, type(r)
```

### 9. Treatment vs Study Relationships

**Multiple predicates for treatment**:
- `treats` (specific approval)
- `applied_to_treat` (off-label use)
- `treats_or_applied_or_studied_to_treat` (comprehensive)
- `associated_with` (generic)

**Solution**: Use comprehensive predicate or combine
```cypher
// MOST COMPREHENSIVE:
MATCH (d:Drug)-[r:treats_or_applied_or_studied_to_treat]->(dis:Disease)

// COMBINE MULTIPLE:
MATCH (d:Drug)-[r:treats|applied_to_treat|studied_to_treat]->(dis:Disease)
```

---

## Path Explosion Zones

### 10. OrganismTaxon: The Black Hole

**Node Count**: 3.2M nodes (35% of entire KG!)

**Relationships**: Likely connected to most Genes/Proteins via `in_taxon`

**Impact**: ANY query through OrganismTaxon will explode

**Solution**: NEVER traverse through OrganismTaxon
```cypher
// DANGEROUS (will explode):
MATCH (g:Gene)-[:in_taxon]->(taxon:OrganismTaxon)-[:in_taxon]-(related)
RETURN related

// AVOID entirely - filter it out:
MATCH (n)-[r]-(other)
WHERE NOT 'biolink:OrganismTaxon' IN labels(other)
RETURN other
```

### 11. SmallMolecule: The Other Black Hole

**Node Count**: 3M nodes (33% of KG)

**Issue**: Much broader than Drug (73K nodes)

**Impact**: Queries using SmallMolecule instead of Drug get 40x more results

**Solution**: Always filter to Drug label specifically
```cypher
// CORRECT:
MATCH (d) WHERE 'biolink:Drug' IN labels(d)

// WRONG (40x more results):
MATCH (d) WHERE 'biolink:SmallMolecule' IN labels(d)
```

---

## Schema Validation Workflow

When designing a new metapath, always validate the schema first:

```cypher
// Step 1: Check if nodes exist
MATCH (n) WHERE n.id = $node_id RETURN n, labels(n)

// Step 2: Discover actual relationships
MATCH (n {id: $node_id})-[r]-()
RETURN DISTINCT type(r), COUNT(*) as count
ORDER BY count DESC
LIMIT 20

// Step 3: Check relationship direction
MATCH (source {id: $source_id})-[r:rel_type]->(target)
RETURN COUNT(*) as forward_count

MATCH (source {id: $source_id})<-[r:rel_type]-(target)
RETURN COUNT(*) as reverse_count

// Step 4: Inspect neighbor types
MATCH (n {id: $node_id})-[r:rel_type]-(neighbor)
RETURN labels(neighbor)[0] as neighbor_type, COUNT(*) as count
ORDER BY count DESC
LIMIT 10
```

---

## Quick Reference: Schema Deviations

| Expected (Biolink) | Actual (Everycure KG) | Fix |
|--------------------|----------------------|-----|
| Protein → Pathway | **Pathway → Protein** (312K) | Reverse query |
| Pathway → Disease | **Disease → Pathway** (607) | Reverse query |
| Gene → Disease (generic) | **Gene → Disease (specific)** (52.8K) | Use `gene_associated_with_condition` |
| Drug → PhenotypicFeature | **Drug → Disease + PhenotypicFeature** | Support both |
| Gene labels | Some as **Protein labels** | Search both |
| Drug (single node) | **Drug + SmallMolecule** (split) | Search multiple labels |
| directly_physically_interacts_with | Sometimes **affects** | Use both |
| DMD gene exists | **DMD gene missing** | Use protein proxy |

---

## Tools for Schema Discovery

### Use `get_schema()` tool:
```python
schema = get_schema(database="everycure-v0.13.0")
print(schema["labels"])  # All node types
print(schema["relationship_types"])  # All relationship types
```

### Use `get_supported_types()` tool:
```python
types = get_supported_types()
print(types["common_node_types"])  # Filtered 25 meaningful types
print(types["common_relationship_types"])  # Filtered 30 types
```

### Use `get_neighborhood_stats()` tool:
```python
stats = get_neighborhood_stats(
    node_id="CHEBI:6801",  # Metformin
    max_hops=1
)
print(stats["relationship_type_distribution"])  # What relationships exist?
print(stats["neighbor_label_distribution"])  # What neighbor types?
```

---

## Key Takeaways

1. **Never assume Biolink Model = KG reality** - Always validate
2. **Direction matters enormously** - 10-300x difference in edge counts
3. **Specific predicates > Generic** - `gene_associated_with_condition` beats `associated_with`
4. **Node types can be ambiguous** - Same entity may have multiple labels
5. **Some genes/proteins missing** - Use proxies or alternative queries
6. **Relationship types vary** - `affects` vs `directly_physically_interacts_with`
7. **Use schema tools first** - Discover before designing queries
8. **Document deviations** - When you find quirks, note them for future reference
