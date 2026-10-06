import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Group Trip Hub", page_icon="🏍️", layout="wide")

st.title("🏍️️ Group Trip & Trek Hub")
st.caption("Live coordination board for riders & trekkers")

# Initialize persistent session state for live tracking
if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

# --- SECTION 1: QUICK RIDER ALERT SYSTEM ---
st.subheader("🚨 Live Status & Emergency Alerts")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⛽ Fuel / Chai Stop"):
        st.session_state.alerts.insert(0, f"[{datetime.now().strftime('%H:%M')}] Rider stopped for Fuel/Tea")
        st.success("Alert sent!")

with col2:
    if st.button("🔧 Mechanical / Puncture"):
        st.session_state.alerts.insert(0, f"[{datetime.now().strftime('%H:%M')}] ⚠️ Breakdown/Puncture reported!")
        st.warning("Alert sent!")

with col3:
    if st.button("📍 Regroup Point Reached"):
        st.session_state.alerts.insert(0, f"[{datetime.now().strftime('%H:%M')}] 🟢 Reached regroup point")
        st.info("Alert sent!")

# Display live alert log
if st.session_state.alerts:
    st.write("### Recent Activity Feed")
    for alert in st.session_state.alerts[:5]:
        st.info(alert)

st.divider()

# --- SECTION 2: TRIP EXPENSE SPLITTER ---
st.subheader("💰 Quick Expense Log")

with st.form("expense_form", clear_on_submit=True):
    spender = st.text_input("Who paid?")
    amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    for_what = st.text_input("For what? (e.g., Fuel, Toll, Snacks, Breakfast)")
    submitted = st.form_submit_button("Add Expense")

    if submitted and spender and amount > 0:
        st.session_state.expenses.append({"Paid By": spender, "Amount (₹)": amount, "Item": for_what})
        st.success(f"Added ₹{amount} by {spender}")

if st.session_state.expenses:
    df_exp = pd.DataFrame(st.session_state.expenses)
    st.dataframe(df_exp, use_container_width=True)
    st.metric(label="Total Trip Expense", value=f"₹{df_exp['Amount (₹)'].sum():,.2f}")
