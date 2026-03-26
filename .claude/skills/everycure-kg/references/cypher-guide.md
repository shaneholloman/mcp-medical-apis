# Cypher Query Mini-Manual for Biomedical Knowledge Graphs

A practical guide to writing read-only Cypher queries against biomedical knowledge graphs.

## 1. Basic Syntax: MATCH, WHERE, RETURN

Cypher queries follow a declarative pattern-matching approach:

```cypher
MATCH <pattern>
WHERE <conditions>
RETURN <results>
```

**Example: Find a disease by name**
```cypher
MATCH (d:Disease)
WHERE d.name = "Alzheimer's disease"
RETURN d
```

**Simplified syntax** (filter in pattern):
```cypher
MATCH (d:Disease {name: "Alzheimer's disease"})
RETURN d
```

**Return specific properties**:
```cypher
MATCH (d:Disease {name: "Alzheimer's disease"})
RETURN d.id, d.name, d.description
```

## 2. Node Patterns

Nodes are enclosed in parentheses `()` with optional labels and properties.

### Syntax Components:
- `(n)` - Any node, bound to variable `n`
- `(n:Label)` - Node with specific label
- `(n:Label1:Label2)` - Node with multiple labels
- `(n:Label {prop: value})` - Node with label and property filter
- `(:Label)` - Anonymous node (not bound to variable)

**Examples:**
```cypher
// All drugs
MATCH (drug:Drug)
RETURN drug.name
LIMIT 10

// Drugs with specific mechanism
MATCH (drug:Drug {mechanism_of_action: "EGFR inhibitor"})
RETURN drug.name, drug.id

// Multiple labels
MATCH (n:Drug:SmallMolecule)
RETURN n.name
```

## 3. Relationship Patterns

Relationships connect nodes and are enclosed in square brackets `[]`.

### Direction:
- `-->` or `-[:TYPE]->` - Outgoing (left to right)
- `<--` or `<-[:TYPE]-` - Incoming (right to left)
- `--` or `-[:TYPE]-` - Undirected (either direction)

### Syntax:
- `-[r]->` - Any relationship
- `-[r:TYPE]->` - Specific relationship type
- `-[:TYPE]->` - Anonymous relationship
- `-[r:TYPE1|TYPE2]->` - Multiple relationship types

**Examples:**
```cypher
// Drugs that treat a disease
MATCH (drug:Drug)-[:TREATS]->(disease:Disease)
WHERE disease.name = "hypertension"
RETURN drug.name

// Genes associated with disease (either direction)
MATCH (gene:Gene)-[:ASSOCIATED_WITH]-(disease:Disease)
WHERE disease.name = "breast cancer"
RETURN gene.symbol, gene.id

// Drugs with relationship properties
MATCH (drug:Drug)-[r:TREATS]->(disease:Disease)
WHERE r.confidence_score > 0.8
RETURN drug.name, disease.name, r.confidence_score
```

## 4. Path Patterns and Variable-Length Paths

Paths represent sequences of connected nodes and relationships.

### Variable-Length Paths:
- `-[*]->` - Any number of hops (0 or more)
- `-[*1..3]->` - Between 1 and 3 hops
- `-[*..5]->` - Up to 5 hops
- `-[*2..]->` - 2 or more hops

**Examples:**
```cypher
// Direct and indirect drug-disease associations (up to 3 hops)
MATCH path = (drug:Drug)-[*1..3]->(disease:Disease)
WHERE drug.name = "metformin"
RETURN path
LIMIT 10

// Find intermediate nodes between drug and disease
MATCH (drug:Drug {name: "aspirin"})-[*2]-(disease:Disease {name: "stroke"})
RETURN *
LIMIT 20

// Drugs connected to diseases via genes
MATCH (drug:Drug)-[:TARGETS]->(gene:Gene)-[:ASSOCIATED_WITH]->(disease:Disease)
RETURN drug.name, gene.symbol, disease.name
LIMIT 50
```

**⚠️ Warning:** Variable-length paths can cause **path explosion** in highly connected graphs. Always use:
- Upper bounds on path length (e.g., `[*1..3]` not `[*]`)
- `LIMIT` clauses
- Specific node/relationship filters

## 5. Filtering with WHERE

`WHERE` provides flexible filtering beyond property matching.

### Operators:
- Comparison: `=`, `<>`, `<`, `>`, `<=`, `>=`
- Logical: `AND`, `OR`, `NOT`
- String: `CONTAINS`, `STARTS WITH`, `ENDS WITH`
- Null checks: `IS NULL`, `IS NOT NULL`
- List membership: `IN`
- Regular expressions: `=~`

