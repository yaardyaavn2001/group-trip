import streamlit as st
import pandas as pd
import math

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Group Trip Hub",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏍️ Group Trip & Ride Manager")

# --- INITIALIZE SESSION STATE FOR DATA STORAGE ---
if "travel_mode" not in st.session_state:
    st.session_state.travel_mode = "Bike Trip"

if "members" not in st.session_state:
    st.session_state.members = [
        {"name": "Rider 1 (Lead)", "role": "Rider", "bike": "Bike A", "lat": 19.2183, "lon": 72.9781},
        {"name": "Pillion 1", "role": "Pillion", "bike": "Bike A", "lat": 19.2183, "lon": 72.9781},
        {"name": "Rider 2 (Mid)", "role": "Rider", "bike": "Bike B", "lat": 19.2050, "lon": 72.9700},
        {"name": "Rider 3 (Sweep)", "role": "Rider", "bike": "Bike C", "lat": 19.1900, "lon": 72.9600},
    ]

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

# Destination Coordinates (Default example: Trip Goal)
DEST_LAT, DEST_LON = 19.2800, 73.0500

# Function to calculate distance (Haversine Formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# --- SIDEBAR: MODE & ROLE SELECTOR ---
st.sidebar.header("⚙️ Trip Settings & Profile")
st.session_state.travel_mode = st.sidebar.radio(
    "Select Mode of Travel:",
    ["Bike Trip", "Train Trip"]
)

user_name = st.sidebar.text_input("Your Name", value="Rider 1 (Lead)")
user_role = st.sidebar.selectbox("Your Role on Bike", ["Rider", "Pillion", "Train Passenger"])

st.sidebar.markdown("---")
st.sidebar.subheader("🚨 One-Tap Live Rider Alerts")
st.sidebar.write("Tap to warn all group riders instantly:")

col_a, col_b = st.sidebar.columns(2)
if col_a.button("🚓 Police Ahead"):
    st.session_state.alerts.insert(0, f"🚓 **ALERT:** Police Checkpoint ahead! Broadcasted by {user_name}.")
if col_b.button("🛑 Bad Pothole"):
    st.session_state.alerts.insert(0, f"🛑 **WARNING:** Heavy potholes/road hazard ahead! ({user_name})")

col_c, col_d = st.sidebar.columns(2)
if col_c.button("⛽ Fuel Stop"):
    st.session_state.alerts.insert(0, f"⛽ **PITSTOP:** Pull over at next fuel pump! ({user_name})")
if col_d.button("🚨 Breakdown"):
    st.session_state.alerts.insert(0, f"🚨 **HELP:** Bike breakdown/flat tire reported by {user_name}!")

# --- DISPLAY LIVE ALERTS AT TOP ---
if st.session_state.alerts:
    st.error(st.session_state.alerts[0])
    with st.expander("View Alert History"):
        for alert in st.session_state.alerts:
            st.write(alert)

# --- NAVIGATION TABS ---
tab_map, tab_instructions, tab_expenses, tab_packing = st.tabs([
    "🗺️ Live Satellite Map & Rankings", 
    "📋 Travel Instructions & Duties", 
    "💰 Expense & Fuel Splitter", 
    "🎒 Smart Checklists"
])

# --- TAB 1: LIVE MAP & LEADERBOARD ---
with tab_map:
    st.subheader(f"Live Tracking & Leaderboard ({st.session_state.travel_mode})")
    
    # Calculate distance to destination for each member
    for m in st.session_state.members:
        m["dist_to_dest_km"] = calculate_distance(m["lat"], m["lon"], DEST_LAT, DEST_LON)
    
    # Sort rankings (closest to destination is #1)
    rankings = sorted(st.session_state.members, key=lambda x: x["dist_to_dest_km"])
    
    col_map, col_rank = st.columns([2, 1])
    
    with col_map:
        st.write("### 🛰️ Live Location Map")
        map_df = pd.DataFrame(rankings)[["lat", "lon"]]
        st.map(map_df, zoom=11)
        
    with col_rank:
        st.write("### 🏆 Ride Leaderboard")
        for i, member in enumerate(rankings):
            st.write(f"**#{i+1} {member['name']}** ({member['bike']})")
            st.caption(f"Distance to Goal: {member['dist_to_dest_km']} km")
            st.progress(max(0.0, min(1.0, 1.0 - (member['dist_to_dest_km'] / 50.0))))

