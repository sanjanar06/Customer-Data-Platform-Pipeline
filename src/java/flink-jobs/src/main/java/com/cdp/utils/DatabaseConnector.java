package com.cdp.utils;

import org.neo4j.driver.AuthTokens;
import org.neo4j.driver.Driver;
import org.neo4j.driver.GraphDatabase;

import com.cdp.config.ConfigManager;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;


public class DatabaseConnector {
    
    public static MongoClient createMongoClient() {
        String mongoUri = ConfigManager.get(ConfigManager.MONGO_URI);
        System.out.println("✅ Connecting to MongoDB: " + maskUri(mongoUri));
        return MongoClients.create(mongoUri);
    }
    
    public static Driver createNeo4jDriver() {
        String neo4jUri = ConfigManager.get(ConfigManager.NEO4J_URI);
        String neoUser = ConfigManager.get(ConfigManager.NEO4J_USER);
        String neoPass = ConfigManager.get(ConfigManager.NEO4J_PASS);
        
        System.out.println("✅ Connecting to Neo4j: " + neo4jUri);
        return GraphDatabase.driver(neo4jUri, AuthTokens.basic(neoUser, neoPass));
    }
    
    public static void closeMongoClient(MongoClient client) {
        if (client != null) {
            try {
                client.close();
                System.out.println("MongoDB connection closed");
            } catch (Exception e) {
                System.err.println("Error closing MongoDB: " + e.getMessage());
            }
        }
    }

    public static void closeNeo4jDriver(Driver driver) {
        if (driver != null) {
            try {
                driver.close();
                System.out.println("Neo4j connection closed");
            } catch (Exception e) {
                System.err.println("Error closing Neo4j: " + e.getMessage());
            }
        }
    }
    
    private static String maskUri(String uri) {
        if (uri == null) return "";
        // Mask password in URI
        return uri.replaceAll("://([^:]+):([^@]+)@", "://$1:****@");
    }
}
