# API Documentation

## Overview

The CDP API provides AI-powered personalization, graph operations, and identity debugging capabilities. It implements the RAG (Retrieve-Augment-Generate) pattern with Google Gemini for personalization, and exposes Neo4j graph operations for identity cluster management.

**Base URL:** `http://localhost:8000`

**API Documentation:** http://localhost:8000/docs (Swagger UI)

## Architecture

```
┌─────────────┐
│   Client    │
│  (Browser/  │
│   Streamlit)│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   FastAPI Router    │
│  ├─ Personalization │
│  └─ Graph Debugging │
└──────┬──────────────┘
       │
       ├────────────────┬──────────────┬─────────────┐
       ▼                ▼              ▼             ▼
┌────────────┐  ┌──────────────┐  ┌────────┐  ┌─────────┐
│  Profile   │  │    Graph     │  │  AI    │  │ Gemini  │
│  Service   │  │   Service    │  │Service │  │   API   │
└─────┬──────┘  └──────┬───────┘  └───┬────┘  └─────────┘
      │                │               │
      ▼                ▼               ▼
┌──────────┐    ┌──────────┐    (AI Analysis)
│ MongoDB  │    │  Neo4j   │
└──────────┘    └──────────┘
```

## Endpoints

### Personalization Endpoints

#### 1. Health Check

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
    "graph_anomalies": "/api/graph/anomalies",
    "graph_cluster": "/api/graph/cluster/{profile_id}",
    "graph_explain": "/api/graph/explain/{profile_id}",
    "graph_split": "/api/graph/split",
    "docs": "/docs",
    "redoc": "/redoc"
  }
}
```

---

#### 2. Generate Personalized Offer

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

#### 3. Get Profile Summary

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
    "deviceID": ["device_xyz789", "device_abc456"]
  },
  "lifetime_value": 2149.99,
  "engagement_score": 85,
  "total_events": 12,
  "last_event_type": "purchase"
}
```

---

### Graph Debugging Endpoints

#### 4. Detect Anomalies

**GET** `/api/graph/anomalies`

Detect anomalous identity clusters (hairballs) in the graph.

**Query Parameters:**
- `email_threshold` (optional, default: 5): Max emails per profile
- `device_threshold` (optional, default: 10): Max devices per profile

**Example Request:**
```bash
curl "http://localhost:8000/api/graph/anomalies?email_threshold=3&device_threshold=5"
```

**Success Response (200):**
```json
{
  "anomalies": [
    {
      "profile_id": "profile_hairball_123",
      "email_count": 8,
      "device_count": 12,
      "issue_type": "excessive_identities",
      "severity": "high"
    },
    {
      "profile_id": "profile_shared_456",
      "email_count": 2,
      "device_count": 15,
      "issue_type": "shared_device",
      "severity": "medium"
    }
  ],
  "total_anomalies": 2,
  "thresholds": {
    "email_threshold": 3,
    "device_threshold": 5
  }
}
```

---

#### 5. Get Identity Cluster

**GET** `/api/graph/cluster/{profile_id}`

Retrieve the complete identity cluster for a profile (for visualization).

**Parameters:**
- `profile_id` (path, required): Master profile ID

**Example Request:**
```bash
curl http://localhost:8000/api/graph/cluster/profile_abc123
```

**Success Response (200):**
```json
{
  "nodes": [
    {
      "id": "profile_abc123",
      "type": "profile",
      "label": "Profile abc123",
      "created_at": "2025-11-15T10:00:00Z"
    },
    {
      "id": "email_user@example.com",
      "type": "identity",
      "identity_type": "email",
      "value": "user@example.com"
    },
    {
      "id": "device_xyz789",
      "type": "identity",
      "identity_type": "deviceID",
      "value": "device_xyz789"
    }
  ],
  "edges": [
    {
      "from": "profile_abc123",
      "to": "email_user@example.com",
      "label": "HAS_IDENTITY"
    },
    {
      "from": "profile_abc123",
      "to": "device_xyz789",
      "label": "HAS_IDENTITY"
    }
  ]
}
```

---

#### 6. Explain Identity Cluster (AI Analysis)

**GET** `/api/graph/explain/{profile_id}`

Use AI to analyze and classify an identity cluster.

**Parameters:**
- `profile_id` (path, required): Master profile ID

**Example Request:**
```bash
curl http://localhost:8000/api/graph/explain/profile_abc123
```

**Success Response (200):**
```json
{
  "profile_id": "profile_abc123",
  "cluster_type": "household",
  "confidence": "high",
  "analysis": {
    "email_count": 3,
    "device_count": 4,
    "email_device_ratio": 0.75,
    "classification": "Likely a household with multiple family members sharing devices"
  },
  "recommendation": "Normal pattern. Multiple users (emails) sharing household devices (tablets, smart TV, etc.). No action needed.",
  "reasoning": "Email-to-device ratio of 0.75 suggests multiple people using shared devices, which is typical for families. Not a data quality issue."
}
```

