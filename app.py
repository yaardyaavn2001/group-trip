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
        "leaderboard": [
            {"rider": "Aryan (Lead)", "bike": "Bike A", "dist_rem": 10.2},
            {"rider": "Pillion 1", "bike": "Bike A", "dist_rem": 10.2},
            {"rider": "Rider 2 (Mid)", "bike": "Bike B", "dist_rem": 11.84},
            {"rider": "Rider 3 (Sweep)", "bike": "Bike C", "dist_rem": 13.76}
        ]
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

cloud_data = load_data()

# --- APP HEADER ---
col_head, col_lock = st.columns([4, 1])
with col_head:
    st.title("🏍️ Group Trip & Ride Manager")
    st.caption("Live Tracking, Leaderboard & Coordination Hub")
with col_lock:
    if st.button("🔒 Lock"):
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# --- SECTION 1: INSTRUCTIONS (RIDERS & PILLIONS) ---
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

# --- SECTION 2: LIVE SATELLITE MAP & RIDE LEADERBOARD ---
st.subheader("🏆 Live Satellite Map & Ride Leaderboard")

# Google Maps launcher bar
with st.expander("📍 Launch Google Maps Navigation", expanded=False):
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        gmaps_dest = st.text_input("Destination Name", "Bhimashankar")
    with col_g2:
        st.write("##")
        encoded_dest = urllib.parse.quote(gmaps_dest)
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_dest}"
        st.markdown(f'<a href="{gmaps_url}" target="_blank"><button style="width:100%; height:3em; background-color:#4285F4; color:white; font-weight:bold; border:none; border-radius:8px; cursor:pointer;">🗺️ Open Google Maps</button></a>', unsafe_allow_html=True)

col_map, col_lb = st.columns([3, 2])

with col_map:
    st.markdown("#### 🗺️ Live Location Map")
    map_mode = st.radio(
        "Layer:",
        ["Esri World Imagery (Real Satellite)", "OpenStreetMap (Standard)", "CartoDB Positron (Light)"],
        horizontal=True
    )
    
    uploaded_gpx = st.file_uploader("Upload GPX Route File", type=["gpx"])
    route_coords = []
    if uploaded_gpx is not None:
        try:
            tree = ET.parse(uploaded_gpx)
            root = tree.getroot()
            ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
            for trkpt in root.findall('.//gpx:trkpt', ns):
                lat = float(trkpt.attrib['lat'])
                lon = float(trkpt.attrib['lon'])
                route_coords.append((lat, lon))
            if not route_coords:
                for trkpt in root.findall('.//trkpt'):
                    lat = float(trkpt.attrib['lat'])
                    lon = float(trkpt.attrib['lon'])
                    route_coords.append((lat, lon))
        except Exception:
            st.error("Error parsing GPX file.")

    start_location = route_coords[0] if route_coords else [19.2183, 72.9781]
    m = folium.Map(location=start_location, zoom_start=11)

    if map_mode == "Esri World Imagery (Real Satellite)":
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Esri Satellite', overlay=False, control=True
        ).add_to(m)
    elif map_mode == "CartoDB Positron (Light)":
        folium.TileLayer('cartodbpositron').add_to(m)

    if route_coords:
        folium.PolyLine(route_coords, color="cyan", weight=5, opacity=0.8).add_to(m)
    else:
        # Markers representing group bikes on map
        folium.Marker([19.2183, 72.9781], popup="Lead Rider (Bike A)", icon=folium.Icon(color="red", icon="motorcycle", prefix="fa")).add_to(m)
        folium.Marker([19.2000, 72.9600], popup="Mid Rider (Bike B)", icon=folium.Icon(color="blue", icon="motorcycle", prefix="fa")).add_to(m)
        folium.Marker([19.1800, 72.9400], popup="Sweep Rider (Bike C)", icon=folium.Icon(color="orange", icon="motorcycle", prefix="fa")).add_to(m)

    st_folium(m, width="100%", height=400)

with col_lb:
    st.markdown("#### 🏆 Ride Leaderboard")
    
    # Sort leaderboard by remaining distance (lowest distance to goal = #1)
    lb_data = cloud_data.get("leaderboard", [])
    lb_sorted = sorted(lb_data, key=lambda x: x.get("dist_rem", 999))
    
    total_trip_dist = 50.0  # reference total km for progress bar rendering
    
    for idx, item in enumerate(lb_sorted, start=1):
        rider = item.get("rider", f"Rider {idx}")
        bike = item.get("bike", "")
        dist = item.get("dist_rem", 0.0)
        
        # Calculate percentage completed
        pct = max(0.0, min(1.0, (total_trip_dist - dist) / total_trip_dist))
        
        st.markdown(f"**#{idx} {rider} ({bike})**")
        st.caption(f"Distance to Goal: **{dist:.2f} km**")
        st.progress(pct)
        st.write("")

    # Update Position Form
    with st.expander("⏱️ Update Rider Distance / Position"):
        with st.form("update_lb_form", clear_on_submit=True):
            r_name = st.text_input("Rider/Pillion Name", "Aryan")
            r_bike = st.text_input("Bike Group", "Bike A")
            r_dist = st.number_input("Distance to Goal Remaining (km)", min_value=0.0, max_value=500.0, value=10.0, step=0.5)
            
            if st.form_submit_button("Update Leaderboard"):
                # Update existing or append new
                found = False
                for entry in cloud_data["leaderboard"]:
                    if entry["rider"].lower() == r_name.lower():
                        entry["dist_rem"] = r_dist
                        entry["bike"] = r_bike
                        found = True
                        break
                if not found:
                    cloud_data["leaderboard"].append({"rider": r_name, "bike": r_bike, "dist_rem": r_dist})
                
                save_data(cloud_data)
                st.success(f"Updated position for {r_name}!")
                st.rerun()

st.divider()

# --- SECTION 3: LIVE STATUS & EMERGENCY ALERTS ---
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

with st.form("custom_alert_form", clear_on_submit=True):
    col_ca1, col_ca2 = st.columns([3, 1])
    with col_ca1:
        custom_msg = st.text_input("Custom Status Alert")
    with col_ca2:
        st.write("##")
        if st.form_submit_button("Post Alert") and custom_msg:
            log_alert(f"📢 {custom_msg}")

if cloud_data.get("alerts"):
    st.markdown("#### Live Activity Feed")
    for alert in cloud_data["alerts"][:5]:
        st.info(alert)

st.divider()

# --- SECTION 4: EXPENSE & FUEL SPLITTER ---
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
