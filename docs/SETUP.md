# CDP Setup Guide

## Prerequisites

### Required Software
- **Python 3.10+** - For Python services
- **Java 17+** - For Flink jobs
- **Docker & Docker Compose** - For infrastructure
- **Gradle** - For building Flink jobs (or use included wrapper)

### Optional Tools
- **MongoDB Compass** - GUI for MongoDB
- **Neo4j Desktop** - GUI for Neo4j
- **Postman/Insomnia** - API testing

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
- Install all dependencies
- Create `.env` file from template
- Verify configuration

### 2. Configure Environment

Edit `.env` file with your configuration:

```env
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=password123

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Gemini AI
GEMINI_API_KEY=your_api_key_here

# API
API_PORT=8000
```

Get a Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Start Infrastructure

```bash
# Start all Docker services (development mode)
./scripts/start_services.sh dev

# Or for production
./scripts/start_services.sh prod
```

This starts:
- MongoDB (port 27017)
- Neo4j (port 7474, 7687)
- Flink JobManager (port 8081)
- Flink TaskManager
- Mongo Express (dev only, port 8082)

### 4. Verify Services

Check that all services are running:

```bash
cd docker
docker-compose ps
```

Access web interfaces:
- Flink Dashboard: http://localhost:8081
- Neo4j Browser: http://localhost:7474 (user: neo4j, pass: password123)
- Mongo Express: http://localhost:8082 (dev mode only)

### 5. Run Event Producer

```bash
# Activate virtual environment
source venv/bin/activate

# Run producer (sends demo events)
python scripts/run_producer.py
```

Or with the script:
```bash
./scripts/seed_data.sh
```

### 6. Submit Flink Job

```bash
# Build and submit the Flink job
./scripts/run_flink_job.sh
```

This compiles the Java code and submits `SocketStreamJob` to Flink.


### 7. Run Batch Job

After events are processed:

```bash
# Compute customer metrics
python scripts/run_batch.py
```

### 8. Start API Server

```bash
# Start personalization API
python scripts/run_api.py
```

Access API:
- API Docs: http://localhost:8000/docs
- Personalize: http://localhost:8000/api/personalize/{profile_id}

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run only unit tests
pytest tests/unit/

# Run only integration tests (requires services running)
pytest tests/integration/ -m integration
```