**Examples:**
```cypher
// Multiple conditions
MATCH (d:Drug)
WHERE d.phase >= 3 AND d.year_approved > 2010
RETURN d.name, d.phase, d.year_approved

// String matching
MATCH (d:Disease)
WHERE d.name CONTAINS "diabetes" OR d.name CONTAINS "diabetic"
RETURN d.name

// Pattern matching with regex (case-insensitive)
MATCH (g:Gene)
WHERE g.symbol =~ "(?i)brca.*"
RETURN g.symbol

// Check for existence of property
MATCH (d:Drug)
WHERE d.fda_approved IS NOT NULL
RETURN d.name

// IN operator for multiple values
MATCH (d:Disease)
WHERE d.id IN ["MONDO:0005148", "MONDO:0007254", "MONDO:0008315"]
RETURN d.name, d.id
```

## 6. Aggregation Functions

Aggregation functions compute summary statistics.

### Common Functions:
- `COUNT()` - Count items
- `COLLECT()` - Collect items into list
- `DISTINCT` - Remove duplicates
- `SUM()`, `AVG()`, `MIN()`, `MAX()` - Numeric aggregations

**Examples:**
```cypher
// Count drugs per disease
MATCH (drug:Drug)-[:TREATS]->(disease:Disease)
RETURN disease.name, COUNT(drug) AS drug_count
ORDER BY drug_count DESC
LIMIT 10

// Collect all genes associated with a disease
MATCH (gene:Gene)-[:ASSOCIATED_WITH]->(disease:Disease {name: "Parkinson's disease"})
RETURN disease.name, COLLECT(gene.symbol) AS associated_genes

// Count distinct relationship types
MATCH (d:Drug)-[r]->(target)
RETURN type(r) AS relationship_type, COUNT(*) AS count
ORDER BY count DESC

// Average confidence scores
MATCH (drug:Drug)-[r:TREATS]->(disease:Disease)
WHERE r.confidence_score IS NOT NULL
RETURN disease.name, AVG(r.confidence_score) AS avg_confidence
ORDER BY avg_confidence DESC
LIMIT 10

// Count with DISTINCT
MATCH (drug:Drug)-[:TREATS]->(disease:Disease)
RETURN COUNT(DISTINCT disease) AS unique_diseases_treated
```

## 7. Limiting and Ordering Results

Control result size and order with `LIMIT`, `SKIP`, and `ORDER BY`.

**Examples:**
```cypher
// Order by property
MATCH (d:Drug)
WHERE d.year_approved IS NOT NULL
RETURN d.name, d.year_approved
ORDER BY d.year_approved DESC
LIMIT 20

// Multiple sort criteria
MATCH (d:Drug)
RETURN d.name, d.phase, d.year_approved
ORDER BY d.phase DESC, d.year_approved DESC
LIMIT 10

// Pagination with SKIP
MATCH (d:Disease)
RETURN d.name
ORDER BY d.name
SKIP 20
LIMIT 10

// Order aggregations
MATCH (pathway:Pathway)<-[:PARTICIPATES_IN]-(gene:Gene)
RETURN pathway.name, COUNT(gene) AS gene_count
ORDER BY gene_count DESC
LIMIT 15
```

## 8. Parameter Syntax

Use parameters for dynamic queries and to prevent injection attacks.

**Parameter syntax:** `$param_name`

**Example query with parameters:**
```cypher
MATCH (d:Disease {id: $disease_id})<-[:TREATS]-(drug:Drug)
WHERE drug.phase >= $min_phase
RETURN drug.name, drug.phase
ORDER BY drug.phase DESC
LIMIT $max_results
```

**Calling with parameters** (depends on client):
```python
# Python example with neo4j driver
result = session.run(
    """
    MATCH (d:Disease {id: $disease_id})<-[:TREATS]-(drug:Drug)
    WHERE drug.phase >= $min_phase
    RETURN drug.name, drug.phase
    LIMIT $max_results
    """,
    disease_id="MONDO:0005148",
    min_phase=2,
    max_results=10
)
```

## 9. Common Pitfalls in Highly Connected Graphs

### Path Explosion
Highly connected nodes (hubs) can create exponential path growth.

**❌ Bad - Can return millions of paths:**
```cypher
MATCH path = (drug:Drug)-[*]-(disease:Disease)
RETURN path
```

**✅ Good - Bounded and filtered:**
```cypher
MATCH path = (drug:Drug)-[*1..3]-(disease:Disease)
WHERE drug.name = "imatinib"
RETURN path
LIMIT 100
```

### Cartesian Products
Missing relationships between matched patterns creates combinatorial explosion.

**❌ Bad - Cartesian product:**
```cypher
MATCH (d:Drug), (dis:Disease)
RETURN d.name, dis.name
// Returns every drug × every disease combination!
```

**✅ Good - Connected patterns:**
```cypher
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
RETURN d.name, dis.name
```

### Missing LIMIT
Always use `LIMIT` for exploration queries.

**❌ Bad:**
```cypher
MATCH (n)
RETURN n
```

**✅ Good:**
```cypher
MATCH (n)
RETURN n
LIMIT 25
```

