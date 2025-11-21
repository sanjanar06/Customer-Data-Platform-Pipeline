# CDP Prototype with ELT Pipeline & Fuzzy Identity Matching

## 🎯 Components

This **Customer Data Platform (CDP) Prototype** combines:
- **Stream Processing** (Apache Flink) for real-time identity resolution with fuzzy matching
- **Profile Store** (MongoDB) for storing unified customer profiles
- **Identity Graph** (Neo4j) for identity stitching with fuzzy matching algorithms
- **Analytics Warehouse** (PostgreSQL) for metrics computation
- **Data Transformation** (dbt) for SQL-based metric calculations
- **ELT Pipeline** for automated batch processing and reverse ETL
- **AI-Powered Services** (FastAPI + Google Gemini) for personalization and graph diagnostics
- **Interactive Frontend** (Streamlit) for identity graph debugging and visualization

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                             │
│              (Socket Server, Future: Kafka)                  │
└────────────────────────┬─────────────────────────────────────┘
                         │ Real-time Events
                         ▼
┌──────────────────────────────────────────────────────────────┐
│           STREAM PROCESSING (Apache Flink)                   │
│  - Identity Normalization (email/phone)                      │
│  - Fuzzy Matching (APOC fuzzy text matching)                 │
│  - Profile Stitching & Graph Updates                         │
└─────────┬────────────────────────────────────┬───────────────┘
          │                                    │
          │ Neo4j Updates                      │ Profile Updates
          ▼                                    ▼
┌──────────────────────┐           ┌──────────────────────────┐
│   IDENTITY GRAPH     │           │   PROFILE STORE          │
│      (Neo4j)         │           │     (MongoDB)            │
│                      │           │                          │
│  - Profile nodes     │           │  - Unified profiles      │
│  - Identity nodes    │           │  - Event history         │
│  - Fuzzy matching    │           │  - Raw attributes        │
│  - APOC algorithms   │           │                          │
└──────────────────────┘           └────────┬─────────────────┘
                                            │
                                            │ ELT Pipeline (Scheduled)
                                            ▼
                    ┌────────────────────────────────────────┐
                    │   ANALYTICS WAREHOUSE (PostgreSQL)     │
                    │                                        │
                    │  MongoDB → profiles_raw → dbt          │
                    │  ├── Staging: stg_profiles             │
                    │  └── Marts: mart_computed_attributes   │
                    └────────┬───────────────────────────────┘
                             │ Reverse ETL (Computed Metrics)
                             ▼
                    ┌────────────────────┐
                    │    MongoDB         │
                    │  (computed_        │
                    │   attributes)      │
                    └────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
          ▼                                     ▼
