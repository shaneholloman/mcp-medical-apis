# Query Patterns for Everycure KG

**Purpose**: Proven query patterns that work reliably in the Everycure KG (9.2M nodes, 77M relationships)

---

## Safe Query Patterns (< 30 seconds, < 1000 results)

### Pattern 1: Direct Treatment Relationships (1-hop)

**Use when**: Finding if a drug directly treats a disease

```cypher
MATCH (d)-[r:treats_or_applied_or_studied_to_treat]->(dis)
WHERE 'biolink:Drug' IN labels(d)
  AND dis.id = $disease_id
RETURN d.id, d.name, type(r)
LIMIT 100
```

**Performance**: Tier 1 (<1s), 0-100 results
**Success Rate**: 100% when direct relationship exists

### Pattern 2: Drug via Protein Targets (2-hop)

**Use when**: Finding mechanistic protein connections

```cypher
MATCH (d:Drug)-[:directly_physically_interacts_with]->(p:Protein)-[:associated_with]->(dis:Disease)
WHERE d.id = $drug_id AND dis.id = $disease_id
RETURN d, p, dis
LIMIT 100
```

**Performance**: Tier 2 (1-5s), 0-100 results
**Success Rate**: 90% for well-studied drugs

### Pattern 3: Gene-Disease Associations

**Use when**: Finding genes linked to a disease

```cypher
MATCH (g:Gene)-[r:gene_associated_with_condition|associated_with]->(dis:Disease)
WHERE dis.id = $disease_id
RETURN g.id, g.name, type(r)
ORDER BY r.score DESC
LIMIT 50
```

**Performance**: Tier 2 (1-5s), 0-50 results
**Success Rate**: 85% for genetic diseases

**Key Insight**: Use `gene_associated_with_condition` (52.8K edges) over generic `associated_with` (38.6K edges)

### Pattern 4: Find Disease-Associated Pathways

**Use when**: Identifying pathways involved in disease

```cypher
MATCH (dis:Disease)-[r:disease_has_basis_in]->(path:Pathway)
WHERE dis.id = $disease_id
RETURN path.id, path.name, type(r)
LIMIT 50
```

**Performance**: Tier 1 (<1s), 0-50 results
**Success Rate**: 60% (sparse annotations, only 607 disease-pathway edges)

**Note**: Use alternative Pattern 4b if no results

### Pattern 4b: Pathways via Proteins (Alternative)

```cypher
MATCH (dis:Disease)<-[:associated_with]-(p:Protein)<-[:has_participant]-(path:Pathway)
WHERE dis.id = $disease_id
RETURN path.id, path.name, COUNT(p) as protein_count
ORDER BY protein_count DESC
LIMIT 20
```

**Performance**: Tier 2 (2-5s), 0-20 results

### Pattern 5: Drug-Gene Overlap

**Use when**: Checking if drug affects disease genes

```cypher
// Step 1: Get disease genes
MATCH (g:Gene)-[:gene_associated_with_condition]->(dis:Disease)
WHERE dis.id = $disease_id
WITH collect(g.id) as disease_genes

// Step 2: Check drug targets
MATCH (d:Drug)-[:directly_physically_interacts_with]->(p:Protein)-[:gene_product_of]->(g:Gene)
WHERE d.id = $drug_id AND g.id IN disease_genes
RETURN d, p, g
LIMIT 50
```

**Performance**: Tier 2 (5-10s), 0-50 results
**Success Rate**: 40% (direct overlap rare, indirect mechanisms common)

### Pattern 6: Neighborhood Statistics (Before Full Query)

**Use when**: Assessing degree before retrieval

```cypher
MATCH (n {id: $node_id})-[r]-()
RETURN count(DISTINCT r) as degree,
       collect(DISTINCT type(r))[0..10] as sample_relationships
```

**Performance**: Tier 1 (<1s)
**Success Rate**: 100%

**Use this BEFORE** running full neighborhood queries to avoid path explosion

---

## Risky Query Patterns (Use with Caution)

### Pattern 7: 2-Hop Neighborhood (Path Explosion Risk)

**Use when**: Must explore broader connections (expect 10K-100K neighbors)

```cypher
MATCH (n {id: $node_id})-[r1]-(intermediate)-[r2]-(neighbor)
RETURN count(DISTINCT neighbor) as neighbor_count
// If count < 1000, then retrieve:
// RETURN neighbor LIMIT 100
```

**Performance**: Tier 3 (5-30s) for COUNT, Tier 4+ for RETURN
**Average Growth**: 440x per hop
**Only use on**: Drug or Disease nodes (NOT Protein, Gene, OrganismTaxon)

