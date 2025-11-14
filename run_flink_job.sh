#!/bin/bash
# Day 4: Script to build and submit Flink job to Docker cluster
# Default: SocketStreamJob that connects to host.docker.internal:9000

# Allow overriding main class (default: SocketStreamJob)
FLINK_CLASS="${FLINK_CLASS:-com.cdp.SocketStreamJob}"
# Allow overriding socket host/port via env
SOCKET_HOST="${SOCKET_HOST:-cdp-flink-jobmanager}"
SOCKET_PORT="${SOCKET_PORT:-9000}"

echo "=================================================="
echo "Building and Submitting Flink Job..."
echo "Class: $FLINK_CLASS"
if [ "$FLINK_CLASS" = "com.cdp.SocketStreamJob" ]; then
    echo "Socket config: $SOCKET_HOST:$SOCKET_PORT"
fi
echo "=================================================="

# Check if Gradle is installed
if ! command -v gradle &> /dev/null; then
    echo "❌ Gradle is not installed!"
    echo "Please install Gradle:"
    echo "  - macOS: brew install gradle"
    echo "  - Linux: sudo apt-get install gradle"
    echo "  - Or use Gradle Wrapper: ./gradlew (will download automatically)"
    echo "  - Or download from: https://gradle.org/install/"
    exit 1
fi

# Build shadow JAR (bundle non-Flink dependencies)
echo "🔨 Building shadow JAR with Gradle (bundles DB drivers)..."
cd flink-jobs

# Use gradle wrapper if available, otherwise use system gradle
if [ -f "./gradlew" ]; then
    echo "Using Gradle Wrapper..."
    chmod +x ./gradlew
    ./gradlew clean shadowJar
else
    echo "Using system Gradle..."
    gradle clean shadowJar
fi

if [ $? -ne 0 ]; then
    echo "❌ Gradle build failed!"
    exit 1
fi

# Prefer the shadow/all JAR which bundles our DB drivers
JAR_FILE=$(find build/libs -name "flink-jobs-*-all.jar" | head -1)

if [ -z "$JAR_FILE" ]; then
    # Fallback: pick a regular jar if the all-jar isn't available
    JAR_FILE=$(find build/libs -name "flink-jobs-*.jar" | grep -v "sources" | grep -v "javadoc" | head -1)
fi

if [ -z "$JAR_FILE" ]; then
    echo "❌ JAR file not found!"
    echo "Expected location: build/libs/flink-jobs-*-all.jar"
    exit 1
fi

echo "✅ JAR file built: $JAR_FILE"

# Copy JAR to container
echo "📁 Copying JAR to container..."
docker cp "$JAR_FILE" cdp-flink-jobmanager:/opt/flink/flink-jobs.jar

# Submit the job using Flink
echo "🚀 Submitting job to Flink cluster..."

# Run command varies by class
if [ "$FLINK_CLASS" = "com.cdp.SocketStreamJob" ]; then
    # For SocketStreamJob: pass host/port as program args
    docker exec -e SOCKET_HOST="$SOCKET_HOST" -e SOCKET_PORT="$SOCKET_PORT" \
        cdp-flink-jobmanager /opt/flink/bin/flink run -d \
        -c "$FLINK_CLASS" /opt/flink/flink-jobs.jar
else
    # For other jobs: run without special args
    docker exec cdp-flink-jobmanager /opt/flink/bin/flink run -d \
        -c "$FLINK_CLASS" /opt/flink/flink-jobs.jar
fi

echo ""
echo "=================================================="
echo "Job submitted! Check the Flink Dashboard:"
echo "http://localhost:8081"
echo ""
echo "To see output, check TaskManager logs:"
echo "docker logs cdp-flink-taskmanager"
echo "=================================================="
