package com.cdp.sinks;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.bson.Document;

import com.cdp.config.ConfigManager;
import com.fasterxml.jackson.databind.JsonNode;
import com.mongodb.client.MongoClient;
import com.mongodb.client.model.UpdateOptions;

/**
 * MongoDB sink for writing unified customer profiles.
 * Implements "union profile" pattern with event history.
 * 
 * Features:
 * - Upsert profiles by master_profile_id
 * - Sync ALL identities from Neo4j (not just event identities)
 * - Append events to history (max 100)
 * - Merge event properties into attributes
 * 
 */
public class MongoSink {
    
    private final MongoClient mongoClient;
    private final String databaseName;
    
    public MongoSink(MongoClient mongoClient) {
        this.mongoClient = mongoClient;
        this.databaseName = ConfigManager.get(ConfigManager.MONGO_DB);
    }
    
    public void updateProfile(String masterProfileId, JsonNode event, List<Map<String, String>> allIdentities) {
        try {
            var database = mongoClient.getDatabase(databaseName);
            var collection = database.getCollection("profiles");
            
            // Log identities being written
            System.out.println("   MongoDB: Writing " + allIdentities.size() + " identities:");
            for (Map<String, String> id : allIdentities) {
                System.out.println("      - " + id.get("type") + ": " + id.get("value"));
            }
            
            // Extract key fields
            String eventType = event.has("event_type") ? event.get("event_type").asText() : "unknown";
            long timestamp = event.has("timestamp") ? event.get("timestamp").asLong() : System.currentTimeMillis() / 1000;
            
            // Build update document
            Document updateDoc = new Document();
            
            // $set: Update fields (last-write-wins)
            Document setDoc = new Document()
                    .append("master_profile_id", masterProfileId)
                    .append("updated_at", new Date())
                    .append("last_event_type", eventType)
                    .append("last_event_timestamp", timestamp);
            
            // Build identities document from ALL identities (from Neo4j)
            Document identitiesDoc = buildIdentitiesDocument(allIdentities);
            setDoc.append("identities", identitiesDoc);
            
            System.out.println("   MongoDB: Identities doc to write: " + identitiesDoc.toJson());
            
            // Merge event properties into attributes
            if (event.has("properties")) {
                mergeProperties(event.get("properties"), setDoc);
            }
            
            updateDoc.append("$set", setDoc);
            
            // $push: Append to event_history
            Document eventHistoryEntry = new Document()
                    .append("event_type", eventType)
                    .append("timestamp", timestamp)
                    .append("data", Document.parse(event.toString()));
            
            updateDoc.append("$push", new Document()
                    .append("event_history", new Document()
                            .append("$each", Collections.singletonList(eventHistoryEntry))
                            .append("$slice", -100)
                    )
            );
            
            // $setOnInsert: Only on document creation
            updateDoc.append("$setOnInsert", new Document()
                    .append("created_at", new Date())
            );
            
            // Upsert
            var filter = new Document("master_profile_id", masterProfileId);
            var options = new UpdateOptions().upsert(true);
            
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
    
    private Document buildIdentitiesDocument(List<Map<String, String>> allIdentities) {
        // Group by type to handle multiple identities of same type
        Map<String, List<String>> identitiesByType = new HashMap<>();
        for (Map<String, String> identity : allIdentities) {
            String type = identity.get("type");
            String value = identity.get("value");
            identitiesByType.computeIfAbsent(type, k -> new ArrayList<>()).add(value);
        }
        
        // Store identities - if only one value, store as string; if multiple, store as array
        Document identitiesDoc = new Document();
        for (Map.Entry<String, List<String>> entry : identitiesByType.entrySet()) {
            String type = entry.getKey();
            List<String> values = entry.getValue();
            if (values.size() == 1) {
                identitiesDoc.append(type, values.get(0));
            } else {
                identitiesDoc.append(type, values);
            }
        }
        
        return identitiesDoc;
    }
    
    private void mergeProperties(JsonNode properties, Document setDoc) {
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
    
    public void cleanupOrphanedProfiles(String masterProfileId, List<Map<String, String>> identities) {
        try {
            var database = mongoClient.getDatabase(databaseName);
            var collection = database.getCollection("profiles");
            
            // Find all profiles that have ANY of these identities
            // but DON'T have the correct master_profile_id
            List<Document> identityFilters = new ArrayList<>();
            for (Map<String, String> identity : identities) {
                String type = identity.get("type");
                String value = identity.get("value");
                identityFilters.add(new Document("identities." + type, value));
            }
            
            // Delete profiles that match identities but have wrong ID
            var filter = new Document("$and", Arrays.asList(
                    new Document("$or", identityFilters),
                    new Document("master_profile_id", new Document("$ne", masterProfileId))
            ));
            
            var result = collection.deleteMany(filter);
            
            if (result.getDeletedCount() > 0) {
                System.out.println("🗑️  MongoDB: Deleted " + result.getDeletedCount() + " orphaned profile(s)");
            }
            
        } catch (Exception e) {
            System.err.println("⚠️  MongoDB cleanup warning: " + e.getMessage());
        }
    }
}
