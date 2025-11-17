package com.cdp.processors;

import java.util.List;
import java.util.Map;

import org.apache.flink.api.common.functions.RichMapFunction;
import org.apache.flink.configuration.Configuration;
import org.neo4j.driver.Driver;

import com.cdp.models.CustomerEvent;
import com.cdp.sinks.MongoSink;
import com.cdp.sinks.Neo4jSink;
import com.cdp.utils.DatabaseConnector;
import com.cdp.utils.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.mongodb.client.MongoClient;

/**
 * Flow:
 * 1. Parse event and extract identities
 * 2. Neo4j stitching → get master_profile_id + all identities
 * 3. MongoDB cleanup → remove orphaned profiles
 * 4. MongoDB update → enrich unified profile with ALL identities
 */
public class ProfileStitcher extends RichMapFunction<String, String> {

    private transient MongoClient mongoClient;
    private transient Driver neo4jDriver;
    private transient MongoSink mongoSink;
    private transient Neo4jSink neo4jSink;

    @Override
    public void open(Configuration parameters) throws Exception {
        super.open(parameters);

        mongoClient = DatabaseConnector.createMongoClient();
        neo4jDriver = DatabaseConnector.createNeo4jDriver();
        
        mongoSink = new MongoSink(mongoClient);
        neo4jSink = new Neo4jSink(neo4jDriver);
        
        System.out.println("✅ ProfileStitcher initialized");
    }

    @Override
    public String map(String jsonString) throws Exception {
        try {
            JsonNode eventNode = JsonParser.parse(jsonString);
            CustomerEvent event = new CustomerEvent(eventNode);
            
            List<Map<String, String>> identities = event.getIdentitiesAsList();
            
            if (identities.isEmpty()) {
                System.out.println("⚠️ No identities found in event, skipping: " + jsonString);
                return jsonString;
            }

            Neo4jSink.StitchResult stitchResult = neo4jSink.stitchIdentities(identities);
            String masterProfileId = stitchResult.masterProfileId;
            List<Map<String, String>> allIdentities = stitchResult.allIdentities;
            
            System.out.println("✅ Stitched identities → master_profile_id: " + masterProfileId);
            System.out.println("   Total identities on profile: " + allIdentities.size());
            
            mongoSink.cleanupOrphanedProfiles(masterProfileId, allIdentities);
            
            mongoSink.updateProfile(masterProfileId, eventNode, allIdentities);
            
            return "SUCCESS: " + masterProfileId;
            
        } catch (Exception e) {
            System.err.println("❌ Error processing event: " + e.getMessage());
            return "ERROR: " + e.getMessage();
        }
    }

    @Override
    public void close() throws Exception {
        // Close database connections using DatabaseConnector
        DatabaseConnector.closeMongoClient(mongoClient);
        DatabaseConnector.closeNeo4jDriver(neo4jDriver);
        
        super.close();
    }
}
