#!/usr/bin/env python3
"""
Day 11: AI-Powered Personalization API
RAG-based personalization using Gemini API

Architecture:
1. Retrieve: Fetch unified profile from MongoDB
2. Augment: Build context-rich prompt with profile data
3. Generate: Use Gemini to create personalized offer
4. Return: Structured JSON response
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from pymongo import MongoClient
import os
import json
from datetime import datetime

# ============================================================
# Configuration
# ============================================================

# Get API key from environment (or use default for testing)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    print("⚠️  WARNING: No GEMINI_API_KEY set. API will return mock responses.")
    model = None

# Initialize FastAPI
app = FastAPI(
    title="CDP Personalization API",
    description="AI-powered customer personalization using RAG",
    version="1.0.0"
)

# CORS (allow browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Data Models
# ============================================================

class PersonalizedOffer(BaseModel):
    """Response model for personalized offers"""
    profile_id: str
    offer_type: str
    title: str
    message: str
    products: Optional[List[str]] = []
    discount: Optional[str] = None
    reasoning: Optional[str] = None
    generated_at: str

class ProfileSummary(BaseModel):
    """Profile summary for debugging"""
    master_profile_id: str
    identities: Dict[str, Any]
    lifetime_value: float
    engagement_score: int
    total_events: int
    last_event_type: str

# ============================================================
# Database Functions
# ============================================================

def get_mongodb_client():
    """Get MongoDB client"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB connection failed: {str(e)}")

def fetch_profile(profile_id: str) -> Dict[str, Any]:
    """Retrieve unified profile from MongoDB"""
    client = get_mongodb_client()
    try:
        db = client["cdp"]
        collection = db["profiles"]
        
        profile = collection.find_one({"master_profile_id": profile_id})
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
        
        # Remove MongoDB _id for cleaner JSON
        profile.pop("_id", None)
        
        return profile
    finally:
        client.close()

# ============================================================
# Prompt Engineering
# ============================================================

def build_personalization_prompt(profile: Dict[str, Any]) -> str:
    """
    Build a context-rich prompt for the LLM.
    This is the "Augmentation" step in RAG.
    """
    
    # Extract key data
    identities = profile.get("identities", {})
    attributes = profile.get("attributes", {})
    computed = profile.get("computed_attributes", {})
    
    # Email (if available)
    email = identities.get("email", "unknown")
    
    # Computed metrics
    ltv = computed.get("lifetime_value", 0)
    engagement = computed.get("engagement_score", 0)
    event_metrics = computed.get("event_metrics", {})
    product_metrics = computed.get("product_metrics", {})
    
    # Recent activity
    last_event = profile.get("last_event_type", "unknown")
    products_viewed = product_metrics.get("products_viewed", [])
    products_purchased = product_metrics.get("products_purchased", [])
    
    # Build the prompt
    prompt = f"""You are an expert marketing AI for an e-commerce company specializing in electronics.

Your task: Create a highly personalized offer for this customer based on their complete profile.

CUSTOMER PROFILE:
- Customer ID: {profile.get('master_profile_id')}
- Email: {email}
- Customer Value: ${ltv:,.2f}
- Engagement Level: {engagement}/100 {"(High)" if engagement > 70 else "(Medium)" if engagement > 40 else "(Low)"}
- Total Events: {event_metrics.get('total_events', 0)}
- Last Activity: {last_event}

BEHAVIOR INSIGHTS:
- Products Viewed: {', '.join(products_viewed[:3]) if products_viewed else 'None'}
- Products Purchased: {', '.join(products_purchased) if products_purchased else 'None'}
- Shopping Pattern: {"Active buyer" if ltv > 500 else "Browser" if event_metrics.get('total_events', 0) > 3 else "New visitor"}

CONTEXT:
- Recent activity shows interest in: {attributes.get('product_name', 'general browsing')}
- Price range comfortable with: ${attributes.get('price', 'unknown')}

YOUR TASK:
Create a personalized offer that:
1. Matches their shopping behavior and preferences
2. Acknowledges their customer value tier
3. Feels genuinely personal, not generic
4. Includes specific product recommendations

CRITICAL: Return ONLY valid JSON in this EXACT format (no markdown, no backticks):
{{
  "offer_type": "upsell" or "cross-sell" or "loyalty" or "win-back" or "welcome",
  "title": "Compelling offer title",
  "message": "Personal message explaining the offer (2-3 sentences)",
  "products": ["Product 1", "Product 2", "Product 3"],
  "discount": "Discount amount (e.g., '15%' or '$50 off' or 'Buy 1 Get 1')",
  "reasoning": "Brief explanation of why this offer fits this customer"
}}
"""
    
    return prompt

# ============================================================
# LLM Generation
# ============================================================

