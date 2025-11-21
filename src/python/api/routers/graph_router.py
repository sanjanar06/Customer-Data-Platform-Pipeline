"""
Identity Graph Router
API endpoints for graph operations and debugging.
"""
from fastapi import APIRouter
from config.logging_config import get_logger
from ..services.ai_service import AIService
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

@router.get("/anomalies")
async def check_graph_anomalies(email_threshold: int = 3, device_threshold: int = 5):
    """
    Scan the Identity Graph for suspicious 'supernodes' (hairballs).
    Useful for detecting shared devices (library computers) or fraud.
    """
    return GraphService.detect_anomalies(email_threshold, device_threshold)

@router.get("/explain/{profile_id}")
async def explain_profile_merge(profile_id: str):
    """
    1. Fetch the graph cluster for the profile.
    2. Ask AI to explain the relationships.
    """
    # 1. Get the raw graph data
    cluster_data = GraphService.get_profile_cluster(profile_id)
    
    # 2. Get AI analysis
    explanation = AIService.explain_identity_cluster(cluster_data)
    
    # 3. Return combined result
    return {
        "profile_id": profile_id,
        "graph_summary": {
            "total_identities": cluster_data.get("total_identities"),
            "identity_preview": cluster_data.get("identities")[:5] # Show first 5 only
        },
        "ai_diagnosis": explanation
    }

@router.post("/split")
async def split_profile_identity(profile_id: str, identity_type: str, identity_value: str):
    """
    Fix a bad merge by detaching a specific identity (email/device) 
    and moving it to a new profile.
    """
    logger.info(f"Request to split {identity_value} from {profile_id}")
    return GraphService.split_identity(profile_id, identity_type, identity_value)