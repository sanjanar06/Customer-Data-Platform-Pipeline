package com.cdp;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.flink.api.common.functions.RichMapFunction;
import org.apache.flink.configuration.Configuration;
import org.neo4j.driver.AuthTokens;
import org.neo4j.driver.Driver;
import org.neo4j.driver.GraphDatabase;
import org.neo4j.driver.Record;
import org.neo4j.driver.Result;
import org.neo4j.driver.Session;
import org.neo4j.driver.Value;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;

/**
 * Day 8: ProfileStitcher with Neo4j + MongoDB Integration
 * 
 * Flow:
 * 1. Extract identities from event
 * 2. Neo4j stitching → get master_profile_id
 * 3. MongoDB update → enrich unified profile
 */
public class ProfileStitcher extends RichMapFunction<String, String> {

    private transient MongoClient mongoClient;
    private transient Driver neo4jDriver;
    private transient ObjectMapper objectMapper;

    @Override
    public void open(Configuration parameters) throws Exception {
        super.open(parameters);

        // Initialize JSON parser
        objectMapper = new ObjectMapper();

        // Connect to MongoDB
        String mongoUri = System.getenv().getOrDefault("MONGO_URI", "mongodb://admin:password123@mongodb:27017");
        mongoClient = MongoClients.create(mongoUri);
        System.out.println("✅ MongoDB connected (ProfileStitcher)");

        // Connect to Neo4j
        String neo4jUri = System.getenv().getOrDefault("NEO4J_URI", "bolt://neo4j:7687");
        String neoUser = System.getenv().getOrDefault("NEO4J_USER", "neo4j");
        String neoPass = System.getenv().getOrDefault("NEO4J_PASS", "password123");
        neo4jDriver = GraphDatabase.driver(neo4jUri, AuthTokens.basic(neoUser, neoPass));
        System.out.println("✅ Neo4j connected (ProfileStitcher)");
    }

    @Override
    public String map(String jsonString) throws Exception {
        try {
            // Parse the incoming JSON event
            JsonNode event = objectMapper.readTree(jsonString);
            
            // Extract identities from the event
            List<Map<String, String>> identities = extractIdentities(event);
            
            if (identities.isEmpty()) {
                System.out.println("⚠️ No identities found in event, skipping: " + jsonString);
                return jsonString;
            }

            // Step 1: Call Neo4j to stitch identities and get master_profile_id + ALL identities
            StitchResult stitchResult = stitchIdentitiesWithResult(identities);
            String masterProfileId = stitchResult.masterProfileId;
            List<Map<String, String>> allIdentities = stitchResult.allIdentities;
            
            System.out.println("✅ Stitched identities → master_profile_id: " + masterProfileId);
            System.out.println("   Total identities on profile: " + allIdentities.size());
            
            // Step 2: Clean up orphaned MongoDB profiles (if any merge happened)
            cleanupOrphanedProfiles(masterProfileId, allIdentities);
            
            // Step 3: Update MongoDB profile with ALL identities from Neo4j
            updateMongoProfile(masterProfileId, event, allIdentities);
            
            return "SUCCESS: " + masterProfileId;
            
        } catch (Exception e) {
            System.err.println("❌ Error processing event: " + e.getMessage());
            e.printStackTrace();
            return "ERROR: " + e.getMessage();
        }
    }
    
    /**
     * Result class to return both profile ID and all identities
     */
    private static class StitchResult {
        String masterProfileId;
        List<Map<String, String>> allIdentities;
        
        StitchResult(String id, List<Map<String, String>> identities) {
            this.masterProfileId = id;
            this.allIdentities = identities;
        }
    }
    
    /**
     * Clean up orphaned MongoDB profiles after a Neo4j merge
     */
    private void cleanupOrphanedProfiles(String masterProfileId, List<Map<String, String>> identities) {
        try {
            var database = mongoClient.getDatabase("cdp");
            var collection = database.getCollection("profiles");
            
            // Find all profiles that have ANY of these identities
            // but DON'T have the correct master_profile_id
            List<org.bson.Document> identityFilters = new ArrayList<>();
            for (Map<String, String> identity : identities) {
                String type = identity.get("type");
                String value = identity.get("value");
                identityFilters.add(new org.bson.Document("identities." + type, value));
            }
            
            // Delete profiles that match identities but have wrong ID
            var filter = new org.bson.Document("$and", java.util.Arrays.asList(
                new org.bson.Document("$or", identityFilters),
                new org.bson.Document("master_profile_id", new org.bson.Document("$ne", masterProfileId))
            ));
            
            var result = collection.deleteMany(filter);
            
            if (result.getDeletedCount() > 0) {
                System.out.println("🗑️  MongoDB: Deleted " + result.getDeletedCount() + " orphaned profile(s)");
            }
            
        } catch (Exception e) {
            System.err.println("⚠️  MongoDB cleanup warning: " + e.getMessage());
            // Don't throw - cleanup is best-effort
        }
    }

