# API Documentation

## Overview

The CDP Personalization API provides AI-powered personalized offers using customer data. It implements the RAG (Retrieve-Augment-Generate) pattern with Google Gemini.

**Base URL:** `http://localhost:8000`

**API Documentation:** http://localhost:8000/docs (Swagger UI)

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────┐
│   FastAPI   │────▶│ MongoDB  │
│   Router    │     └──────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────┐
│  Services   │────▶│  Gemini  │
│   Layer     │     │   API    │
└─────────────┘     └──────────┘
```

## Endpoints

### 1. Health Check

**GET** `/`

Check API status and configuration.

**Response:**
```json
{
  "service": "CDP Personalization API",
  "status": "running",
  "version": "1.0.0",
  "environment": "development",
  "gemini_enabled": true,
  "endpoints": {
    "personalize": "/api/personalize/{profile_id}",
    "profile_summary": "/api/profile/{profile_id}",
    "docs": "/docs",
    "redoc": "/redoc"
  }
}
```

---

### 2. Generate Personalized Offer

**GET** `/api/personalize/{profile_id}`

Generate a personalized offer for a customer using AI.

**RAG Pipeline:**
1. **Retrieve:** Fetch customer profile from MongoDB
2. **Augment:** Build context-rich prompt with customer data
3. **Generate:** Use Gemini AI to create personalized offer

**Parameters:**
- `profile_id` (path, required): Customer's master profile ID

**Example Request:**
```bash
curl http://localhost:8000/api/personalize/profile_abc123
```

**Success Response (200):**
```json
{
  "profile_id": "profile_abc123",
  "offer_type": "loyalty",
  "title": "VIP Customer Exclusive - Thank You!",
  "message": "As one of our most valued customers with over $2,000 in purchases, we want to show our appreciation. Enjoy 20% off your next purchase plus free expedited shipping on all orders!",
  "products": [
    "Premium Wireless Earbuds",
    "Extended Warranty Package",
    "Priority Customer Support"
  ],
  "discount": "20% off + free shipping",
  "reasoning": "High-value customer (LTV > $2000) with strong engagement score (85/100). Reward loyalty with premium benefits and exclusive products.",
  "generated_at": "2025-11-15T10:30:00.000Z"
}
```

**Error Response (404):**
```json
{
  "detail": "Profile profile_xyz not found"
}
```

**Error Response (503):**
```json
{
  "detail": "MongoDB connection failed: ..."
}
```

---

### 3. Get Profile Summary

**GET** `/api/profile/{profile_id}`

Retrieve a summary of a customer profile for debugging.

**Parameters:**
- `profile_id` (path, required): Customer's master profile ID

**Example Request:**
```bash
curl http://localhost:8000/api/profile/profile_abc123
```

**Success Response (200):**
```json
{
  "master_profile_id": "profile_abc123",
  "identities": {
    "email": "customer@example.com",
    "deviceID": "device_xyz789"
  },
  "lifetime_value": 2149.99,
  "engagement_score": 85,
  "total_events": 12,
  "last_event_type": "purchase"
}
```

**Error Response (404):**
```json
{
  "detail": "Profile profile_xyz not found"
}
```

---

## Data Models

### PersonalizedOffer

```typescript
{
  profile_id: string;
  offer_type: "upsell" | "cross-sell" | "loyalty" | "win-back" | "welcome";
  title: string;
  message: string;
  products: string[];
  discount: string | null;
  reasoning: string | null;
  generated_at: string;  // ISO 8601 datetime
}
```

### ProfileSummary

```typescript
{
  master_profile_id: string;
  identities: {
    email?: string;
    deviceID?: string;
    userID?: string;
    phone?: string;
  };
  lifetime_value: number;
  engagement_score: number;  // 0-100
  total_events: number;
  last_event_type: string;
}
```

---

## Offer Types

| Type | Description | Use Case |
|------|-------------|----------|
| `welcome` | First-time customer offers | LTV = $0, new visitors |
| `cross-sell` | Complementary products | Recent purchasers |
| `upsell` | Premium products | Medium-value customers |
| `loyalty` | VIP rewards | High-value customers (LTV > $1000) |
| `win-back` | Re-engagement | Inactive customers |

---

## Configuration

### Environment Variables

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=cdp

# AI
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024
```

### Getting Gemini API Key

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Create new API key
4. Add to `.env`: `GEMINI_API_KEY=your_key_here`

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Cause |
|------|---------|-------|
| 200 | Success | Request completed successfully |
| 404 | Not Found | Profile ID doesn't exist |
| 503 | Service Unavailable | Database connection failed |
| 500 | Internal Server Error | Unexpected error |

### Fallback Behavior

If Gemini API is unavailable or `GEMINI_API_KEY` is not set:
- API returns **mock offers** based on customer tier
- No AI generation, uses rule-based logic
- All endpoints remain functional

---
## CORS

CORS is enabled for all origins in development.

**Current Configuration:**
```python
allow_origins=["*"]
allow_methods=["*"]
allow_headers=["*"]
```

**Production Recommendation:**
- Restrict `allow_origins` to specific domains
- Use authentication tokens
- Implement proper security headers

---

## Testing

### Manual Testing

```bash
# Start API
python scripts/run_api.py

# Test health check
curl http://localhost:8000/

# Test personalization (replace with actual profile ID)
curl http://localhost:8000/api/personalize/profile_abc123

# Test profile summary
curl http://localhost:8000/api/profile/profile_abc123
```

### Using Swagger UI

1. Start API: `python scripts/run_api.py`
2. Open browser: http://localhost:8000/docs
3. Click "Try it out" on any endpoint
4. Enter parameters and execute

### Automated Testing

```bash
# Run API integration tests
pytest tests/integration/test_api_endpoints.py

# With coverage
pytest tests/integration/test_api_endpoints.py --cov=src.python.api
```