# CDP Prototype - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Deep Dive](#component-deep-dive)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Decisions](#design-decisions)
7. [Fuzzy Identity Matching](#fuzzy-identity-matching)
8. [ELT Pipeline Architecture](#elt-pipeline-architecture)

---

## 1. System Overview

### What is a Customer Data Platform (CDP)?

A Customer Data Platform is a packaged software that creates a persistent, unified customer database accessible to other systems. This prototype implements advanced CDP capabilities:

1. **Data Ingestion**: Real-time event collection via Apache Flink
2. **Identity Resolution**: Fuzzy matching algorithms for intelligent stitching
3. **Profile Unification**: Single customer view across devices/channels
4. **Analytics Transformation**: SQL-based metric computation with dbt
5. **Reverse ETL**: Computed metrics synced back to operational store
6. **Activation**: AI-powered personalization and graph debugging
7. **Monitoring**: Anomaly detection and graph health diagnostics

### Architecture Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                             │
│              (Python Producer / External APIs)               │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    MESSAGE BUS (Kafka)                       │
│  Topic: cdp.events (Partitioned)                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│           STREAM PROCESSING (Apache Flink)                   │
│  - Source: KafkaSource (Group: cdp-flink-group)              │
│  - Logic: Fuzzy Matching & Profile Stitching                 │
│  - State: Checkpointing enabled                              │
└─────────┬────────────────────────────────────┬───────────────┘
          │                                    │
          │ Neo4j Updates                      │ Profile Updates
          ▼                                    ▼
┌──────────────────────┐           ┌──────────────────────────┐
│   IDENTITY GRAPH     │           │   PROFILE STORE          │
│      (Neo4j)         │           │     (MongoDB)            │
└──────────────────────┘           └────────┬─────────────────┘
                                            │
                                            │ ELT Pipeline
                                            ▼
                    ┌────────────────────────────────────────┐
                    │   ANALYTICS WAREHOUSE (PostgreSQL)     │
                    │  dbt models: LTV, Engagement, Churn    │
                    └────────────────────────────────────────┘
```

## 2. Architecture Patterns

### 2.1 Lambda Architecture (Enhanced)

This CDP implements an enhanced Lambda Architecture with reverse ETL:

- **Speed Layer (Real-time)**: Flink processes events with fuzzy matching
- **Batch Layer**: dbt computes aggregate metrics in PostgreSQL
- **Serving Layer**: MongoDB serves unified profiles with computed attributes
- **Reverse ETL**: Metrics flow back from warehouse to operational store

### 2.2 Event-Driven Architecture

- Events are the source of truth
- All state changes are event-derived
- Complete audit trail with event history
- Immutable event log in MongoDB

### 2.3 Polyglot Persistence

Different databases optimized for different purposes:

| Database | Purpose | Why This DB? |
|----------|---------|--------------|
| **Neo4j** | Identity graph | Graph algorithms, fuzzy matching with APOC, relationship traversal |
| **MongoDB** | Profile store | Flexible schema, fast document retrieval, JSONB arrays for events |
| **PostgreSQL** | Analytics | SQL transformations, ACID compliance, dbt compatibility |

### 2.4 RAG Pattern (Retrieval-Augmented Generation)

The personalization API uses RAG:

1. **Retrieve**: Fetch customer profile from MongoDB (with computed metrics)
2. **Augment**: Build context-rich prompt with profile data and event history
3. **Generate**: Gemini LLM creates personalized content

### 2.5 ELT vs ETL

**Traditional ETL**: Transform in Python → Load

**Modern ELT** (this system):
- **Extract**: MongoDB → PostgreSQL (raw)
- **Load**: Bulk insert without transformation
- **Transform**: SQL-based (dbt) in warehouse
- **Benefits**: Version control, testing, replayability, observability

---

## 3. Component Deep Dive

### 3.1 Event Producer (`producer/event_generator.py`)

**Purpose**: Simulate customer events for testing and development

**Three Modes**:

1. **Demo Mode** (default):
   - Realistic customer journey
   - Anonymous visit → Login → Multi-device → Purchase
   - Sequential events demonstrating identity stitching

2. **Fuzzy Mode** (`--mode fuzzy`):
   - Tests fuzzy matching algorithms
   - Generates similar but not identical identities
   - Examples: `john.doe@gmail.com` vs `johndoe@gmail.com`

3. **Hairball Mode** (`simulate_hairball.py`):
   - Stress testing for anomaly detection
   - 10 different users from same device
   - Simulates library kiosk or shared computer scenario

**Event Schema**:
```json
{
  "event_type": "page_view | login | add_to_cart | purchase",
  "identities": {
    "deviceID": "device_abc123",
    "email": "user@example.com",
    "phone": "+1-555-123-4567"
  },
  "properties": {
    "page": "/products/laptop",
    "product_name": "MacBook Pro",
    "price": 1299.99,
    "category": "Electronics"
  },
  "timestamp": 1234567890,
  "sequence": 1
}
```

**Why Socket Connection?**
- Simple for prototyping
- Demonstrates concept without Kafka complexity
- Flink has native socket source connector
- In production: Replace with Kafka, Kinesis, or Pub/Sub

---

### 3.2 Stream Processing Layer (Flink Jobs)

#### CustomerEvent.java - Identity Normalization

**Purpose**: Parse events and normalize identities before processing

**Key Features**:
- **Identity Normalization**: Uses `IdentityNormalizer` utility
  - Emails: Lowercase and trim
  - Phones: Strip non-numeric characters, format consistently
- **Property Type Detection**: Handles string, number, boolean values
- **Moved Responsibility**: Normalization happens at parse time (not in stitcher)

**Code Pattern**:
```java
// Normalize identities during parsing
for (Map.Entry<String, Object> entry : identities.entrySet()) {
    String type = entry.getKey();
    String value = entry.getValue().toString();
    
    // Normalize based on type
    String normalized = IdentityNormalizer.normalize(type, value);
    normalizedIdentities.put(type, normalized);
}
```

---

### 3.2 Stream Processing Layer (Flink Jobs)

#### SocketStreamJob.java

**Purpose**: Entry point for Flink streaming application

**Key Code**:
```java
// Connect to producer on host machine
final String host = "host.docker.internal";
final int port = 9001;

// Create stream from socket
DataStream<String> stream = env.socketTextStream(host, port);

// Process each event through ProfileStitcher
stream.map(new ProfileStitcher())
      .print();
```

**Why "host.docker.internal"?**
- Flink runs inside Docker container
- Needs to reach producer running on host machine
- `host.docker.internal` is Docker's special DNS name for the host

---

#### ProfileStitcher.java

**Purpose**: Core CDP logic - identity stitching and profile unification

**Workflow**:

```
Event arrives
    │
    ├─► Extract identities (email, deviceID, etc.)
    │
    ├─► Query Neo4j: Find/merge profiles with these identities
    │   │
    │   ├─► Case 1: New identities → Create new profile
    │   ├─► Case 2: Match one profile → Add new identity to it
    │   └─► Case 3: Match multiple profiles → MERGE them!
    │
    ├─► Get master_profile_id + ALL identities from Neo4j
    │
    ├─► Clean up orphaned MongoDB profiles (if merge happened)
    │
    └─► Update MongoDB with unified profile + all identities + event
```

**Critical Design Decision: Neo4j as Source of Truth for Identities**

The code explicitly states:
```java
// Step 3: Update MongoDB profile with ALL identities from Neo4j
updateMongoProfile(masterProfileId, event, allIdentities);
```

Why?
- Neo4j is authoritative for identity relationships
- MongoDB profiles sync from Neo4j (not vice versa)
- Prevents identity drift between systems

**Profile Merging Logic**:

When the same email appears on two different devices:
1. Neo4j detects both profiles have shared identity
2. Merges Profile nodes in graph
3. Returns single master_profile_id
4. ProfileStitcher deletes orphaned MongoDB documents
5. Updates remaining profile with ALL identities

---

### 3.3 Identity Graph (Neo4j)

**Schema**:

```
(:Profile {master_profile_id: "profile_uuid"})
    │
    ├─[:HAS_IDENTITY]─> (:Identity {type: "email", value: "user@example.com"})
    ├─[:HAS_IDENTITY]─> (:Identity {type: "deviceID", value: "device_123"})
    └─[:HAS_IDENTITY]─> (:Identity {type: "phone", value: "+1234567890"})
```

**Why Graph Database?**
- Identity resolution is fundamentally a graph problem
- "Which profiles share any identities?" = graph traversal
- Cypher query language is expressive for this use case

**Example Query**:
```cypher
// Find all profiles connected to this email
MATCH (i:Identity {type: "email", value: "user@example.com"})
      <-[:HAS_IDENTITY]-(p:Profile)
RETURN p
```

---

### 3.4 Profile Store (MongoDB)

**Document Schema**:

```javascript
{
  "_id": ObjectId("..."),
  "master_profile_id": "profile_abc123",  // Links to Neo4j
  
  // ALL identities (synced from Neo4j)
  "identities": {
    "email": "user@example.com",
    "deviceID": ["device_123", "device_456"],  // Multiple values = array
    "phone": "+1234567890"
  },
  
  // Latest event info (last-write-wins)
  "last_event_type": "purchase",
  "last_event_timestamp": 1234567890,
  
  // Custom attributes (enriched from events)
  "attributes": {
    "product_name": "MacBook Pro",
    "price": 1299.99
  },
  
  // Event history (append-only)
  "event_history": [
    {
      "event_type": "page_view",
      "timestamp": 1234567890,
      "data": { /* event payload */ }
    }
  ],
  
  // Computed metrics (from batch job)
  "computed_attributes": {
    "lifetime_value": 1299.99,
    "engagement_score": 85,
    "event_metrics": { /* ... */ },
    "time_metrics": { /* ... */ },
    "product_metrics": { /* ... */ }
  },
  
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**Update Pattern: Upsert with Nested Updates**

```java
// $set: Last-write-wins fields
"$set": {
  "identities": { /* all identities */ },
  "last_event_type": "purchase",
  "attributes.price": 1299.99
}

// $push: Append to arrays
"$push": {
  "event_history": { /* event */ }
}

// $max: Keep maximum value
"$max": {
  "last_event_timestamp": 1234567890
}
```

**Why MongoDB?**
- Flexible schema (customer attributes vary widely)
- Fast key-value lookups by master_profile_id
- Rich query capabilities for segmentation
- Native support for nested documents

---

### 3.5 Batch Processing (`batch_job.py`)

**Purpose**: Compute aggregate metrics that are expensive to calculate in real-time

**Metrics Computed**:

1. **Lifetime Value (LTV)**
   ```python
   total = sum(event['properties']['total'] 
               for event in events 
               if event['type'] == 'purchase')
   ```

2. **Engagement Score (0-100)**
   - Event activity (40 points)
   - Purchase behavior (30 points)
   - Recent activity (20 points)
   - Diversity of actions (10 points)

3. **Event Metrics**
   - Total event count
   - Unique event types
   - Event type distribution

4. **Time Metrics**
   - Days since first/last event
   - Customer lifetime (days)

5. **Product Metrics**
   - Products viewed/purchased
   - Category preferences

**When to Run**: 
- Nightly batch job (in production)
- On-demand (for this prototype)

---

### 3.6 Personalization API (`personalization_api.py`)

**Architecture: RAG (Retrieval-Augmented Generation)**

**Endpoints**:

1. `GET /personalize/{profile_id}`
   - Retrieves profile from MongoDB
   - Builds context-rich prompt
   - Calls Gemini API
   - Returns personalized offer

2. `GET /profile/{profile_id}`
   - Returns profile summary for debugging

**Prompt Engineering**:

```python
prompt = f"""
You are an expert marketing AI.

CUSTOMER PROFILE:
- Customer ID: {profile_id}
- Lifetime Value: ${ltv}
- Engagement: {engagement}/100
- Last Activity: {last_event}
- Products Viewed: {products}

YOUR TASK:
Create a personalized offer that matches their behavior.

Return ONLY valid JSON:
{{
  "offer_type": "upsell|cross-sell|loyalty|win-back",
  "title": "...",
  "message": "...",
  "products": [...],
  "discount": "..."
}}
"""
```

**Why Gemini?**
- Multimodal capabilities (future: product images)
- Fast inference
- Good at following JSON schema constraints
- Free tier for prototyping

---

## 4. Data Flow

### 4.1 New Customer Journey

```
Step 1: Anonymous Visit
───────────────────────
Event: {event_type: "page_view", identities: {deviceID: "device_123"}}
  │
  ├─► Flink receives event
  ├─► ProfileStitcher extracts deviceID
  ├─► Neo4j: Create Identity node + Profile node
  ├─► MongoDB: Create profile document
  │
Result: Profile created with anonymous identity


Step 2: User Logs In
──────────────────────
Event: {event_type: "login", identities: {deviceID: "device_123", email: "user@example.com"}}
  │
  ├─► ProfileStitcher extracts both identities
  ├─► Neo4j: Find profile by deviceID (exists!)
  │           Add email identity to SAME profile
  ├─► MongoDB: Add email to identities object
  │
Result: Profile now has 2 identities


Step 3: Login from Different Device
─────────────────────────────────────
Event: {event_type: "page_view", identities: {deviceID: "device_456"}}
  │
  ├─► New deviceID → Neo4j creates 2nd Profile
  │
Result: 2 separate profiles exist


Step 4: Login with Same Email (THE MERGE!)
────────────────────────────────────────────
Event: {event_type: "login", identities: {deviceID: "device_456", email: "user@example.com"}}
  │
  ├─► ProfileStitcher extracts identities
  ├─► Neo4j finds TWO profiles with these identities!
  │   │
  │   ├─► Profile A has: device_123, email
  │   └─► Profile B has: device_456
  │
  ├─► Neo4j MERGE:
  │   ├─► Keep Profile A
  │   ├─► Delete Profile B
  │   └─► Link all 3 identities to Profile A
  │
  ├─► MongoDB cleanup:
  │   └─► Delete orphaned Profile B document
  │
  ├─► MongoDB update Profile A:
  │   └─► identities: {email: "...", deviceID: ["device_123", "device_456"]}
  │
Result: Single unified profile with all identities!
```

---

### 4.2 ELT Pipeline Flow (Scheduled Every 5 Minutes)

```
APScheduler Triggers
  │
  ├─► 1. EXTRACT & LOAD (Ingestor.py)
  │   │
  │   ├─► Connect to MongoDB
  │   ├─► Fetch all profiles
  │   ├─► Drop PostgreSQL profiles_raw table
  │   ├─► Recreate table schema
  │   └─► Bulk insert profiles as JSONB
  │
  ├─► 2. TRANSFORM (dbt)
  │   │
  │   ├─► dbt run
  │   │   │
  │   │   ├─► stg_profiles.sql
  │   │   │   ├─► Parse JSONB event arrays
  │   │   │   ├─► Unnest to relational format
  │   │   │   └─► Clean and type-cast columns
  │   │   │
  │   │   └─► mart_computed_attributes.sql
  │   │       ├─► Calculate LTV (SUM purchase totals)
  │   │       ├─► Engagement Score (4 components):
  │   │       │   ├─► Event activity (max 40 pts)
  │   │       │   ├─► Purchase behavior (max 30 pts)
  │   │       │   ├─► Recency (max 20 pts)
  │   │       │   └─► Diversity (max 10 pts)
  │   │       ├─► Time metrics (days since first/last)
  │   │       └─► Product metrics (counts)
  │   │
  │   └─► dbt test (data quality validation)
  │
  ├─► 3. REVERSE ETL (Syncer.py)
  │   │
  │   ├─► Query mart_computed_attributes
  │   ├─► For each profile:
  │   │   └─► MongoDB UpdateOne:
  │   │       "$set": {
  │   │         "computed_attributes": { LTV, engagement, metrics }
  │   │       }
  │   └─► Bulk execute updates
  │
  └─► Job Complete → Wait 5 minutes → Repeat
```

**Why This Pattern?**
- **Separation of Concerns**: Extraction logic separate from transformation
- **SQL for Metrics**: More declarative, testable, and maintainable than Python
- **Reverse ETL**: Operational store (MongoDB) gets enriched data from warehouse
- **Scheduling**: Automated with APScheduler, graceful shutdown on SIGINT/SIGTERM

---

### 4.3 Personalization Flow

```
User Request: GET /personalize/profile_123
  │
  ├─► Fetch profile from MongoDB
  │   └─► Includes: identities, LTV, engagement, events, products, computed_attributes
  │
  ├─► Build prompt with customer context:
  │   "Customer has $1200 LTV, viewed laptops, engaged score 85..."
  │
  ├─► Call Gemini API (gemini-1.5-flash)
  │   └─► LLM generates personalized offer based on context
  │
  ├─► Parse JSON response
  │
  └─► Return to client
```

---

### 4.4 Graph Debugging Flow

```
Frontend Request: Inspect profile_123
  │
  ├─► GET /api/graph/cluster/profile_123
  │   │
  │   ├─► Neo4j Query:
  │   │   MATCH (p:Profile {master_profile_id: "profile_123"})
  │   │         -[:HAS_IDENTITY]->(i:Identity)
  │   │   RETURN p, i
  │   │
  │   └─► Return nodes + edges for visualization
  │
  ├─► GET /api/graph/explain/profile_123
  │   │
  │   ├─► Calculate ratios: email_count / device_count
  │   ├─► Send to Gemini AI with context
  │   └─► Return classification:
  │       ├─► single_user: Normal
  │       ├─► household: Normal (family)
  │       ├─► shared_device: Investigate
  │       └─► data_quality_issue: Fix needed
  │
  └─► Render in streamlit-agraph with color-coding
```

---

## 7. Fuzzy Identity Matching

### The Problem

Traditional identity resolution uses **exact matching**:
```
"john.doe@gmail.com" == "john.doe@gmail.com"  ✅
"john.doe@gmail.com" == "johndoe@gmail.com"   ❌
```

But real-world data has:
- **Typos**: `johndoe@gmial.com` vs `johndoe@gmail.com`
- **Format variations**: `(555) 123-4567` vs `555-123-4567`
- **Case differences**: `John.Doe@gmail.com` vs `john.doe@gmail.com`

### The Solution: APOC Fuzzy Matching

**Neo4jSink.java** implements an 11-step Cypher query with fuzzy matching:

```cypher
// Step 1: Find existing identities (exact match)
UNWIND $identities AS identity_map
MATCH (single_identity:Identity {type: identity_map.type, value: identity_map.value})

// Step 2: Find profiles via existing identities
OPTIONAL MATCH (single_identity)<-[:HAS_IDENTITY]-(exact_p:Profile)

// Step 3: FUZZY MATCH using APOC 🔍
OPTIONAL MATCH (other:Identity)
WHERE other.type = single_identity.type
  AND other <> single_identity
  AND apoc.text.fuzzyMatch(other.value, single_identity.value)
OPTIONAL MATCH (other)<-[:HAS_IDENTITY]-(fuzzy_p:Profile)

// Step 4: Collect all matching profiles
WITH identity_map, exact_p, collect(DISTINCT fuzzy_p) AS fuzzy_matches

// Step 5: Combine exact + fuzzy matches
WITH identity_map, 
     CASE WHEN exact_p IS NOT NULL 
          THEN [exact_p] + fuzzy_matches 
          ELSE fuzzy_matches 
     END AS all_matches
     
// Step 6: Deduplicate with APOC
WITH identity_map, apoc.coll.toSet(all_matches) AS unique_profiles

// Step 7: Sort by creation time (oldest profile wins)
WITH identity_map, apoc.coll.sortNodes(unique_profiles, 'created_at') AS sorted_profiles

// Steps 8-11: Merge/create profiles, link identities, return master_profile_id
```

### Fuzzy Matching Algorithm

**APOC `fuzzyMatch()` Function**:
- **Algorithm**: Levenshtein distance or similar
- **Returns**: Boolean (true if strings are "similar enough")
- **Use Cases**:
  - Email typos: `gmail.com` vs `gmial.com`
  - Phone formatting: `+1-555-123-4567` vs `15551234567`
  - Case variations: `JohnDoe` vs `johndoe`

**Example Matches**:
```
apoc.text.fuzzyMatch("john.doe@gmail.com", "johndoe@gmail.com") → true
apoc.text.fuzzyMatch("555-123-4567", "(555) 123-4567") → true  // After normalization
apoc.text.fuzzyMatch("totally@different.com", "other@email.com") → false
```

### Normalization + Fuzzy Matching

**Two-Layer Approach**:

1. **Normalization** (IdentityNormalizer.java):
   ```java
   // Before fuzzy matching
   email = email.toLowerCase().trim();
   phone = phone.replaceAll("[^0-9]", "");  // Remove formatting
   ```

2. **Fuzzy Matching** (Neo4jSink with APOC):
   - Even after normalization, catches typos and variations
   - More forgiving than exact match
   - Prevents duplicate profiles from minor differences

---

## 8. ELT Pipeline Architecture

**DBT Approach**:
- ✅ SQL-based transformations (declarative)
- ✅ Version controlled in Git
- ✅ Built-in testing framework
- ✅ Lineage and documentation

### dbt Project Structure

```
analytics/cdp_dbt_project/
├── dbt_project.yml          # Project config
├── packages.yml             # dbt-utils dependency
│
├── models/
│   ├── staging/
│   │   ├── sources.yml      # Source table definitions
│   │   └── stg_profiles.sql # Clean + structure raw data
│   │
│   └── marts/
│       ├── schema.yml       # Tests + documentation
│       └── mart_computed_attributes.sql  # Final metrics
│
└── tests/                   # Custom SQL tests
```

### Engagement Score Calculation

**SQL Logic** (mart_computed_attributes.sql):
```sql
LEAST(total_events * 5, 40) +  -- Event activity (max 40)

(CASE 
  WHEN lifetime_value > 1000 THEN 30 
  WHEN lifetime_value > 0 THEN 15 
  ELSE 0 
END) +  -- Purchase behavior (max 30)

(CASE 
  WHEN days_since_last < 1 THEN 20
  WHEN days_since_last < 7 THEN 10
  WHEN days_since_last < 30 THEN 5 
  ELSE 0 
END) +  -- Recency (max 20)

LEAST(unique_event_types * 2, 10) AS engagement_score  -- Diversity (max 10)
```

**Data Quality Test** (schema.yml):
```yaml
tests:
  - dbt_utils.expression_is_true:
      expression: ">= 0 and engagement_score <= 100"
```

### Benefits of ELT Approach

1. **Observability**: dbt logs show what transformed
2. **Testing**: Automated data quality checks
3. **Documentation**: Schema.yml generates docs site
4. **Modularity**: Staging → Marts separation
5. **Replayability**: Rerun transformations anytime
6. **Team Collaboration**: SQL is more accessible than Python for analysts

---

## 9. Technology Stack

### Why These Technologies?

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Apache Flink 1.18** | Stream processing | Exactly-once semantics, stateful processing, mature Java ecosystem |
| **Neo4j 5.13 + APOC** | Identity graph | Native graph DB, Cypher expressiveness, APOC fuzzy matching algorithms |
| **MongoDB** | Profile store | Flexible schema, JSONB arrays, fast document lookups, horizontal scaling |
| **PostgreSQL 15** | Analytics warehouse | SQL standard, ACID compliance, dbt ecosystem, reliable aggregations |
| **dbt 1.7** | Data transformation | SQL-based, version control friendly, testing framework, documentation |
| **APScheduler 3.10** | Job scheduling | Python-native, cron-like scheduling, graceful shutdown, simple API |
| **Docker Compose** | Orchestration | Multi-container setup, reproducible environments, easy local development |
| **FastAPI** | API framework | Modern Python, async support, automatic OpenAPI docs, type validation |
| **Google Gemini 1.5 Flash** | LLM | Fast inference, multimodal, good JSON structure following, free tier |
| **Streamlit** | Frontend | Rapid prototyping, Python-native, interactive widgets, agraph integration |
| **Python 3.13 / Java 17** | Languages | Latest features, async support (Python), modern Java syntax |

---

## 10. Data Consistency

### Consistency Model

**Neo4j ↔ MongoDB**:
- Eventually consistent
- Neo4j writes happen first (source of truth for identities)
- MongoDB updates follow (sync identities from graph)
- Cleanup jobs reconcile orphaned documents

**PostgreSQL ↔ MongoDB**:
- Batch reconciliation every 5 minutes
- PostgreSQL is read-only (no writes from API)
- MongoDB is operational store (serves API requests)
- Reverse ETL pattern: warehouse enriches operational data

### Conflict Resolution

**Identity Conflicts**:
- Neo4j graph merge determines winning profile (oldest created_at)
- MongoDB orphaned profiles deleted
- All identities consolidated under master_profile_id

**Metric Conflicts**:
- Batch job is authoritative (dbt-calculated metrics)
- MongoDB computed_attributes overwritten on each sync
- No concurrent writes to metrics (batch job has exclusive access)

---

## 11. Design Decisions

### Why Neo4j for Identity Resolution?

**Alternatives Considered**:
- Relational DB with self-joins: ❌ Complex queries, poor performance
- Document DB with embedded arrays: ❌ No traversal capabilities
- Dedicated ID resolution service: ❌ Overkill for prototype

**Neo4j Wins Because**:
- Graph queries are natural for "find connected identities"
- APOC provides fuzzy matching out-of-the-box
- Cypher is expressive and readable
- Performance scales with graph size

### Why ELT Instead of ETL?

**Decision**: Transform in warehouse (dbt) instead of Python

**Rationale**:
- SQL is declarative (what, not how)
- Data stays in warehouse longer (easier debugging)
- dbt provides testing/docs/lineage
- Analysts can contribute (SQL > Python for many teams)

### Why Reverse ETL?

**Decision**: Sync computed metrics back to MongoDB

**Rationale**:
- API needs fast reads (MongoDB is faster than PostgreSQL for key-value)
- Separation of OLTP (MongoDB) and OLAP (PostgreSQL)
- Batch job owns metric computation
- Operational store serves real-time requests

### Why APScheduler Over Airflow?

**Decision**: Simple scheduling with APScheduler

**Rationale**:
- Lightweight (no separate infrastructure)
- Python-native (easy to integrate)
- Good enough for single-machine deployment
- Future: Scale to Airflow/Prefect if needed

---

## 12. Future Enhancements

**Stream Processing**:
- [ ] Kafka integration (replace socket)
- [ ] Multiple Flink jobs for different event types
- [ ] Checkpointing and state recovery

**Identity Resolution**:
- [ ] ML-based fuzzy matching (train on labeled data)
- [ ] Configurable similarity thresholds
- [ ] Identity scoring (confidence levels)

**Analytics**:
- [ ] Real-time aggregations (Flink state)
- [ ] Predictive models (churn, LTV forecast)
- [ ] Time-series databases (InfluxDB, TimescaleDB)

**Activation**:
- [ ] Multi-channel personalization (email, push, SMS)
- [ ] A/B testing framework
- [ ] Campaign orchestration

**Governance**:
- [ ] GDPR compliance (right to be forgotten)
- [ ] Audit logs for all identity changes
- [ ] Data lineage visualization
- [ ] Access control and encryption

---

## 5. Technology Stack

### Why These Technologies?

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Apache Flink** | Stream processing | Industry standard, exactly-once processing, state management, Java ecosystem |
| **Neo4j** | Identity graph | Native graph DB, Cypher query language, ACID transactions, perfect for identity resolution |
| **MongoDB** | Profile store | Flexible schema, fast reads, rich querying, horizontal scaling |
| **Docker Compose** | Orchestration | Simple multi-container setup, reproducible environments, easy development |
| **FastAPI** | API framework | Modern Python, async support, automatic OpenAPI docs, type hints |
| **Google Gemini** | LLM | Multimodal, fast, good instruction following, free tier |
| **Gradle** | Build tool | Java standard, dependency management, shadow JAR for Flink |
---

## 8. Data Consistency

### Consistency Model

**Neo4j ↔ MongoDB**:
- Eventually consistent
- Neo4j writes happen first
- MongoDB updates follow
- Cleanup jobs reconcile