    /**
     * Extract identities from event JSON.
     */
    private List<Map<String, String>> extractIdentities(JsonNode event) {
        List<Map<String, String>> identities = new ArrayList<>();
        
        JsonNode identitiesNode = event.get("identities");
        if (identitiesNode != null && identitiesNode.isObject()) {
            identitiesNode.fields().forEachRemaining(entry -> {
                String type = entry.getKey();
                String value = entry.getValue().asText();
                
                Map<String, String> identity = new HashMap<>();
                identity.put("type", type);
                identity.put("value", value);
                identities.add(identity);
            });
        }
        
        return identities;
    }

    /**
     * Neo4j identity stitching - returns profile ID AND all identities
     */
    private StitchResult stitchIdentitiesWithResult(List<Map<String, String>> identities) {
        try (Session session = neo4jDriver.session()) {
            
            String query = 
                // Step 1: Create/find all identities from this event
                "UNWIND $identities AS identity_data " +
                "MERGE (i:Identity {type: identity_data.type, value: identity_data.value}) " +
                "ON CREATE SET i.created_at = datetime() " +
                "WITH collect(DISTINCT i) AS event_identities " +
                
                // Step 2: Find ALL profiles that have ANY of these identities
                "UNWIND event_identities AS single_identity " +
                "OPTIONAL MATCH (single_identity)<-[:HAS_IDENTITY]-(prof:Profile) " +
                "WITH event_identities, collect(DISTINCT prof) AS found_profiles " +
                "WITH event_identities, [p IN found_profiles WHERE p IS NOT NULL] AS existing_profiles " +
                
                // Step 3: BEFORE doing anything, collect ALL identities from ALL existing profiles
                "OPTIONAL MATCH (existing_prof:Profile)-[:HAS_IDENTITY]->(existing_identity:Identity) " +
                "WHERE existing_prof IN existing_profiles " +
                "WITH event_identities, existing_profiles, collect(DISTINCT existing_identity) AS all_old_identities " +
                
                // Step 4: Combine event identities + old identities (BEFORE any deletes!)
                "WITH existing_profiles, " +
                "     event_identities + [i IN all_old_identities WHERE i IS NOT NULL AND NOT i IN event_identities] AS complete_identity_list " +
                
                // Step 5: Choose the master_profile_id
                "WITH existing_profiles, complete_identity_list, " +
                "     CASE " +
                "       WHEN size(existing_profiles) > 0 THEN existing_profiles[0].master_profile_id " +
                "       ELSE 'profile_' + toString(randomUUID()) " +
                "     END AS final_id " +
                
                // Step 6: Create or find the final profile
                "MERGE (final_profile:Profile {master_profile_id: final_id}) " +
                "ON CREATE SET final_profile.created_at = datetime() " +
                
                // Step 7: Delete duplicate profiles (NOT the final one)
                "WITH final_profile, existing_profiles, complete_identity_list " +
                "FOREACH (old_prof IN [p IN existing_profiles WHERE p.master_profile_id <> final_profile.master_profile_id] | " +
                "  DETACH DELETE old_prof " +
                ") " +
                
                // Step 8: Link ALL identities (from complete list) to final profile
                "WITH final_profile, complete_identity_list " +
                "FOREACH (identity IN complete_identity_list | " +
                "  MERGE (final_profile)-[:HAS_IDENTITY]->(identity) " +
                ") " +
                
                // Step 9: Return result with all identities
                "RETURN final_profile.master_profile_id AS master_profile_id, " +
                "       [(final_profile)-[:HAS_IDENTITY]->(i:Identity) | {type: i.type, value: i.value}] AS all_identities";

            Map<String, Object> params = new HashMap<>();
            params.put("identities", identities);
            
            System.out.println("   Neo4j: Processing " + identities.size() + " identities from event");
            
            Result result = session.run(query, params);
            
            if (result.hasNext()) {
                Record record = result.next();
                String masterProfileId = record.get("master_profile_id").asString();
                
                // Parse all identities from Neo4j response
                Value allIdentitiesValue = record.get("all_identities");
                List<Map<String, String>> allIdentities = new ArrayList<>();
                for (Object obj : allIdentitiesValue.asList()) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> idMap = (Map<String, Object>) obj;
                    Map<String, String> identity = new HashMap<>();
                    identity.put("type", idMap.get("type").toString());
                    identity.put("value", idMap.get("value").toString());
                    allIdentities.add(identity);
                }
                
                System.out.println("   Neo4j: Final profile has " + allIdentities.size() + " total identities");
                
                return new StitchResult(masterProfileId, allIdentities);
            } else {
                throw new RuntimeException("Neo4j query returned no results");
            }
            
        } catch (Exception e) {
            System.err.println("❌ Neo4j stitching failed: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Identity stitching failed", e);
        }
    }

    /**
     * MongoDB profile update - implements "union profile" pattern
     * Now syncs ALL identities from Neo4j (not just event identities)
     */
    private void updateMongoProfile(String masterProfileId, JsonNode event, List<Map<String, String>> allIdentities) {
        try {
            var database = mongoClient.getDatabase("cdp");
            var collection = database.getCollection("profiles");
            
            // LOG: What identities are we writing?
            System.out.println("   MongoDB: Writing " + allIdentities.size() + " identities:");
            for (Map<String, String> id : allIdentities) {
                System.out.println("      - " + id.get("type") + ": " + id.get("value"));
            }
            
            // Extract key fields
            String eventType = event.has("event_type") ? event.get("event_type").asText() : "unknown";
            long timestamp = event.has("timestamp") ? event.get("timestamp").asLong() : System.currentTimeMillis() / 1000;
            
            // Build update document
            org.bson.Document updateDoc = new org.bson.Document();
            
            // $set: Update fields (last-write-wins)
            org.bson.Document setDoc = new org.bson.Document()
                .append("master_profile_id", masterProfileId)
                .append("updated_at", new java.util.Date())
                .append("last_event_type", eventType)
                .append("last_event_timestamp", timestamp);
            
            // Build identities document from ALL identities (from Neo4j)
            // Group by type to handle multiple identities of same type
            Map<String, List<String>> identitiesByType = new HashMap<>();
            for (Map<String, String> identity : allIdentities) {
                String type = identity.get("type");
                String value = identity.get("value");
                identitiesByType.computeIfAbsent(type, k -> new ArrayList<>()).add(value);
            }
            
            // Store identities - if only one value, store as string; if multiple, store as array
            org.bson.Document identitiesDoc = new org.bson.Document();
            for (Map.Entry<String, List<String>> entry : identitiesByType.entrySet()) {
                String type = entry.getKey();
                List<String> values = entry.getValue();
                if (values.size() == 1) {
                    identitiesDoc.append(type, values.get(0));
                } else {
                    identitiesDoc.append(type, values);
                }
            }
            
            // CRITICAL: Replace the ENTIRE identities object with fresh data from Neo4j
            setDoc.append("identities", identitiesDoc);
            
            System.out.println("   MongoDB: Identities doc to write: " + identitiesDoc.toJson());
            
            // Merge event properties into attributes
            if (event.has("properties")) {
                JsonNode properties = event.get("properties");
                properties.fieldNames().forEachRemaining(fieldName -> {
                    JsonNode fieldValue = properties.get(fieldName);
                    Object value;
                    if (fieldValue.isTextual()) {
                        value = fieldValue.asText();
                    } else if (fieldValue.isNumber()) {
                        value = fieldValue.asDouble();
                    } else if (fieldValue.isBoolean()) {
                        value = fieldValue.asBoolean();
                    } else {
                        value = fieldValue.toString();
                    }
                    setDoc.append("attributes." + fieldName, value);
                });
            }
            
            updateDoc.append("$set", setDoc);
            
            // $push: Append to event_history
            org.bson.Document eventHistoryEntry = new org.bson.Document()
                .append("event_type", eventType)
                .append("timestamp", timestamp)
                .append("data", org.bson.Document.parse(event.toString()));
            
            updateDoc.append("$push", new org.bson.Document()
                .append("event_history", new org.bson.Document()
                    .append("$each", java.util.Arrays.asList(eventHistoryEntry))
                    .append("$slice", -100)
                )
            );
            
            // $setOnInsert: Only on document creation
            updateDoc.append("$setOnInsert", new org.bson.Document()
                .append("created_at", new java.util.Date())
            );
            
            // Upsert
            var filter = new org.bson.Document("master_profile_id", masterProfileId);
            var options = new com.mongodb.client.model.UpdateOptions().upsert(true);
            
            var result = collection.updateOne(filter, updateDoc, options);
            
            if (result.getUpsertedId() != null) {
                System.out.println("✅ MongoDB: Created profile");
            } else {
                System.out.println("✅ MongoDB: Updated profile");
            }
            
        } catch (Exception e) {
            System.err.println("❌ MongoDB update failed: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("MongoDB update failed", e);
        }
    }

    @Override
    public void close() throws Exception {
        try {
            if (mongoClient != null) {
                mongoClient.close();
                System.out.println("MongoDB closed");
            }
        } catch (Exception e) {
            System.err.println("Error closing MongoDB: " + e.getMessage());
        }
        
        try {
            if (neo4jDriver != null) {
                neo4jDriver.close();
                System.out.println("Neo4j closed");
            }
        } catch (Exception e) {
            System.err.println("Error closing Neo4j: " + e.getMessage());
        }
        
        super.close();
    }
}