# Customer Data Platform (CDP) Prototype

A real-time Customer Data Platform built with Apache Flink, MongoDB, and Neo4j for stream processing, profile management, and identity resolution.

## 🎯 Overview

This project is a learning prototype that demonstrates the core concepts of a Customer Data Platform:

- **Real-time Stream Processing**: Apache Flink processes customer events as they arrive
- **Profile Store**: MongoDB stores unified customer profiles with attributes and event history
- **Identity Graph**: Neo4j manages identity stitching across multiple customer touchpoints
- **AI-Powered Personalization**: FastAPI + Google Gemini for personalized recommendations

## 🏗️ Architecture

```
┌─────────────────┐
│  Data Producer  │ (Python Socket Server)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Apache Flink (Stream Processing)  │
│   - JobManager (Port 8081)          │
│   - TaskManager (Processing)        │
│   - ProfileStitcher (Java)          │
└────────┬────────────────────────────┘
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   MongoDB    │  │    Neo4j     │  │  FastAPI     │
│  (Profiles)  │  │ (Identity    │  │  (AI Agent)  │
│  Port 27017  │  │   Graph)     │  │              │
│              │  │ Port 7474/   │  │              │
│              │  │      7687    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 📁 Project Structure

```
cdp-prototype/
├── docker-compose.yml          # Infrastructure orchestration
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── PROJECT_OVERVIEW.md        # Detailed project documentation
├── STARTUP_COMMANDS.md        # Docker and service management commands
├── neo4j_cypher.md           # Neo4j query reference
│
├── producer.py                # Event producer (sends events to Flink)
├── batch_job.py              # Batch processing job for metrics computation
├── personalization_api.py    # FastAPI AI personalization service
├── test_mongo.py             # MongoDB connectivity test
├── test_neo4j.py             # Neo4j connectivity test
├── run_flink_job.sh          # Script to build and submit Flink jobs
│
└── flink-jobs/               # Apache Flink Java jobs
    ├── build.gradle          # Gradle build configuration
    ├── settings.gradle       # Gradle settings
    ├── gradlew              # Gradle wrapper
    └── src/main/java/com/cdp/
        ├── HelloWorldJob.java       # Simple Flink test job
        ├── SocketStreamJob.java     # Socket stream consumer
        └── ProfileStitcher.java     # Identity stitching processor
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Java 17+ (for building Flink jobs)
- Gradle (or use included Gradle wrapper)

### 1. Start Infrastructure

```bash
# Start all services (MongoDB, Neo4j, Flink)
docker compose up -d

# Verify services are running
docker compose ps
```

### 2. Test Database Connectivity

```bash
# Test MongoDB
python test_mongo.py

# Test Neo4j
python test_neo4j.py
```

### 3. Run Stream Processing Pipeline

```bash
# Terminal 1: Start the event producer
python producer.py

# Terminal 2: Build and submit Flink job
./run_flink_job.sh
```

### 4. Run Batch Processing

```bash
# Compute aggregate metrics on customer profiles
python batch_job.py
```

### 5. Start AI Personalization API

```bash
# Install dependencies
pip install -r requirements.txt

# Set Gemini API key (optional - will use mock data if not set)
export GEMINI_API_KEY="your-api-key-here"

# Start the API
uvicorn personalization_api:app --reload

# Access at http://localhost:8000/docs
```

## 🔍 Key Components

### Event Producer (`producer.py`)
Simulates customer events and sends them to Flink via socket connection:
- Page views
- User logins
- Add to cart events
- Purchase events

### Profile Stitcher (`ProfileStitcher.java`)
Core Flink processor that:
1. Extracts identities from incoming events
2. Stitches identities in Neo4j graph
3. Updates unified profiles in MongoDB
4. Handles profile merging across devices

### Batch Job (`batch_job.py`)
Computes aggregate metrics:
- Lifetime value (LTV)
- Engagement scores
- Event metrics
- Product interactions
- Time-based metrics

### Personalization API (`personalization_api.py`)
AI-powered personalization using RAG pattern:
- Retrieves customer profile from MongoDB
- Augments context with profile data
- Generates personalized offers using Gemini AI
- Returns structured JSON responses

## 🌐 Service URLs

- **Flink Web UI**: http://localhost:8081
- **Neo4j Browser**: http://localhost:7474
- **MongoDB**: localhost:27017
- **Personalization API**: http://localhost:8000

## 📊 Example Queries

### Neo4j: View Identity Graph
```cypher
MATCH (p:Profile)-[r:HAS_IDENTITY]->(i:Identity) 
RETURN p, r, i
```

### MongoDB: View Customer Profiles
```javascript
db.profiles.find().pretty()
```

## 🛠️ Development

### Build Flink Jobs

```bash
cd flink-jobs
./gradlew clean shadowJar

cd ..
./run_flink_job.sh
```

### View Logs

```bash
# View all service logs
docker compose logs -f

# View specific service
docker compose logs -f flink-jobmanager
docker compose logs -f mongodb
docker compose logs -f neo4j
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove all data
docker compose down -v
```

## 📚 Learning Resources

See `PROJECT_OVERVIEW.md` for detailed component explanations and architecture details.

See `STARTUP_COMMANDS.md` for comprehensive Docker management commands.

See `neo4j_cypher.md` for Neo4j query examples and identity stitching logic.

## 🔐 Default Credentials

- **MongoDB**: admin / password123
- **Neo4j**: neo4j / password123

⚠️ **Note**: These are development credentials only. Never use in production!

## 🤝 Contributing

This is a personal learning project, but feel free to fork and experiment!

---

**Built with** ❤️ **for learning Customer Data Platforms**
