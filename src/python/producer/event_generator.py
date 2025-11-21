from typing import List, Dict, Any
import time
from config.constants import (
    EVENT_TYPE_PAGE_VIEW,
    EVENT_TYPE_LOGIN,
    EVENT_TYPE_ADD_TO_CART,
    EVENT_TYPE_PURCHASE,
)

# Demo event sequence for identity stitching demonstration
DEMO_EVENTS: List[Dict[str, Any]] = [
    {
        "event_type": EVENT_TYPE_PAGE_VIEW,
        "identities": {
            "deviceID": "device_abc123"
        },
        "properties": {
            "page": "/home",
            "referrer": "google.com",
            "user_agent": "Mozilla/5.0"
        },
        "description": "Event 1: Anonymous visitor (device_abc123)"
    },
    {
        "event_type": EVENT_TYPE_LOGIN,
        "identities": {
            "deviceID": "device_abc123",
            "email": "user@example.com"
        },
        "properties": {
            "login_method": "password",
            "login_success": True
        },
        "description": "Event 2: User logs in (links email)"
    },
    {
        "event_type": EVENT_TYPE_PAGE_VIEW,
        "identities": {
            "email": "user@example.com"
        },
        "properties": {
            "page": "/products/laptop",
            "category": "electronics",
            "product_name": "MacBook Pro"
        },
        "description": "Event 3: Views product"
    },
    {
        "event_type": EVENT_TYPE_ADD_TO_CART,
        "identities": {
            "deviceID": "device_abc123",
            "email": "user@example.com"
        },
        "properties": {
            "product_id": "laptop_001",
            "product_name": "MacBook Pro",
            "price": 1299.99,
            "quantity": 1
        },
        "description": "Event 4: Adds to cart"
    },
    {
        "event_type": EVENT_TYPE_PAGE_VIEW,
        "identities": {
            "deviceID": "device_xyz789"
        },
        "properties": {
            "page": "/home",
            "user_agent": "Mobile Safari"
        },
        "description": "Event 5: Different device (creates 2nd profile)"
    },
    {
        "event_type": EVENT_TYPE_LOGIN,
        "identities": {
            "deviceID": "device_xyz789",
            "email": "user@example.com"
        },
        "properties": {
            "login_method": "password",
            "login_success": True
        },
        "description": "Event 6: THE MERGE! (same email, profiles merge)"
    },
    {
        "event_type": EVENT_TYPE_PURCHASE,
        "identities": {
            "deviceID": "device_xyz789",
            "email": "user@example.com"
        },
        "properties": {
            "order_id": "ORDER_12345",
            "total": 1299.99,
            "items": ["laptop_001"],
            "payment_method": "credit_card",
            "shipping_address": "123 Main St"
        },
        "description": "Event 7: Purchase complete"
    }
]

def get_hairball_events():
    events = []
    shared_device = "device_HAIRBALL_01"
    for i in range(1, 11):
        events.append({
            "event_type": "login",
            "identities": {
                "deviceID": shared_device,
                "email": f"victim_{i}@bad-merge.com"
            },
            "properties": {"risk": "high"},
            "description": f"Hairball Event {i}"
        })
    return events

def get_fuzzy_events():
    return [
        {
            "event_type": "login",
            "identities": {
                "deviceID": "device_A",
                "email": "reuben@gmail.com"  # Correct spelling
            },
            "properties": {"method": "password"},
            "description": "Event 1: Original User (Reuben)"
        },
        {
            "event_type": "page_view",
            "identities": {
                "deviceID": "device_B",
                "email": "reubn@gmail.com"   
            },
            "properties": {"page": "/home"},
            "description": "Event 2: User with Typo (Reubn)"
        }
    ]


def generate_event_with_timestamp(event_template: Dict[str, Any], sequence: int) -> Dict[str, Any]:
    event = event_template.copy()
    event["timestamp"] = int(time.time())
    event["sequence"] = sequence
    # Remove description (only for console output)
    event.pop("description", None)
    return event


def get_demo_events() -> List[Dict[str, Any]]:
    return DEMO_EVENTS