# --- TAB 2: ROLE INSTRUCTIONS ---
with tab_instructions:
    st.subheader("📋 Travel Instructions & Guidelines")
    
    if st.session_state.travel_mode == "Bike Trip":
        if user_role == "Rider":
            st.info("🎯 **RIDER DUTIES:**")
            st.markdown("""
            - Check tire pressure, engine oil level, and fuel before start.
            - Keep headlamp ON during highway runs.
            - Maintain safe 3-second distance behind lead bike.
            - Never overtake from the left side on highways.
            """)
        elif user_role == "Pillion":
            st.success("📸 **PILLION (BACKSITTER) DUTIES:**")
            st.markdown("""
            - Keep emergency hazard alert tab ready on phone.
            - Handle phone navigation/GPS map reading for the rider.
            - Secure all bungee cords and luggage straps at every halt.
            - Capture photos/videos and handle group communication.
            """)
        else:
            st.write("Please select Rider or Pillion role in the sidebar.")
    else:
        st.info("🚂 **TRAIN TRAVEL INSTRUCTIONS:**")
        st.markdown("""
        - Keep digital ticket copies and valid original IDs ready.
        - Lock luggage to under-seat chain loops.
        - Keep emergency power banks and water bottles handy.
        """)

# --- TAB 3: EXPENSE & FUEL SPLITTER ---
with tab_expenses:
    st.subheader("💰 Expense & Fuel Cost Splitter")
    
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        exp_title = st.text_input("Expense Description (e.g., Fuel, Dhaba Lunch)")
        exp_amount = st.number_input("Amount (₹)", min_value=0.0, step=50.0)
        exp_payer = st.selectbox("Paid By", [m["name"] for m in st.session_state.members])
        
        if st.button("Add Expense"):
            if exp_amount > 0 and exp_title:
                st.session_state.expenses.append({"item": exp_title, "amount": exp_amount, "payer": exp_payer})
                st.success(f"Added ₹{exp_amount} for {exp_title}")
    
    with col_exp2:
        st.write("### 📜 Expense Summary")
        if st.session_state.expenses:
            df_exp = pd.DataFrame(st.session_state.expenses)
            st.dataframe(df_exp, use_container_width=True)
            
            total_spent = df_exp["amount"].sum()
            per_head = total_spent / len(st.session_state.members)
            
            st.metric("Total Group Spend", f"₹{total_spent:,.2f}")
            st.metric("Per Person Share", f"₹{per_head:,.2f}")
        else:
            st.write("No expenses logged yet.")

# --- TAB 4: PACKING CHECKLISTS ---
with tab_packing:
    st.subheader("🎒 Smart Packing Checklist")
    
    if st.session_state.travel_mode == "Bike Trip":
        st.checkbox("Helmet with clear visor")
        st.checkbox("Riding Jacket & Gloves")
        st.checkbox("Raincoat / Waterproof Cover")
        st.checkbox("Bungee Cords & Luggage Straps")
        st.checkbox("Tire Puncture Repair Kit & Portable Pump")
        st.checkbox("First Aid Kit & Emergency Medicines")
        st.checkbox("Power Bank & Bike Phone Mount")
    else:
        st.checkbox("Train Tickets & Government IDs")
        st.checkbox("Luggage Chain & Padlock")
        st.checkbox("Power Bank & Charging Cable")
        st.checkbox("Snacks & Water Bottle")
        st.checkbox("Toiletries & Microfiber Towel")