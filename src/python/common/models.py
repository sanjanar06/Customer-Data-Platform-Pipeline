from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, EmailStr


class Identity(BaseModel):
    email: Optional[EmailStr] = None
    deviceID: Optional[str] = Field(None, alias="deviceID")
    userID: Optional[str] = Field(None, alias="userID")
    phone: Optional[str] = None
    cookie: Optional[str] = None
    
    class Config:
        populate_by_name = True


class CustomerEvent(BaseModel):
    event_type: str
    timestamp: int
    identities: Identity
    properties: Dict[str, Any] = Field(default_factory=dict)
    sequence: Optional[int] = None
    
    class Config:
        populate_by_name = True


class EventMetrics(BaseModel):
    total_events: int = 0
    unique_event_types: int = 0
    event_type_counts: Dict[str, int] = Field(default_factory=dict)


class TimeMetrics(BaseModel):
    days_since_first_event: float = 0.0
    days_since_last_event: float = 0.0
    customer_lifetime_days: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class ProductMetrics(BaseModel):
    products_viewed_count: int = 0
    products_viewed: List[str] = Field(default_factory=list)
    products_added_to_cart_count: int = 0
    products_purchased_count: int = 0
    products_purchased: List[str] = Field(default_factory=list)


class ComputedAttributes(BaseModel):
    lifetime_value: float = 0.0
    engagement_score: int = 0
    event_metrics: EventMetrics = Field(default_factory=EventMetrics)
    time_metrics: TimeMetrics = Field(default_factory=TimeMetrics)
    product_metrics: ProductMetrics = Field(default_factory=ProductMetrics)


class Profile(BaseModel):
    master_profile_id: str
    identities: Identity
    attributes: Dict[str, Any] = Field(default_factory=dict)
    event_history: List[Dict[str, Any]] = Field(default_factory=list)
    computed_attributes: Optional[ComputedAttributes] = None
    created_at: datetime
    updated_at: datetime
    last_event_type: Optional[str] = None
    batch_processed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
