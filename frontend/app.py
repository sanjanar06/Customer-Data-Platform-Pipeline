import streamlit as st
import requests
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000/api"
st.set_page_config(page_title="CDP Identity Debugger", layout="wide", page_icon="🕵️‍♀️")

# --- STYLING ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .stAlert {
        padding: 10px;
        border-radius: 5px;
    }
    /* Increase tab font size */
    button[data-baseweb="tab"] div p {
        font-size: 18px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("CDP Identity Debugger")
st.markdown("Explore probabilistic matches, visualize identity graphs, and get AI-powered diagnostics.")
# --- FUNCTIONS ---
def fetch_anomalies():
    try:
        response = requests.get(f"{API_BASE_URL}/graph/anomalies")
        if response.status_code == 200:
            return response.json()
    except:
        return None

def fetch_profile_graph(profile_id):
    try:
        response = requests.get(f"{API_BASE_URL}/graph/cluster/{profile_id}")
        if response.status_code == 200:
            return response.json()
    except:
        return None

def fetch_ai_diagnosis(profile_id):
    try:
        with st.spinner("🤖 AI Doctor is analyzing the graph..."):
            response = requests.get(f"{API_BASE_URL}/graph/explain/{profile_id}")
            if response.status_code == 200:
                return response.json().get("ai_diagnosis", {})
    except:
        return {"error": "Failed to connect to AI Service"}

def split_identity(profile_id, type, value):
    try:
        url = f"{API_BASE_URL}/graph/split?profile_id={profile_id}&identity_type={type}&identity_value={value}"
        response = requests.post(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def fetch_personalized_offer(profile_id):
    try:
        response = requests.get(f"{API_BASE_URL}/personalize/{profile_id}")
        if response.status_code == 200:
            return response.json()
    except:
        return None


# --- MAIN NAVIGATION (Horizontal Banner) ---
tab_inspector, tab_health, tab_personalize = st.tabs(["Profile Inspector", "Graph Health Monitor", "Personalize"])

# --- TAB 1: PROFILE INSPECTOR ---
with tab_inspector:
    st.subheader("Profile Inspection Tool")
    
    # Input
    profile_id_input = st.text_input("Enter Master Profile ID", placeholder="profile_...", key="inspector_input")
    
    if profile_id_input:
        graph_data = fetch_profile_graph(profile_id_input)
        
        if graph_data:
            # Layout: Graph on Left, AI on Right
            left_col, right_col = st.columns([2, 1])
            
            with left_col:
                st.markdown("#### Identity Graph Visualization")
                
                # Build Graph
                nodes = []
                edges = []
                
                # 1. Master Profile Node (Center)
                nodes.append(Node(
                    id=graph_data["profile_id"], 
                    label="Master Profile", 
                    size=40,                 # Made bigger
                    color="#FF4B4B",         # Bright Red
                    symbolType="diamond",
                    # FIX: Force white text for dark mode
                    font={"color": "white", "size": 16} 
                ))
                
                # 2. Identity Nodes (Satellites)
                for identity in graph_data.get("identities", []):
                    node_id = f"{identity['type']}:{identity['value']}"
                    label = identity['value']
                    
                    # High Contrast Neon Colors
                    if identity['type'] == "email":
                        color = "#00FFA3"   # Neon Green/Teal
                        icon = "📧"
                    elif identity['type'] == "deviceID":
                        color = "#2E86C1"   # Bright Blue
                        icon = "📱"
                    else:
                        color = "#9B59B6"   # Purple (for phones/others)
                        icon = "🆔"
                    
                    nodes.append(Node(
                        id=node_id,
                        label=f"{icon}\n{label}", # Multi-line label
                        size=20,
                        color=color,
                        # FIX: Force white text
                        font={"color": "white", "size": 12} 
                    ))
                    
                    edges.append(Edge(
                        source=graph_data["profile_id"],
                        target=node_id,
                        # FIX: Bright white lines to stand out on dark background
                        color="#ffffff",
                        width=2
                    ))
                
                # Config (Physics and Interactions)
                config = Config(
                    width=700,
                    height=500,
                    directed=True, 
                    physics=True, 
                    hierarchical=False,
                    # FIX: Add node highlighting
                    nodeHighlightBehavior=True,
                    highlightColor="#F7A541", # Orange highlight on hover
                    collapsible=False
                )
                
                agraph(nodes=nodes, edges=edges, config=config)
                
                st.divider()
                st.subheader("✂️ Graph Surgery")
                st.info("Select an identity to detach from this profile.")
                            
                # List identities with "Split" buttons
                for identity in graph_data.get("identities", []):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**{identity['type']}**: {identity['value']}")
                    with col_b:
                        if st.button("Detach", key=f"btn_{identity['value']}"):
                            result = split_identity(
                                graph_data["profile_id"], 
                                identity['type'], 
                                identity['value']
                            )
                            if "status" in result:
                                st.success(f"Detached! New Profile: {result.get('new_profile_id')}")
                                st.rerun() # Refresh to show the change
                            else:
                                st.error("Failed to detach.")
            
            with right_col:
                st.markdown("#### 🤖 AI Diagnosis")
                
                diagnosis = fetch_ai_diagnosis(profile_id_input)
                
                if "error" in diagnosis:
                    st.error(diagnosis["error"])
                else:
                    # Classification Badge
                    classification = diagnosis.get("classification", "Unknown")
                    confidence = diagnosis.get("confidence_score", 0)
                    
                    if classification == "Fraud":
                        st.error(f"🛑 **{classification}** ({confidence}% Confidence)")
                    elif classification == "Shared Device":
                        st.warning(f"⚠️ **{classification}** ({confidence}% Confidence)")
                    else:
                        st.success(f"✅ **{classification}** ({confidence}% Confidence)")
                    
                    st.markdown("### Explanation")
                    st.write(diagnosis.get("explanation"))
                    
                    st.markdown("### Recommendation")
                    st.info(diagnosis.get("recommended_action"))
                    
                    # Raw JSON expander
                    with st.expander("View Raw API Response"):
                        st.json(diagnosis)

        else:
            st.warning("Profile not found.")


# --- TAB 2: GRAPH HEALTH ---
with tab_health:
    st.subheader("Real-time Anomaly Detection")
    
    col_scan, col_spacer = st.columns([1, 5])
    with col_scan:
        scan_btn = st.button("Scan for Anomalies", type="primary")
    
    if scan_btn:
        data = fetch_anomalies()
        if data:
            st.success(data.get("summary"))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🔥 Hairballs (High Email Count)")
                emails = data.get("high_email_profiles", [])
                if emails:
                    df = pd.DataFrame(emails)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No email anomalies found.")

            with col2:
                st.markdown("### 🏢 Public Kiosks (High Device Count)")
                devices = data.get("high_device_profiles", [])
                if devices:
                    df = pd.DataFrame(devices)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No device anomalies found.")
        else:
            st.error("Could not connect to API. Is it running?")

# --- TAB 3: PERSONALIZE ---
with tab_personalize:
    st.subheader("Personalized Offers")
    
    profile_id_personalize = st.text_input("Enter Master Profile ID", placeholder="profile_...", key="personalize_input")
    
    if profile_id_personalize:
        offer_data = fetch_personalized_offer(profile_id_personalize)
        
        if offer_data:
            st.success("Offer Generated Successfully!")
            
            # Display offer details
            st.markdown(f"### {offer_data.get('title', 'Special Offer')}")
            st.markdown(f"**Offer Type:** `{offer_data.get('offer_type', 'N/A')}`")
            
            if offer_data.get('discount'):
                st.info(f" **Discount:** {offer_data.get('discount')}")
            
            st.markdown("#### Message")
            st.write(offer_data.get('message', 'No message available'))
            
            # Products
            if offer_data.get('products'):
                st.markdown("#### Recommended Products")
                for product in offer_data.get('products', []):
                    st.markdown(f"- {product}")
            
            # Reasoning
            if offer_data.get('reasoning'):
                with st.expander("AI Reasoning"):
                    st.write(offer_data.get('reasoning'))
            
            # Timestamp
            st.caption(f"Generated at: {offer_data.get('generated_at', 'N/A')}")
            
        else:
            st.error("Could not fetch personalized offer. Check if the API is running and the profile exists.")