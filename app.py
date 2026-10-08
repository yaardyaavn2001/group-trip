import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import json
import os
import xml.etree.ElementTree as ET
import urllib.parse
import math
import streamlit.components.v1 as components

# --- PAGE SETUP & MOBILE UX ---
st.set_page_config(
    page_title="Group Trip Hub",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        border-radius: 8px;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- SECURITY & PASSCODE ACCESS ---
TRIP_PIN = "2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Group Trip Hub - Security Access")
    st.caption("Enter group passcode to proceed")
    
    user_pin = st.text_input("Trip Passcode", type="password", max_chars=4)
    if st.button("Unlock Trip Dashboard"):
        if user_pin == TRIP_PIN:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect passcode. Ask your trip admin.")
    st.stop()

# --- PERSISTENT DATA ENGINE ---
DATA_FILE = "trip_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "alerts": [],
        "expenses": [],
        "rider_inst": [],
        "pillion_inst": [],
        "leaderboard": {}
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

cloud_data = load_data()

# --- HAVERSINE DISTANCE CALCULATION (KM) ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- APP HEADER ---
col_head, col_lock = st.columns([4, 1])
with col_head:
    st.title("🏍️ Group Trip & Ride Manager")
    st.caption("Live Automatic Tracking, Leaderboard & Coordination Hub")
with col_lock:
    if st.button("🔒 Lock"):
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# --- SECTION 1: LIVE GPS TRACKING CONTROLLER ---
st.subheader("📡 Live GPS Location Sync")

col_user1, col_user2 = st.columns([2, 2])
with col_user1:
    current_rider = st.text_input("Enter Your Rider / Bike Name", value="Aryan (Lead)")
with col_user2:
    target_dest_coords = st.text_input("Destination Coordinates (Lat, Lon)", value="19.0728, 73.5358") # Default Bhimashankar

# Parse destination coordinates
try:
    dest_lat, dest_lon = [float(x.strip()) for x in target_dest_coords.split(",")]
except Exception:
    dest_lat, dest_lon = 19.0728, 73.5358

# HTML / JS auto-location streamer
gps_html = f"""
<div style="background:#1e1e1e; color:white; padding:10px; border-radius:8px; font-family:sans-serif; text-align:center;">
    <p id="status" style="margin:0; font-size:14px; font-weight:bold;">📡 Initializing Live GPS Tracking...</p>
</div>
<script>
    function updatePosition(position) {{
        var lat = position.coords.latitude;
        var lon = position.coords.longitude;
        document.getElementById("status").innerHTML = "🟢 Live Location Transmitting: " + lat.toFixed(4) + ", " + lon.toFixed(4);
    }}
    function handleError(error) {{
        document.getElementById("status").innerHTML = "🔴 GPS Error: Please allow Location Permission on your phone browser.";
    }}
    if (navigator.geolocation) {{
        navigator.geolocation.watchPosition(updatePosition, handleError, {{
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 5000
        }});
    }} else {{
        document.getElementById("status").innerHTML = "❌ Geolocation is not supported by this browser.";
    }}
</script>
"""
components.html(gps_html, height=60)

# Optional Manual Coordinate Override for Testing/Fallback
with st.expander("⚙️ Manual GPS Coordinate Sync (Fallback)"):
    with st.form("manual_gps_form"):
        c_lat = st.number_input("Your Current Latitude", value=19.2183, format="%.4f")
        c_lon = st.number_input("Your Current Longitude", value=72.9781, format="%.4f")
        if st.form_submit_button("Broadcast Location"):
            dist_to_go = calculate_distance(c_lat, c_lon, dest_lat, dest_lon)
            cloud_data["leaderboard"][current_rider] = {
                "lat": c_lat,
                "lon": c_lon,
                "dist_rem": round(dist_to_go, 2),
                "last_seen": datetime.now().strftime('%H:%M:%S')
            }
            save_data(cloud_data)
            st.success("Location broadcasted!")
            st.rerun()

st.divider()

# --- SECTION 2: LIVE SATELLITE MAP & AUTO LEADERBOARD ---
st.subheader("🏆 Live Satellite Map & Automatic Leaderboard")

col_map, col_lb = st.columns([3, 2])

with col_map:
    st.markdown("#### 🗺️ Live Location Map")
    map_mode = st.radio(
        "Layer:",
        ["Esri World Imagery (Real Satellite)", "OpenStreetMap (Standard)", "CartoDB Positron (Light)"],
        horizontal=True
    )

    m = folium.Map(location=[dest_lat, dest_lon], zoom_start=10)

    if map_mode == "Esri World Imagery (Real Satellite)":
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Esri Satellite', overlay=False, control=True
        ).add_to(m)

    # Plot destination marker
    folium.Marker([dest_lat, dest_lon], popup="Destination", icon=folium.Icon(color="green", icon="flag")).add_to(m)

    # Plot live riders from leaderboard storage
    for rider_name, info in cloud_data.get("leaderboard", {}).items():
        folium.Marker(
            [info["lat"], info["lon"]],
            popup=f"{rider_name} ({info['dist_rem']} km left)",
            icon=folium.Icon(color="red", icon="motorcycle", prefix="fa")
        ).add_to(m)

    st_folium(m, width="100%", height=400)

