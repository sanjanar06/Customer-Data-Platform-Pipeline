# Code Explanation: Line-by-Line Analysis

This document provides a detailed line-by-line explanation of every file in the CDP prototype.

## Table of Contents

1. [Python Files](#python-files)
   - [producer.py](#producerpy)
   - [batch_job.py](#batch_jobpy)
   - [personalization_api.py](#personalization_apipy)
   - [test_mongo.py](#test_mongopy)
   - [test_neo4j.py](#test_neo4jpy)

2. [Java Files](#java-files)
   - [ProfileStitcher.java](#profilestitcherjava)
   - [SocketStreamJob.java](#socketstreamjobjava)
   - [HelloWorldJob.java](#helloworldjobjava)

3. [Configuration Files](#configuration-files)
   - [docker-compose.yml](#docker-composeyml)
   - [requirements.txt](#requirementstxt)
   - [build.gradle](#buildgradle)
   - [run_flink_job.sh](#run_flink_jobsh)

---

## Python Files

### producer.py

**Purpose**: Simulates a customer event stream by sending JSON events through a socket to Flink.

#### Line-by-Line Explanation:

```python
#!/usr/bin/env python3
```
- **Shebang**: Makes the script directly executable on Unix systems
- Specifies to use Python 3 from the environment

```python
"""
Day 7: CDP Event Producer
Sends realistic CDP events with identities for testing identity stitching.
```
- **Docstring**: Documents the purpose of the module
- This is a "Day 7" project, indicating it's part of a learning journey

```python
Demo Sequence:
1. Anonymous visitor (deviceID only)
2. User logs in (deviceID + email) - Should stitch to same profile
3. User from different device (different deviceID + same email) - Should merge profiles
"""
```
- Explains the demo flow demonstrating the "identity stitching" scenario
- Shows how a user's journey across devices creates a unified profile

```python
import argparse
import socket
import time
import json
import sys
```
- **argparse**: Parse command-line arguments
- **socket**: Create TCP socket server to send data
- **time**: Add delays between events
- **json**: Serialize Python dicts to JSON
- **sys**: Access stderr for logging (keeps output separate from data)

```python
DEMO_EVENTS = [
    {
        "event_type": "page_view",
        "identities": {
            "deviceID": "device_abc123"
        },
        "properties": {
            "page": "/home",
            "referrer": "google.com",
            "user_agent": "Mozilla/5.0"
        },
        "description": "📱 Event 1: Anonymous visitor (device_abc123)"
    },
```
- **DEMO_EVENTS**: Predefined list of events that tell a story
- **Event 1**: Anonymous user visits the site
  - Only has `deviceID` (browser fingerprint or cookie)
  - No email yet (user hasn't logged in)
  - Properties contain event-specific data
  - Description is for logging (removed before sending)

```python
    {
        "event_type": "login",
        "identities": {
            "deviceID": "device_abc123",
            "email": "user@example.com"
        },
        "properties": {
            "login_method": "password",
            "login_success": True
        },
        "description": "🔑 Event 2: User logs in (links email)"
    },
```
- **Event 2**: User logs in on the same device
  - NOW we have both `deviceID` AND `email`
  - This is the "identity stitching" moment
  - Flink will link the email to the existing deviceID profile

```python
    {
        "event_type": "page_view",
        "identities": {
            "deviceID": "device_xyz789"
        },
        "properties": {
            "page": "/home",
            "user_agent": "Mobile Safari"
        },
        "description": "📱 Event 5: Different device (creates 2nd profile)"
    },
```
- **Event 5**: User visits from a DIFFERENT device (e.g., mobile phone)
  - Different deviceID
  - No email yet (not logged in)
  - Creates a SECOND profile (temporarily)

```python
    {
        "event_type": "login",
        "identities": {
            "deviceID": "device_xyz789",
            "email": "user@example.com"
        },
        "properties": {
            "login_method": "password",
            "login_success": True
        },
        "description": "🔗 Event 6: THE MERGE! (same email, profiles merge)"
    },
```
- **Event 6**: THE CRITICAL EVENT - Profile merge!
  - New deviceID (`device_xyz789`) + SAME email (`user@example.com`)
  - Flink detects: "This email exists on another profile!"
  - Triggers profile merge: 2 profiles → 1 unified profile
  - Final profile has BOTH deviceIDs linked to same email

```python
    {
        "event_type": "purchase",
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
        "description": "💰 Event 7: Purchase complete"
    }
```
- **Event 7**: Purchase from the second device
  - Goes to the UNIFIED profile (both devices are now stitched)
  - Contains business-critical data (purchase total, items)
  - Used later for LTV calculation

```python
def serve_demo(host: str, port: int, interval: float, loop: bool = False):
    """
    Serve the demo event sequence to connected Flink clients.
    """
```
- **serve_demo()**: Main function for demo mode
- **Parameters**:
  - `host`: IP to bind to (0.0.0.0 = all interfaces)
  - `port`: TCP port (9001)
  - `interval`: Seconds between events
  - `loop`: Whether to repeat the sequence

```python
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```
- Create TCP socket (SOCK_STREAM = TCP, SOCK_DGRAM = UDP)
- AF_INET = IPv4 address family

```python
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```
- **Critical for development**: Allow reusing the port immediately
- Without this: "Address already in use" error after restart
- SOL_SOCKET = socket layer, SO_REUSEADDR = allow reuse

```python
    sock.bind((host, port))
    sock.listen(1)
```
- **bind**: Attach socket to host:port
- **listen(1)**: Accept up to 1 pending connection (we only expect Flink)

```python
    print(f"🚀 CDP Event Producer started on {host}:{port}", file=sys.stderr)
```
- Print to **stderr** (not stdout)
- **Why stderr?**: Stdout is for data (JSON events), stderr is for logs
- Prevents log messages from mixing with data stream

```python
    try:
        while True:
            conn, addr = sock.accept()
            print(f"✅ Flink connected from {addr}\n", file=sys.stderr)
```
- **Infinite loop**: Wait for connections
- **accept()**: Blocks until a client (Flink) connects
- Returns: connection object and client address

```python
            try:
                iteration = 0
                while True:
                    iteration += 1
                    print(f"{'='*60}", file=sys.stderr)
                    print(f"Iteration {iteration} - Sending {len(DEMO_EVENTS)} events:", file=sys.stderr)
```
- Inner loop for sending events
- Supports multiple iterations if `loop=True`
- Logs iteration number for debugging

```python
                    for idx, event_template in enumerate(DEMO_EVENTS, 1):
                        # Create a copy and add timestamp
                        event = event_template.copy()
                        event["timestamp"] = int(time.time())
                        event["sequence"] = idx
```
- **enumerate(DEMO_EVENTS, 1)**: Loop with 1-based index
- **event_template.copy()**: Don't modify original (allows looping)
- **timestamp**: Unix timestamp (seconds since 1970)
- **sequence**: Event order number

```python
                        # Remove description before sending (it's just for console)
                        description = event.pop("description", "")
```
- **pop()**: Remove and return the "description" field
- Description is only for human-readable logs
- Don't send it to Flink (not part of data schema)

```python
                        # Send to Flink
                        line = json.dumps(event) + "\n"
                        try:
                            conn.sendall(line.encode("utf-8"))
```
- **json.dumps()**: Convert Python dict to JSON string
- **+ "\n"**: Add newline (socket source reads line-by-line)
- **encode("utf-8")**: Convert string to bytes
- **sendall()**: Send all bytes (handles partial sends)

```python
                            print(f"[{idx}/{len(DEMO_EVENTS)}] {description}", file=sys.stderr)
                            print(f"     Sent: {json.dumps(event, indent=2)}\n", file=sys.stderr)
```
- Log what was sent (pretty-printed JSON for debugging)

```python
                        except (BrokenPipeError, ConnectionResetError):
                            print("⚠️ Flink disconnected", file=sys.stderr)
                            raise
```
- **BrokenPipeError**: Client closed connection
- **ConnectionResetError**: Connection was forcibly closed
- **raise**: Re-raise to exit inner loop

```python
                        time.sleep(interval)
```
- Wait before sending next event
- Simulates realistic event arrival rate
- Default: 2 seconds between events

```python
                    if not loop:
                        print(f"\n{'='*60}", file=sys.stderr)
                        print(f"✅ All {len(DEMO_EVENTS)} events sent!", file=sys.stderr)
                        break
                    else:
                        print(f"\n🔄 Looping... (Ctrl+C to stop)\n", file=sys.stderr)
                        time.sleep(interval * 2)  # Pause between loops
```
- **if not loop**: Send once and exit
- **else**: Loop continuously (useful for load testing)
- **Pause between loops**: Give time to observe results

```python
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
                if not loop:
                    break
```
- **except**: Handle disconnection gracefully
- **finally**: Always close connection
- **break**: Exit outer loop if not looping

```python
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user. Shutting down...", file=sys.stderr)
    finally:
        try:
            sock.close()
        except Exception:
            pass
```
- **KeyboardInterrupt**: Catch Ctrl+C
- **finally**: Close socket even if error occurred

```python
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="CDP Event Producer for Flink")
    p.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    p.add_argument("--port", type=int, default=9001, help="Port to bind (default: 9001)")
    p.add_argument("--interval", type=float, default=2.0, help="Seconds between events (default: 2.0)")
    p.add_argument("--mode", choices=["demo", "random"], default="demo", 
                   help="demo: send CDP event sequence, random: send random data (default: demo)")
    p.add_argument("--loop", action="store_true", help="Loop the demo sequence continuously")
```
- **argparse**: Parse command-line flags
- **--host**: Which network interface to bind to
- **0.0.0.0**: All interfaces (accessible from Docker containers)
- **--port**: TCP port number
- **--interval**: Speed of event stream
- **--mode**: demo (realistic) vs random (for load testing)
- **--loop**: Boolean flag (present = True)

```python
    args = p.parse_args()
    
    if args.mode == "demo":
        serve_demo(args.host, args.port, args.interval, args.loop)
    else:
        serve_random(args.host, args.port, args.interval)
```
- Parse arguments and call appropriate function

**Key Concepts**:
1. **Socket Programming**: TCP server that clients connect to
2. **Event Sourcing**: Events are the source of truth
3. **Identity Stitching Demo**: Events designed to show profile merging
4. **Logging to stderr**: Separate logs from data stream

---

### batch_job.py

**Purpose**: Compute aggregate metrics on customer profiles (simulates nightly Spark batch job).

#### Critical Lines Explained:

```python
#!/usr/bin/env python3
"""
Day 10: Mock Spark Batch Job
Simulates a nightly batch job that computes aggregate metrics on customer profiles.
"""
```
- Simulates what would run on Apache Spark in production
- Batch processing (vs real-time streaming)
- Runs periodically (e.g., nightly) to compute expensive aggregations

```python
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
```
- **Lifetime Value (LTV)**: Total $ spent by customer
- Loop through ALL events in history
- Sum up purchase totals
- **Why batch?**: Expensive to compute on every event
  - Customer with 10,000 events = 10,000 iterations
  - Better to compute once per day

```python
def compute_event_metrics(profile):
    """Compute event-based metrics"""
    event_history = profile.get("event_history", [])
    
    if not event_history:
        return {
            "total_events": 0,
            "unique_event_types": 0,
            "event_type_counts": {}
        }
```
- Handle edge case: New profile with no events
- Return default values (prevents divide-by-zero errors later)

```python
    event_types = [e.get("event_type") for e in event_history]
    event_type_counts = dict(Counter(event_types))
```
- **List comprehension**: Extract all event types
- **Counter**: Built-in Python class that counts occurrences
  - Example: `Counter(['page_view', 'page_view', 'login'])` → `{'page_view': 2, 'login': 1}`

```python
def compute_engagement_score(profile, metrics):
    """Compute engagement score (0-100)"""
    score = 0
    
    # Event activity (max 40 points)
    total_events = metrics["event_metrics"]["total_events"]
    score += min(total_events * 5, 40)
```
- **Engagement Score**: Custom metric (0-100)
- **Weighted scoring system**:
  - Event activity: 40 points
  - Purchase behavior: 30 points
  - Recent activity: 20 points
  - Diversity: 10 points
- **min(total_events * 5, 40)**: Cap at 40 points
  - 8+ events = full 40 points

```python
    # Purchase behavior (max 30 points)
    ltv = metrics["lifetime_value"]
    if ltv > 0:
        score += 15
    if ltv > 1000:
        score += 15
```
- **Purchase behavior scoring**:
  - Any purchase: +15 points
  - High-value customer (>$1000): +15 more
- Encourages purchase conversion

```python
    # Recent activity (max 20 points)
    days_since_last = metrics["time_metrics"]["days_since_last_event"]
    if days_since_last < 1:
        score += 20
    elif days_since_last < 7:
        score += 10
    elif days_since_last < 30:
        score += 5
```
- **Recency matters**: Active users score higher
- Tiers: <1 day (20pts), <1 week (10pts), <1 month (5pts)
- Helps identify churning users (low recency score)

```python
def process_profiles(client):
    """Main batch processing logic"""
    db = client["cdp"]
    profiles_collection = db["profiles"]
    
    profiles = list(profiles_collection.find({}))
    print(f"\n📊 Processing {len(profiles)} profiles...")
```
- **find({})**: Get ALL profiles (no filter)
- **list()**: Load all into memory
- **Why it's OK here**: Small prototype dataset
- **Production**: Would use Spark to process in parallel across cluster

```python
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
```
- **update_one()**: Update single document
- **$set operator**: Replaces the `computed_attributes` field
- Adds timestamp showing when batch job ran

```python
def print_summary(client):
    """Print summary statistics"""
    db = client["cdp"]
    profiles_collection = db["profiles"]
    
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
```
- **MongoDB Aggregation Pipeline**: Similar to SQL GROUP BY
- **$group**: Aggregate across all profiles (`_id: None` = single group)
- **$sum**: Count or sum values
- **$avg**: Calculate average
- **Why aggregation?**: More efficient than loading all in Python

**Key Concepts**:
1. **Batch vs Stream**: Some computations are too expensive for real-time
2. **Engagement Scoring**: Business logic to rank customers
3. **Separation of Concerns**: Stream processes events, batch computes aggregates

---

### personalization_api.py

**Purpose**: AI-powered personalization API using RAG (Retrieval-Augmented Generation) pattern.

#### Critical Architecture:

```python
# Get API key from environment (or use default for testing)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017")
```
- **os.getenv()**: Read environment variable (secure way to handle secrets)
- **Default value**: Falls back if not set (development convenience)
- **Security**: Never hardcode API keys in source code

```python
# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    print("⚠️  WARNING: No GEMINI_API_KEY set. API will return mock responses.")
    model = None
```
- **Graceful degradation**: Works without API key (uses mock data)
- **gemini-pro**: Google's general-purpose LLM model

```python
# Initialize FastAPI
app = FastAPI(
    title="CDP Personalization API",
    description="AI-powered customer personalization using RAG",
    version="1.0.0"
)
```
- **FastAPI**: Modern Python web framework
- **Auto-generated docs**: Creates OpenAPI/Swagger UI

```python
# CORS (allow browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- **CORS**: Cross-Origin Resource Sharing
- **allow_origins=["*"]**: Allow requests from any domain
- **Why needed**: Browser security blocks cross-origin requests by default
- **Production**: Would restrict to specific origins

```python
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
```
- **Pydantic BaseModel**: Data validation + serialization
- **Type hints**: `str`, `List[str]`, etc.
- **Optional**: Field can be None
- **Why Pydantic?**: 
  - Automatic validation
  - Auto-generated API documentation
  - Type safety

```python
def fetch_profile(profile_id: str) -> Dict[str, Any]:
    """Retrieve unified profile from MongoDB"""
    client = get_mongodb_client()
    try:
        db = client["cdp"]
        collection = db["profiles"]
        
        profile = collection.find_one({"master_profile_id": profile_id})
```
- **Retrieval step** of RAG
- Fetch complete customer profile
- Single document lookup (fast)

```python
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
```
- **HTTP 404**: Standard "not found" error
- **FastAPI HTTPException**: Automatically converts to JSON error response

```python
def build_personalization_prompt(profile: Dict[str, Any]) -> str:
    """
    Build a context-rich prompt for the LLM.
    This is the "Augmentation" step in RAG.
    """
```
- **Augmentation step** of RAG
- Take raw profile data, create narrative prompt for LLM

```python
    prompt = f"""You are an expert marketing AI for an e-commerce company specializing in electronics.

Your task: Create a highly personalized offer for this customer based on their complete profile.

CUSTOMER PROFILE:
- Customer ID: {profile.get('master_profile_id')}
- Email: {email}
- Customer Value: ${ltv:,.2f}
- Engagement Level: {engagement}/100 {"(High)" if engagement > 70 else "(Medium)" if engagement > 40 else "(Low)"}
```
- **Prompt engineering**: Critical for good LLM results
- **Role definition**: "You are an expert marketing AI..."
- **Context**: Provide all relevant customer data
- **Formatting**: Human-readable format with labels

```python
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
```
- **Structured output**: Force LLM to return JSON
- **CRITICAL**: Emphasize format requirements
- **Schema definition**: Show exact field names and types
- **Why?**: LLMs sometimes add markdown formatting, need to strip it

```python
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
```
- **Generation step** of RAG
- Call LLM with augmented prompt
- Fallback to mock if no API key

```python
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
```
- **Robust parsing**: Handle markdown formatting
- LLMs often wrap JSON in ```json ... ``` blocks
- Split on ``` and take middle section

```python
        # Parse JSON
        offer_data = json.loads(response_text)
        
        # Validate required fields
        required_fields = ["offer_type", "title", "message"]
        for field in required_fields:
            if field not in offer_data:
                raise ValueError(f"Missing required field: {field}")
```
- **Validation**: Ensure LLM returned required fields
- **Defense programming**: LLMs don't always follow instructions perfectly

```python
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        # Fallback to mock
        return generate_mock_offer(profile)
```
- **Error handling**: If LLM response is invalid JSON
- **Fallback**: Use rule-based mock offer
- **Logging**: Print the invalid response for debugging

```python
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
```
- **FastAPI endpoint**: `GET /personalize/{profile_id}`
- **Path parameter**: `{profile_id}` from URL
- **async**: FastAPI supports async for better performance
- **response_model**: Pydantic validates response structure

```python
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
```
- Create Pydantic model from offer data
- **get() with defaults**: Graceful handling of missing fields
- **generated_at**: Timestamp for caching/debugging

**Key Concepts - RAG Pattern**:
1. **R**etrieve: Get customer data from database
2. **A**ugment: Build context-rich prompt
3. **G**enerate: LLM creates personalized content

**Why RAG?**
- LLMs don't have access to your customer data
- Need to "augment" the prompt with context
- Better than fine-tuning (data changes constantly)

---

## (Continued in next response due to length...)
