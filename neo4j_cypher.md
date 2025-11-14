// ============================================================
// CDP Identity Stitching - Cypher Queries Repository
// ============================================================
// This file contains all Neo4j Cypher queries used in the 
// Customer Data Platform (CDP) prototype for identity 
// resolution and profile stitching.
// ============================================================

// ============================================================
// SECTION 1: SETUP & CLEANUP
// ============================================================

// Clear entire database (⚠️ WARNING: Deletes all data!)
// Use: Start fresh during testing
MATCH (n) DETACH DELETE n;

// Clear only test data (safer for development)
// Removes test profiles and orphaned identities
MATCH (p:Profile)
WHERE p.master_profile_id STARTS WITH 'profile_test_'
DETACH DELETE p;

MATCH (i:Identity)
WHERE NOT (i)<-[:HAS_IDENTITY]-()
DELETE i;


// ============================================================
// SECTION 2: CORE IDENTITY STITCHING QUERY (PRODUCTION)
// ============================================================
// This is the main query used in the Flink processor.
// It handles all three cases automatically:
// 1. New user → Create profile
// 2. Existing user + new identity → Add to profile
// 3. Multiple profiles → Merge them
// ============================================================

// Parameters expected:
// $identities = [
//   {type: 'email', value: 'user@example.com'},
//   {type: 'deviceID', value: 'device_123'}
// ]

UNWIND $identities AS identity_data

// Step 1: Find or create each identity
MERGE (i:Identity {type: identity_data.type, value: identity_data.value})
ON CREATE SET i.created_at = datetime()

WITH collect(i) AS all_identities

// Step 2: Find all profiles connected to ANY of these identities
UNWIND all_identities AS identity
OPTIONAL MATCH (identity)<-[:HAS_IDENTITY]-(p:Profile)
WITH all_identities, collect(DISTINCT p) AS connected_profiles

// Step 3: Determine the primary profile (first one found, or null)
WITH all_identities, connected_profiles,
     CASE 
       WHEN size(connected_profiles) > 0 THEN connected_profiles[0]
       ELSE NULL
     END AS primary_profile

// Step 4: Create new profile if none exists
CALL {
  WITH primary_profile, all_identities
  WITH primary_profile, all_identities
  WHERE primary_profile IS NULL
  CREATE (new_profile:Profile {
    master_profile_id: 'profile_' + toString(randomUUID()),
    created_at: datetime()
  })
  RETURN new_profile AS profile
  UNION
  WITH primary_profile, all_identities
  WHERE primary_profile IS NOT NULL
  RETURN primary_profile AS profile
}

WITH profile AS final_profile, all_identities, connected_profiles

// Step 5: Delete duplicate profiles (merge)
FOREACH (old_profile IN [p IN connected_profiles WHERE p <> final_profile] |
  DETACH DELETE old_profile
)

// Step 6: Link all identities to final profile
FOREACH (identity IN all_identities |
  MERGE (final_profile)-[:HAS_IDENTITY]->(identity)
)

// Step 7: Return result
RETURN final_profile.master_profile_id AS master_profile_id,
       final_profile.created_at AS created_at,
       [(final_profile)-[:HAS_IDENTITY]->(i:Identity) | {type: i.type, value: i.value}] AS all_identities;


// ============================================================
// SECTION 3: CASE 1 - NEW USER PROFILE
// ============================================================
// Creates a new profile when no existing identities are found.
// Use case: Anonymous visitor lands on website for first time
// ============================================================

MERGE (i:Identity {type: 'deviceID', value: 'device_abc123'})
ON CREATE SET i.created_at = datetime()

WITH i

// Check if identity already has a profile, otherwise create new one
MERGE (p:Profile {master_profile_id: COALESCE(
    [(i)<-[:HAS_IDENTITY]-(existing:Profile) | existing.master_profile_id][0],
    'profile_' + toString(id(i))
)})
ON CREATE SET p.created_at = datetime()

// Link profile to identity
MERGE (p)-[:HAS_IDENTITY]->(i)

RETURN p.master_profile_id AS master_profile_id, 
       collect({type: i.type, value: i.value}) AS identities;

// Expected Result:
// - New Profile created: profile_<unique_id>
// - New Identity created: deviceID = device_abc123
// - Relationship: Profile -[:HAS_IDENTITY]-> Identity


// ============================================================
// SECTION 4: CASE 2 - ADD IDENTITY TO EXISTING PROFILE
// ============================================================
// Adds a new identity (e.g., email) to existing profile (e.g., deviceID)
// Use case: Anonymous user logs in and provides email
// ============================================================

MERGE (i:Identity {type: 'email', value: 'user@example.com'})
ON CREATE SET i.created_at = datetime()

WITH i

