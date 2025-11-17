from typing import Dict, Any
from fastapi import HTTPException
from config import settings
from config.logging_config import get_logger
from config.constants import MONGO_COLLECTION_PROFILES
from src.python.common.database import get_mongodb_client

logger = get_logger(__name__)


class ProfileService:
    
    @staticmethod
    def fetch_profile(profile_id: str) -> Dict[str, Any]:
        """
        Retrieve unified profile from MongoDB.
        
        Args:
            profile_id: Master profile ID
            
        Returns:
            Profile document
            
        Raises:
            HTTPException: If profile not found or database error
        """
        try:
            client = get_mongodb_client()
        except ConnectionError as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"MongoDB connection failed: {str(e)}"
            )
        try:
            db = client[settings.MONGO_DB]
            collection = db[MONGO_COLLECTION_PROFILES]
            
            profile = collection.find_one({"master_profile_id": profile_id})
            
            if not profile:
                logger.warning(f"Profile not found: {profile_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile {profile_id} not found"
                )
            
            profile.pop("_id", None)
            
            logger.info(f"Retrieved profile: {profile_id}")
            return profile
        finally:
            client.close()