┌──────────────────────┐           ┌──────────────────────────┐
│   ACTIVATION LAYER   │           │   DEBUGGING FRONTEND     │
│   (FastAPI)          │           │   (Streamlit)            │
│                      │           │                          │
│  - Personalization   │           │  - Graph visualization   │
│  - Graph operations  │           │  - Anomaly detection     │
│  - AI diagnostics    │           │  - Graph surgery tools   │
│  - Anomaly detection │           │  - AI cluster analysis   │
└──────────────────────┘           └──────────────────────────┘
```

---

## 📁 Project Structure

```
cdp-prototype/
├── README.md
├── .gitignore
├── .env
│
├── analytics/                   # dbt project for metrics
│   └── cdp_dbt_project/
│       ├── dbt_project.yml
│       ├── packages.yml         
│       ├── models/
│       │   ├── staging/
│       │   │   ├── sources.yml  # PostgreSQL raw tables
│       │   │   └── stg_profiles.sql
│       │   └── marts/
│       │       ├── schema.yml   # Tests & documentation
│       │       └── mart_computed_attributes.sql
│       └── logs/
│
├── docker/
│   └── docker-compose.yml       
│   
├── config/                      # Pydantic configuration
│   ├── __init__.py
│   ├── settings.py              # All environment settings
│   ├── logging_config.py
│   └── constants.py
│
├── frontend/                    # Streamlit graph debugger
│   └── app.py                   # Identity graph visualization
│
├── src/
│   ├── python/
│   │   ├── __init__.py
│   │   │
│   │   ├── common/              # Shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── database.py      
│   │   │   └── models.py        
│   │   │
│   │   ├── producer/            # Event producer : Future - Kafka
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── event_generator.py  
│   │   │   └── socket_server.py
│   │   │
│   │   ├── batch/               # ELT Pipeline
│   │   │   ├── __init__.py
│   │   │   ├── main.py          # Orchestrator
│   │   │   ├── ingestor.py      # MongoDB → PostgreSQL
│   │   │   ├── syncer.py        # PostgreSQL → MongoDB (Reverse ETL)
│   │   │   └── scheduler.py     # APScheduler job automation
│   │   │
│   │   └── api/                 # FastAPI server
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── routers/
│   │       │   ├── __init__.py
│   │       │   ├── personalization.py
│   │       │   └── graph_router.py      # Graph debugging endpoints
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── profile_service.py
│   │       │   ├── ai_service.py        # Gemini integration
│   │       │   └── graph_service.py     # Neo4j graph operations
│   │       └── models/
│   │           ├── __init__.py
│   │           └── schemas.py
│   │
│   └── java/                    # Flink stream processing
│       └── flink-jobs/
│           ├── build.gradle
│           ├── settings.gradle
│           ├── gradlew
│           └── src/
│               ├── main/java/com/cdp/
│               │   ├── config/
│               │   │   └── ConfigManager.java
│               │   ├── models/
│               │   │   └── CustomerEvent.java      # Event parsing
│               │   ├── processors/
│               │   │   └── ProfileStitcher.java    # Identity stitching
│               │   ├── sinks/
│               │   │   ├── MongoSink.java
│               │   │   └── Neo4jSink.java          # Fuzzy matching logic
│               │   ├── sources/
│               │   │   └── EventSource.java
│               │   ├── jobs/
│               │   │   └── SocketStreamJob.java
│               │   └── utils/
│               │       ├── DatabaseConnector.java
│               │       ├── JsonParser.java
│               │       └── IdentityNormalizer.java # Email/phone normalization
│               └── test/java/com/cdp/
│                   └── utils/
│                       └── IdentityNormalizationTest.java
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_event_generator.py
│   │   └── test_ai_service.py
│   │
│   └── integration/
│       ├── __init__.py
│       ├── test_mongodb_integration.py
│       ├── test_neo4j_integration.py
│       └── test_api_endpoints.py
│
├── scripts/
│   ├── setup.sh                 # Initial setup
│   ├── start_services.sh        # Start Docker services
│   ├── stop_services.sh         # Stop all services
│   ├── run_flink_job.sh         # Submit Flink job
│   ├── run_producer.py          # Event producer CLI
│   ├── run_api.py               # Start FastAPI server
│   ├── run_batch.py             # Run ELT pipeline once
│   ├── run_scheduler.py         # Start scheduled batch jobs
│   ├── simulate_hairball.py     # Test anomaly detection
│   ├── seed_data.sh             # Load test data
│   └── cleanup.sh               # Clean up resources
│
└── docs/
    ├── ARCHITECTURE.md          # System design documentation
    ├── API_DOCUMENTATION.md     # API reference
    └── SETUP.md                 # Installation guide
```

---

## 🔧 Components Explained

### 1. **Docker Compose Setup** (`docker-compose.yml`)

The infrastructure includes 5 main services:

#### **MongoDB (Profile Store)**
- **Purpose**: Stores unified customer profiles and event history
- **Port**: 27017
- **Credentials**: admin/password123
- **Collections**: 
  - `profiles` - Unified customer data with computed metrics
  - Event history stored as embedded documents

#### **Neo4j (Identity Graph with APOC)**
- **Purpose**: Identity resolution with fuzzy matching capabilities
- **Ports**: 7474 (Browser UI), 7687 (Bolt protocol)
- **Credentials**: neo4j/password123
- **Plugins**: APOC (Awesome Procedures On Cypher) for fuzzy text matching
- **Key Features**:
  - `apoc.text.fuzzyMatch()` for similarity detection
  - `apoc.coll.toSet()` for deduplication
  - Graph algorithms for identity stitching

#### **PostgreSQL 15 (Analytics Warehouse)**
- **Purpose**: Analytics database for dbt transformations
- **Port**: 5432
- **Credentials**: cdp_user/cdp_password
- **Database**: cdp_analytics
- **Schema**: 
  - `profiles_raw` - Raw data from MongoDB
  - `public_marts` - dbt-transformed metrics

#### **Apache Flink (Stream Processing)**
- **JobManager**: Coordinates jobs, Web UI on port 8081
- **TaskManager**: Executes data processing tasks
- **Purpose**: Real-time identity resolution and profile stitching
- **Key Features**:
  - Identity normalization (lowercase emails, formatted phones)
  - Fuzzy matching via Neo4j APOC
  - Stateful stream processing

---

### 2. **ELT Pipeline** (`src/python/batch/`)


#### **Ingestor** (`ingestor.py`)
- **Extract**: Reads profiles from MongoDB
- **Load**: Bulk inserts into PostgreSQL `profiles_raw` table
- **Pattern**: Full table refresh (drop/recreate)

#### **dbt Transformations** (`analytics/cdp_dbt_project/`)
- **Staging**: `stg_profiles.sql` - Cleans and structures raw data
- **Marts**: `mart_computed_attributes.sql` - Calculates metrics:
  - Lifetime Value (LTV) from purchase events
  - Engagement Score (0-100) with 4 components:
    - Event activity (max 40 points)
    - Purchase behavior (max 30 points)
    - Recency (max 20 points)
    - Diversity (max 10 points)
  - Time metrics (days since first/last event)
  - Product metrics (viewed/purchased counts)
- **Testing**: Data quality tests with dbt_utils

#### **Syncer** (`syncer.py`)
- **Reverse ETL**: Reads `mart_computed_attributes` from PostgreSQL
- **Load**: Bulk updates MongoDB `computed_attributes` field
- **Pattern**: Upsert with bulk operations

#### **Scheduler** (`scheduler.py`)
- **Automation**: APScheduler runs pipeline every 5 minutes
- **Features**: 
  - Graceful shutdown (SIGINT/SIGTERM handlers)
  - Prevents overlapping executions
  - Immediate first run, then interval-based

---

### 3. **Fuzzy Identity Matching** (`Neo4jSink.java`)

Cypher query for intelligent identity resolution:

```cypher
-- Step 1: Find existing identities (exact match)
-- Step 2: Find profiles via existing identities
-- Step 3: FUZZY MATCH using APOC
OPTIONAL MATCH (other:Identity)
WHERE other.type = single_identity.type
  AND other <> single_identity
  AND apoc.text.fuzzyMatch(other.value, single_identity.value)
