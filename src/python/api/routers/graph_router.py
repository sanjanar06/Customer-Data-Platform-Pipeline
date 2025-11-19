"""
Identity Graph Router
API endpoints for graph operations and debugging.
"""
from fastapi import APIRouter
from config.logging_config import get_logger
from ..services.graph_service import GraphService

logger = get_logger(__name__)

# Use a separate router prefix for admin/debugger tools
router = APIRouter(prefix="/api/graph", tags=["identity_graph"])


@router.get("/cluster/{profile_id}")
async def get_cluster_data(profile_id: str):
    """
    Retrieve all nodes and edges related to a profile for visualization/debugging.
    """
    logger.info(f"Graph cluster request for profile: {profile_id}")
    return GraphService.get_profile_cluster(profile_id)


@router.post("/merge")
async def merge_profiles_manual(source_id: str, target_id: str):
    """
    Manual override to merge a source profile into a target profile.
    This is an administrative/debugging tool.
    """
    logger.warning(f"MANUAL MERGE REQUEST: Merging {source_id} into {target_id}")
    
    # 1. Perform Neo4j merge
    GraphService.merge_profiles(source_id, target_id)
    
    # 2. Add: Trigger MongoDB cleanup (like Flink does, but manually)
    
    return {"status": "success", "message": f"Profile {source_id} merged into {target_id}. MongoDB cleanup pending."}