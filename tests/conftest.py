"""
Pytest Configuration and Fixtures
Shared test fixtures and configuration for all tests.
"""
import pytest
import os
import sys
from typing import Generator
from pymongo import MongoClient
from neo4j import GraphDatabase

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import settings
from src.python.common.database import get_mongodb_client, get_neo4j_driver


# ============================================================
# Configuration Fixtures
# ============================================================

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    # Use test database names
    original_mongo_db = settings.MONGO_DB
    original_environment = settings.ENVIRONMENT
    
    settings.MONGO_DB = "cdp_test"
    settings.ENVIRONMENT = "test"
    
    yield settings
    
    # Restore original settings
    settings.MONGO_DB = original_mongo_db
    settings.ENVIRONMENT = original_environment


# ============================================================
# Database Fixtures
# ============================================================

@pytest.fixture(scope="function")
def mongo_client() -> Generator[MongoClient, None, None]:
    """Provide MongoDB client for testing."""
    client = get_mongodb_client()
    yield client
    # Cleanup: drop test database
    client.drop_database("cdp_test")
    client.close()


@pytest.fixture(scope="function")
def mongo_db(mongo_client):
    """Provide MongoDB database for testing."""
    return mongo_client["cdp_test"]


@pytest.fixture(scope="function")
def neo4j_driver() -> Generator:
    """Provide Neo4j driver for testing."""
    driver = get_neo4j_driver()
    yield driver
    # Cleanup: delete all test nodes
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()


# ============================================================
# Sample Data Fixtures
# ============================================================

@pytest.fixture
def sample_customer_event():
    """Sample customer event for testing."""
    return {
        "event_type": "page_view",
        "timestamp": 1699999999,
        "identities": {
            "deviceID": "test_device_123",
            "email": "test@example.com"
        },
        "properties": {
            "page": "/products",
            "category": "electronics"
        },
        "sequence": 1
    }


@pytest.fixture
def sample_profile():
    """Sample customer profile for testing."""
    return {
        "master_profile_id": "profile_test_123",
        "identities": {
            "email": "test@example.com",
            "deviceID": "test_device_123"
        },
        "attributes": {
            "product_name": "MacBook Pro",
            "price": 1299.99
        },
        "event_history": [],
        "computed_attributes": {
            "lifetime_value": 1299.99,
            "engagement_score": 85,
            "event_metrics": {
                "total_events": 5,
                "unique_event_types": 3,
                "event_type_counts": {
                    "page_view": 2,
                    "add_to_cart": 1,
                    "purchase": 2
                }
            }
        }
    }


@pytest.fixture
def sample_event_history():
    """Sample event history for testing."""
    return [
        {
            "event_type": "page_view",
            "timestamp": 1699999990,
            "data": {
                "properties": {"page": "/home"}
            }
        },
        {
            "event_type": "purchase",
            "timestamp": 1699999995,
            "data": {
                "properties": {
                    "total": 1299.99,
                    "product_name": "MacBook Pro"
                }
            }
        }
    ]


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    return {
        "offer_type": "loyalty",
        "title": "VIP Customer Exclusive",
        "message": "Thank you for being a valued customer!",
        "products": ["Premium Accessories", "Extended Warranty"],
        "discount": "20% off",
        "reasoning": "High-value customer - reward loyalty"
    }