```

**Fuzzy Matching Examples**:
- `john.doe@gmail.com` ≈ `johndoe@gmail.com`
- `(555) 123-4567` ≈ `555-123-4567`
- Handles typos, formatting differences, case variations

---

### 4. **Graph Debugging Frontend** (`frontend/app.py`)

Streamlit application with two modes:

#### **Profile Inspector**
- Enter profile ID to visualize identity cluster
- Interactive graph with `streamlit-agraph`
- Color-coded nodes (profiles vs identities)
- AI-powered cluster analysis via Gemini

#### **Graph Health Monitor**
- Detect anomaly patterns (hairballs):
  - Profiles with >5 emails
  - Profiles with >10 devices
- Graph surgery tools:
  - Detach identities from bad merges
  - Split profiles manually
  - Real-time graph updates

---

### 5. **AI Services** (`src/python/api/services/`)

#### **AIService** (`ai_service.py`)
- **Gemini Model**: gemini-1.5-flash
- **Capabilities**:
  - Personalized offer generation (RAG pattern)
  - Identity cluster diagnosis
  - Anomaly classification (Household/Shared Device/Fraud)

#### **GraphService** (`graph_service.py`)
- **Anomaly Detection**: Cypher queries for hairball patterns
- **Graph Surgery**: Split/merge operations
- **Cluster Retrieval**: Full subgraph extraction

---

### 6. **Event Producer Modes** (`producer/event_generator.py`)

Three simulation modes:

1. **Demo Mode** (default): Realistic customer journey
   - Anonymous → Login → Multi-device → Purchase
   
2. **Fuzzy Mode** (`--mode fuzzy`): Tests fuzzy matching
   - Slight variations in emails/phones
   - Case differences, formatting variations
   
3. **Hairball Mode** (`simulate_hairball.py`): Stress testing
   - 10 users from 1 shared device (library kiosk scenario)
   - Generates anomalies for detection testing

---

## 🔄 Data Flow

### Real-Time Stream Processing
```
Event Source (Socket)
    │
    ├─► Flink receives event
    ├─► Identity normalization (lowercase, format)
    ├─► Neo4j fuzzy matching & stitching
    ├─► MongoDB profile update
    └─► Event appended to history
```

### Batch ELT Pipeline (Every 5 minutes)
```
MongoDB profiles
    │
    ├─► Ingestor: Extract → Load to PostgreSQL
    ├─► dbt: Transform (staging → marts)
    │   ├─► Parse JSON event arrays
    │   ├─► Calculate engagement scores
    │   ├─► Compute LTV and metrics
    │   └─► Materialize mart_computed_attributes
    ├─► Syncer: Reverse ETL to MongoDB
    └─► computed_attributes field updated
```

### Personalization & Graph Debugging
```
API Request
    │
    ├─► MongoDB: Fetch unified profile
    ├─► Gemini AI: Generate personalized offer
    └─► Response to client

