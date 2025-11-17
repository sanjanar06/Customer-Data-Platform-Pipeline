"""
Unit Tests for AI Service
Tests AI/LLM service functionality.
"""
import pytest
from unittest.mock import Mock, patch
from src.python.api.services.ai_service import AIService


class TestPromptBuilding:
    """Tests for prompt building."""
    
    def test_build_personalization_prompt(self, sample_profile):
        """Test prompt generation from profile."""
        prompt = AIService.build_personalization_prompt(sample_profile)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert sample_profile["master_profile_id"] in prompt
        assert "CUSTOMER PROFILE" in prompt
        assert "BEHAVIOR INSIGHTS" in prompt
    
    def test_prompt_includes_ltv(self, sample_profile):
        """Test prompt includes lifetime value."""
        prompt = AIService.build_personalization_prompt(sample_profile)
        ltv = sample_profile["computed_attributes"]["lifetime_value"]
        
        assert f"${ltv:,.2f}" in prompt
    
    def test_prompt_includes_engagement(self, sample_profile):
        """Test prompt includes engagement score."""
        prompt = AIService.build_personalization_prompt(sample_profile)
        engagement = sample_profile["computed_attributes"]["engagement_score"]
        
        assert str(engagement) in prompt


class TestMockOfferGeneration:
    """Tests for mock offer generation."""
    
    def test_generate_mock_offer_high_value(self):
        """Test mock offer for high-value customer."""
        profile = {
            "master_profile_id": "test_123",
            "computed_attributes": {
                "lifetime_value": 2000.0
            }
        }
        
        offer = AIService.generate_mock_offer(profile)
        
        assert offer["offer_type"] == "loyalty"
        assert "VIP" in offer["title"]
        assert "products" in offer
        assert "discount" in offer
    
    def test_generate_mock_offer_existing_customer(self):
        """Test mock offer for existing customer."""
        profile = {
            "master_profile_id": "test_123",
            "computed_attributes": {
                "lifetime_value": 500.0
            }
        }
        
        offer = AIService.generate_mock_offer(profile)
        
        assert offer["offer_type"] == "cross-sell"
        assert "products" in offer
        assert len(offer["products"]) > 0
    
    def test_generate_mock_offer_new_visitor(self):
        """Test mock offer for new visitor."""
        profile = {
            "master_profile_id": "test_123",
            "computed_attributes": {
                "lifetime_value": 0.0
            }
        }
        
        offer = AIService.generate_mock_offer(profile)
        
        assert offer["offer_type"] == "welcome"
        assert "Welcome" in offer["title"] or "welcome" in offer["title"]
        assert "products" in offer


class TestOfferValidation:
    """Tests for offer data validation."""
    
    def test_mock_offer_has_required_fields(self, sample_profile):
        """Test mock offers have all required fields."""
        offer = AIService.generate_mock_offer(sample_profile)
        
        required_fields = ["offer_type", "title", "message", "products", "discount", "reasoning"]
        for field in required_fields:
            assert field in offer
    
    def test_mock_offer_products_is_list(self, sample_profile):
        """Test products field is a list."""
        offer = AIService.generate_mock_offer(sample_profile)
        
        assert isinstance(offer["products"], list)
        assert len(offer["products"]) > 0
