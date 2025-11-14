# CDP Prototype - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Deep Dive](#component-deep-dive)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Decisions](#design-decisions)

---

## 1. System Overview

### What is a Customer Data Platform (CDP)?

A Customer Data Platform is a packaged software that creates a persistent, unified customer database accessible to other systems. This prototype implements the core CDP capabilities:

1. **Data Ingestion**: Collect events from multiple sources
2. **Identity Resolution**: Stitch together customer identities across devices/channels
3. **Profile Unification**: Create a single view of each customer
4. **Segmentation**: Compute metrics and segment customers
5. **Activation**: Use unified profiles for personalization

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                            │
│                    (Simulated via producer.py)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ Events via Socket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STREAM PROCESSING LAYER                      │
│                       (Apache Flink)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SocketStreamJob.java                                    │  │
│  │  Receives events → ProfileStitcher.java → Processes      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────┬─────────────────────────────────────────┬──────────────┘
         │                                         │
         │ Identity Stitching                      │ Profile Updates
         ▼                                         ▼
┌──────────────────────┐                 ┌──────────────────────┐
│   IDENTITY GRAPH     │                 │   PROFILE STORE      │
│      (Neo4j)         │◄────────────────┤     (MongoDB)        │
│                      │   Queries       │                      │
│  Manages:            │                 │  Stores:             │
│  - Profile nodes     │                 │  - Unified profiles  │
│  - Identity nodes    │                 │  - All identities    │
│  - Relationships     │                 │  - Event history     │
│  - Graph traversal   │                 │  - Computed metrics  │
└──────────────────────┘                 └──────┬───────────────┘
                                                 │
                                                 │ Profile Retrieval
                                                 ▼
                                        ┌──────────────────────┐
                                        │   BATCH PROCESSING   │
                                        │   (batch_job.py)     │
                                        │                      │
                                        │  Computes:           │
                                        │  - LTV               │
                                        │  - Engagement        │
                                        │  - Segments          │
                                        └──────────────────────┘
                                                 │
                                                 │ Enriched Profiles
                                                 ▼
                                        ┌──────────────────────┐
                                        │  ACTIVATION LAYER    │
                                        │ (personalization_    │
                                        │      api.py)         │
                                        │                      │
                                        │  RAG Pattern:        │
                                        │  1. Retrieve profile │
                                        │  2. Augment context  │
                                        │  3. Generate AI      │
                                        └──────────────────────┘
```

---

## 2. Architecture Patterns

### 2.1 Lambda Architecture (Simplified)

This CDP implements a simplified Lambda Architecture:

- **Speed Layer (Real-time)**: Flink processes events as they arrive
- **Batch Layer**: batch_job.py computes aggregate metrics periodically
- **Serving Layer**: MongoDB serves unified profiles to applications

### 2.2 Event-Driven Architecture

- Events are the source of truth
- All state changes are derived from events
- Event history is preserved for audit and reprocessing

### 2.3 Polyglot Persistence

Different databases for different purposes:

| Database | Purpose | Why This DB? |
|----------|---------|--------------|
| **Neo4j** | Identity graph | Graph queries for identity resolution, efficient for relationship traversal |
| **MongoDB** | Profile store | Flexible schema for evolving customer attributes, fast document retrieval |

### 2.4 RAG Pattern (Retrieval-Augmented Generation)

The personalization API uses RAG:

1. **Retrieve**: Fetch customer profile from MongoDB
2. **Augment**: Build context-rich prompt with profile data
3. **Generate**: LLM creates personalized content

---

## 3. Component Deep Dive

### 3.1 Event Producer (`producer.py`)

**Purpose**: Simulate customer events for testing

**Key Features**:
- Socket server that sends JSON events to Flink
- Predefined event sequence demonstrating identity stitching
- Supports both demo mode (realistic sequence) and random mode

**Event Schema**:
```json
{
  "event_type": "page_view | login | add_to_cart | purchase",
  "identities": {
    "deviceID": "device_abc123",
    "email": "user@example.com"
  },
  "properties": {
    "page": "/products/laptop",
    "product_name": "MacBook Pro",
    "price": 1299.99
  },
  "timestamp": 1234567890,
  "sequence": 1
}
```

**Why Socket Connection?**
- Simple for prototyping
- In production, would use Kafka, Kinesis, or Pub/Sub
- Flink has native socket source connector

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

#### HelloWorldJob.java

**Purpose**: Simple test job to verify Flink cluster connectivity

**Usage**: First job to run when setting up the environment

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

**Why Not Real-time?**
- Complex aggregations across entire event history
- Not latency-sensitive (daily is fine)
- Reduces load on stream processing

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

### 4.2 Batch Processing Flow

```
Nightly Job Triggers
  │
  ├─► Connect to MongoDB
  ├─► Fetch all profiles
  │
  ├─► For each profile:
  │   │
  │   ├─► Compute LTV from purchase events
  │   ├─► Compute engagement score
  │   ├─► Compute time metrics
  │   ├─► Compute product metrics
  │   │
  │   └─► Update profile with computed_attributes
  │
  └─► Job complete
```

---

### 4.3 Personalization Flow

```
User Request: GET /personalize/profile_123
  │
  ├─► Fetch profile from MongoDB
  │   └─► Includes: identities, LTV, engagement, events, products
  │
  ├─► Build prompt with customer context:
  │   "Customer has $1200 LTV, viewed laptops, engaged score 85..."
  │
  ├─► Call Gemini API
  │   └─► LLM generates personalized offer based on context
  │
  ├─► Parse JSON response
  │
  └─► Return to client
