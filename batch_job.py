#!/usr/bin/env python3
"""
Day 10: Mock Spark Batch Job
Simulates a nightly batch job that computes aggregate metrics on customer profiles.
"""

from pymongo import MongoClient
from datetime import datetime, timezone
from collections import Counter
import sys

def connect_mongodb():
    """Connect to MongoDB"""
    try:
        client = MongoClient(
            "mongodb://admin:password123@localhost:27017/",
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
        return client
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        sys.exit(1)

def compute_lifetime_value(profile):
    """Compute total lifetime value from purchase events"""
    total = 0.0
    event_history = profile.get("event_history", [])
    for event in event_history:
        if event.get("event_type") == "purchase":
            event_data = event.get("data", {})
            properties = event_data.get("properties", {})
            total += properties.get("total", 0.0)
    return round(total, 2)

def compute_event_metrics(profile):
    """Compute event-based metrics"""
    event_history = profile.get("event_history", [])
    
    if not event_history:
        return {
            "total_events": 0,
            "unique_event_types": 0,
            "event_type_counts": {}
        }
    
    event_types = [e.get("event_type") for e in event_history]
    event_type_counts = dict(Counter(event_types))
    
    return {
        "total_events": len(event_history),
        "unique_event_types": len(event_type_counts),
        "event_type_counts": event_type_counts
    }

def compute_time_metrics(profile):
    """Compute time-based metrics"""
    event_history = profile.get("event_history", [])
    
    if not event_history:
        return {
            "days_since_first_event": 0,
            "days_since_last_event": 0,
            "customer_lifetime_days": 0
        }
    
    timestamps = [e.get("timestamp") for e in event_history if e.get("timestamp")]
    
    if not timestamps:
        return {
            "days_since_first_event": 0,
            "days_since_last_event": 0,
            "customer_lifetime_days": 0
        }
    
    first_event_ts = min(timestamps)
    last_event_ts = max(timestamps)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    days_since_first = (now_ts - first_event_ts) / 86400
    days_since_last = (now_ts - last_event_ts) / 86400
    customer_lifetime = (last_event_ts - first_event_ts) / 86400
    
    return {
        "days_since_first_event": round(days_since_first, 1),
        "days_since_last_event": round(days_since_last, 1),
        "customer_lifetime_days": round(customer_lifetime, 1),
        "first_seen": datetime.fromtimestamp(first_event_ts, tz=timezone.utc),
        "last_seen": datetime.fromtimestamp(last_event_ts, tz=timezone.utc)
    }

def compute_product_metrics(profile):
    """Compute product-related metrics"""
    event_history = profile.get("event_history", [])
    
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
        elif event_type == "purchase":
            products_purchased.add(product_name)
    
    return {
        "products_viewed_count": len(products_viewed),
        "products_viewed": list(products_viewed),
        "products_added_to_cart_count": len(products_added_to_cart),
        "products_purchased_count": len(products_purchased),
        "products_purchased": list(products_purchased)
    }

def compute_engagement_score(profile, metrics):
    """Compute engagement score (0-100)"""
    score = 0
    
    # Event activity (max 40 points)
    total_events = metrics["event_metrics"]["total_events"]
    score += min(total_events * 5, 40)
    
    # Purchase behavior (max 30 points)
    ltv = metrics["lifetime_value"]
    if ltv > 0:
        score += 15
    if ltv > 1000:
        score += 15
    
    # Recent activity (max 20 points)
    days_since_last = metrics["time_metrics"]["days_since_last_event"]
    if days_since_last < 1:
        score += 20
    elif days_since_last < 7:
        score += 10
    elif days_since_last < 30:
        score += 5
    
    # Diversity of actions (max 10 points)
    unique_events = metrics["event_metrics"]["unique_event_types"]
    score += min(unique_events * 2, 10)
    
    return min(score, 100)

def process_profiles(client):
    """Main batch processing logic"""
    db = client["cdp"]
    profiles_collection = db["profiles"]
    
    profiles = list(profiles_collection.find({}))
    print(f"\n📊 Processing {len(profiles)} profiles...")
    print("=" * 60)
    
    if not profiles:
        print("⚠️  No profiles found. Run Day 9 demo first!")
        return
    
    for idx, profile in enumerate(profiles, 1):
        master_profile_id = profile.get("master_profile_id", "unknown")
        
        print(f"\n[{idx}/{len(profiles)}] Profile: {master_profile_id}")
        print("-" * 60)
        
        # Compute all metrics
        lifetime_value = compute_lifetime_value(profile)
        event_metrics = compute_event_metrics(profile)
        time_metrics = compute_time_metrics(profile)
        product_metrics = compute_product_metrics(profile)
        
        computed_metrics = {
            "lifetime_value": lifetime_value,
            "event_metrics": event_metrics,
            "time_metrics": time_metrics,
            "product_metrics": product_metrics
        }
        
        engagement_score = compute_engagement_score(profile, computed_metrics)
        computed_metrics["engagement_score"] = engagement_score
        
        # Print summary
        print(f"   💰 Lifetime Value: ${lifetime_value:,.2f}")
        print(f"   📈 Total Events: {event_metrics['total_events']}")
        print(f"   🎯 Engagement Score: {engagement_score}/100")
        print(f"   🕒 Customer Lifetime: {time_metrics['customer_lifetime_days']} days")
        print(f"   📦 Products Purchased: {product_metrics['products_purchased_count']}")
        
        # Update MongoDB
        update_result = profiles_collection.update_one(
            {"_id": profile["_id"]},
            {
                "$set": {
                    "computed_attributes": computed_metrics,
                    "batch_processed_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if update_result.modified_count > 0:
            print(f"   ✅ Updated with computed attributes")
        else:
            print(f"   ⚠️  No changes made")
    
    print("\n" + "=" * 60)
    print("✅ Batch job complete!")
    print("=" * 60)

def print_summary(client):
    """Print summary statistics"""
    db = client["cdp"]
    profiles_collection = db["profiles"]
    
    print("\n" + "=" * 60)
    print("BATCH JOB SUMMARY")
    print("=" * 60)
    
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_profiles": {"$sum": 1},
                "total_ltv": {"$sum": "$computed_attributes.lifetime_value"},
                "avg_engagement": {"$avg": "$computed_attributes.engagement_score"},
                "total_events": {"$sum": "$computed_attributes.event_metrics.total_events"}
            }
        }
    ]
    
    result = list(profiles_collection.aggregate(pipeline))
    
    if result:
        stats = result[0]
        print(f"\n📊 Profiles Processed: {stats.get('total_profiles', 0)}")
        print(f"💰 Total LTV: ${stats.get('total_ltv', 0):,.2f}")
        print(f"📈 Avg Engagement Score: {stats.get('avg_engagement', 0):.1f}/100")
        print(f"📝 Total Events: {stats.get('total_events', 0)}")
    
    print("\n🏆 Top Profiles by Lifetime Value:")
    print("-" * 60)
    
    top_profiles = profiles_collection.find(
        {"computed_attributes.lifetime_value": {"$gt": 0}},
        {
            "master_profile_id": 1,
            "identities.email": 1,
            "computed_attributes.lifetime_value": 1,
            "computed_attributes.engagement_score": 1
        }
    ).sort("computed_attributes.lifetime_value", -1).limit(5)
    
    for idx, profile in enumerate(top_profiles, 1):
        email = profile.get("identities", {}).get("email", "N/A")
        ltv = profile.get("computed_attributes", {}).get("lifetime_value", 0)
        engagement = profile.get("computed_attributes", {}).get("engagement_score", 0)
        print(f"{idx}. {email:30} | LTV: ${ltv:8,.2f} | Engagement: {engagement:3}/100")
    
    print("\n" + "=" * 60)

def main():
    print("=" * 60)
    print("CDP BATCH JOB - Mock Spark Processing")
    print("=" * 60)
    print("\nThis simulates a nightly Spark job that:")
    print("  1. Reads profiles from MongoDB")
    print("  2. Computes aggregate metrics")
    print("  3. Writes computed attributes back")
    print("")
    
    client = connect_mongodb()
    
    try:
        process_profiles(client)
        print_summary(client)
        
        print("\n💡 View results in MongoDB Compass:")
        print("   Database: cdp")
        print("   Collection: profiles")
        print("   Look for: computed_attributes field")
        print("")
        
    except Exception as e:
        print(f"\n❌ Batch job failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print("\n👋 Batch job finished.\n")

if __name__ == "__main__":
    main()