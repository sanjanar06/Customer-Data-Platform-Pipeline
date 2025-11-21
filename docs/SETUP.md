# CDP Setup Guide

## Prerequisites

### Required Software
- **Python 3.13+** - For Python services (batch, API, frontend)
- **Java 17+** - For Flink stream processing jobs
- **Docker & Docker Compose** - For infrastructure (MongoDB, Neo4j, Flink, PostgreSQL)
- **Gradle** - For building Flink jobs (or use included wrapper)
- **dbt** - For data transformations (installed via pip)

### Optional Tools
- **MongoDB Compass** - GUI for MongoDB
- **Neo4j Desktop** - GUI for Neo4j (or use browser at localhost:7474)
- **DBeaver** - PostgreSQL GUI clients
- **Postman** - API testing
- **VS Code** - Recommended editor with Python and Java extensions

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/sanjanar06/Customer-Data-Platform-Pipeline.git
cd Customer-Data-Platform-Pipeline

# Run setup script
./scripts/setup.sh
```

This script will:
- Create Python virtual environment
- Install all dependencies (including dbt, APScheduler, Streamlit)
- Create `.env` file from template
- Verify configuration
- Install dbt packages (dbt-utils)

### 2. Configure Environment

Edit `.env` file with your configuration:

```env
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# MongoDB (Profile Store)
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=password123
MONGO_DB=cdp

# Neo4j (Identity Graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# PostgreSQL (Analytics Warehouse)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cdp_analytics
POSTGRES_USER=cdp_user
POSTGRES_PASSWORD=cdp_password

# Gemini AI
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Batch Processing
BATCH_INTERVAL_MINUTES=5

# Event Producer
PRODUCER_PORT=9001
PRODUCER_HOST=0.0.0.0

# Flink Configuration
FLINK_JOBMANAGER_HOST=localhost
FLINK_JOBMANAGER_PORT=8081
```

Get a Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Start Infrastructure

```bash
# Start all Docker services
./scripts/start_services.sh

# Or start specific services
cd docker
docker-compose up -d mongo neo4j postgres flink-jobmanager flink-taskmanager
```

This starts:
- MongoDB (port 27017) - Profile store
- Neo4j (ports 7474, 7687) - Identity graph with APOC
- PostgreSQL (port 5432) - Analytics warehouse
- Flink JobManager (port 8081) - Stream processing coordinator
- Flink TaskManager - Processing execution

### 4. Verify Services

Check that all services are running:

```bash
cd docker
docker-compose ps
```

All services should show status "Up". Access web interfaces:
- **Flink Dashboard**: http://localhost:8081
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, pass: password123)
- **MongoDB**: Use MongoDB Compass or CLI (mongodb://admin:password123@localhost:27017)
- **PostgreSQL**: Use pgAdmin or CLI (psql -h localhost -U cdp_user -d cdp_analytics)

### 5. Initialize dbt Project

```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Navigate to dbt project
cd analytics/cdp_dbt_project

# Install dbt dependencies
dbt deps

# Test dbt connection
dbt debug

# Create PostgreSQL schema (if needed)
dbt run-operation create_schema

# Verify setup
dbt compile
```
### 6. Run Components

Choose which components to run based on your use case:

#### A. Event Producer (Generate Test Data)

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Option 1: Demo mode (realistic customer journey)
python scripts/run_producer.py

# Option 2: Fuzzy matching mode (test similarity algorithms)
python scripts/run_producer.py --mode fuzzy

# Option 3: Hairball mode (anomaly testing)
python scripts/simulate_hairball.py
```

#### B. Flink Stream Processing

```bash
# Build and submit Flink job
./scripts/run_flink_job.sh
```

Monitor the job at http://localhost:8081

#### C. Batch ELT Pipeline

```bash
# Option 1: Run batch job once
python scripts/run_batch.py

# Option 2: Start scheduler (runs every 5 minutes)
python scripts/run_scheduler.py
```

The batch pipeline:
1. Extracts profiles from MongoDB
2. Loads into PostgreSQL `profiles_raw`
3. Runs dbt transformations (staging → marts)
4. Syncs computed metrics back to MongoDB

#### D. FastAPI Server

```bash
# Start API server
python scripts/run_api.py
```

Access:
- **API Documentation**: http://localhost:8000/docs
- **Personalization endpoint**: http://localhost:8000/api/personalize/{profile_id}
- **Graph endpoints**: http://localhost:8000/api/graph/

