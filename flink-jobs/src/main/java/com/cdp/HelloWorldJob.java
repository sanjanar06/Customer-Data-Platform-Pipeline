package com.cdp;

import java.util.Arrays;
import java.util.List;

import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

/**
 * Day 3: Flink "Hello, World!" Job
 * The simplest possible Flink job to verify cluster connectivity.
 * 
 * This is the Java equivalent of the Python flink_hello_world.py job.
 */
public class HelloWorldJob {
    
    public static void main(String[] args) throws Exception {
        // Create the execution environment
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // Set parallelism to 1 for simpler output
        env.setParallelism(1);
        
        // Create a simple data source from a list
        List<String> data = Arrays.asList(
            "Hello from Flink Java!",
            "Day 3 test is working!",
            "Streaming job running on Docker cluster.",
            "This proves local -> Flink connectivity!",
            "Ready for real streaming logic!"
        );
        
        // Create a data stream from the collection
        DataStream<String> dataStream = env.fromCollection(data);
        
        // Print each element (this will show in Flink TaskManager logs)
        dataStream.print();
        
        // Execute the job
        env.execute("Day 3: Flink Hello World (Java)");
    }
}