// Check if email already belongs to a profile
OPTIONAL MATCH (i)<-[:HAS_IDENTITY]-(existing_profile:Profile)

WITH i, existing_profile

// Check if OTHER identity (deviceID) has a profile
OPTIONAL MATCH (other:Identity {type: 'deviceID', value: 'device_abc123'})
              <-[:HAS_IDENTITY]-(other_profile:Profile)

WITH i, existing_profile, other_profile

// Use existing profile (prefer email's profile, then device's, then create new)
MERGE (p:Profile {master_profile_id: COALESCE(
    existing_profile.master_profile_id,
    other_profile.master_profile_id,
    'profile_' + toString(id(i))
)})
ON CREATE SET p.created_at = datetime()

// Link email to profile
MERGE (p)-[:HAS_IDENTITY]->(i)

RETURN p.master_profile_id AS master_profile_id,
       collect({type: i.type, value: i.value}) AS new_identities;

// Expected Result:
// - Same Profile ID as Case 1 (reused!)
// - New Identity: email = user@example.com
// - Profile now has 2 identities


// ============================================================
// SECTION 5: CASE 3 - MERGE DUPLICATE PROFILES
// ============================================================
// Merges two separate profiles when they share a common identity
// Use case: User has 2 profiles from different sessions, 
//           discovered via shared email
// ============================================================

// Step 1: Create a second profile (simulate another session)
MERGE (i:Identity {type: 'deviceID', value: 'device_xyz789'})
ON CREATE SET i.created_at = datetime()

WITH i

MERGE (p:Profile {master_profile_id: COALESCE(
    [(i)<-[:HAS_IDENTITY]-(existing:Profile) | existing.master_profile_id][0],
    'profile_' + toString(id(i))
)})
ON CREATE SET p.created_at = datetime()

MERGE (p)-[:HAS_IDENTITY]->(i)

RETURN p.master_profile_id AS master_profile_id;

// Now we have 2 separate profiles:
// Profile A: deviceID=abc123, email=user@example.com
// Profile B: deviceID=xyz789

// Step 2: THE MERGE - User logs in with device_xyz789 AND email
WITH 'user@example.com' AS email_value, 'device_xyz789' AS device_value

// Find or create both identities
MERGE (email_identity:Identity {type: 'email', value: email_value})
ON CREATE SET email_identity.created_at = datetime()

MERGE (device_identity:Identity {type: 'deviceID', value: device_value})
ON CREATE SET device_identity.created_at = datetime()

WITH email_identity, device_identity

// Find profiles connected to these identities
OPTIONAL MATCH (email_identity)<-[:HAS_IDENTITY]-(email_profile:Profile)
OPTIONAL MATCH (device_identity)<-[:HAS_IDENTITY]-(device_profile:Profile)

WITH email_identity, device_identity, 
     email_profile, device_profile,
     // Primary profile = prefer email's profile, else device's profile
     CASE 
       WHEN email_profile IS NOT NULL THEN email_profile
       WHEN device_profile IS NOT NULL THEN device_profile
       ELSE NULL
     END AS primary_profile,
     // If they're DIFFERENT profiles, mark one for deletion
     CASE
       WHEN email_profile IS NOT NULL 
            AND device_profile IS NOT NULL 
            AND email_profile <> device_profile 
       THEN device_profile
       ELSE NULL
     END AS profile_to_merge

// If we need to merge, connect device to primary profile
FOREACH (ignore IN CASE WHEN profile_to_merge IS NOT NULL THEN [1] ELSE [] END |
  MERGE (primary_profile)-[:HAS_IDENTITY]->(device_identity)
)

// Delete the duplicate profile
FOREACH (old IN CASE WHEN profile_to_merge IS NOT NULL THEN [profile_to_merge] ELSE [] END |
  DETACH DELETE old
)

// Ensure both identities are linked to primary
WITH primary_profile, email_identity, device_identity
MERGE (primary_profile)-[:HAS_IDENTITY]->(email_identity)
MERGE (primary_profile)-[:HAS_IDENTITY]->(device_identity)

RETURN primary_profile.master_profile_id AS master_profile_id,
       [(primary_profile)-[:HAS_IDENTITY]->(i:Identity) | {type: i.type, value: i.value}] AS all_identities;

// Expected Result:
// - ONE master_profile_id (Profile A)
// - THREE identities: device_abc123, device_xyz789, user@example.com
// - Profile B deleted (merged into Profile A)


// ============================================================
// SECTION 6: UTILITY QUERIES
// ============================================================

// Find profile by identity value
MATCH (i:Identity {value: $identity_value})<-[:HAS_IDENTITY]-(p:Profile)
RETURN p.master_profile_id,
       [(p)-[:HAS_IDENTITY]->(identity:Identity) | {type: identity.type, value: identity.value}] AS all_identities;

