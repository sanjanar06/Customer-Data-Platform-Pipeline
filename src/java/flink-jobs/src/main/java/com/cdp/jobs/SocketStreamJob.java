package com.cdp.jobs;

import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.cdp.processors.ProfileStitcher;
import com.cdp.sources.EventSource;

public class SocketStreamJob {

    private static final Logger LOG = LoggerFactory.getLogger(SocketStreamJob.class);

    public static void main(String[] args) throws Exception {

        LOG.info("Starting Socket Stream Job");
        
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);

        DataStream<String> stream = EventSource.createSocketStream(env);

        stream.map(new ProfileStitcher())
              .map(value -> "FLINK-LOG: " + value)
              .print();

        LOG.info("Submitting job to cluster...");
        env.execute("Socket Stream Job (com.cdp.jobs.SocketStreamJob)");
    }
}
