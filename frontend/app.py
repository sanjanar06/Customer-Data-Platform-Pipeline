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
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🕵️‍♀️ Identity Debugger")
st.sidebar.markdown("Explore probabilistic matches and AI diagnostics.")

# Mode Selection
mode = st.sidebar.radio("Mode", ["Profile Inspector", "Graph Health"])

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

# --- PAGE: GRAPH HEALTH ---
if mode == "Graph Health":
    st.title("🚨 Graph Health Monitor")
    
    if st.button("Scan for Anomalies"):
        data = fetch_anomalies()
        if data:
            st.success(data.get("summary"))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔥 Hairballs (High Email Count)")
                emails = data.get("high_email_profiles", [])
                if emails:
                    df = pd.DataFrame(emails)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No email anomalies found.")

            with col2:
                st.subheader("🏢 Public Kiosks (High Device Count)")
                devices = data.get("high_device_profiles", [])
                if devices:
                    df = pd.DataFrame(devices)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No device anomalies found.")
        else:
            st.error("Could not connect to API. Is it running?")


# --- PAGE: PROFILE INSPECTOR ---
elif mode == "Profile Inspector":
    st.title("🔍 Profile Inspector")
    
    # Input
    col1, col2 = st.columns([3, 1])
    with col1:
        profile_id_input = st.text_input("Enter Master Profile ID", placeholder="profile_...")
    with col2:
        # Quick-load button for demo purposes
        if st.button("Load Random Hairball"):
            anomalies = fetch_anomalies()
            if anomalies and anomalies.get("high_email_profiles"):
                profile_id_input = anomalies["high_email_profiles"][0]["profile_id"]
                st.rerun()

    if profile_id_input:
        graph_data = fetch_profile_graph(profile_id_input)
        
        if graph_data:
            # Layout: Graph on Left, AI on Right
            left_col, right_col = st.columns([2, 1])
            
            with left_col:
                st.subheader("Identity Graph Visualization")
                
                # Build Graph
                nodes = []
                edges = []
                
                # 1. Master Profile Node
                nodes.append(Node(
                    id=graph_data["profile_id"], 
                    label="Master Profile", 
                    size=25, 
                    color="#FF4B4B", # Red
                    symbolType="diamond"
                ))
                
                # 2. Identity Nodes
                for identity in graph_data.get("identities", []):
                    node_id = f"{identity['type']}:{identity['value']}"
                    label = identity['value']
                    
                    # Color code by type
                    color = "#00CC96" if identity['type'] == "email" else "#636EFA"
                    icon = "📧" if identity['type'] == "email" else "📱"
                    
                    nodes.append(Node(
                        id=node_id,
                        label=f"{icon} {label}",
                        size=15,
                        color=color
                    ))
                    
                    edges.append(Edge(
                        source=graph_data["profile_id"],
                        target=node_id,
                        color="#888"
                    ))
                
                # Config
                config = Config(
                    width=700,
                    height=500,
                    directed=True, 
                    physics=True, 
                    hierarchical=False
                )
                
                agraph(nodes=nodes, edges=edges, config=config)
            
            with right_col:
                st.subheader("🤖 AI Diagnosis")
                
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

            with left_col:
                st.divider()
                st.subheader("✂️ Graph Surgery")
                st.info("Select an identity to detach from this profile.")
                            
                # List identities with "Split" buttons
                for identity in graph_data.get("identities", []):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**{identity['type']}**: {identity['value']}")
                    with col_b:
                        if st.button("Detach", key=identity['value']):
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

        else:
            st.warning("Profile not found.")