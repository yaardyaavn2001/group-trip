import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import json
import os
import xml.etree.ElementTree as ET
import urllib.parse

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
    return {"alerts": [], "expenses": [], "rider_inst": [], "pillion_inst": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

cloud_data = load_data()

# --- APP HEADER ---
col_head, col_lock = st.columns([4, 1])
with col_head:
    st.title("🏍️ Group Trip & Trek Hub")
    st.caption("Production Coordination Board | Live Group Sync")
with col_lock:
    if st.button("🔒 Lock"):
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# --- SECTION 1: INSTRUCTIONS (RIDERS & PILLIONS) ---
st.subheader("📋 Briefing & Assignments")

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

# --- SECTION 2: MAP, GOOGLE MAPS LAUNCHER & GPX ENGINE ---
st.subheader("🗺️ Navigation, Satellite & GPX Trail Engine")

# Quick Google Maps Launcher for Riders
with st.expander("📍 Quick Launch Google Maps Navigation", expanded=True):
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        gmaps_dest = st.text_input("Enter Destination / Location Name (e.g. Matheran, Kothaligad, Bhimashankar)", "Bhimashankar")
    with col_g2:
        st.write("##")
        encoded_dest = urllib.parse.quote(gmaps_dest)
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_dest}"
        st.markdown(f'<a href="{gmaps_url}" target="_blank"><button style="width:100%; height:3em; background-color:#4285F4; color:white; font-weight:bold; border:none; border-radius:8px; cursor:pointer;">🗺️ Open in Google Maps</button></a>', unsafe_allow_html=True)

st.write("")

col_m1, col_m2 = st.columns([2, 1])

with col_m1:
    map_mode = st.radio(
        "Satellite / Map Layer View:",
        ["Esri World Imagery (Real Satellite)", "OpenStreetMap (Standard)", "CartoDB Positron (Light)"],
        horizontal=True
    )

with col_m2:
    uploaded_gpx = st.file_uploader("Upload GPX Trail File (For Offroad/Treks)", type=["gpx"])

# Parse GPX if uploaded
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
    except Exception as e:
        st.error("Error reading GPX file. Ensure it is a valid track file.")

start_location = route_coords[0] if route_coords else [19.2183, 72.9781]
m = folium.Map(location=start_location, zoom_start=12 if not route_coords else 13)

if map_mode == "Esri World Imagery (Real Satellite)":
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Esri Satellite', overlay=False, control=True
    ).add_to(m)
elif map_mode == "CartoDB Positron (Light)":
    folium.TileLayer('cartodbpositron').add_to(m)

if route_coords:
    folium.PolyLine(route_coords, color="cyan", weight=5, opacity=0.8, tooltip="Planned Trail Route").add_to(m)
    folium.Marker(route_coords[0], popup="Trail Start", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(route_coords[-1], popup="Trail End / Peak", icon=folium.Icon(color="red", icon="flag")).add_to(m)
else:
    folium.Marker([19.2183, 72.9781], popup="Regroup Checkpoint", tooltip="Start / Regroup Area", icon=folium.Icon(color="red", icon="flag")).add_to(m)

st_folium(m, width="100%", height=450)

st.divider()

# --- SECTION 3: LIVE STATUS & EMERGENCY ALERTS ---
st.subheader("🚨 Live Alerts & Status Feed")

col_a1, col_a2, col_a3 = st.columns(3)

def log_alert(msg):
    cloud_data["alerts"].insert(0, f"[{datetime.now().strftime('%H:%M')}] {msg}")
    save_data(cloud_data)
    st.rerun()

with col_a1:
    if st.button("⛽ Fuel / Chai Stop"):
        log_alert("Rider stopped for Fuel/Tea")
with col_a2:
    if st.button("🔧 Mechanical / Breakdown"):
        log_alert("⚠️ Breakdown or Puncture reported!")
with col_a3:
    if st.button("📍 Regroup Point Reached"):
        log_alert("🟢 Reached regroup checkpoint")

if cloud_data.get("alerts"):
    st.markdown("#### Activity Feed")
    for alert in cloud_data["alerts"][:5]:
        st.info(alert)

st.divider()

# --- SECTION 4: EXPENSE TRACKER & SPLITTER ---
st.subheader("💰 Group Expense Splitter")

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