#### E. Streamlit Frontend

```bash
# Start Streamlit debugger
streamlit run frontend/app.py
```

Access at http://localhost:8501

Features:
- **Profile Inspector**: Visualize identity clusters
- **Graph Health**: Detect and fix anomalies
- **AI Analysis**: Get cluster insights from Gemini
- **Graph Surgery**: Manual split/detach operations

---

## Running Tests

### Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_event_generator.py
```

### Integration Tests

**Prerequisite**: All Docker services must be running

```bash
# Run integration tests
pytest tests/integration/

# Specific integration tests
pytest tests/integration/test_mongodb_integration.py
pytest tests/integration/test_neo4j_integration.py
pytest tests/integration/test_api_endpoints.py
```

### dbt Tests

```bash
# Navigate to dbt project
cd analytics/cdp_dbt_project

# Run dbt tests
dbt test

# Test specific model
dbt test --models mart_computed_attributes

# Run tests with verbose output
dbt test --debug
```

---

## Complete Workflow

### End-to-End Testing

```bash
# 1. Start all infrastructure
./scripts/start_services.sh

# 2. Generate events (in separate terminal)
python scripts/run_producer.py

# 3. Submit Flink job
./scripts/run_flink_job.sh

# 4. Wait for events to process (check Flink dashboard)

# 5. Run batch ELT once
python scripts/run_batch.py

# 6. Start API server (in separate terminal)
python scripts/run_api.py

# 7. Start frontend (in separate terminal)
streamlit run frontend/app.py

# 8. Test in frontend
# - Navigate to http://localhost:8501
# - Use Profile Inspector to view identity clusters
# - Check Graph Health for anomalies
```

### Testing Fuzzy Matching

```bash
# 1. Ensure Flink job is running
./scripts/run_flink_job.sh

# 2. Generate fuzzy test events
python scripts/run_producer.py --mode fuzzy

# 3. Check Neo4j Browser
# Navigate to http://localhost:7474
# Run: MATCH (p:Profile)-[r:HAS_IDENTITY]->(i:Identity) RETURN p, r, i

# 4. Verify fuzzy matches in Streamlit
streamlit run frontend/app.py
# Look for profiles with similar but not identical emails/phones
```

### Testing Anomaly Detection

```bash
# 1. Generate hairball scenario
python scripts/simulate_hairball.py

# 2. Run batch pipeline to compute metrics
python scripts/run_batch.py

# 3. Check anomalies via API
curl "http://localhost:8000/api/graph/anomalies?email_threshold=3"

# 4. View in Streamlit Graph Health tab
streamlit run frontend/app.py
# Navigate to "Graph Health" tab
# See detected anomalies and perform surgery if needed
```

---

## Troubleshooting

### Common Issues

#### Flink Job Won't Submit

**Problem**: `./scripts/run_flink_job.sh` fails

**Solutions**:
```bash
# 1. Check Flink is running
docker-compose ps flink-jobmanager flink-taskmanager

# 2. Check Flink logs
docker-compose logs flink-jobmanager

# 3. Rebuild Java code
cd src/java/flink-jobs
./gradlew clean build shadowJar

# 4. Verify JAR was created
ls build/libs/flink-jobs-1.0-SNAPSHOT-all.jar
```

#### dbt Connection Failed

**Problem**: `dbt debug` shows connection error

**Solutions**:
```bash
# 1. Verify PostgreSQL is running
docker-compose ps postgres

# 2. Test connection manually
psql -h localhost -U cdp_user -d cdp_analytics

# 3. Check environment variables
echo $POSTGRES_HOST
echo $POSTGRES_USER

# 4. Verify dbt profiles.yml
cd analytics/cdp_dbt_project
cat ~/.dbt/profiles.yml

# 5. Recreate profiles.yml if needed
dbt init cdp_dbt_project
```

#### MongoDB Connection Refused

**Problem**: API or batch jobs can't connect to MongoDB

**Solutions**:
```bash
# 1. Check MongoDB is running
docker-compose ps mongo

# 2. Test connection
mongosh mongodb://admin:password123@localhost:27017

# 3. Check logs
docker-compose logs mongo