### Pattern 8: Custom 3-Hop Metapath (High Risk)

**Use when**: Predefined metapaths don't exist AND you've validated each step

```cypher
// ALWAYS COUNT FIRST
MATCH (source {id: $source_id})-[r1:rel_type1]->(intermediate1)
      -[r2:rel_type2]->(intermediate2)-[r3:rel_type3]->(target {id: $target_id})
WHERE 'biolink:NodeType1' IN labels(source)
  AND 'biolink:NodeType2' IN labels(intermediate1)
  AND 'biolink:NodeType3' IN labels(intermediate2)
  AND 'biolink:NodeType4' IN labels(target)
RETURN COUNT(*) as path_count

// Only retrieve if path_count < 100:
// RETURN source, r1, intermediate1, r2, intermediate2, r3, target LIMIT 10
```

**Performance**: Tier 3-4 (10-60s) for COUNT
**Success Rate**: 30% (many fail due to missing relationships)

**Critical**: Each hop must use specific relationship types (no wildcards!)

---

## Anti-Patterns (NEVER USE)

### ❌ Anti-Pattern 1: Unlimited Variable-Length Paths

```cypher
// NEVER DO THIS:
MATCH path = (source)-[*]-(target)
WHERE source.id = $source_id AND target.id = $target_id
RETURN path
```

**Result**: Query timeout, billions of paths, system crash

### ❌ Anti-Pattern 2: No LIMIT Clause

```cypher
// NEVER DO THIS:
MATCH (d:Drug)-[r]->(dis:Disease)
RETURN d, r, dis
// Missing LIMIT - will return 35K rows!
```

**Result**: Overwhelming output, context window overflow

### ❌ Anti-Pattern 3: Through OrganismTaxon or SmallMolecule

```cypher
// NEVER DO THIS:
MATCH (d:Drug)-[:in_taxon]->(taxon:OrganismTaxon)-[:in_taxon]-(g:Gene)
RETURN g
```

**Result**: Path explosion (3.2M OrganismTaxon nodes)

### ❌ Anti-Pattern 4: Generic Node Labels

```cypher
// NEVER DO THIS:
MATCH (d:Drug)-[r]-(thing:NamedThing)-[r2]-(target)
RETURN target
```

**Result**: Explosion through generic 83K NamedThing nodes

### ❌ Anti-Pattern 5: RETURN Before COUNT

```cypher
// NEVER DO THIS for multi-hop:
MATCH (d)-[r1]-(mid)-[r2]-(target)
WHERE d.id = $drug_id
RETURN d, mid, target  // Should COUNT first!
LIMIT 100
```

**Result**: Hangs trying to materialize millions of paths before limiting

---

## Query Workflow Decision Tree

```
START: Do you know both source and target nodes?
├─ YES: Is it 1-hop direct relationship?
│  ├─ YES → Use Pattern 1 (direct treatment)
│  └─ NO: Is it 2-hop?
│     ├─ YES → Use Pattern 2 (via protein targets)
│     └─ NO: 3+ hops?
│        ├─ Use predefined metapath if available
│        └─ Use Pattern 8 (custom 3-hop) with COUNT first
│
└─ NO: Are you exploring from one node?
   ├─ Exploring disease → Use Pattern 3 (find genes)
   ├─ Exploring disease → Use Pattern 4 (find pathways)
   ├─ Exploring drug-gene overlap → Use Pattern 5
   └─ Exploring neighborhood → Use Pattern 6 (stats first!)
```

---

## Performance Tier Reference

| Tier | Time | Query Types | Max Results |
|------|------|-------------|-------------|
| 1 | <1s | Node lookups, 1-hop direct, stats | 100 |
| 2 | 1-5s | 2-hop filtered, neighborhood stats | 100 |
| 3 | 5-30s | 2-hop unfiltered counts, 3-hop counts | 1000 |
| 4 | >30s | 3+ hop queries, broad neighborhood | AVOID |

---

## Node Type Safety Reference

| Node Type | Count | Avg Degree | Safety | Use as... |
|-----------|-------|------------|--------|-----------|
| Drug | 73K | 125 | ✅ SAFE | Start point |
| Disease | 112K | 1.4K | ✅ SAFE | Start/end point |
| Pathway | 117K | - | ⚠️ MODERATE | Intermediate |
| Gene | 264K | - | ⚠️ HIGH RISK | Endpoint preferred |
| Protein | 458K | 3.5K | ⚠️ HIGH RISK | Intermediate only |
| SmallMolecule | 3M | - | ❌ NEVER | - |
| OrganismTaxon | 3.2M | - | ❌ NEVER | - |

---

## Relationship Type Preferences

