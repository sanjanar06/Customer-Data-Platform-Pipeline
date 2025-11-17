"""
Unit Tests for Metrics Calculator
Tests all metric computation functions.
"""
import pytest
from src.python.batch.metrics_calculator import (
    compute_lifetime_value,
    compute_event_metrics,
    compute_time_metrics,
    compute_product_metrics,
    compute_engagement_score
)
from src.python.common.models import EventMetrics, TimeMetrics


class TestLifetimeValue:
    """Tests for lifetime value computation."""
    
    def test_compute_ltv_with_purchases(self, sample_event_history):
        """Test LTV calculation with purchase events."""
        ltv = compute_lifetime_value(sample_event_history)
        assert ltv == 1299.99
    
    def test_compute_ltv_no_purchases(self):
        """Test LTV with no purchase events."""
        events = [
            {"event_type": "page_view", "data": {"properties": {}}}
        ]
        ltv = compute_lifetime_value(events)
        assert ltv == 0.0
    
    def test_compute_ltv_empty_history(self):
        """Test LTV with empty event history."""
        ltv = compute_lifetime_value([])
        assert ltv == 0.0


class TestEventMetrics:
    """Tests for event metrics computation."""
    
    def test_compute_event_metrics(self, sample_event_history):
        """Test event metrics calculation."""
        metrics = compute_event_metrics(sample_event_history)
        
        assert isinstance(metrics, EventMetrics)
        assert metrics.total_events == 2
        assert metrics.unique_event_types == 2
        assert "page_view" in metrics.event_type_counts
        assert "purchase" in metrics.event_type_counts
    
    def test_compute_event_metrics_empty(self):
        """Test event metrics with empty history."""
        metrics = compute_event_metrics([])
        
        assert metrics.total_events == 0
        assert metrics.unique_event_types == 0
        assert metrics.event_type_counts == {}


class TestTimeMetrics:
    """Tests for time metrics computation."""
    
    def test_compute_time_metrics(self, sample_event_history):
        """Test time metrics calculation."""
        metrics = compute_time_metrics(sample_event_history)
        
        assert isinstance(metrics, TimeMetrics)
        assert metrics.customer_lifetime_days >= 0
        assert metrics.days_since_first_event >= 0
        assert metrics.days_since_last_event >= 0
        assert metrics.first_seen is not None
        assert metrics.last_seen is not None
    
    def test_compute_time_metrics_empty(self):
        """Test time metrics with empty history."""
        metrics = compute_time_metrics([])
        
        assert metrics.days_since_first_event == 0
        assert metrics.days_since_last_event == 0
        assert metrics.customer_lifetime_days == 0


class TestProductMetrics:
    """Tests for product metrics computation."""
    
    def test_compute_product_metrics(self):
        """Test product metrics calculation."""
        events = [
            {
                "event_type": "page_view",
                "data": {"properties": {"product_name": "MacBook Pro"}}
            },
            {
                "event_type": "add_to_cart",
                "data": {"properties": {"product_name": "MacBook Pro"}}
            },
            {
                "event_type": "purchase",
                "data": {"properties": {"product_name": "MacBook Pro"}}
            }
        ]
        
        metrics = compute_product_metrics(events)
        
        assert metrics.products_viewed_count == 1
        assert "MacBook Pro" in metrics.products_viewed
        assert metrics.products_added_to_cart_count == 1
        assert metrics.products_purchased_count == 1
        assert "MacBook Pro" in metrics.products_purchased
    
    def test_compute_product_metrics_no_products(self):
        """Test product metrics with no product data."""
        events = [{"event_type": "page_view", "data": {"properties": {}}}]
        metrics = compute_product_metrics(events)
        
        assert metrics.products_viewed_count == 0
        assert metrics.products_purchased_count == 0


class TestEngagementScore:
    """Tests for engagement score computation."""
    
    def test_high_engagement_score(self):
        """Test high engagement score calculation."""
        ltv = 2000.0
        event_metrics = EventMetrics(
            total_events=10,
            unique_event_types=5,
            event_type_counts={}
        )
        time_metrics = TimeMetrics(days_since_last_event=0.5)
        
        score = compute_engagement_score(ltv, event_metrics, time_metrics)
        
        assert score >= 70
        assert score <= 100
    
    def test_low_engagement_score(self):
        """Test low engagement score calculation."""
        ltv = 0.0
        event_metrics = EventMetrics(total_events=1, unique_event_types=1)
        time_metrics = TimeMetrics(days_since_last_event=100)
        
        score = compute_engagement_score(ltv, event_metrics, time_metrics)
        
        assert score >= 0
        assert score <= 40
    
    def test_engagement_score_max_100(self):
        """Test engagement score doesn't exceed 100."""
        ltv = 10000.0
        event_metrics = EventMetrics(total_events=100, unique_event_types=10)
        time_metrics = TimeMetrics(days_since_last_event=0.1)
        
        score = compute_engagement_score(ltv, event_metrics, time_metrics)
        
        assert score == 100