with col_lb:
    st.markdown("#### 🏆 Auto-Sorted Ride Leaderboard")
    
    # Sort leaderboard by remaining distance
    lb_dict = cloud_data.get("leaderboard", {})
    sorted_riders = sorted(lb_dict.items(), key=lambda x: x[1].get("dist_rem", 999))

    if not sorted_riders:
        st.info("No live rider data broadcasting yet. Enter rider name and allow location access.")
    else:
        total_reference_dist = 60.0 # reference km for progress bar
        for idx, (rider, info) in enumerate(sorted_riders, start=1):
            dist = info.get("dist_rem", 0.0)
            last_seen = info.get("last_seen", "--:--")
            
            pct = max(0.0, min(1.0, (total_reference_dist - dist) / total_reference_dist))
            
            st.markdown(f"**#{idx} {rider}**")
            st.caption(f"Distance Remaining: **{dist:.2f} km** | Sync: {last_seen}")
            st.progress(pct)
            st.write("")

st.divider()

# --- SECTION 3: INSTRUCTIONS & DUTIES ---
st.subheader("📋 Travel Instructions & Duties")
col_r, col_b = st.columns(2)

with col_r:
    st.markdown("### 🏍️ For Particular Riders")
    with st.form("rider_inst_form", clear_on_submit=True):
        target_rider = st.text_input("Rider Name / Bike No.")
        instruction_text = st.text_area("Instruction / Assignment")
        if st.form_submit_button("Assign Instruction") and target_rider and instruction_text:
            cloud_data["rider_inst"].insert(0, {
                "time": datetime.now().strftime('%H:%M'),
                "assignee": target_rider,
                "task": instruction_text
            })
            save_data(cloud_data)
            st.success("Instruction updated!")
            st.rerun()

    for item in cloud_data.get("rider_inst", [])[:5]:
        st.warning(f"**[{item['time']}] {item['assignee']}**: {item['task']}")

with col_b:
    st.markdown("### 🎒 For Pillions (Backsitters)")
    with st.form("pillion_inst_form", clear_on_submit=True):
        target_pillion = st.text_input("Pillion Name / Assigned Rider")
        pillion_text = st.text_area("Task (Navigation, Photo duty, Expense log)")
        if st.form_submit_button("Assign Task") and target_pillion and pillion_text:
            cloud_data["pillion_inst"].insert(0, {
                "time": datetime.now().strftime('%H:%M'),
                "assignee": target_pillion,
                "task": pillion_text
            })
            save_data(cloud_data)
            st.success("Task assigned!")
            st.rerun()

    for item in cloud_data.get("pillion_inst", [])[:5]:
        st.info(f"**[{item['time']}] {item['assignee']}**: {item['task']}")

st.divider()

# --- SECTION 4: LIVE ONE-TAP ALERTS ---
st.subheader("🚨 Live One-Tap Rider Alerts")
col_a1, col_a2, col_a3, col_a4 = st.columns(4)

def log_alert(msg):
    cloud_data["alerts"].insert(0, f"[{datetime.now().strftime('%H:%M')}] {msg}")
    save_data(cloud_data)
    st.rerun()

with col_a1:
    if st.button("👮 Police Ahead"):
        log_alert("🚨 Police / Checking ahead!")
with col_a2:
    if st.button("⚠️ Bad Pothole"):
        log_alert("⚠️ Bad Pothole / Rough Road ahead!")
with col_a3:
    if st.button("⛽ Fuel Stop"):
        log_alert("⛽ Rider stopped for Fuel/Tea")
with col_a4:
    if st.button("🔧 Breakdown"):
        log_alert("⚠️ Breakdown or Puncture reported!")

if cloud_data.get("alerts"):
    st.markdown("#### Live Activity Feed")
    for alert in cloud_data["alerts"][:5]:
        st.info(alert)

st.divider()

# --- SECTION 5: EXPENSE SPLITTER ---
st.subheader("💰 Expense & Fuel Splitter")
with st.form("expense_form", clear_on_submit=True):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        spender = st.text_input("Who Paid?")
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    with col_e2:
        for_what = st.text_input("For What? (Fuel, Toll, Food, Stay)")
        add_exp = st.form_submit_button("Add Expense")

    if add_exp and spender and amount > 0:
        cloud_data["expenses"].append({"Paid By": spender, "Amount (₹)": amount, "Item": for_what})
        save_data(cloud_data)
        st.success(f"Logged ₹{amount:.2f} by {spender}")
        st.rerun()

if cloud_data.get("expenses"):
    df_exp = pd.DataFrame(cloud_data["expenses"])
    st.dataframe(df_exp, use_container_width=True)
    st.metric(label="Total Group Expense", value=f"₹{df_exp['Amount (₹)'].sum():,.2f}")
