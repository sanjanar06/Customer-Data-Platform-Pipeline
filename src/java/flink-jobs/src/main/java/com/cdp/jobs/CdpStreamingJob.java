package com.cdp.jobs;

import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.cdp.processors.ProfileStitcher;
import com.cdp.sources.EventSource;

public class CdpStreamingJob {

    private static final Logger LOG = LoggerFactory.getLogger(CdpStreamingJob.class);

    public static void main(String[] args) throws Exception {

        LOG.info("Starting CDP Streaming Job (Kafka Edition");
        
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // 1. Enable Checkpointing every 10 seconds (Fault Tolerance)
        env.enableCheckpointing(10000); 
        
        // 2. Parallelism (Matches your Kafka Partitions)
        env.setParallelism(2);

        // 3. Source: Kafka
        DataStream<String> stream = EventSource.createKafkaStream(env);

        // 4. Process: Identity Stitching
        stream.map(new ProfileStitcher())
              .name("Profile Stitcher")
              .uid("profile-stitcher") // Stable ID for state
              .print();

        LOG.info("Submitting job to cluster...");
        env.execute("CDP Streaming Job");

        
    }
}
