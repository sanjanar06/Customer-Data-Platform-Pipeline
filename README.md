# CDP Prototype

## 🎯 Components

This **Customer Data Platform (CDP) Prototype** combines:
- **Stream Processing** (Apache Flink) for real-time data processing
- **Profile Store** (MongoDB) for storing customer profiles
- **Identity Graph** (Neo4j) for managing customer identity relationships
- **AI Agent** capabilities (FastAPI + Google Generative AI) for intelligent interactions

---

## 🏗️ Architecture Overview

```
┌─────────────────┐
│  Data Sources   │ (Future: Kafka, APIs, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Apache Flink (Stream Processing)  │
│   - JobManager (Port 8081)          │
│   - TaskManager (Processing)        │
└────────┬────────────────────────────┘
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   MongoDB    │  │    Neo4j     │  │  AI Agent    │
│  (Profiles)  │  │ (Identity    │  │  (FastAPI)   │
│  Port 27017  │  │   Graph)     │  │              │
│              │  │ Port 7474/   │  │              │
│              │  │      7687    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 📁 Project Structure

```
cdp-prototype/
├── README.md
├── .gitignore
├── .env
│
├── docker/
│   └── docker-compose.yml
│   
├── config/                      # Pydantic setup
│   ├── __init__.py
│   ├── settings.py              # Centralized configuration
│   ├── logging_config.py        # Logging setup
│   └── constants.py             # App constants
│
├── src/
│   ├── python/
│   │   ├── __init__.py
│   │   │
│   │   ├── common/              # Shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # DB connection managers
│   │   │   └── models.py        # Shared data models
│   │   │
│   │   ├── producer/            # Event producer
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── event_generator.py
│   │   │   └── socket_server.py
│   │   │
│   │   ├── batch/               # Batch processing
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── metrics_calculator.py
│   │   │   └── profile_processor.py
│   │   │
│   │   └── api/                 # Personalization API
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── routers/
│   │       │   ├── __init__.py
│   │       │   └── personalization.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── profile_service.py
│   │       │   └── ai_service.py
│   │       └── models/
│   │           ├── __init__.py
│   │           └── schemas.py
│   │
│   └── java/                    # Flink jobs
│       └── flink-jobs/
│           ├── build.gradle
│           ├── settings.gradle
│           ├── gradlew
│           └── src/
│               ├── main/java/com/cdp/
│               │   ├── config/
│               │   │   └── ConfigManager.java
│               │   ├── models/
│               │   │   └── CustomerEvent.java
│               │   ├── processors/
│               │   │   └── ProfileStitcher.java
│               │   ├── sinks/
│               │   │   ├── MongoSink.java
│               │   │   └── Neo4jSink.java
│               │   ├── sources/
│               │   │   └── EventSource.java
│               │   ├── jobs/
│               │   │   ├── SocketStreamJob.java
│               │   └── utils/
│               │       ├── DatabaseConnector.java
│               │       └── JsonParser.java
│               └── test/java/com/cdp/
│                   └── processors/
│                       └── ProfileStitcherTest.java
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_metrics_calculator.py
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
│   ├── setup.sh                 # Initial setup script
│   ├── start_services.sh        # Start all Docker services
│   ├── stop_services.sh         # Stop all services
│   ├── run_flink_job.sh         # Submit Flink job
│   ├── seed_data.sh             # Load test data
│   └── cleanup.sh               # Clean up resources
│
```

---

## 🔧 Components Explained

### 1. **Docker Compose Setup** (`docker-compose.yml`)

The infrastructure is containerized with 4 main services:

#### **MongoDB (Profile Store)**
- **Purpose**: Stores unified customer profile data (documents)
- **Port**: 27017
- **Credentials**: admin/password123
- **Use Case**: Fast read/write access to customer attributes, preferences, profiles
- **Example Data**: Customer name, email, preferences, purchase history

#### **Neo4j (Identity Graph)**
- **Purpose**: Manages customer identity relationships
- **Ports**: 
  - 7474 (Browser UI)
  - 7687 (Bolt protocol)
- **Credentials**: neo4j/password123
- **Use Case**: Links customer identities across devices, channels, and systems
- **Example Data**: Customer A (email) ←IDENTIFIED_AS→ Customer A (phone) ←PURCHASED→ Product X

#### **Apache Flink (Stream Processing)**
- **JobManager**: Coordinates jobs, Web UI on port 8081
- **TaskManager**: Executes data processing tasks
- **Purpose**: Real-time stream processing of customer events
- **Use Case**: Process events as they arrive, transform data, route to databases
- **Current Setup**: 
  - Python 3.10 installed
  - PyFlink extracted and configured
  - Protobuf installed for Python-Flink communication

---

### 2. **Python Dependencies** (`requirements.txt`)

#### **Database Connectivity**
- `pymongo==4.6.1` - MongoDB Python driver
- `neo4j==5.14.1` - Neo4j Python driver

#### **Stream Processing**
- `apache-flink==1.18.0` - Commented out (requires Python <3.11)
  - Note: PyFlink is bundled in the Flink Docker image instead

#### **AI Agent Stack**
- `fastapi==0.104.1` - Modern web framework for APIs
- `uvicorn==0.24.0` - ASGI server for FastAPI
- `google-generativeai==0.3.1` - Google's Generative AI (Gemini) integration
- `pydantic>=2.9.0` - Data validation (updated for Python 3.13)

#### **Utilities**
- `python-dotenv==1.0.0` - Environment variable management

---

### 3. **Job Submission Script** (`run_flink_job.sh`)

#### **What it does**:
1. Copies the Python job file into the Flink container
2. Submits the job to the Flink cluster
3. Provides instructions for monitoring

---

## 🔄 Data Flow

1. **Data Sources** → Kafka/APIs → **Flink** processes events
2. **Flink** → Writes to **MongoDB** (customer profiles)
3. **Flink** → Updates **Neo4j** (identity relationships)
4. **AI Agent** (FastAPI) → Queries both databases → Provides intelligent responses

---

## 📊 Service Access Points

| Service | URL/Port | Purpose |
|---------|----------|---------|
| MongoDB | localhost:27017 | Database connection |
| Neo4j Browser | http://localhost:7474 | Graph visualization |
| Neo4j Bolt | localhost:7687 | Database connection |
| Flink Dashboard | http://localhost:8081 | Job monitoring |
| Flink Socket | localhost:9000 | Future: Mock Kafka |

---

## 📚 Learning Resources

- **Flink**: https://flink.apache.org/docs/
- **PyFlink**: https://nightlies.apache.org/flink/flink-docs-master/docs/dev/python/
- **MongoDB**: https://www.mongodb.com/docs/
- **Neo4j**: https://neo4j.com/docs/
- **FastAPI**: https://fastapi.tiangolo.com/

---


