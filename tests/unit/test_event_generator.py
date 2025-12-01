"""
Unit Tests for Event Generator
Tests event generation logic.
"""
import pytest
from src.python.producer.event_generator import (
    get_demo_events,
    DEMO_EVENTS
)


class TestEventGeneration:
    """Tests for event generation functions."""
    
    def test_get_demo_events(self):
        """Test retrieving demo events."""
        events = get_demo_events()
        
        assert isinstance(events, list)
        assert len(events) == len(DEMO_EVENTS)
        assert len(events) == 7  # Known demo event count
    
    def test_demo_events_structure(self):
        """Test demo events have required fields."""
        events = get_demo_events()
        
        for event in events:
            assert "event_type" in event
            assert "identities" in event
            assert "properties" in event
            assert "description" in event


class TestDemoEventSequence:
    """Tests for the demo event sequence."""
    
    def test_first_event_anonymous(self):
        """Test first event is anonymous visitor."""
        events = get_demo_events()
        first = events[0]
        
        assert first["event_type"] == "page_view"
        assert "deviceID" in first["identities"]
        assert "email" not in first["identities"]
    
    def test_login_event_links_email(self):
        """Test login event includes email."""
        events = get_demo_events()
        login_event = events[1]
        
        assert login_event["event_type"] == "login"
        assert "deviceID" in login_event["identities"]
        assert "email" in login_event["identities"]
    
    def test_purchase_event_complete(self):
        """Test purchase event has all required fields."""
        events = get_demo_events()
        purchase_event = events[-1]  # Last event is purchase
        
        assert purchase_event["event_type"] == "purchase"
        assert "order_id" in purchase_event["properties"]
        assert "total" in purchase_event["properties"]
        assert purchase_event["properties"]["total"] > 0
