package com.cdp.sources;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import com.cdp.config.ConfigManager;

public class EventSource {
    
    public static DataStream<String> createKafkaStream(StreamExecutionEnvironment env) {
        // Flink runs INSIDE Docker, so it uses the internal Docker network name for Kafka

        String brokers = ConfigManager.get(ConfigManager.KAFKA_BROKER);
        String topic = ConfigManager.get(ConfigManager.KAFKA_TOPIC);
        String groupId = ConfigManager.get(ConfigManager.KAFKA_GROUP_ID);

        System.out.println("Connecting to Kafka: " + brokers + " | Topic: " + topic);

        KafkaSource<String> source = KafkaSource.<String>builder()
                .setBootstrapServers(brokers)
                .setTopics(topic)
                .setGroupId(groupId)
                .setStartingOffsets(OffsetsInitializer.earliest()) // Catch up on missed events
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();
     
        return env.fromSource(source, WatermarkStrategy.noWatermarks(), "Kafka Source");
    }
}