**Cluster Classifications:**
- `single_user`: 1 person, multiple devices (normal)
- `household`: Multiple people sharing devices (normal)
- `shared_device`: Public/shared device like kiosk (investigate)
- `data_quality_issue`: Suspicious pattern (fix needed)
- `potential_fraud`: Anomalous behavior (urgent review)

---

#### 7. Split Identity Cluster

**POST** `/api/graph/split`

Manually detach an identity from a profile (graph surgery).

**Request Body:**
```json
{
  "profile_id": "profile_abc123",
  "identity_type": "email",
  "identity_value": "wrong@example.com"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/graph/split \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "profile_abc123",
    "identity_type": "email",
    "identity_value": "wrong@example.com"
  }'
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Identity detached successfully",
  "original_profile": "profile_abc123",
  "new_profile": "profile_new_456",
  "detached_identity": {
    "type": "email",
    "value": "wrong@example.com"
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Identity not found in profile"
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
    email?: string | string[];  // Can be array if multiple
    deviceID?: string | string[];
    userID?: string | string[];
    phone?: string | string[];
  };
  lifetime_value: number;
  engagement_score: number;  // 0-100
  total_events: number;
  last_event_type: string;
}
```

### GraphAnomaly

```typescript
{
  profile_id: string;
  email_count: number;
  device_count: number;
  issue_type: "excessive_identities" | "shared_device" | "suspicious_pattern";
  severity: "low" | "medium" | "high" | "critical";
}
```

### IdentityCluster

```typescript
{
  nodes: Array<{
    id: string;
    type: "profile" | "identity";
    label: string;
    identity_type?: "email" | "deviceID" | "phone" | "userID";
    value?: string;
    created_at?: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    label: "HAS_IDENTITY";
  }>;
}
```

### ClusterAnalysis

```typescript
{
  profile_id: string;
  cluster_type: "single_user" | "household" | "shared_device" | "data_quality_issue" | "potential_fraud";
  confidence: "low" | "medium" | "high";
  analysis: {
    email_count: number;
    device_count: number;
    email_device_ratio: number;
    classification: string;
  };
  recommendation: string;
  reasoning: string;
}
```

### SplitRequest

```typescript
{
  profile_id: string;
  identity_type: "email" | "deviceID" | "phone" | "userID";
  identity_value: string;
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

### Using Swagger UI

1. Start API: `python scripts/run_api.py`
2. Open browser: http://localhost:8000/docs
3. Click "Try it out" on any endpoint
4. Enter parameters and execute

### Using Streamlit Frontend

1. Start API: `python scripts/run_api.py`
2. Start frontend: `streamlit run frontend/app.py`
3. Navigate to http://localhost:8501
4. Use interactive interface:
   - **Profile Inspector**: Enter profile ID, view graph, get AI analysis
   - **Graph Health**: Monitor anomalies, perform graph surgery

## Use Cases

### 1. E-commerce Personalization

**Scenario**: Customer visits website after previous purchase

```python
# Retrieve profile and generate offer
response = requests.get(f"http://localhost:8000/api/personalize/{profile_id}")
offer = response.json()

# Display personalized banner
show_banner(offer['title'], offer['message'], offer['discount'])
```

### 2. Identity Debugging

**Scenario**: Support team investigating duplicate profiles

```python
# Check for anomalies
anomalies = requests.get("http://localhost:8000/api/graph/anomalies").json()

for anomaly in anomalies['anomalies']:
    # Get cluster details
    cluster = requests.get(f"http://localhost:8000/api/graph/cluster/{anomaly['profile_id']}").json()
    
    # Get AI analysis
    analysis = requests.get(f"http://localhost:8000/api/graph/explain/{anomaly['profile_id']}").json()
    
    # Decide action based on classification
    if analysis['cluster_type'] == 'data_quality_issue':
        # Perform graph surgery
        split_identity(anomaly['profile_id'], bad_identity)
```

### 3. Real-time Offers

**Scenario**: Show offer when customer adds item to cart

```python
# Event triggers API call
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    profile_id = session['profile_id']
    
    # Get real-time personalized upsell
    offer = get_personalized_offer(profile_id)
    
    return {
        'item_added': True,
        'upsell_offer': offer
    }
```

### 4. Fraud Detection

**Scenario**: Detect suspicious identity patterns

```python
# Monitor for high-severity anomalies
anomalies = get_anomalies(email_threshold=2, device_threshold=3)

critical_cases = [
    a for a in anomalies['anomalies'] 
    if a['severity'] == 'high' or a['severity'] == 'critical'
]

for case in critical_cases:
    analysis = explain_cluster(case['profile_id'])
    
    if analysis['cluster_type'] == 'potential_fraud':
        # Flag for manual review
        flag_for_review(case['profile_id'], analysis['reasoning'])
```