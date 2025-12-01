# CDP Prototype - Architecture Patterns

### Lambda Architecture (Enhanced)

This CDP implements an enhanced Lambda Architecture with reverse ETL:

- **Speed Layer (Real-time)**: Flink processes events with fuzzy matching
- **Batch Layer**: dbt computes aggregate metrics in PostgreSQL
- **Serving Layer**: MongoDB serves unified profiles with computed attributes
- **Reverse ETL**: Metrics flow back from warehouse to operational store

### Event-Driven Architecture

- Events are the source of truth
- All state changes are event-derived
- Complete audit trail with event history
- Immutable event log in MongoDB

### Polyglot Persistence

Different databases optimized for different purposes:

| Database | Purpose | Why This DB? |
|----------|---------|--------------|
| **Neo4j** | Identity graph | Graph algorithms, fuzzy matching with APOC, relationship traversal |
| **MongoDB** | Profile store | Flexible schema, fast document retrieval, JSONB arrays for events |
| **PostgreSQL** | Analytics | SQL transformations, ACID compliance, dbt compatibility |

### RAG Pattern (Retrieval-Augmented Generation)

The personalization API uses RAG:

1. **Retrieve**: Fetch customer profile from MongoDB (with computed metrics)
2. **Augment**: Build context-rich prompt with profile data and event history
3. **Generate**: Gemini LLM creates personalized content

### ELT vs ETL

**Traditional ETL**: Transform in Python → Load

**Modern ELT** (this system):
- **Extract**: MongoDB → PostgreSQL (raw)
- **Load**: Bulk insert without transformation
- **Transform**: SQL-based (dbt) in warehouse
- **Benefits**: Version control, testing, replayability, observability



