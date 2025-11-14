# CDP Prototype - Startup Commands Guide

This document contains all the commands needed to start, manage, and interact with your CDP Prototype.

---

## 🚀 Quick Start

### Start All Services
```bash
docker compose up -d
```

### Stop All Services
```bash
docker compose down
```

### View Service Status
```bash
docker compose ps
```

---

## 📦 Docker Compose Commands

### Start Services

#### Start in Background (Detached Mode)
```bash
docker compose up -d
```

#### Start with Logs Visible
```bash
docker compose up
```

#### Start Specific Services
```bash
docker compose up -d mongodb neo4j
docker compose up -d flink-jobmanager flink-taskmanager
```

### Stop Services

#### Stop All Services
```bash
docker compose down
```

#### Stop and Remove Volumes (⚠️ Deletes Data)
```bash
docker compose down -v
```

#### Stop Specific Services
```bash
docker compose stop mongodb
docker compose stop flink-jobmanager
```

### Restart Services

#### Restart All Services
```bash
docker compose restart
```

#### Restart Specific Service
```bash
docker compose restart mongodb
docker compose restart flink-jobmanager
docker compose restart flink-taskmanager
```

### View Logs

#### View All Logs
```bash
docker compose logs
```

#### View Logs for Specific Service
```bash
docker compose logs mongodb
docker compose logs neo4j
docker compose logs flink-jobmanager
docker compose logs flink-taskmanager
```

#### Follow Logs (Real-time)
```bash
docker compose logs -f
docker compose logs -f mongodb
docker compose logs -f flink-jobmanager
```

#### View Last N Lines
```bash
docker compose logs --tail=100 mongodb
docker compose logs --tail=50 flink-taskmanager
```

---

## 🗄️ MongoDB Commands

### Connect to MongoDB

#### Using mongosh (Inside Container)
```bash
docker exec -it cdp-mongodb mongosh -u admin -p password123
```

#### Using Python Script
```bash
python test_mongo.py
```

### MongoDB Operations

#### List Databases
```bash
docker exec cdp-mongodb mongosh -u admin -p password123 --eval "db.adminCommand('listDatabases')"
```

#### List Collections in a Database
```bash
docker exec cdp-mongodb mongosh -u admin -p password123 --eval "use cdp_test; db.getCollectionNames()"
```

#### Count Documents in Collection
```bash
docker exec cdp-mongodb mongosh -u admin -p password123 --eval "use cdp_test; db.test_collection.countDocuments()"
```

#### View Documents
```bash
docker exec cdp-mongodb mongosh -u admin -p password123 --eval "use cdp_test; db.test_collection.find().pretty()"
```

---

## 🕸️ Neo4j Commands

### Access Neo4j Browser
```
Open in browser: http://localhost:7474
Username: neo4j
Password: password123
```

### Connect to Neo4j

#### Using cypher-shell (Inside Container)
```bash
docker exec -it cdp-neo4j cypher-shell -u neo4j -p password123
```

#### Using Python Script
```bash
python test_neo4j.py
```

### Neo4j Operations

#### Run Cypher Query
```bash
docker exec cdp-neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) AS node_count"
```

#### View All Nodes
```bash
docker exec cdp-neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN n LIMIT 10"
```

#### View All Relationships
```bash
docker exec cdp-neo4j cypher-shell -u neo4j -p password123 "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10"
```

---

## ⚡ Flink Commands

### Access Flink Dashboard
```
Open in browser: http://localhost:8081
```

### Submit Flink Job

#### Using the Provided Script
```bash
./run_flink_job.sh
```

#### Manual Job Submission
```bash
# Copy job file to container
docker cp flink_hello_world.py cdp-flink-jobmanager:/opt/flink/

# Submit job
docker exec cdp-flink-jobmanager /opt/flink/bin/flink run \
    --python /opt/flink/flink_hello_world.py \
    --jobmanager localhost:8081
```

### Flink Job Management

#### List Running Jobs
```bash
docker exec cdp-flink-jobmanager /opt/flink/bin/flink list
```

#### Cancel a Job
```bash
docker exec cdp-flink-jobmanager /opt/flink/bin/flink cancel <job-id>
```

#### View Job Details
```bash
docker exec cdp-flink-jobmanager /opt/flink/bin/flink info <job-id>
```

### Flink Logs

#### View TaskManager Logs
```bash
docker logs cdp-flink-taskmanager
```

#### View JobManager Logs
```bash
docker logs cdp-flink-jobmanager
```

#### Follow TaskManager Logs
```bash
docker logs -f cdp-flink-taskmanager
```

---

## 🐍 Python Environment Commands

