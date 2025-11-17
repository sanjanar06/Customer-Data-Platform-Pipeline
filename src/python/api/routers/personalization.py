"""
Personalization Router
API endpoints for personalized offers and profile queries.
"""
from datetime import datetime
from fastapi import APIRouter
from config.logging_config import get_logger
from ..models.schemas import PersonalizedOffer, ProfileSummary
from ..services.profile_service import ProfileService
from ..services.ai_service import AIService

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["personalization"])


@router.get("/personalize/{profile_id}", response_model=PersonalizedOffer)
async def personalize(profile_id: str):
    """
    Generate a personalized offer for a customer.
    
    This implements the complete RAG pipeline:
    1. Retrieve: Fetch profile from MongoDB
    2. Augment: Build context-rich prompt
    3. Generate: Use Gemini to create offer
    
    Args:
        profile_id: Customer's master profile ID
        
    Returns:
        Personalized offer
    """
    logger.info(f"Personalization request for profile: {profile_id}")
    
    # Step 1: RETRIEVE profile from MongoDB
    profile = ProfileService.fetch_profile(profile_id)
    
    # Step 2 & 3: AUGMENT prompt and GENERATE offer
    offer_data = AIService.generate_personalized_offer(profile)
    
    # Step 4: Return structured response
    return PersonalizedOffer(
        profile_id=profile_id,
        offer_type=offer_data.get("offer_type", "generic"),
        title=offer_data.get("title", "Special Offer"),
        message=offer_data.get("message", ""),
        products=offer_data.get("products", []),
        discount=offer_data.get("discount"),
        reasoning=offer_data.get("reasoning"),
        generated_at=datetime.utcnow().isoformat()
    )


@router.get("/profile/{profile_id}", response_model=ProfileSummary)
async def get_profile_summary(profile_id: str):
    logger.info(f"Profile summary request for: {profile_id}")
    
    profile = ProfileService.fetch_profile(profile_id)
    computed = profile.get("computed_attributes", {})
    event_metrics = computed.get("event_metrics", {})
    
    return ProfileSummary(
        master_profile_id=profile.get("master_profile_id"),
        identities=profile.get("identities", {}),
        lifetime_value=computed.get("lifetime_value", 0),
        engagement_score=computed.get("engagement_score", 0),
        total_events=event_metrics.get("total_events", 0),
        last_event_type=profile.get("last_event_type", "unknown")
    )
