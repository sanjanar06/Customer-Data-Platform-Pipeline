# CDP Prototype - Project Overview

## 🎯 What You've Built

You've created a **Customer Data Platform (CDP) Prototype** that combines:
- **Stream Processing** (Apache Flink) for real-time data processing
- **Profile Store** (MongoDB) for storing customer profiles
- **Identity Graph** (Neo4j) for managing customer identity relationships
- **AI Agent** capabilities (FastAPI + Google Generative AI) for intelligent interactions

This is a modern, scalable architecture for handling customer data in real-time.

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
├── docker-compose.yml          # Infrastructure orchestration
├── requirements.txt            # Python dependencies
├── test_mongo.py              # MongoDB connectivity test
├── test_neo4j.py              # Neo4j connectivity test
├── flink_hello_world.py       # PyFlink sample job
├── run_flink_job.sh           # Script to submit Flink jobs
└── venv/                      # Python virtual environment
```

---

## 🔧 Components Explained

### 1. **Docker Compose Setup** (`docker-compose.yml`)

Your infrastructure is containerized with 4 main services:

#### **MongoDB (Profile Store)**
- **Purpose**: Stores customer profile data (documents)
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

### 3. **Testing Scripts**

#### **`test_mongo.py`** - MongoDB Connectivity Test
- **What it does**:
  - Connects to MongoDB
  - Creates a test database (`cdp_test`)
  - Inserts a test document
  - Reads it back
  - Verifies connectivity

- **Run it**: `python test_mongo.py`

#### **`test_neo4j.py`** - Neo4j Connectivity Test
- **What it does**:
  - Connects to Neo4j
  - Creates a test node (`TestPerson`)
  - Queries the graph
  - Verifies connectivity

- **Run it**: `python test_neo4j.py`
- **View in Browser**: http://localhost:7474

---

### 4. **Flink Job** (`flink_hello_world.py`)

#### **What it does**:
- Creates a Flink streaming environment
- Generates a simple data stream from a list
- Prints each element (outputs to TaskManager logs)
- Demonstrates PyFlink connectivity

#### **Key Concepts**:
- **StreamExecutionEnvironment**: Flink's execution context
- **from_collection()**: Creates a stream from a Python list
- **print()**: Outputs stream elements
- **execute()**: Starts the job

#### **Run it**: `./run_flink_job.sh`

---

### 5. **Job Submission Script** (`run_flink_job.sh`)

#### **What it does**:
1. Copies the Python job file into the Flink container
2. Submits the job to the Flink cluster
3. Provides instructions for monitoring

#### **Steps**:
```bash
# 1. Copy job to container
docker cp flink_hello_world.py cdp-flink-jobmanager:/opt/flink/

# 2. Submit job
docker exec cdp-flink-jobmanager /opt/flink/bin/flink run \
    --python /opt/flink/flink_hello_world.py \
    --jobmanager localhost:8081
```

---

## 🔄 Data Flow (Current State)

### Current Flow:
1. **Flink Job** processes data (currently from a static list)
2. **Output** goes to TaskManager logs (via `print()`)

### Future Flow (What You Can Build):
1. **Data Sources** → Kafka/APIs → **Flink** processes events
2. **Flink** → Writes to **MongoDB** (customer profiles)
3. **Flink** → Updates **Neo4j** (identity relationships)
4. **AI Agent** (FastAPI) → Queries both databases → Provides intelligent responses

---

## 🚀 How to Use Your Project

### 1. **Start All Services**
```bash
docker compose up -d
```

### 2. **Check Service Status**
```bash
docker compose ps
```

### 3. **Test MongoDB**
```bash
python test_mongo.py
```

### 4. **Test Neo4j**
```bash
python test_neo4j.py
# Then visit: http://localhost:7474
```

### 5. **Run Flink Job**
```bash
./run_flink_job.sh
# Check dashboard: http://localhost:8081
# Check logs: docker logs cdp-flink-taskmanager
```

### 6. **View Service Logs**
```bash
docker compose logs mongodb
docker compose logs neo4j
docker compose logs flink-jobmanager
docker compose logs flink-taskmanager
```

### 7. **Stop Services**
```bash
docker compose down
```

---

## 🎓 Key Concepts You've Learned

### 1. **Containerization**
- Docker Compose orchestrates multiple services
- Each service runs in isolation
- Services communicate via a shared network

### 2. **Stream Processing**
- Flink processes data in real-time
- Jobs can be written in Python (PyFlink)
- Jobs run distributed across TaskManagers

### 3. **Data Storage**
- **MongoDB**: Document store for flexible, JSON-like data
- **Neo4j**: Graph database for relationship-heavy data

### 4. **Infrastructure as Code**
- `docker-compose.yml` defines your entire stack
- Reproducible, version-controlled infrastructure

---

## 🔮 Next Steps (What You Can Build)

### 1. **Real Data Sources**
- Connect Kafka for event streaming
- Add API connectors for external data
- Set up file watchers for batch imports

### 2. **Flink Jobs**
- Process customer events in real-time
- Enrich data from multiple sources
- Route events to appropriate databases
- Aggregate metrics and statistics

### 3. **Identity Resolution**
- Use Neo4j to link customer identities
- Match emails, phones, device IDs
- Build customer identity graphs

### 4. **AI Agent**
- Build FastAPI endpoints
- Query MongoDB for customer profiles
- Query Neo4j for relationships
- Use Google Generative AI for insights
- Provide personalized recommendations

### 5. **Data Pipeline**
```
Events → Flink → MongoDB (Profiles)
                ↓
            Neo4j (Relationships)
                ↓
            AI Agent → Insights
```

---

## 🛠️ Technical Challenges You Solved

1. **Python 3.13 Compatibility**
   - Updated `pydantic` to version 2.9.0+
   - Commented out `apache-flink` (requires Python <3.11)
   - Used PyFlink from Flink Docker image instead

2. **Flink Python Support**
   - Installed Python 3.10 in Flink containers
   - Extracted PyFlink zip file
   - Set PYTHONPATH for Python module discovery
   - Installed protobuf for Python-Flink communication

3. **Docker Compose Configuration**
   - Configured multi-service orchestration
   - Set up persistent volumes
   - Created shared network
   - Added health checks

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

## 🎯 Project Status

✅ **Completed**:
- Docker infrastructure setup
- MongoDB connectivity
- Neo4j connectivity
- Flink cluster setup
- PyFlink job execution
- Python environment configuration

🚧 **In Progress**:
- Flink job execution (working on PyFlink module discovery)

🔮 **Future**:
- Real-time event processing
- Identity resolution logic
- AI agent implementation
- Data pipeline integration

---

## 💡 Key Takeaways

1. **Modern CDP Architecture**: You've built a foundation for a scalable customer data platform
2. **Stream Processing**: Flink enables real-time data processing
3. **Multi-Database Strategy**: MongoDB for profiles, Neo4j for relationships
4. **Containerization**: Docker makes deployment and scaling easier
5. **Python Integration**: Everything can be controlled and extended with Python

---

## 📚 Learning Resources

- **Flink**: https://flink.apache.org/docs/
- **PyFlink**: https://nightlies.apache.org/flink/flink-docs-master/docs/dev/python/
- **MongoDB**: https://www.mongodb.com/docs/
- **Neo4j**: https://neo4j.com/docs/
- **FastAPI**: https://fastapi.tiangolo.com/

---

**Congratulations!** You've built a solid foundation for a Customer Data Platform. 🎉

