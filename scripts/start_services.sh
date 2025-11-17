#!/bin/bash
# Start All Docker Services

set -e

echo "=========================================="
echo "Starting CDP Docker Services"
echo "=========================================="

cd docker

# Start services
echo "Starting services..."
docker-compose up -d

echo ""
echo "=========================================="
echo "✅ Services Started!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - MongoDB: localhost:27017"
echo "  - Neo4j Browser: http://localhost:7474"
echo "  - Flink Dashboard: http://localhost:8081"
echo ""
echo "Check status: docker-compose ps"
echo "View logs: docker-compose logs -f [service-name]"
echo "Stop services: ./scripts/stop_services.sh"
echo ""
