import random
from typing import List, Dict, Any
import time
from config.constants import (
    EVENT_TYPE_PAGE_VIEW,
    EVENT_TYPE_LOGIN,
    EVENT_TYPE_ADD_TO_CART,
    EVENT_TYPE_PURCHASE,
)

def get_fuzzy_events():
    """
    This function is just to demonstrate fuzzy matching with two events.
    One event has the correct email, the other has a typo.  
    """
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

def get_demo_events() -> List[Dict[str, Any]]:
    return [
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

def introduce_typo(email: str) -> str:
    """
    Deliberately introduces a typo into an email address 
    to test Fuzzy Matching capabilities.
    """
    if "@" not in email: return email
    
    local, domain = email.split("@")
    if len(local) < 4: return email
    
    typo_type = random.choice(['swap', 'delete', 'double', 'none'])
    
    if typo_type == 'none':
        return email
        
    chars = list(local)
    idx = random.randint(0, len(chars) - 2)
    
    if typo_type == 'swap':
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
    elif typo_type == 'delete':
        del chars[idx]
    elif typo_type == 'double':
        chars.insert(idx, chars[idx])
        
    return "".join(chars) + "@" + domain

def get_large_scale_events(num_profiles=20) -> List[Dict[str, Any]]:
    """
    Generates 100+ events simulating a real user base.
    - 20 Users
    - 5-10 Events per user
    - Device switching
    - Email typos (Fuzzy Match test)
    """
    events = []
    base_time = int(time.time()) - 3600  # Start 1 hour ago
    
    # Product Catalog for realism
    products = [
        {"id": "P1", "name": "MacBook Pro", "price": 1299.99},
        {"id": "P2", "name": "AirPods Max", "price": 549.00},
        {"id": "P3", "name": "Mechanical Keyboard", "price": 149.50},
        {"id": "P4", "name": "4K Monitor", "price": 399.99}
    ]

    for i in range(num_profiles):
        # 1. Create a Persona
        base_name = f"user_{random.randint(1000, 9999)}"
        real_email = f"{base_name}@example.com"
        device_a = f"device_{base_name}_A"
        device_b = f"device_{base_name}_B"
        
        # 2. Simulate Journey
        # Step A: Browse on Device A (Anonymous)
        events.append({
            "event_type": EVENT_TYPE_PAGE_VIEW,
            "timestamp": base_time + random.randint(1, 60),
            "identities": {"deviceID": device_a},
            "properties": {"page": "/home"},
            "description": f"User {i}: Anon Browse (Device A)"
        })
        
        # Step B: Login on Device A (Links Email)
        events.append({
            "event_type": EVENT_TYPE_LOGIN,
            "timestamp": base_time + random.randint(61, 120),
            "identities": {"deviceID": device_a, "email": real_email},
            "properties": {"method": "password"},
            "description": f"User {i}: Login (Device A)"
        })
        
        # Step C: Browse on Device B (New Device)
        events.append({
            "event_type": EVENT_TYPE_PAGE_VIEW,
            "timestamp": base_time + random.randint(200, 300),
            "identities": {"deviceID": device_b},
            "properties": {"page": "/products"},
            "description": f"User {i}: Browse (Device B)"
        })
        
        # Step D: Login on Device B with TYPO (Tests Fuzzy Match)
        # 30% chance of typo
        login_email = introduce_typo(real_email) if random.random() < 0.3 else real_email
        desc = f"User {i}: Login Device B (Typo: {login_email})" if login_email != real_email else f"User {i}: Login Device B (Clean)"
        
        events.append({
            "event_type": EVENT_TYPE_LOGIN,
            "timestamp": base_time + random.randint(301, 400),
            "identities": {"deviceID": device_b, "email": login_email},
            "properties": {"method": "bio"},
            "description": desc
        })
        
        # Step E: Purchase (Conversion)
        if random.random() > 0.5: # 50% conversion rate
            prod = random.choice(products)
            events.append({
                "event_type": EVENT_TYPE_PURCHASE,
                "timestamp": base_time + random.randint(401, 600),
                "identities": {"deviceID": device_b, "email": real_email},
                "properties": {"total": prod["price"], "product": prod["name"]},
                "description": f"User {i}: Purchased {prod['name']}"
            })

    events.sort(key=lambda x: x["timestamp"])
    
    for idx, event in enumerate(events, 1):
        event["sequence"] = idx
        
    return events
