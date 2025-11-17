from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Response model for personalized offers
class PersonalizedOffer(BaseModel):
    profile_id: str
    offer_type: str
    title: str
    message: str
    products: Optional[List[str]] = []
    discount: Optional[str] = None
    reasoning: Optional[str] = None
    generated_at: str

# Debugging schema for profile summaries
class ProfileSummary(BaseModel):
    master_profile_id: str
    identities: Dict[str, Any]
    lifetime_value: float
    engagement_score: int
    total_events: int
    last_event_type: str