Frontend Request
    │
    ├─► Neo4j: Query identity cluster
    ├─► Graph visualization (streamlit-agraph)
    ├─► AI cluster analysis
    └─► Surgery operations (split/detach)
```

---

## 🚀 Quick Start

### 1. Setup
```bash
git clone https://github.com/sanjanar06/Customer-Data-Platform-Pipeline.git
cd Customer-Data-Platform-Pipeline
./scripts/setup.sh
```

### 2. Configure `.env`
```env
# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=password123

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# PostgreSQL (Analytics)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=cdp_user
POSTGRES_PASSWORD=cdp_password
POSTGRES_DB=cdp_analytics

# AI
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash

# Batch
BATCH_INTERVAL_MINUTES=5
```

### 3. Start Services
```bash
./scripts/start_services.sh
```

### 4. Run Components

#### A. Event Producer (Choose mode)
```bash
# Demo mode (realistic journey)
python scripts/run_producer.py

# Fuzzy matching mode
python scripts/run_producer.py --mode fuzzy

# Hairball anomaly mode
python scripts/simulate_hairball.py
```

#### B. Flink Stream Processing
```bash
./scripts/run_flink_job.sh
```

#### C. Batch ELT Scheduler
```bash
# Run once
python scripts/run_batch.py

# Or start scheduler (every 5 min)
python scripts/run_scheduler.py
```

#### D. API Server
```bash
python scripts/run_api.py
# Access: http://localhost:8000/docs
```

#### E. Frontend Debugger
```bash
streamlit run frontend/app.py
# Access: http://localhost:8501
```

---

## 📊 Service Access Points

| Service | URL/Port | Purpose |
|---------|----------|---------|
| MongoDB | localhost:27017 | Profile database |
| Neo4j Browser | http://localhost:7474 | Graph visualization |
| Neo4j Bolt | localhost:7687 | Database connection |
| PostgreSQL | localhost:5432 | Analytics warehouse |
| Flink Dashboard | http://localhost:8081 | Job monitoring |
| FastAPI Docs | http://localhost:8000/docs | API documentation |
| Streamlit UI | http://localhost:8501 | Graph debugger |

---

## 🏗️ Key Features

### ✅ Identity Resolution
- **Exact matching**: Email, phone, deviceID, userID
- **Fuzzy matching**: APOC text similarity for typos/variations
- **Normalization**: Lowercase, trim, format standardization
- **Multi-identity**: Same customer across devices/channels

### ✅ Profile Unification
- **Real-time stitching**: Flink streams update Neo4j graph
- **Automatic merging**: Shared identities trigger profile consolidation
- **Event history**: Complete audit trail preserved
- **Computed metrics**: Engagement, LTV, product preferences

### ✅ ELT Pipeline
- **SQL-based metrics**: dbt replaces Python calculators
- **Reverse ETL**: Computed metrics sync back to MongoDB
- **Scheduled execution**: APScheduler automation (5-minute intervals)
- **Data quality**: dbt tests validate metric ranges

### ✅ Graph Debugging
- **Visual inspection**: Interactive D3-based graph visualization
- **Anomaly detection**: Hairball pattern identification
- **AI diagnostics**: Gemini classifies cluster types
- **Graph surgery**: Manual split/detach operations
- **Health monitoring**: Real-time anomaly dashboard

### ✅ AI Personalization
- **RAG pattern**: Retrieve profile → Augment context → Generate offer
- **Context-aware**: Uses LTV, engagement, event history
- **Offer types**: Welcome, cross-sell, upsell, loyalty, win-back
- **Reasoning**: Explains recommendation logic

---

## 📚 Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System design, data flows, technical decisions
- **[API Documentation](docs/API_DOCUMENTATION.md)**: Endpoint reference, schemas, examples
- **[Setup Guide](docs/SETUP.md)**: Detailed installation and configuration

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Stream Processing | Apache Flink 1.18 | Real-time event processing |
| Identity Graph | Neo4j 5.13 + APOC | Fuzzy matching & stitching |
| Profile Store | MongoDB | Unified customer profiles |
| Analytics | PostgreSQL 15 | Metrics warehouse |
| Transformation | dbt 1.7 | SQL-based transformations |
| Batch Jobs | APScheduler 3.10 | ELT automation |
| API | FastAPI | REST endpoints |
| Frontend | Streamlit | Graph debugging UI |
| AI | Google Gemini 1.5 Flash | Personalization & diagnostics |
| Language | Python 3.13 / Java 17 | Runtime environments |

---


