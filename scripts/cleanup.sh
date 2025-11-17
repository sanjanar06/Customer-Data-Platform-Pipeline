#!/bin/bash
# Cleanup Resources

set -e

echo "=========================================="
echo "Cleaning Up CDP Resources"
echo "=========================================="

echo "Stopping Docker services..."
cd docker
docker-compose down -v

echo ""
echo "Removing Python cache and build artifacts..."
cd ..
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

echo "Removing Java build artifacts..."
cd src/java/flink-jobs
if [ -f "./gradlew" ]; then
    ./gradlew clean
else
    gradle clean 2>/dev/null || true
fi

cd ../../..

echo ""
echo "=========================================="
echo "✅ Cleanup Complete!"
echo "=========================================="
echo ""
echo "To start fresh:"
echo "1. ./scripts/setup.sh"
echo "2. ./scripts/start_services.sh"
echo ""
