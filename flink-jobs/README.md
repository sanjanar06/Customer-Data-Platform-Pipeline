# CDP Flink Jobs

Java-based Apache Flink jobs for the Customer Data Platform.

## Prerequisites

- Java 11 or higher
- Gradle 7.0 or higher (or use Gradle Wrapper)
- Docker and Docker Compose (for running Flink cluster)

## Project Structure

```
flink-jobs/
├── build.gradle              # Gradle build configuration
├── settings.gradle           # Gradle settings
├── src/
│   └── main/
│       └── java/
│           └── com/
│               └── cdp/
│                   └── HelloWorldJob.java
└── build/                    # Generated files (gitignored)
    └── libs/                 # Generated JAR files
```

## Building

### Build JAR file
```bash
gradle clean shadowJar
```

Or using Gradle Wrapper (recommended):
```bash
./gradlew clean shadowJar
```

This will create a fat JAR file in the `build/libs/` directory:
- `flink-jobs-1.0-all.jar` - Fat JAR with all dependencies

### Build tasks
```bash
# Clean build directory
gradle clean

# Build JAR (regular)
gradle jar

# Build fat JAR (includes all dependencies)
gradle shadowJar

# Run tests
gradle test

# Build without tests
gradle clean shadowJar -x test
```

## Running Jobs

### Using the script (recommended)
```bash
# From project root
./run_flink_job.sh
```

### Manual submission
```bash
# 1. Build JAR
cd flink-jobs
gradle clean shadowJar

# 2. Copy JAR to Flink container
docker cp build/libs/flink-jobs-1.0-all.jar cdp-flink-jobmanager:/opt/flink/

# 3. Submit job
docker exec cdp-flink-jobmanager /opt/flink/bin/flink run \
    /opt/flink/flink-jobs-1.0-all.jar
```

## Available Jobs

### HelloWorldJob
Simple "Hello World" job that demonstrates Flink connectivity.

**Run it:**
```bash
./run_flink_job.sh
```

**Check output:**
```bash
docker logs cdp-flink-taskmanager
```

## Adding New Jobs

1. Create a new Java class in `src/main/java/com/cdp/`
2. Implement the `main` method with your Flink job logic
3. Update `build.gradle` if you need additional dependencies
4. Update the `mainClass` in `build.gradle` if you want to change the default entry point
5. Build and submit as above

### Example Job Structure
```java
package com.cdp;

import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

public class MyNewJob {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = 
            StreamExecutionEnvironment.getExecutionEnvironment();
        
        // Your Flink job logic here
        
        env.execute("My New Job");
    }
}
```

## Dependencies

All Flink dependencies are included in the build. The `shadowJar` task creates a fat JAR that includes all necessary dependencies, so you can submit it directly to the Flink cluster.

### Adding New Dependencies

Edit `build.gradle` and add to the `dependencies` block:

```gradle
dependencies {
    // Existing dependencies...
    
    // Your new dependency
    implementation 'group:artifact:version'
}
```

## Gradle Wrapper (Recommended)

The Gradle Wrapper ensures everyone uses the same Gradle version. To set it up:

```bash
# Generate wrapper files
gradle wrapper --gradle-version 8.5

# Or use the latest version
gradle wrapper
```

Then use `./gradlew` instead of `gradle`:
```bash
./gradlew clean shadowJar
```

## Troubleshooting

### Gradle not found
```bash
# macOS
brew install gradle

# Linux
sudo apt-get install gradle

# Or use Gradle Wrapper (recommended)
# It will download Gradle automatically
```

### Build fails
- Ensure Java 11+ is installed: `java -version`
- Ensure Gradle is installed: `gradle -version`
- Check that Flink containers are running: `docker compose ps`
- Try cleaning first: `gradle clean`

### Job submission fails
- Check Flink cluster is running: `docker compose ps`
- Check Flink dashboard: http://localhost:8081
- Check container logs: `docker logs cdp-flink-jobmanager`
- Verify JAR was copied: `docker exec cdp-flink-jobmanager ls -la /opt/flink/`

### JAR file not found
- Check build output: `ls -la build/libs/`
- Ensure `shadowJar` task completed successfully
- The JAR should be named `flink-jobs-*-all.jar`

## Development Tips

1. **Use IDE**: Import this as a Gradle project in IntelliJ IDEA or Eclipse
2. **Local testing**: You can test Flink jobs locally before deploying to cluster
3. **Logging**: Use SLF4J for logging (already configured)
4. **Debugging**: Check Flink dashboard at http://localhost:8081 for job details
5. **Gradle Daemon**: Gradle uses a daemon for faster builds (runs in background)

## Gradle vs Maven

This project uses Gradle instead of Maven for:
- More concise build files
- Better dependency management
- Faster incremental builds
- More flexible build configuration
- Better IDE integration
