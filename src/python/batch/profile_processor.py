"""
Profile Processor
Processes customer profiles for batch computation.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from pymongo import MongoClient
from config.logging_config import get_logger
from config.constants import MONGO_COLLECTION_PROFILES
from src.python.common.models import ComputedAttributes
from .metrics_calculator import (
    compute_lifetime_value,
    compute_event_metrics,
    compute_time_metrics,
    compute_product_metrics,
    compute_engagement_score
)

logger = get_logger(__name__)


class ProfileProcessor:
    """Processes customer profiles to compute aggregate metrics."""
    
    def __init__(self, client: MongoClient, database: str):
        """
        Initialize profile processor.
        
        Args:
            client: MongoDB client
            database: Database name
        """
        self.db = client[database]
        self.profiles_collection = self.db[MONGO_COLLECTION_PROFILES]
    
    def process_all_profiles(self, limit: int = None) -> int:
        """
        Process all profiles and compute metrics.
        
        Args:
            limit: Maximum number of profiles to process (None = all)
            
        Returns:
            Number of profiles processed
        """
        query = {}
        profiles = list(self.profiles_collection.find(query).limit(limit) if limit else self.profiles_collection.find(query))
        
        total = len(profiles)
        logger.info(f"Processing {total} profiles...")
        
        if not profiles:
            logger.warning("No profiles found. Run the producer and Flink job first!")
            return 0
        
        for idx, profile in enumerate(profiles, 1):
            self._process_single_profile(profile, idx, total)
        
        logger.info(f"Batch job complete! Processed {total} profiles")
        return total
    
    def _process_single_profile(self, profile: Dict[str, Any], idx: int, total: int) -> None:
        """
        Process a single profile.
        
        Args:
            profile: Profile document
            idx: Current index
            total: Total profiles
        """
        master_profile_id = profile.get("master_profile_id", "unknown")
        event_history = profile.get("event_history", [])
        
        logger.info(f"[{idx}/{total}] Processing profile: {master_profile_id}")
        
        # Compute all metrics
        lifetime_value = compute_lifetime_value(event_history)
        event_metrics = compute_event_metrics(event_history)
        time_metrics = compute_time_metrics(event_history)
        product_metrics = compute_product_metrics(event_history)
        
        # Compute engagement score
        engagement_score = compute_engagement_score(
            lifetime_value,
            event_metrics,
            time_metrics
        )
        
        # Build computed attributes
        computed_attrs = ComputedAttributes(
            lifetime_value=lifetime_value,
            engagement_score=engagement_score,
            event_metrics=event_metrics,
            time_metrics=time_metrics,
            product_metrics=product_metrics
        )
        
        # Log summary
        logger.info(f"Lifetime Value: ${lifetime_value:,.2f}")
        logger.info(f"Total Events: {event_metrics.total_events}")
        logger.info(f"Engagement Score: {engagement_score}/100")
        logger.info(f"Customer Lifetime: {time_metrics.customer_lifetime_days} days")
        logger.info(f"Products Purchased: {product_metrics.products_purchased_count}")
        
        # Update MongoDB
        self._update_profile(profile["_id"], computed_attrs)
    
    def _update_profile(self, profile_id: Any, computed_attrs: ComputedAttributes) -> None:
        """
        Update profile with computed attributes.
        
        Args:
            profile_id: Profile _id
            computed_attrs: Computed attributes
        """
        result = self.profiles_collection.update_one(
            {"_id": profile_id},
            {
                "$set": {
                    "computed_attributes": computed_attrs.model_dump(),
                    "batch_processed_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count > 0:
            logger.debug("Updated with computed attributes")
        else:
            logger.warning("No changes made")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics across all profiles.
        
        Returns:
            Summary statistics
        """
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_profiles": {"$sum": 1},
                    "total_ltv": {"$sum": "$computed_attributes.lifetime_value"},
                    "avg_engagement": {"$avg": "$computed_attributes.engagement_score"},
                    "total_events": {"$sum": "$computed_attributes.event_metrics.total_events"}
                }
            }
        ]
        
        result = list(self.profiles_collection.aggregate(pipeline))
        
        if result:
            return result[0]
        return {}
    
    def get_top_profiles(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top profiles by lifetime value.
        
        Args:
            limit: Number of profiles to return
            
        Returns:
            List of top profiles
        """
        return list(
            self.profiles_collection.find(
                {"computed_attributes.lifetime_value": {"$gt": 0}},
                {
                    "master_profile_id": 1,
                    "identities.email": 1,
                    "computed_attributes.lifetime_value": 1,
                    "computed_attributes.engagement_score": 1
                }
            )
            .sort("computed_attributes.lifetime_value", -1)
            .limit(limit)
        )
