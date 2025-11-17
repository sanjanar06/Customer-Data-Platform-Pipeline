"""
Metrics Calculator
Computes customer metrics from event history.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from collections import Counter
from config.constants import EVENT_TYPE_PURCHASE
from src.python.common.models import EventMetrics, TimeMetrics, ProductMetrics


def compute_lifetime_value(event_history: List[Dict[str, Any]]) -> float:
    """
    Compute total lifetime value from purchase events.
    
    Args:
        event_history: List of customer events
        
    Returns:
        Total purchase value
    """
    total = 0.0
    for event in event_history:
        if event.get("event_type") == EVENT_TYPE_PURCHASE:
            event_data = event.get("data", {})
            properties = event_data.get("properties", {})
            total += properties.get("total", 0.0)
    return round(total, 2)


def compute_event_metrics(event_history: List[Dict[str, Any]]) -> EventMetrics:
    """
    Compute event-based metrics.
    
    Args:
        event_history: List of customer events
        
    Returns:
        Event metrics
    """
    if not event_history:
        return EventMetrics()
    
    event_types = [e.get("event_type") for e in event_history]
    event_type_counts = dict(Counter(event_types))
    
    return EventMetrics(
        total_events=len(event_history),
        unique_event_types=len(event_type_counts),
        event_type_counts=event_type_counts
    )


def compute_time_metrics(event_history: List[Dict[str, Any]]) -> TimeMetrics:
    """
    Compute time-based metrics.
    
    Args:
        event_history: List of customer events
        
    Returns:
        Time metrics
    """
    if not event_history:
        return TimeMetrics()
    
    timestamps = [e.get("timestamp") for e in event_history if e.get("timestamp")]
    
    if not timestamps:
        return TimeMetrics()
    
    first_event_ts = min(timestamps)
    last_event_ts = max(timestamps)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    days_since_first = (now_ts - first_event_ts) / 86400
    days_since_last = (now_ts - last_event_ts) / 86400
    customer_lifetime = (last_event_ts - first_event_ts) / 86400
    
    return TimeMetrics(
        days_since_first_event=round(days_since_first, 1),
        days_since_last_event=round(days_since_last, 1),
        customer_lifetime_days=round(customer_lifetime, 1),
        first_seen=datetime.fromtimestamp(first_event_ts, tz=timezone.utc),
        last_seen=datetime.fromtimestamp(last_event_ts, tz=timezone.utc)
    )


def compute_product_metrics(event_history: List[Dict[str, Any]]) -> ProductMetrics:
    """
    Compute product-related metrics.
    
    Args:
        event_history: List of customer events
        
    Returns:
        Product metrics
    """
    products_viewed = set()
    products_added_to_cart = set()
    products_purchased = set()
    
    for event in event_history:
        event_type = event.get("event_type")
        event_data = event.get("data", {})
        properties = event_data.get("properties", {})
        
        product_name = properties.get("product_name")
        if not product_name:
            continue
        
        if event_type == "page_view":
            products_viewed.add(product_name)
        elif event_type == "add_to_cart":
            products_added_to_cart.add(product_name)
        elif event_type == EVENT_TYPE_PURCHASE:
            products_purchased.add(product_name)
    
    return ProductMetrics(
        products_viewed_count=len(products_viewed),
        products_viewed=list(products_viewed),
        products_added_to_cart_count=len(products_added_to_cart),
        products_purchased_count=len(products_purchased),
        products_purchased=list(products_purchased)
    )


def compute_engagement_score(
    lifetime_value: float,
    event_metrics: EventMetrics,
    time_metrics: TimeMetrics
) -> int:
    """
    Compute engagement score (0-100).
    
    Scoring breakdown:
    - Event activity: max 40 points
    - Purchase behavior: max 30 points
    - Recent activity: max 20 points
    - Diversity of actions: max 10 points
    
    Args:
        lifetime_value: Total customer lifetime value
        event_metrics: Event-based metrics
        time_metrics: Time-based metrics
        
    Returns:
        Engagement score (0-100)
    """
    score = 0
    
    # Event activity (max 40 points)
    total_events = event_metrics.total_events
    score += min(total_events * 5, 40)
    
    # Purchase behavior (max 30 points)
    if lifetime_value > 0:
        score += 15
    if lifetime_value > 1000:
        score += 15
    
    # Recent activity (max 20 points)
    days_since_last = time_metrics.days_since_last_event
    if days_since_last < 1:
        score += 20
    elif days_since_last < 7:
        score += 10
    elif days_since_last < 30:
        score += 5
    
    # Diversity of actions (max 10 points)
    unique_events = event_metrics.unique_event_types
    score += min(unique_events * 2, 10)
    
    return min(score, 100)
