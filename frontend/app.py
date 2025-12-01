import streamlit as st
import requests
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
from datetime import datetime

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000/api"
st.set_page_config(
    page_title="CDP Identity Debugger", 
    layout="wide", 
    page_icon="🕵️‍♀️",
    initial_sidebar_state="expanded"
)

# --- ENHANCED STYLING ---
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
    }
    
    /* Custom metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Alert styling */
    .stAlert {
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
    }
    
    /* Button enhancements */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s;
        font-weight: 500;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Header styling */
    h1 {
        color: #667eea;
        font-weight: 700;
    }
    
    h2 {
        color: #764ba2;
        font-weight: 600;
    }
    
    /* Identity badge */
    .identity-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 3px;
    }
    
    .badge-email {
        background: #e3f2fd;
        color: #1976d2;
    }
    
    .badge-phone {
        background: #f3e5f5;
        color: #7b1fa2;
    }
    
    .badge-device {
        background: #fff3e0;
        color: #e65100;
    }
    
    /* Status indicators */
    .status-healthy {
        color: #4caf50;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
    
    .status-critical {
        color: #f44336;
        font-weight: bold;
    }
    
    /* Graph container */
    .graph-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- ENHANCED SIDEBAR ---
st.sidebar.title("🕵️‍♀️ CDP Identity Debugger")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Navigation")
st.sidebar.markdown("Explore identity graphs with AI-powered diagnostics")

# Mode Selection with icons
mode = st.sidebar.radio(
    "Select Mode",
    ["🔍 Profile Inspector", "🚨 Graph Health", "📊 Analytics Dashboard"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Connection Status
st.sidebar.markdown("### 🔌 System Status")
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=2)
    if response.status_code == 200:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Error")
except:
    st.sidebar.error("❌ API Offline")

# Quick Stats
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Quick Stats")
st.sidebar.metric("Session Time", datetime.now().strftime("%H:%M:%S"))

# Help Section
with st.sidebar.expander("ℹ️ Help & Info"):
    st.markdown("""
    **Profile Inspector**
    - Visualize identity clusters
    - AI-powered diagnostics
    - Graph surgery tools
    
    **Graph Health**
    - Detect anomalies
    - Monitor data quality
    - Find hairball patterns
    
    **Analytics Dashboard**
    - System metrics
    - Performance insights
    - Data statistics
    """)

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

# --- PAGE: ANALYTICS DASHBOARD ---
if mode == "📊 Analytics Dashboard":
    st.title("📊 System Analytics Dashboard")
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Total Profiles</div>
            <div class="metric-value">1,247</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="metric-label">Active Sessions</div>
            <div class="metric-value">89</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div class="metric-label">Events Today</div>
            <div class="metric-value">5.2K</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <div class="metric-label">Avg Match Score</div>
            <div class="metric-value">94%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Section
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Event Volume Trend")
        # Placeholder for chart
        chart_data = pd.DataFrame({
            'hour': range(24),
            'events': [120, 145, 160, 175, 190, 210, 230, 250, 280, 310, 340, 360,
                      380, 370, 350, 330, 310, 290, 270, 250, 230, 200, 180, 150]
        })
        st.line_chart(chart_data.set_index('hour'))
    
    with col_right:
        st.subheader("🎯 Identity Distribution")
        identity_data = pd.DataFrame({
            'type': ['Email', 'Phone', 'Device ID', 'User ID'],
            'count': [1847, 1432, 2156, 987]
        })
        st.bar_chart(identity_data.set_index('type'))
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("🕐 Recent Activity")
    activity_data = pd.DataFrame({
        'Timestamp': ['2025-11-27 14:35:22', '2025-11-27 14:34:18', '2025-11-27 14:33:45'],
        'Event': ['Profile Merged', 'New Identity Added', 'Anomaly Detected'],
        'Profile ID': ['profile_abc123', 'profile_xyz789', 'profile_def456'],
        'Status': ['✅ Success', '✅ Success', '⚠️ Warning']
    })
    st.dataframe(activity_data, use_container_width=True, hide_index=True)

# --- PAGE: GRAPH HEALTH ---
elif mode == "🚨 Graph Health":
    st.title("🚨 Graph Health Monitor")
    
    # Header with refresh
    col_header1, col_header2 = st.columns([4, 1])
    with col_header1:
        st.markdown("### Real-time anomaly detection and data quality monitoring")
    with col_header2:
        scan_button = st.button("🔄 Scan Now", use_container_width=True, type="primary")
    
    if scan_button:
        with st.spinner("🔍 Scanning graph for anomalies..."):
            data = fetch_anomalies()
            
            if data:
                # Summary Banner
                summary_text = data.get("summary", "Scan complete")
                if "No anomalies" in summary_text:
                    st.success(f"✅ {summary_text}")
                else:
                    st.warning(f"⚠️ {summary_text}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Anomaly Cards
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🔥 Email Hairballs")
                    st.caption("Profiles with suspicious email clustering")
                    
                    emails = data.get("high_email_profiles", [])
                    if emails:
                        for profile in emails[:5]:  # Show top 5
                            with st.container():
                                st.markdown(f"""
                                <div style='background: #fff3cd; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #ff9800;'>
                                    <strong>Profile:</strong> {profile['profile_id']}<br>
                                    <strong>Email Count:</strong> <span class='status-critical'>{profile['email_count']}</span><br>
                                    <small>⚠️ Potential identity storm detected</small>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Full table in expander
                        with st.expander("📋 View All Email Anomalies"):
                            df = pd.DataFrame(emails)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.success("✅ No email anomalies detected")

                with col2:
                    st.markdown("### 🏢 Device Anomalies")
                    st.caption("Profiles with high device count (shared kiosks)")
                    
                    devices = data.get("high_device_profiles", [])
                    if devices:
                        for profile in devices[:5]:
                            with st.container():
                                st.markdown(f"""
                                <div style='background: #e8f5e9; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #4caf50;'>
                                    <strong>Profile:</strong> {profile['profile_id']}<br>
                                    <strong>Device Count:</strong> <span class='status-warning'>{profile['device_count']}</span><br>
                                    <small>ℹ️ Possible shared device scenario</small>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with st.expander("📋 View All Device Anomalies"):
                            df = pd.DataFrame(devices)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.success("✅ No device anomalies detected")
            else:
                st.error("❌ Could not connect to API. Please check if the service is running.")
    else:
        st.info("👆 Click 'Scan Now' to detect anomalies in the identity graph")


# --- PAGE: PROFILE INSPECTOR ---
elif mode == "🔍 Profile Inspector":
    st.title("🔍 Profile Inspector")
    st.markdown("### Visualize identity clusters and perform AI-powered diagnostics")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Enhanced Input Section
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        profile_id_input = st.text_input(
            "Master Profile ID",
            placeholder="Enter profile ID (e.g., profile_abc123)",
            label_visibility="collapsed",
            help="Enter the unique identifier for the profile you want to inspect"
        )
    with col2:
        load_random = st.button("🎲 Random", use_container_width=True, help="Load a random anomaly profile")
    with col3:
        clear_btn = st.button("🗑️ Clear", use_container_width=True, help="Clear the current view")
    
    if load_random:
        with st.spinner("Loading random anomaly..."):
            anomalies = fetch_anomalies()
            if anomalies and anomalies.get("high_email_profiles"):
                profile_id_input = anomalies["high_email_profiles"][0]["profile_id"]
                st.rerun()
    
    if clear_btn:
        profile_id_input = ""
        st.rerun()

    if profile_id_input:
        graph_data = fetch_profile_graph(profile_id_input)
        
        if graph_data:
            # Layout: Graph on Left, AI on Right
            left_col, right_col = st.columns([2, 1])
            
            with left_col:
                st.markdown("### 🕸️ Identity Graph Visualization")
                
                # Identity Summary Stats
                identity_counts = {}
                for identity in graph_data.get("identities", []):
                    identity_type = identity['type']
                    identity_counts[identity_type] = identity_counts.get(identity_type, 0) + 1
                
                stat_cols = st.columns(len(identity_counts) if identity_counts else 1)
                for idx, (id_type, count) in enumerate(identity_counts.items()):
                    with stat_cols[idx]:
                        icon = "📧" if id_type == "email" else "📱" if id_type == "phone" else "💻"
                        st.metric(f"{icon} {id_type.title()}", count)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Build Enhanced Graph
                nodes = []
                edges = []
                
                # 1. Master Profile Node (Center)
                nodes.append(Node(
                    id=graph_data["profile_id"], 
                    label="🎯 Master Profile", 
                    size=30, 
                    color="#667eea",
                    font={'size': 16, 'color': '#ffffff', 'face': 'arial', 'bold': True},
                    shape="diamond"
                ))
                
                # 2. Identity Nodes with enhanced styling
                color_map = {
                    "email": "#00CC96",
                    "phone": "#AB63FA", 
                    "device_id": "#FFA15A",
                    "user_id": "#19D3F3"
                }
                
                icon_map = {
                    "email": "📧",
                    "phone": "📱",
                    "device_id": "💻",
                    "user_id": "👤"
                }
                
                for identity in graph_data.get("identities", []):
                    node_id = f"{identity['type']}:{identity['value']}"
                    id_type = identity['type']
                    label = identity['value']
                    
                    # Get color and icon
                    color = color_map.get(id_type, "#636EFA")
                    icon = icon_map.get(id_type, "🔗")
                    
                    # Truncate long labels
                    display_label = label if len(label) < 25 else label[:22] + "..."
                    
                    nodes.append(Node(
                        id=node_id,
                        label=f"{icon} {display_label}",
                        size=18,
                        color=color,
                        font={'size': 12}
                    ))
                    
                    edges.append(Edge(
                        source=graph_data["profile_id"],
                        target=node_id,
                        color="#cccccc",
                        width=2
                    ))
                
                # Enhanced Config
                config = Config(
                    width=750,
                    height=550,
                    directed=False, 
                    physics={
                        'enabled': True,
                        'barnesHut': {
                            'gravitationalConstant': -8000,
                            'centralGravity': 0.3,
                            'springLength': 150,
                            'springConstant': 0.04
                        },
                        'stabilization': {'iterations': 100}
                    },
                    hierarchical=False,
                    nodeHighlightBehavior=True,
                    highlightColor="#667eea"
                )
                
                # Graph container with custom styling
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                agraph(nodes=nodes, edges=edges, config=config)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with right_col:
                st.markdown("### 🤖 AI Diagnosis")
                
                diagnosis = fetch_ai_diagnosis(profile_id_input)
                
                if "error" in diagnosis:
                    st.error(f"❌ {diagnosis['error']}")
                else:
                    # Enhanced Classification Badge
                    classification = diagnosis.get("classification", "Unknown")
                    confidence = diagnosis.get("confidence_score", 0)
                    
                    # Custom classification card
                    if classification == "Fraud":
                        badge_color = "#f44336"
                        badge_icon = "🛑"
                        badge_bg = "#ffebee"
                    elif classification == "Shared Device":
                        badge_color = "#ff9800"
                        badge_icon = "⚠️"
                        badge_bg = "#fff3e0"
                    else:
                        badge_color = "#4caf50"
                        badge_icon = "✅"
                        badge_bg = "#e8f5e9"
                    
                    st.markdown(f"""
                    <div style='background: {badge_bg}; padding: 20px; border-radius: 12px; border-left: 5px solid {badge_color}; margin-bottom: 20px;'>
                        <div style='font-size: 2rem; margin-bottom: 10px;'>{badge_icon}</div>
                        <div style='font-size: 1.5rem; font-weight: bold; color: {badge_color};'>{classification}</div>
                        <div style='font-size: 1rem; color: #666; margin-top: 5px;'>Confidence: {confidence}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Explanation Card
                    st.markdown("#### 📝 Explanation")
                    st.markdown(f"""
                    <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                        {diagnosis.get("explanation", "No explanation available")}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Recommendation Card
                    st.markdown("#### 💡 Recommendation")
                    recommendation = diagnosis.get("recommended_action", "No recommendation available")
                    st.info(recommendation)
                    
                    # Additional Insights
                    with st.expander("🔍 Detailed Analysis"):
                        st.markdown(f"""
                        **Profile ID:** `{graph_data['profile_id']}`  
                        **Total Identities:** {len(graph_data.get('identities', []))}  
                        **Classification:** {classification}  
                        **Confidence Score:** {confidence}%  
                        **Analysis Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        """)
                    
                    # Raw JSON expander
                    with st.expander("📄 Raw API Response"):
                        st.json(diagnosis)

            with left_col:
                st.markdown("---")
                st.markdown("### ✂️ Graph Surgery")
                st.info("💡 Detach identities to fix incorrect profile merges")
                
                if graph_data.get("identities"):
                    # Group identities by type
                    identity_groups = {}
                    for identity in graph_data.get("identities", []):
                        id_type = identity['type']
                        if id_type not in identity_groups:
                            identity_groups[id_type] = []
                        identity_groups[id_type].append(identity)
                    
                    # Display grouped identities with enhanced styling
                    for id_type, identities in identity_groups.items():
                        icon = icon_map.get(id_type, "🔗")
                        
                        with st.expander(f"{icon} {id_type.title()} ({len(identities)})", expanded=True):
                            for identity in identities:
                                col_a, col_b = st.columns([4, 1])
                                with col_a:
                                    st.markdown(f"""
                                    <div style='padding: 8px; background: #f8f9fa; border-radius: 5px; margin: 5px 0;'>
                                        <code>{identity['value']}</code>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_b:
                                    if st.button("🔪 Detach", key=identity['value'], use_container_width=True):
                                        with st.spinner(f"Detaching {identity['value']}..."):
                                            result = split_identity(
                                                graph_data["profile_id"], 
                                                identity['type'], 
                                                identity['value']
                                            )
                                            if "status" in result:
                                                st.success(f"✅ Successfully detached! New Profile: `{result.get('new_profile_id')}`")
                                                st.balloons()
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to detach: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("No identities found to manage")

        else:
            st.warning("⚠️ Profile not found. Please check the Profile ID and try again.")
            st.info("💡 Tip: Use the 🎲 Random button to load a sample anomaly profile")