### Activate Virtual Environment
```bash
source venv/bin/activate
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Run Tests

#### Test MongoDB Connection
```bash
python test_mongo.py
```

#### Test Neo4j Connection
```bash
python test_neo4j.py
```

---

## 🔧 Container Management Commands

### Execute Commands in Containers

#### MongoDB Container
```bash
docker exec -it cdp-mongodb bash
```

#### Neo4j Container
```bash
docker exec -it cdp-neo4j bash
```

#### Flink JobManager Container
```bash
docker exec -it cdp-flink-jobmanager bash
```

#### Flink TaskManager Container
```bash
docker exec -it cdp-flink-taskmanager bash
```

### Check Container Status

#### View All Containers
```bash
docker ps
docker ps -a  # Include stopped containers
```

#### View Container Details
```bash
docker inspect cdp-mongodb
docker inspect cdp-flink-jobmanager
```

#### View Container Resource Usage
```bash
docker stats
docker stats cdp-mongodb
```

### Copy Files to/from Containers

#### Copy File to Container
```bash
docker cp flink_hello_world.py cdp-flink-jobmanager:/opt/flink/
```

#### Copy File from Container
```bash
docker cp cdp-flink-jobmanager:/opt/flink/flink_hello_world.py ./flink_hello_world_backup.py
```

---

## 🧹 Cleanup Commands

### Stop and Remove Containers
```bash
docker compose down
```

### Remove Containers and Volumes (⚠️ Deletes All Data)
```bash
docker compose down -v
```

### Remove All Containers, Networks, and Volumes
```bash
docker compose down -v --remove-orphans
```

### Remove Specific Volume
```bash
docker volume rm cdp-prototype_mongodb_data
docker volume rm cdp-prototype_neo4j_data
```

### Clean Up Unused Docker Resources
```bash
docker system prune
docker system prune -a  # Remove all unused images
```

---

## 🔍 Troubleshooting Commands

### Check Service Health

#### Check All Services
```bash
docker compose ps
```

#### Check Specific Service Logs
```bash
docker compose logs mongodb
docker compose logs neo4j
docker compose logs flink-jobmanager
```

### Network Diagnostics

#### Check Network Connectivity
```bash
docker network ls
docker network inspect cdp-prototype_cdp-network
```

#### Test Connection Between Containers
```bash
docker exec cdp-flink-jobmanager ping cdp-mongodb
docker exec cdp-flink-jobmanager ping cdp-neo4j
```

### Port Verification

#### Check if Ports are in Use
```bash
lsof -i :27017  # MongoDB
lsof -i :7474   # Neo4j Browser
lsof -i :7687   # Neo4j Bolt
lsof -i :8081   # Flink Dashboard
```

#### Check Port Mappings
```bash
docker port cdp-mongodb
docker port cdp-neo4j
docker port cdp-flink-jobmanager
```

### Python Environment Check

#### Check Python Version in Container
```bash
docker exec cdp-flink-jobmanager python --version
docker exec cdp-flink-taskmanager python --version
```

#### Check if PyFlink is Available
```bash
docker exec -e PYTHONPATH=/opt/flink/opt/python cdp-flink-taskmanager python -c "import pyflink; print('PyFlink available')"
```

#### Check Installed Python Packages
```bash
docker exec cdp-flink-jobmanager pip list
```

---

## 📊 Monitoring Commands

### View Resource Usage
```bash
docker stats
```

### View Disk Usage
```bash
docker system df
docker volume ls
```

### View Container Logs with Timestamps
```bash
docker compose logs -t mongodb
docker compose logs -t flink-jobmanager
```

---

## 🔄 Common Workflows

### Full Restart Workflow
```bash
# Stop all services
docker compose down

# Start all services
docker compose up -d

# Wait for services to be ready
sleep 10

# Check status
docker compose ps

# Test connections
python test_mongo.py
python test_neo4j.py
```

### Development Workflow
```bash
# Start services
docker compose up -d

# Activate virtual environment
source venv/bin/activate

# Run tests
python test_mongo.py
python test_neo4j.py

# Submit Flink job
./run_flink_job.sh

# Monitor logs
docker compose logs -f flink-taskmanager
```

### Clean Start Workflow (⚠️ Deletes All Data)
```bash
# Stop and remove everything
docker compose down -v

# Remove unused Docker resources
docker system prune -f

# Start fresh
docker compose up -d

# Wait for services
sleep 15

# Test connections
python test_mongo.py
python test_neo4j.py
```

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Start
docker compose up -d

# Stop
docker compose down

# Status
docker compose ps

# Logs
docker compose logs -f

# Test MongoDB
python test_mongo.py

# Test Neo4j
python test_neo4j.py

# Run Flink Job
./run_flink_job.sh

# Flink Dashboard
open http://localhost:8081

# Neo4j Browser
open http://localhost:7474
```

### Service URLs
- **MongoDB**: `mongodb://admin:password123@localhost:27017`
- **Neo4j Browser**: http://localhost:7474
- **Neo4j Bolt**: `bolt://localhost:7687`
- **Flink Dashboard**: http://localhost:8081

### Credentials
- **MongoDB**: `admin` / `password123`
- **Neo4j**: `neo4j` / `password123`

---

## 📝 Notes

1. **First Time Setup**: Run `docker compose up -d` and wait for all services to be healthy before running tests.

2. **Flink Jobs**: Make sure Flink containers are running before submitting jobs. Check with `docker compose ps`.

3. **Data Persistence**: Data is stored in Docker volumes. Use `docker compose down -v` only if you want to delete all data.

4. **Port Conflicts**: If ports are already in use, stop the conflicting services or modify ports in `docker-compose.yml`.

5. **Python Environment**: Always activate the virtual environment (`source venv/bin/activate`) before running Python scripts.

6. **Container Logs**: Use `docker compose logs -f` to follow logs in real-time for debugging.

---

## 🆘 Troubleshooting

### Services Won't Start
```bash
# Check if ports are available
lsof -i :27017 :7474 :7687 :8081

# Check Docker daemon
docker info

# Check container logs
docker compose logs
```

### Connection Issues
```bash
# Verify containers are running
docker compose ps

# Check network connectivity
docker network inspect cdp-prototype_cdp-network

# Test from inside container
docker exec cdp-flink-jobmanager ping cdp-mongodb
```

### Flink Job Fails
```bash
# Check TaskManager logs
docker logs cdp-flink-taskmanager

# Verify Python is installed
docker exec cdp-flink-taskmanager python --version

# Check PyFlink availability
docker exec -e PYTHONPATH=/opt/flink/opt/python cdp-flink-taskmanager python -c "import pyflink"
```

---

**Happy Coding! 🚀**

