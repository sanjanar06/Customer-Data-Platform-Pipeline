#!/bin/bash
# Submit Flink Job to Cluster

set -e

# Configuration
FLINK_CLASS="${FLINK_CLASS:-com.cdp.jobs.SocketStreamJob}"
SOCKET_HOST="${SOCKET_HOST:-jobmanager}"
SOCKET_PORT="${SOCKET_PORT:-9001}"

echo "=========================================="
echo "Building and Submitting Flink Job"
echo "=========================================="
echo "Class: $FLINK_CLASS"
if [ "$FLINK_CLASS" = "com.cdp.jobs.SocketStreamJob" ]; then
    echo "Socket: $SOCKET_HOST:$SOCKET_PORT"
fi
echo ""

# Navigate to Flink jobs directory
cd "$(dirname "$0")/../src/java/flink-jobs"

# Build shadow JAR
echo "Building shadow JAR..."
if [ -f "./gradlew" ]; then
    chmod +x ./gradlew
    ./gradlew clean shadowJar
else
    gradle clean shadowJar
fi

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Find the JAR file
JAR_FILE=$(find build/libs -name "*-all.jar" | head -1)

if [ -z "$JAR_FILE" ]; then
    echo "❌ JAR file not found!"
    exit 1
fi

echo "✅ Build complete: $JAR_FILE"
echo ""

# Submit to Flink
echo "Submitting to Flink cluster..."

# Check if running in Docker
if [ -f "/.dockerenv" ]; then
    FLINK_BIN="flink"
    JAR_PATH="$JAR_FILE"
else
    # Copy JAR to a location accessible by Docker container
    DOCKER_JAR_PATH="/tmp/$(basename $JAR_FILE)"
    docker cp "$JAR_FILE" "cdp-flink-jobmanager:$DOCKER_JAR_PATH"
    FLINK_BIN="docker exec cdp-flink-jobmanager flink"
    JAR_PATH="$DOCKER_JAR_PATH"
fi

$FLINK_BIN run \
    --class "$FLINK_CLASS" \
    "$JAR_PATH" \
    --host "$SOCKET_HOST" \
    --port "$SOCKET_PORT"

echo ""
echo "=========================================="
echo "✅ Job Submitted!"
echo "=========================================="
echo ""
echo "View jobs: http://localhost:8081"
echo ""
