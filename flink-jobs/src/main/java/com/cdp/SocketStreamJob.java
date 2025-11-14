package com.cdp;

import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.cdp.ProfileStitcher;

public class SocketStreamJob {

// Add a logger so we can see what's happening
    private static final Logger LOG = LoggerFactory.getLogger(SocketStreamJob.class);

    public static void main(String[] args) throws Exception {

       // THE FIX IS HERE:
       // "host.docker.internal" is the magic address for your host laptop
       // as seen from inside a Docker container.
       final String host = "host.docker.internal";
       final int port = 9001;

       LOG.info("Starting Socket Stream Job.");
       LOG.info("Attempting to connect to producer (producer.py) at {}:{}", host, port);

        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);

       // This now uses the correct 'host' variable
       DataStream<String> stream = env.socketTextStream(host, port);

     // Pass each incoming line through ProfileStitcher which initializes DB clients
     stream.map(new ProfileStitcher())
         .map(value -> "FLINK-LOG: " + value)
         .print();

       LOG.info("Submitting job to cluster...");
        env.execute("Socket Stream Job (com.cdp.SocketStreamJob)");
    }
}