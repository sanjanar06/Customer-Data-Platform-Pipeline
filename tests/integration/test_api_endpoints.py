"""
Integration Tests for API Endpoints
Tests FastAPI endpoints with actual services.
"""
import pytest
from fastapi.testclient import TestClient
from src.python.api.main import app


client = TestClient(app)


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "CDP Personalization API"
        assert data["status"] == "running"
        assert "endpoints" in data
    
    def test_personalize_endpoint_not_found(self):
        """Test personalize endpoint with non-existent profile."""
        response = client.get("/api/personalize/nonexistent_profile")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_profile_summary_not_found(self):
        """Test profile summary with non-existent profile."""
        response = client.get("/api/profile/nonexistent_profile")
        
        assert response.status_code == 404
    
    @pytest.mark.skip(reason="Requires actual profile data in MongoDB")
    def test_personalize_endpoint_success(self):
        """Test personalize endpoint with valid profile."""
        # This test requires MongoDB to have actual profile data
        profile_id = "actual_profile_id"
        response = client.get(f"/api/personalize/{profile_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "profile_id" in data
        assert "offer_type" in data
        assert "title" in data
        assert "message" in data
    
    def test_api_docs_accessible(self):
        """Test API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
