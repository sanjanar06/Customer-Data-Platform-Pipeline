from typing import Dict, Any, List
from fastapi import HTTPException
from config.logging_config import get_logger
from src.python.common.database import Neo4jContext

logger = get_logger(__name__)

class GraphService:
    
    @staticmethod
    def _execute_read_query(query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Helper to run Neo4j read transaction."""
        with Neo4jContext() as driver:
            with driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
    
    @staticmethod
    def _execute_write_query(query: str, parameters: Dict[str, Any] = None) -> None:
        """Helper to run Neo4j write transaction."""
        with Neo4jContext() as driver:
            with driver.session() as session:
                session.run(query, parameters)

    @staticmethod
    def get_profile_cluster(profile_id: str) -> Dict[str, Any]:
        """
        Retrieves the entire identity cluster for a given master profile ID.
        This forms the core data for the D3.js visualization.
        """
        query = """
        MATCH (p:Profile {master_profile_id: $profile_id})-[:HAS_IDENTITY]->(i:Identity)
        WITH p, collect({type: i.type, value: i.value}) AS identities, count(i) AS total_identities
        OPTIONAL MATCH (p)-[r:LINK]->(other) // Placeholder for future cross-profile links
        RETURN 
          p.master_profile_id AS master_profile_id,
          identities,
          total_identities,
          collect({target: other.master_profile_id, rel_type: type(r)}) AS related_profiles
        """
        try:
            results = GraphService._execute_read_query(query, {"profile_id": profile_id})
            if not results:
                raise HTTPException(status_code=404, detail=f"Graph cluster for {profile_id} not found")
            
            # Simple aggregation to create the graph model for the front-end
            first_record = results[0]
            
            return {
                "profile_id": first_record['master_profile_id'],
                "identities": first_record['identities'],
                "total_identities": first_record['total_identities'],
                "connections": first_record['related_profiles']
            }
            
        except ConnectionError as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise HTTPException(status_code=503, detail="Neo4j connection failed")


    @staticmethod
    def merge_profiles(source_id: str, target_id: str) -> None:
        """
        Manually merge two profiles (admin/debugger function).
        Moves all identities/relationships from SOURCE to TARGET, then deletes SOURCE.
        """
        query = """
        MATCH (source:Profile {master_profile_id: $source_id})
        MATCH (target:Profile {master_profile_id: $target_id})
        
        // 1. Re-link identities from source to target
        MATCH (source)-[r:HAS_IDENTITY]->(i:Identity)
        MERGE (target)-[:HAS_IDENTITY]->(i)
        
        // 2. Delete the source profile and its relationships
        DETACH DELETE source
        """
        try:
            GraphService._execute_write_query(query, {"source_id": source_id, "target_id": target_id})
            logger.info(f"Manually merged profile {source_id} into {target_id}")
        except Exception as e:
            logger.error(f"Neo4j merge failed: {e}")
            raise HTTPException(status_code=500, detail="Manual profile merge failed")
            
    @staticmethod
    def detect_anomalies(threshold_emails: int = 3, threshold_devices: int = 5) -> Dict[str, Any]:
        """
        Scans the graph for 'Hairball' profiles that might represent 
        shared devices or bad merges.
        """
        # Query 1: Find profiles with too many emails (potential shared account or bad merge)
        email_query = """
        MATCH (p:Profile)-[:HAS_IDENTITY]->(i:Identity {type: 'email'})
        WITH p, count(i) AS email_count, collect(i.value) AS emails
        WHERE email_count >= $threshold
        RETURN p.master_profile_id AS profile_id, email_count, emails
        ORDER BY email_count DESC
        LIMIT 10
        """
        
        # Query 2: Find profiles with too many devices (potential public kiosk)
        device_query = """
        MATCH (p:Profile)-[:HAS_IDENTITY]->(i:Identity {type: 'deviceID'})
        WITH p, count(i) AS device_count, collect(i.value) AS devices
        WHERE device_count >= $threshold
        RETURN p.master_profile_id AS profile_id, device_count, devices
        ORDER BY device_count DESC
        LIMIT 10
        """
        
        try:
            suspicious_emails = GraphService._execute_read_query(email_query, {"threshold": threshold_emails})
            suspicious_devices = GraphService._execute_read_query(device_query, {"threshold": threshold_devices})
            
            return {
                "summary": f"Found {len(suspicious_emails)} profiles with >{threshold_emails} emails and {len(suspicious_devices)} with >{threshold_devices} devices.",
                "high_email_profiles": suspicious_emails,
                "high_device_profiles": suspicious_devices
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to run anomaly check")
    
    @staticmethod
    def split_identity(profile_id: str, identity_type: str, identity_value: str) -> Dict[str, Any]:
        """
        'Graph Surgery': Detaches a specific identity from a profile and 
        assigns it to a brand new profile.
        Useful for fixing 'Hairballs' or bad merges.
        """
        query = """
        MATCH (old_p:Profile {master_profile_id: $profile_id})-[r:HAS_IDENTITY]->(i:Identity {type: $type, value: $value})
        
        // 1. Delete the old relationship
        DELETE r
        
        // 2. Create a NEW Profile for this identity
        CREATE (new_p:Profile {
            master_profile_id: 'profile_' + toString(randomUUID()), 
            created_at: datetime()
        })
        
        // 3. Link identity to the new profile
        MERGE (new_p)-[:HAS_IDENTITY]->(i)
        
        RETURN old_p.master_profile_id AS old_id, new_p.master_profile_id AS new_id
        """
        
        try:
            result = GraphService._execute_read_query(query, {
                "profile_id": profile_id,
                "type": identity_type,
                "value": identity_value
            })
            
            if not result:
                raise HTTPException(status_code=404, detail="Identity or Profile not found")
            
            return {
                "status": "success", 
                "message": f"Identity {identity_value} moved from {result[0]['old_id']} to {result[0]['new_id']}",
                "new_profile_id": result[0]['new_id']
            }
            
        except Exception as e:
            logger.error(f"Split failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to split profile")