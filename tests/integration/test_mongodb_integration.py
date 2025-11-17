
import pytest


@pytest.mark.integration
class TestMongoDBIntegration:
    """Integration tests for MongoDB operations."""
    
    def test_mongodb_connection(self, mongo_client):
        """Test MongoDB connection."""
        # Should connect without error
        assert mongo_client is not None
        
        # Test ping
        result = mongo_client.admin.command('ping')
        assert result['ok'] == 1.0
    
    def test_create_and_read_profile(self, mongo_db):
        """Test creating and reading a profile."""
        collection = mongo_db["profiles"]
        
        # Create profile
        profile = {
            "master_profile_id": "integration_test_001",
            "identities": {"email": "integration@test.com"},
            "attributes": {},
            "event_history": []
        }
        
        result = collection.insert_one(profile)
        assert result.inserted_id is not None
        
        # Read profile
        found = collection.find_one({"master_profile_id": "integration_test_001"})
        assert found is not None
        assert found["identities"]["email"] == "integration@test.com"
    
    def test_update_profile(self, mongo_db):
        """Test updating a profile."""
        collection = mongo_db["profiles"]
        
        # Create
        profile = {
            "master_profile_id": "integration_test_002",
            "identities": {"email": "test2@example.com"},
            "computed_attributes": {"lifetime_value": 0}
        }
        collection.insert_one(profile)
        
        # Update
        collection.update_one(
            {"master_profile_id": "integration_test_002"},
            {"$set": {"computed_attributes.lifetime_value": 1299.99}}
        )
        
        # Verify
        updated = collection.find_one({"master_profile_id": "integration_test_002"})
        assert updated["computed_attributes"]["lifetime_value"] == 1299.99
    
    def test_query_profiles(self, mongo_db):
        """Test querying profiles."""
        collection = mongo_db["profiles"]
        
        # Insert multiple profiles
        profiles = [
            {"master_profile_id": f"test_{i}", "computed_attributes": {"lifetime_value": i * 100}}
            for i in range(1, 6)
        ]
        collection.insert_many(profiles)
        
        # Query high-value profiles
        high_value = list(collection.find(
            {"computed_attributes.lifetime_value": {"$gt": 300}}
        ))
        
        assert len(high_value) == 2  # test_4 and test_5