### Inefficient Variable-Length Paths
Specify minimum length when you know relationships won't be direct.

**❌ Less efficient:**
```cypher
MATCH (drug:Drug)-[*1..4]-(protein:Protein)
RETURN drug.name, protein.name
LIMIT 100
```

**✅ More efficient (if you know minimum distance is 2):**
```cypher
MATCH (drug:Drug)-[*2..4]-(protein:Protein)
RETURN drug.name, protein.name
LIMIT 100
```

## 10. Biomedical Query Examples

### Find drugs for a disease
```cypher
MATCH (drug:Drug)-[r:TREATS]->(disease:Disease {name: "type 2 diabetes"})
RETURN drug.name, drug.mechanism_of_action, r.evidence_level
ORDER BY r.evidence_level DESC
LIMIT 20
```

### Find drugs targeting a specific gene
```cypher
MATCH (drug:Drug)-[:TARGETS]->(gene:Gene {symbol: "EGFR"})
RETURN drug.name, drug.status, drug.phase
ORDER BY drug.phase DESC
```

### Find shared genes between two diseases
```cypher
MATCH (d1:Disease {name: "Alzheimer's disease"})<-[:ASSOCIATED_WITH]-(gene:Gene)-[:ASSOCIATED_WITH]->(d2:Disease {name: "Parkinson's disease"})
RETURN gene.symbol, gene.name
ORDER BY gene.symbol
```

### Find pathways involving a gene
```cypher
MATCH (gene:Gene {symbol: "TP53"})-[:PARTICIPATES_IN]->(pathway:Pathway)
RETURN pathway.name, pathway.source, pathway.id
ORDER BY pathway.name
```

### Drug repurposing: Drugs treating similar diseases
```cypher
MATCH (target_disease:Disease {name: "COVID-19"})-[:SIMILAR_TO]-(similar_disease:Disease)<-[:TREATS]-(drug:Drug)
WHERE NOT (drug)-[:TREATS]->(target_disease)
RETURN DISTINCT drug.name, similar_disease.name, drug.mechanism_of_action
LIMIT 50
```

### Find mechanistic path from drug to disease
```cypher
MATCH path = (drug:Drug {name: "methotrexate"})-[:TARGETS]->(gene:Gene)-[:ASSOCIATED_WITH]->(disease:Disease)
RETURN drug.name, gene.symbol, disease.name
LIMIT 25
```

### Gene-pathway enrichment
```cypher
MATCH (gene:Gene)-[:ASSOCIATED_WITH]->(disease:Disease {name: "breast cancer"})
WITH COLLECT(gene) AS disease_genes
UNWIND disease_genes AS gene
MATCH (gene)-[:PARTICIPATES_IN]->(pathway:Pathway)
RETURN pathway.name, COUNT(gene) AS gene_count
ORDER BY gene_count DESC
LIMIT 15
```

### Clinical trials for a drug
```cypher
MATCH (drug:Drug {name: "pembrolizumab"})-[:TESTED_IN]->(trial:ClinicalTrial)
WHERE trial.phase IN ["Phase 3", "Phase 4"]
RETURN trial.id, trial.title, trial.status, trial.phase
ORDER BY trial.phase DESC, trial.start_date DESC
LIMIT 20
```

### Find drug combinations
```cypher
MATCH (d1:Drug)-[:COMBINED_WITH]->(d2:Drug)
WHERE d1.name < d2.name  // Avoid duplicates
RETURN d1.name AS drug1, d2.name AS drug2
LIMIT 50
```

### Protein-protein interactions for a gene
```cypher
MATCH (gene:Gene {symbol: "BRCA1"})-[:ENCODES]->(protein:Protein)-[:INTERACTS_WITH]->(other_protein:Protein)
RETURN other_protein.name, other_protein.id
LIMIT 30
```

## Best Practices Summary

1. **Always use LIMIT** for exploratory queries
2. **Bound variable-length paths** with explicit ranges (e.g., `[*1..3]`)
3. **Filter early** - use WHERE or inline properties to reduce search space
4. **Use parameters** for dynamic values
5. **Test incrementally** - start with simple patterns, add complexity
6. **Profile queries** - use `PROFILE` or `EXPLAIN` prefix to understand performance
7. **Avoid Cartesian products** - ensure patterns are connected
8. **Be specific with labels** - helps Neo4j optimize queries
9. **Use DISTINCT** when aggregating may produce duplicates
10. **Order before limiting** - ensure consistent, meaningful results

## Query Optimization Tip

Add `EXPLAIN` or `PROFILE` before any query to understand execution:

```cypher
PROFILE
MATCH (drug:Drug)-[:TREATS]->(disease:Disease)
WHERE disease.name = "diabetes"
RETURN drug.name
LIMIT 10
```

`EXPLAIN` shows the query plan without executing. `PROFILE` executes and shows actual row counts and timings.

---

**End of Mini-Manual** - For more details, see [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