```

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

## 6. Design Decisions

### 6.1 Why Java for Flink Jobs?

**Decision**: Use Java instead of PyFlink

**Reasoning**:
- Better Flink ecosystem support (more connectors)
- Production systems typically use Java Flink
- Better performance for stateful operations
- Easier to package dependencies (shadow JAR)

**Tradeoff**:
- More verbose than Python
- Requires Java/Gradle knowledge

---

### 6.2 Why Socket Source Instead of Kafka?

**Decision**: Use socket source for events

**Reasoning**:
- Simpler for learning/prototyping
- No need to run Kafka cluster
- Demonstrates Flink sources without infrastructure complexity

**Production Alternative**:
```java
// Would use Kafka:
FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(
    "customer-events", 
    new SimpleStringSchema(), 
    kafkaProps
);
```

---

### 6.3 Why Two Databases?

**Decision**: Use both Neo4j AND MongoDB instead of one DB

**Reasoning**:

**Neo4j for Identity Graph**:
- Identity resolution is a graph problem
- Need to traverse relationships efficiently
- "Find all profiles connected by shared identities" = graph query
- Trying to do this in SQL or document DB is painful

**MongoDB for Profiles**:
- Need fast lookups by master_profile_id
- Customer attributes are flexible/nested
- Don't need graph queries for profile data
- Event history is append-only (good for documents)

**Why Not One DB?**:
- Neo4j is overkill for simple profile retrieval
- MongoDB can't efficiently model identity graph
- Polyglot persistence: right tool for right job

---

### 6.4 Event Sourcing vs State Snapshots

**Decision**: Store event history in MongoDB

**Reasoning**:
- Allows recomputation of metrics (batch job)
- Audit trail of customer actions
- Can replay events if business logic changes

**Tradeoff**:
- Storage overhead (events accumulate)
- Could implement event log compaction later

---

### 6.5 Identity Stitching Strategy

**Decision**: Neo4j is source of truth for identities, MongoDB syncs from it

**Alternative Considered**: MongoDB as source of truth

**Why Neo4j Wins**:
```
Scenario: User logs in from 2 devices

MongoDB Approach:
  1. Find profiles with this email (query)
  2. Find profiles with these devices (query)
  3. Merge documents in application code
  4. Handle race conditions
  5. Complex business logic

Neo4j Approach:
  1. Single Cypher query
  2. Graph naturally represents relationships
  3. MERGE operation is atomic
  4. Returns all connected identities
  5. Simple, declarative
```

---

## 7. Scalability Considerations

### Current Limitations (Prototype)

1. **Single Flink TaskManager**: Limited parallelism
2. **No Kafka**: Socket source doesn't scale
3. **No partitioning**: All events processed sequentially
4. **MongoDB single node**: No sharding
5. **Neo4j single node**: No clustering

### Production Scaling Path

```
1. Replace socket with Kafka
   - Partitioned topics
   - Multiple producers
   - Exactly-once semantics

2. Scale Flink
   - Multiple TaskManagers
   - State partitioning by customer ID
   - Checkpointing to S3

3. Scale Neo4j
   - Causal clustering
   - Read replicas
   - Sharding by master_profile_id

4. Scale MongoDB
   - Replica sets
   - Sharding by master_profile_id
   - Read preference to secondaries

5. Add caching layer
   - Redis for hot profiles
   - Reduce DB load
```

---

## 8. Data Consistency

### Consistency Model

**Neo4j ↔ MongoDB**:
- Eventually consistent
- Neo4j writes happen first
- MongoDB updates follow
- Cleanup jobs reconcile

**Handling Inconsistencies**:

```java
// ProfileStitcher ensures sync:
cleanupOrphanedProfiles(masterProfileId, allIdentities);
```

This deletes MongoDB profiles that should have been merged based on Neo4j state.

### Why Not Distributed Transactions?

**Decision**: No 2-phase commit between Neo4j and MongoDB

**Reasoning**:
- Adds complexity and latency
- CDP can tolerate eventual consistency
- Idempotent operations make retries safe
- Cleanup jobs fix drift

---

## 9. Monitoring & Observability

### Current State (Prototype)

**Logging**:
```java
System.out.println("✅ Stitched identities → master_profile_id: " + masterProfileId);
```

### Production Requirements

1. **Metrics**:
   - Events processed per second
   - Profile merge rate
   - API latency
   - Database query performance

2. **Logging**:
   - Structured logs (JSON)
   - Log aggregation (ELK, Splunk)
   - Correlation IDs

3. **Tracing**:
   - Distributed tracing (Jaeger)
   - End-to-end event flow

4. **Alerting**:
   - Data quality issues
   - Processing lag
   - Database errors

---

## 10. Security Considerations

### Current State (Prototype)

⚠️ **Development credentials only!**
```yaml
NEO4J_AUTH: neo4j/password123
MONGO_INITDB_ROOT_PASSWORD: password123
```

### Production Requirements

1. **Secrets Management**:
   - Vault, AWS Secrets Manager
   - No hardcoded credentials

2. **Network Security**:
   - Private VPC
   - No public database access
   - TLS for all connections

3. **Data Privacy**:
   - PII encryption at rest
   - PII masking in logs
   - GDPR compliance (right to delete)

4. **Authentication/Authorization**:
   - API authentication (OAuth)
   - Role-based access control
   - Audit logs

---

## Summary

This CDP prototype demonstrates:

✅ **Real-time stream processing** with Flink
✅ **Identity resolution** using graph database
✅ **Profile unification** across devices/channels  
✅ **Batch analytics** for computed metrics
✅ **AI-powered activation** using RAG pattern

The architecture is production-ready in design but simplified for learning. Each component can be scaled independently.

**Next Steps**:
1. Add Kafka for durable event streaming
2. Implement proper monitoring/alerting  
3. Add data quality checks
4. Implement GDPR compliance (deletion, export)
5. Add more activation channels (email, push notifications)
