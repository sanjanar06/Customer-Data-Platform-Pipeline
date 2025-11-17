package com.cdp.config;

import java.util.HashMap;
import java.util.Map;

public class ConfigManager {
    
    private static final Map<String, String> CONFIG = new HashMap<>();
    
    // Configuration keys
    public static final String MONGO_URI = "MONGO_URI";
    public static final String MONGO_DB = "MONGO_DB";
    public static final String NEO4J_URI = "NEO4J_URI";
    public static final String NEO4J_USER = "NEO4J_USER";
    public static final String NEO4J_PASS = "NEO4J_PASS";
    public static final String SOCKET_HOST = "SOCKET_HOST";
    public static final String SOCKET_PORT = "SOCKET_PORT";
    
    static {
        // Load configuration from environment variables with defaults
        CONFIG.put(MONGO_URI, getEnv(MONGO_URI, "mongodb://admin:password123@mongodb:27017"));
        CONFIG.put(MONGO_DB, getEnv(MONGO_DB, "cdp"));
        CONFIG.put(NEO4J_URI, getEnv(NEO4J_URI, "bolt://neo4j:7687"));
        CONFIG.put(NEO4J_USER, getEnv(NEO4J_USER, "neo4j"));
        CONFIG.put(NEO4J_PASS, getEnv(NEO4J_PASS, "password123"));
        CONFIG.put(SOCKET_HOST, getEnv(SOCKET_HOST, "host.docker.internal"));
        CONFIG.put(SOCKET_PORT, getEnv(SOCKET_PORT, "9001"));
    }
    
    public static String get(String key) {
        if (!CONFIG.containsKey(key)) {
            throw new IllegalArgumentException("Configuration key not found: " + key);
        }
        return CONFIG.get(key);
    }
    
    public static int getInt(String key) {
        return Integer.parseInt(get(key));
    }
    
    public static String get(String key, String defaultValue) {
        return CONFIG.getOrDefault(key, defaultValue);
    }
    
    private static String getEnv(String key, String defaultValue) {
        String value = System.getenv(key);
        return (value != null && !value.isEmpty()) ? value : defaultValue;
    }

    public static void printConfig() {
        System.out.println("=== Configuration ===");
        CONFIG.forEach((key, value) -> {
            // Mask passwords
            String displayValue = key.contains("PASS") ? "****" : value;
            System.out.println(key + ": " + displayValue);
        });
        System.out.println("====================");
    }
}