def generate_personalized_offer(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate personalized offer using Gemini API.
    This is the "Generation" step in RAG.
    """
    
    # Build prompt with profile context
    prompt = build_personalization_prompt(profile)
    
    # If no API key, return mock response
    if not model:
        return generate_mock_offer(profile)
    
    try:
        # Call Gemini API
        response = model.generate_content(prompt)
        
        # Extract text
        response_text = response.text.strip()
        
        # Clean up response (remove markdown if present)
        if response_text.startswith("```"):
            # Remove markdown code blocks
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        # Parse JSON
        offer_data = json.loads(response_text)
        
        # Validate required fields
        required_fields = ["offer_type", "title", "message"]
        for field in required_fields:
            if field not in offer_data:
                raise ValueError(f"Missing required field: {field}")
        
        return offer_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        # Fallback to mock
        return generate_mock_offer(profile)
    except Exception as e:
        print(f"❌ LLM generation error: {e}")
        # Fallback to mock
        return generate_mock_offer(profile)

def generate_mock_offer(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback mock offer when API is unavailable"""
    computed = profile.get("computed_attributes", {})
    ltv = computed.get("lifetime_value", 0)
    
    if ltv > 1000:
        return {
            "offer_type": "loyalty",
            "title": "VIP Customer Exclusive",
            "message": "As one of our most valued customers, enjoy 20% off your next purchase plus free expedited shipping!",
            "products": ["Premium Accessories", "Extended Warranty", "Priority Support"],
            "discount": "20% off",
            "reasoning": "High-value customer (LTV > $1000) - reward loyalty with premium benefits"
        }
    elif ltv > 0:
        return {
            "offer_type": "cross-sell",
            "title": "Complete Your Setup",
            "message": "Based on your recent purchase, we've handpicked accessories that pair perfectly with your new device.",
            "products": ["Protective Case", "Screen Protector", "Charging Cable"],
            "discount": "15% off accessories",
            "reasoning": "Recent purchaser - perfect time for complementary products"
        }
    else:
        return {
            "offer_type": "welcome",
            "title": "Welcome! First Purchase Discount",
            "message": "Start your journey with us! Get 10% off your first order and free shipping on orders over $50.",
            "products": ["Trending Electronics", "Best Sellers", "New Arrivals"],
            "discount": "10% off first order",
            "reasoning": "New visitor - incentivize first purchase"
        }

# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "CDP Personalization API",
        "status": "running",
        "version": "1.0.0",
        "gemini_enabled": model is not None,
        "endpoints": {
            "personalize": "/personalize/{profile_id}",
            "profile_summary": "/profile/{profile_id}",
            "docs": "/docs"
        }
    }

@app.get("/personalize/{profile_id}", response_model=PersonalizedOffer)
async def personalize(profile_id: str):
    """
    Generate a personalized offer for a customer.
    
    This implements the complete RAG pipeline:
    1. Retrieve: Fetch profile from MongoDB
    2. Augment: Build context-rich prompt
    3. Generate: Use Gemini to create offer
    """
    
    # Step 1: RETRIEVE profile from MongoDB
    profile = fetch_profile(profile_id)
    
    # Step 2 & 3: AUGMENT prompt and GENERATE offer
    offer_data = generate_personalized_offer(profile)
    
    # Step 4: Return structured response
    return PersonalizedOffer(
        profile_id=profile_id,
        offer_type=offer_data.get("offer_type", "generic"),
        title=offer_data.get("title", "Special Offer"),
        message=offer_data.get("message", ""),
        products=offer_data.get("products", []),
        discount=offer_data.get("discount"),
        reasoning=offer_data.get("reasoning"),
        generated_at=datetime.utcnow().isoformat()
    )

@app.get("/profile/{profile_id}", response_model=ProfileSummary)
async def get_profile_summary(profile_id: str):
    """
    Get a summary of a customer profile.
    Useful for debugging and understanding the data.
    """
    
    profile = fetch_profile(profile_id)
    computed = profile.get("computed_attributes", {})
    event_metrics = computed.get("event_metrics", {})
    
    return ProfileSummary(
        master_profile_id=profile.get("master_profile_id"),
        identities=profile.get("identities", {}),
        lifetime_value=computed.get("lifetime_value", 0),
        engagement_score=computed.get("engagement_score", 0),
        total_events=event_metrics.get("total_events", 0),
        last_event_type=profile.get("last_event_type", "unknown")
    )

# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 Starting CDP Personalization API")
    print("=" * 60)
    print("")
    print("📡 Endpoints:")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Personalize: http://localhost:8000/personalize/{profile_id}")
    print("   - Profile: http://localhost:8000/profile/{profile_id}")
    print("")
    
    if not GEMINI_API_KEY:
        print("⚠️  WARNING: GEMINI_API_KEY not set!")
        print("   Set it with: export GEMINI_API_KEY='your-key-here'")
        print("   Get a key at: https://makersuite.google.com/app/apikey")
        print("   API will use mock responses for now.")
    else:
        print("✅ Gemini API enabled")
    
    print("")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)