**For Gene → Disease**:
1. `gene_associated_with_condition` (52.8K edges) - BEST
2. `associated_with` (38.6K edges) - Good
3. `causes` (7.5K edges) - Strong evidence
4. `contributes_to` - Moderate evidence

**For Protein ↔ Pathway**:
1. `Pathway -[:has_participant]-> Protein` (312K edges) - DOMINANT (reversed!)
2. `Protein -[:actively_involved_in]-> Pathway` (23.9K edges) - Forward direction

**For Pathway → Disease**:
1. `Disease -[:disease_has_basis_in]-> Pathway` (607 edges) - ONLY option (reversed!)

**For Drug → Side Effects**:
1. `Drug -[:causes]-> Disease` (35K edges) - PRIMARY
2. `Drug -[:causes]-> PhenotypicFeature` (25K edges) - ALTERNATIVE

---

## Debugging Failed Queries

### Symptom: 0 results returned

**Diagnosis Steps**:
1. Verify node IDs exist: `MATCH (n {id: $node_id}) RETURN n`
2. Check relationship direction: Try bidirectional `-[r]-` first
3. List actual relationships: `MATCH (n {id: $node_id})-[r]-() RETURN DISTINCT type(r) LIMIT 20`
4. Verify node labels: `MATCH (n {id: $node_id}) RETURN labels(n)`

### Symptom: Query hangs/times out

**Diagnosis Steps**:
1. Add COUNT before RETURN
2. Reduce hops (3 → 2 → 1)
3. Add specific relationship types (remove wildcards)
4. Check node types aren't in danger zone (Protein, Gene, OrganismTaxon)

### Symptom: Too many results (>1000)

**Diagnosis Steps**:
1. Add LIMIT clause (start with 10-100)
2. Add more specific filters (node labels, relationship types)
3. Order by relevance first: `ORDER BY r.score DESC LIMIT 20`
4. Use aggregation: `COUNT(*)`, `collect(...)[0..10]`

---

## Example Successful Query Sessions

### Session 1: Metformin → IPF
```cypher
// Step 1: Find Metformin
MATCH (d) WHERE d.name CONTAINS 'Metformin' AND 'biolink:Drug' IN labels(d)
RETURN d.id, d.name  // Found: CHEBI:6801

// Step 2: Find IPF
MATCH (dis) WHERE dis.name CONTAINS 'pulmonary fibrosis' AND 'biolink:Disease' IN labels(dis)
RETURN dis.id, dis.name  // Found: MONDO:0800029

// Step 3: Direct treatment?
MATCH (d {id: 'CHEBI:6801'})-[r:treats_or_applied_or_studied_to_treat]->(dis {id: 'MONDO:0800029'})
RETURN r  // SUCCESS: 1 path found

// Step 4: Find mechanisms
MATCH (d {id: 'CHEBI:6801'})-[:directly_physically_interacts_with]->(p:Protein)
      -[:associated_with]->(dis {id: 'MONDO:0800029'})
RETURN p.id, p.name  // SUCCESS: 50 proteins including HDAC6 (AMPK pathway)
```

### Session 2: Gene-Disease-Drug Triangle
```cypher
// Step 1: Find MS-associated genes
MATCH (g:Gene)-[r:gene_associated_with_condition]->(dis:Disease)
WHERE dis.name CONTAINS 'multiple sclerosis'
RETURN g.id, g.name
LIMIT 20  // Found: IKZF1, SLAMF7, CTLA4, etc.

// Step 2: Find drugs targeting those genes
MATCH (d:Drug)-[:directly_physically_interacts_with]->(p:Protein)
      -[:gene_product_of]->(g:Gene {id: 'HGNC:13176'})  // IKZF1
RETURN d.id, d.name  // Found: Lenalidomide (IMiD drug class)

// Step 3: Validate MS relevance
MATCH (d {id: 'CHEMBL:CHEMBL1336'})  // Lenalidomide
MATCH (dis:Disease) WHERE dis.name CONTAINS 'sclerosis'
MATCH path = (d)-[*1..2]-(dis)
RETURN path LIMIT 5  // Check if any MS connections exist
```

---

## Key Takeaways

1. **Always start simple**: 1-hop direct, then 2-hop, then consider 3-hop
2. **COUNT before RETURN**: For any multi-hop query
3. **Specific > Generic**: Specific relationships and node types always win
4. **Know your node types**: Drug/Disease safe, Protein/Gene risky, OrganismTaxon deadly
5. **Schema validation**: When in doubt, query the schema first
6. **Informative nulls**: 0 results may mean indirect mechanism (biology, not failure)
7. **Use patterns**: Don't reinvent - these patterns cover 90% of use cases
