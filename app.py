import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Page Configuration
st.set_page_config(page_title="Group Trip Hub", page_icon="🏍️", layout="wide")

st.title("🏍️ Group Trip & Trek Hub")
st.caption("Live coordination board for riders & trekkers")

# Persistent Session States
if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "rider_instructions" not in st.session_state:
    st.session_state.rider_instructions = []

if "backsitter_instructions" not in st.session_state:
    st.session_state.backsitter_instructions = []

# --- SECTION 1: MANUAL INSTRUCTIONS (RIDERS & PILLIONS) ---
st.subheader("📋 Rider & Pillion Briefing")

col_r, col_b = st.columns(2)

with col_r:
    st.markdown("### 🏍️ For Particular Riders")
    with st.form("rider_inst_form", clear_on_submit=True):
        target_rider = st.text_input("Rider Name / Bike No.")
        instruction_text = st.text_area("Instruction / Assignment")
        add_rider_inst = st.form_submit_button("Assign Instruction")

        if add_rider_inst and target_rider and instruction_text:
            st.session_state.rider_instructions.append({
                "Rider": target_rider,
                "Instruction": instruction_text,
                "Time": datetime.now().strftime('%H:%M')
            })
            st.success("Instruction added for rider!")

    if st.session_state.rider_instructions:
        for idx, item in enumerate(st.session_state.rider_instructions):
            st.warning(f"**[{item['Time']}] {item['Rider']}**: {item['Instruction']}")

with col_b:
    st.markdown("### 🎒 For Pillions (Backsitters)")
    with st.form("backsitter_inst_form", clear_on_submit=True):
        target_backsitter = st.text_input("Pillion Name / Assigned Rider")
        backsitter_text = st.text_area("Task (e.g., Navigation, Photo duty, Expense log)")
        add_back_inst = st.form_submit_button("Assign Task")

        if add_back_inst and target_backsitter and backsitter_text:
            st.session_state.backsitter_instructions.append({
                "Pillion": target_backsitter,
                "Task": backsitter_text,
                "Time": datetime.now().strftime('%H:%M')
            })
            st.success("Task assigned to pillion!")

    if st.session_state.backsitter_instructions:
        for idx, item in enumerate(st.session_state.backsitter_instructions):
            st.info(f"**[{item['Time']}] {item['Pillion']}**: {item['Task']}")

st.divider()

# --- SECTION 2: INTERACTIVE SATELLITE & ROAD MAP ---
st.subheader("🗺️ Live Route & Terrain Map")

map_mode = st.radio(
    "Select Map Layer View:",
    ["Esri World Imagery (Real Satellite)", "OpenStreetMap (Standard Road Map)", "CartoDB Positron (Light View)"],
    horizontal=True
)

# Base coordinates
m = folium.Map(location=[19.2183, 72.9781], zoom_start=11)

if map_mode == "Esri World Imagery (Real Satellite)":
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(m)
elif map_mode == "CartoDB Positron (Light View)":
    folium.TileLayer('cartodbpositron').add_to(m)

# Add sample regroup checkpoint marker
folium.Marker(
    [19.2183, 72.9781],
    popup="Starting Point / Regroup Area",
    tooltip="Regroup Point",
    icon=folium.Icon(color="red", icon="info-sign")
).add_to(m)

st_folium(m, width="100%", height=450)

st.divider()

# --- SECTION 3: QUICK ALERTS ---
st.subheader("🚨 Live Status & Alerts")
a_col1, a_col2, a_col3 = st.columns(3)
with a_col1:
    if st.button("⛽ Fuel / Chai Stop", use_container_width=True):
        st.session_state.alerts.insert(0, f"[{datetime.now().strftime('%H:%M')}] Rider stopped for Fuel/Tea")
with a_col2:
    if st.button("🔧 Puncture / Mechanical", use_container_width=True):
        st.session_state.alerts.insert(0, f"[{datetime.now().strftime('%H:%M')}] ⚠️ Breakdown/Puncture reported!")
with a_col3:
    if st.button("📍 Regroup Point Reached", use_container_width=True):
        st.session_state.alerts.insert(0, f"[{datetime.now().strftime('%H:%M')}] 🟢 Reached regroup point")

if st.session_state.alerts:
    for alert in st.session_state.alerts[:5]:
        st.write(alert)

st.divider()

# --- SECTION 4: EXPENSE LOG ---
st.subheader("💰 Quick Expense Log")
with st.form("expense_form", clear_on_submit=True):
    spender = st.text_input("Who paid?")
    amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    for_what = st.text_input("For what?")
    submitted = st.form_submit_button("Add Expense")

    if submitted and spender and amount > 0:
        st.session_state.expenses.append({"Paid By": spender, "Amount (₹)": amount, "Item": for_what})

if st.session_state.expenses:
    df_exp = pd.DataFrame(st.session_state.expenses)
    st.dataframe(df_exp, use_container_width=True)
    st.metric(label="Total Trip Expense", value=f"₹{df_exp['Amount (₹)'].sum():,.2f}")