// Get all identities for a specific profile
MATCH (p:Profile {master_profile_id: $profile_id})-[:HAS_IDENTITY]->(i:Identity)
RETURN collect({type: i.type, value: i.value}) AS identities;

// Find profile by email
MATCH (i:Identity {type: 'email', value: $email})<-[:HAS_IDENTITY]-(p:Profile)
RETURN p.master_profile_id AS master_profile_id;

// Find profile by deviceID
MATCH (i:Identity {type: 'deviceID', value: $device_id})<-[:HAS_IDENTITY]-(p:Profile)
RETURN p.master_profile_id AS master_profile_id;

// Count profiles and identities
MATCH (p:Profile)
WITH count(p) AS profile_count
MATCH (i:Identity)
WITH profile_count, count(i) AS identity_count
RETURN profile_count, identity_count;

// Find profiles with multiple identities
MATCH (p:Profile)-[:HAS_IDENTITY]->(i:Identity)
WITH p, count(i) AS identity_count
WHERE identity_count > 1
RETURN p.master_profile_id, identity_count
ORDER BY identity_count DESC;

// Find orphaned identities (no profile connection)
MATCH (i:Identity)
WHERE NOT (i)<-[:HAS_IDENTITY]-()
RETURN i.type, i.value;


// ============================================================
// SECTION 7: VERIFICATION & DEBUGGING
// ============================================================

// View all profiles and their identities
MATCH (p:Profile)-[:HAS_IDENTITY]->(i:Identity)
RETURN p.master_profile_id, 
       collect({type: i.type, value: i.value}) AS identities
ORDER BY p.master_profile_id;

// Visualize entire graph (use in Neo4j Browser)
MATCH (p:Profile)-[r:HAS_IDENTITY]->(i:Identity)
RETURN p, r, i;

// Count nodes by label
MATCH (n)
RETURN labels(n) AS label, count(*) AS count;

// Find duplicate profiles (profiles sharing same identity)
MATCH (i:Identity)<-[:HAS_IDENTITY]-(p:Profile)
WITH i, collect(p) AS profiles
WHERE size(profiles) > 1
RETURN i.type, i.value, [p IN profiles | p.master_profile_id] AS duplicate_profiles;

// Profile merge history (if you add metadata)
MATCH (p:Profile)
WHERE p.merged_from IS NOT NULL
RETURN p.master_profile_id, p.merged_from, p.merged_at
ORDER BY p.merged_at DESC;

// Check for profiles with no identities (shouldn't exist)
MATCH (p:Profile)
WHERE NOT (p)-[:HAS_IDENTITY]->()
RETURN p.master_profile_id;


// ============================================================
// SECTION 8: CREATE INDEXES (Run once on setup)
// ============================================================

// Index on Identity type and value (critical for performance)
CREATE INDEX identity_type_value IF NOT EXISTS
FOR (i:Identity) ON (i.type, i.value);

// Index on Profile master_profile_id
CREATE INDEX profile_master_id IF NOT EXISTS
FOR (p:Profile) ON (p.master_profile_id);

// Verify indexes
SHOW INDEXES;


// ============================================================
// SECTION 9: SAMPLE DATA FOR TESTING
// ============================================================

// Clear and create sample data
MATCH (n) DETACH DELETE n;

// Create Profile 1 (Alice)
CREATE (p1:Profile {master_profile_id: 'profile_alice', created_at: datetime()})
CREATE (i1:Identity {type: 'email', value: 'alice@example.com', created_at: datetime()})
CREATE (i2:Identity {type: 'deviceID', value: 'device_alice_laptop', created_at: datetime()})
CREATE (i3:Identity {type: 'phone', value: '+1234567890', created_at: datetime()})
CREATE (p1)-[:HAS_IDENTITY]->(i1)
CREATE (p1)-[:HAS_IDENTITY]->(i2)
CREATE (p1)-[:HAS_IDENTITY]->(i3);

// Create Profile 2 (Bob)
CREATE (p2:Profile {master_profile_id: 'profile_bob', created_at: datetime()})
CREATE (i4:Identity {type: 'email', value: 'bob@example.com', created_at: datetime()})
CREATE (i5:Identity {type: 'deviceID', value: 'device_bob_phone', created_at: datetime()})
CREATE (p2)-[:HAS_IDENTITY]->(i4)
CREATE (p2)-[:HAS_IDENTITY]->(i5);

// Verify sample data
MATCH (p:Profile)-[:HAS_IDENTITY]->(i:Identity)
RETURN p.master_profile_id, 
       collect({type: i.type, value: i.value}) AS identities;


// ============================================================
// END OF FILE
// ============================================================