# 4. Restart MongoDB
docker-compose restart mongo
```

#### Neo4j APOC Plugin Missing

**Problem**: Fuzzy matching doesn't work, errors mentioning `apoc.text.fuzzyMatch`

**Solutions**:
```bash
# 1. Verify APOC is installed
# Open Neo4j Browser (http://localhost:7474)
# Run: CALL dbms.procedures() YIELD name WHERE name CONTAINS 'apoc'

# 2. Check docker-compose.yml includes:
NEO4J_PLUGINS: '["apoc"]'

# 3. Restart Neo4j
docker-compose restart neo4j

# 4. Check logs
docker-compose logs neo4j | grep -i apoc
```

#### Streamlit Frontend Not Loading

**Problem**: http://localhost:8501 won't load

**Solutions**:
```bash
# 1. Check if port is in use
lsof -i :8501

# 2. Kill existing process
kill -9 <PID>

# 3. Run with different port
streamlit run frontend/app.py --server.port 8502

# 4. Check dependencies
pip install streamlit streamlit-agraph pandas requests
```

#### Batch Job Fails

**Problem**: `python scripts/run_batch.py` throws errors

**Solutions**:
```bash
# 1. Check all databases are accessible
python -c "from src.python.common.database import MongoContext, Neo4jContext; print('OK')"

# 2. Verify PostgreSQL tables exist
psql -h localhost -U cdp_user -d cdp_analytics -c "\dt"

# 3. Run ingestor separately
python -c "from src.python.batch.ingestor import MongoToPostgresIngestor; i = MongoToPostgresIngestor(); i.run()"

# 4. Run dbt separately
cd analytics/cdp_dbt_project
dbt run

# 5. Check logs
cat logs/batch.log
```

#### Java Build Fails

**Problem**: Gradle build errors

**Solutions**:
```bash
# 1. Verify Java version
java -version  # Should be Java 17+

# 2. Clean and rebuild
cd src/java/flink-jobs
./gradlew clean
./gradlew build --refresh-dependencies

# 3. Check for missing dependencies
./gradlew dependencies

# 4. Use wrapper if gradlew doesn't work
gradle clean build shadowJar
```

---

## Configuration Reference

### Docker Compose Services

| Service | Port(s) | Purpose | Healthcheck |
|---------|---------|---------|-------------|
| mongo | 27017 | Profile store | mongosh connection test |
| neo4j | 7474, 7687 | Identity graph | HTTP health endpoint |
| postgres | 5432 | Analytics warehouse | pg_isready command |
| flink-jobmanager | 8081 | Flink coordinator | HTTP API check |
| flink-taskmanager | - | Processing | Heartbeat to jobmanager |

### Python Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup.sh` | Initial setup | First time setup |
| `start_services.sh` | Start Docker | Every session start |
| `stop_services.sh` | Stop Docker | Clean shutdown |
| `run_producer.py` | Generate events | Testing, demos |
| `run_flink_job.sh` | Submit Flink job | After code changes |
| `run_batch.py` | Run ELT once | Manual execution |
| `run_scheduler.py` | Auto batch | Production-like mode |
| `run_api.py` | Start FastAPI | API testing |
| `simulate_hairball.py` | Create anomalies | Anomaly detection testing |

### Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `BATCH_INTERVAL_MINUTES`: How often batch pipeline runs (default: 5)
- `GEMINI_MODEL`: AI model to use (default: gemini-1.5-flash)
- `DEFAULT_EMAIL_THRESHOLD`: Max emails per profile for anomaly detection (default: 5)
- `DEFAULT_DEVICE_THRESHOLD`: Max devices per profile for anomaly detection (default: 10)

---

## Next Steps

After successful setup:

1. **Read Architecture**: Review `docs/ARCHITECTURE.md` for system design
2. **Check API Docs**: Visit `docs/API_DOCUMENTATION.md` for endpoint reference
3. **Explore Code**: Start with `src/java/flink-jobs/src/main/java/com/cdp/sinks/Neo4jSink.java` for fuzzy matching logic
4. **Run E2E Test**: Follow the complete workflow above
5. **Customize**: Modify event schemas, add new identity types, tune fuzzy matching thresholds

---

## Uninstall

```bash
# Stop and remove all containers
cd docker
docker-compose down -v

# Remove Python virtual environment
cd ..
rm -rf venv

# Remove dbt artifacts
cd analytics/cdp_dbt_project
rm -rf target/ logs/ dbt_packages/

# Remove logs
rm -rf logs/
```