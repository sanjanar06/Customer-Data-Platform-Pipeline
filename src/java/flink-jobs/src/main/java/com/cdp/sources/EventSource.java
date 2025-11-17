package com.cdp.sources;

import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import com.cdp.config.ConfigManager;

public class EventSource {
    
    public static DataStream<String> createSocketStream(StreamExecutionEnvironment env) {
        String host = ConfigManager.get(ConfigManager.SOCKET_HOST);
        int port = ConfigManager.getInt(ConfigManager.SOCKET_PORT);
        
        System.out.println("📡 Creating socket stream: " + host + ":" + port);
        
        return env.socketTextStream(host, port);
    }
}
