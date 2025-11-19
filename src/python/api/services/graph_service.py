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
        WITH p, collect({type: i.type, value: i.value}) AS identities
        OPTIONAL MATCH (p)-[r:LINK]->(other) // Placeholder for future cross-profile links
        RETURN 
          p.master_profile_id AS master_profile_id,
          identities,
          count(i) AS total_identities,
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
            
    # Placeholder for split_profiles method...