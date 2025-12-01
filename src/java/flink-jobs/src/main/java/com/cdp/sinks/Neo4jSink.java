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
            // Step 1: Create all identity nodes from event
            "UNWIND $identities AS identity_data " +
            "MERGE (i:Identity {type: identity_data.type, value: identity_data.value}) " +
            "ON CREATE SET i.created_at = datetime() " +
            "WITH collect(DISTINCT i) AS event_identities " +
            
            // Step 2: For EACH identity, find exact AND fuzzy matched profiles
            "UNWIND event_identities AS single_identity " +
            "OPTIONAL MATCH (single_identity)<-[:HAS_IDENTITY]-(exact_p:Profile) " +
            
            // Step 3: Fuzzy match using apoc.text.fuzzyMatch
            "WITH event_identities, single_identity, collect(DISTINCT exact_p) AS exact_matches " +
            "CALL { " +
            "  WITH single_identity " +
            "  OPTIONAL MATCH (other:Identity) " +
            "  WHERE other.type = single_identity.type " +
            "    AND other <> single_identity " +
            "    AND apoc.text.fuzzyMatch(other.value, single_identity.value) " +
            "  OPTIONAL MATCH (other)<-[:HAS_IDENTITY]-(fuzzy_p:Profile) " +
            "  RETURN collect(DISTINCT fuzzy_p) AS fuzzy_matches " +
            "} " +
            
            // Step 4: Combine exact and fuzzy for this identity
            "WITH event_identities, exact_matches + fuzzy_matches AS matches_for_identity " +
            
            // Step 5: Flatten all matches across ALL identities
            "WITH event_identities, apoc.coll.flatten(collect(matches_for_identity)) AS all_profiles " +
            "WITH event_identities, [p IN all_profiles WHERE p IS NOT NULL] AS existing_profiles " +
            
            // Step 6: Deduplicate and sort
            "WITH event_identities, apoc.coll.toSet(existing_profiles) AS unique_profiles " + 
            "WITH event_identities, apoc.coll.sortNodes(unique_profiles, 'created_at') AS sorted_profiles " +
            
            // Step 7: Choose master ID
            "WITH event_identities, sorted_profiles, " +
            "     CASE " +
            "       WHEN size(sorted_profiles) > 0 THEN sorted_profiles[0].master_profile_id " +
            "       ELSE 'profile_' + randomUUID() " +
            "     END AS final_id " +
            
            // Step 8: Gather all old identities from losing profiles
            "UNWIND CASE WHEN size(sorted_profiles) > 0 THEN sorted_profiles ELSE [null] END AS prof " +
            "OPTIONAL MATCH (prof)-[:HAS_IDENTITY]->(old_identity:Identity) " +
            "WITH final_id, event_identities, sorted_profiles, collect(DISTINCT old_identity) AS old_identities " +
            "WITH final_id, sorted_profiles, " +
            "     event_identities + [i IN old_identities WHERE i IS NOT NULL AND NOT i IN event_identities] AS all_identities " +
            
            // Step 9: Create/Merge Final Profile
            "MERGE (final_profile:Profile {master_profile_id: final_id}) " +
            "ON CREATE SET final_profile.created_at = datetime() " +
            
            // Step 10: Link ALL identities
            "WITH final_profile, all_identities, sorted_profiles " +
            "FOREACH (identity IN all_identities | MERGE (final_profile)-[:HAS_IDENTITY]->(identity)) " +
            
            // Step 11: Delete Losing Profiles
            "WITH final_profile, sorted_profiles " +
            "FOREACH (loser IN [p IN sorted_profiles WHERE p.master_profile_id <> final_profile.master_profile_id] | " +
            "  DETACH DELETE loser " +
            ") " +
            
            "RETURN final_profile.master_profile_id AS master_profile_id, " +
            "       [(final_profile)-[:HAS_IDENTITY]->(id:Identity) | {type: id.type, value: id.value}] AS all_identities";
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
