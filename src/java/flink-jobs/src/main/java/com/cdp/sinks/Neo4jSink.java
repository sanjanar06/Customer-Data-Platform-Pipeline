package com.cdp.sinks;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.neo4j.driver.Driver;
import org.neo4j.driver.Record;
import org.neo4j.driver.Result;
import org.neo4j.driver.Session;
import org.neo4j.driver.Value;

/**
 * Neo4j sink for identity stitching and graph operations.
 * Implements identity resolution using graph patterns.
 * 
 * Algorithm:
 * 1. Create/find all identities from event
 * 2. Find ALL profiles that have ANY of these identities
 * 3. Collect ALL identities from existing profiles (before merge)
 * 4. Merge duplicate profiles into one master profile
 * 5. Link ALL identities to master profile
 * 6. Return master_profile_id + all identities
 * 
 */
public class Neo4jSink {
    
    private final Driver neo4jDriver;
    
    public static class StitchResult {
        public final String masterProfileId;
        public final List<Map<String, String>> allIdentities;
        
        public StitchResult(String id, List<Map<String, String>> identities) {
            this.masterProfileId = id;
            this.allIdentities = identities;
        }
    }

    public Neo4jSink(Driver neo4jDriver) {
        this.neo4jDriver = neo4jDriver;
    }
    

    public StitchResult stitchIdentities(List<Map<String, String>> identities) {
        try (Session session = neo4jDriver.session()) {
            
            String query = buildStitchQuery();
            
            Map<String, Object> params = new HashMap<>();
            params.put("identities", identities);
            
            System.out.println("   Neo4j: Processing " + identities.size() + " identities from event");
            
            Result result = session.run(query, params);
            
            if (result.hasNext()) {
                Record record = result.next();
                String masterProfileId = record.get("master_profile_id").asString();
                
                // Parse all identities from Neo4j response
                Value allIdentitiesValue = record.get("all_identities");
                List<Map<String, String>> allIdentities = parseIdentities(allIdentitiesValue);
                
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
    
    private String buildStitchQuery() {
        return 
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
    }
    
    private List<Map<String, String>> parseIdentities(Value allIdentitiesValue) {
        List<Map<String, String>> allIdentities = new ArrayList<>();
        
        for (Object obj : allIdentitiesValue.asList()) {
            @SuppressWarnings("unchecked")
            Map<String, Object> idMap = (Map<String, Object>) obj;
            Map<String, String> identity = new HashMap<>();
            identity.put("type", idMap.get("type").toString());
            identity.put("value", idMap.get("value").toString());
            allIdentities.add(identity);
        }
        
        return allIdentities;
    }
}
