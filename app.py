import streamlit as st
from datetime import datetime, date
from supabase import create_client
import pytz

# --- Config ---
ADMIN_PASSWORD = "Verhuizing2025!"
MAX_SPOTS = 17

# --- Setup timezone ---
tz = pytz.timezone("Europe/Amsterdam")
now = datetime.now(tz)
today = now.date()

# --- Load Supabase credentials ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Strategy Room Allocator", page_icon="📍")
st.title("📍 Strategy Office Attendance")

# --- Admin Panel ---
st.sidebar.title("🔐 Admin Panel")
admin_mode = False
open_votes_override = False

admin_pwd = st.sidebar.text_input("Enter admin password", type="password")
if admin_pwd == ADMIN_PASSWORD:
    st.sidebar.success("Admin access granted ✅")
    admin_mode = True

    # Reset button
    if st.sidebar.button("🧼 Reset today's submissions"):
        supabase.table("strategy_signups").delete().eq("date", str(today)).execute()
        st.sidebar.success("✅ Submissions cleared")

    # Force voting open toggle
    open_votes_override = st.sidebar.toggle("🟢 Force-open voting window", value=False)

# --- Submission Logic ---
if now.hour >= 17 or open_votes_override:
    name = st.text_input("Enter your name to sign up:")

    if name:
        # Check if user already signed up
        existing = supabase.table("strategy_signups") \
            .select("*") \
            .eq("date", str(today)) \
            .eq("name", name) \
            .execute()

        # Count total signups for today
        total = supabase.table("strategy_signups") \
            .select("*", count="exact") \
            .eq("date", str(today)) \
            .execute()

        if existing.data:
            st.info("✅ You already signed up.")
        elif total.count >= MAX_SPOTS:
            st.warning("🚫 All 17 spots are full.")
        else:
            if st.button("✅ I'm going to the office"):
                supabase.table("strategy_signups").insert({
                    "name": name,
                    "date": str(today)
                }).execute()
                st.success("🎉 You're signed up!")
else:
    st.info("🕔 Submissions open daily after 17:00 (Dutch time).")

# --- Display current signups ---
st.subheader("Confirmed for tomorrow:")
signups = supabase.table("strategy_signups") \
    .select("*") \
    .eq("date", str(today)) \
    .order("created_at", desc=False) \
    .execute()

for entry in signups.data:
    st.markdown(f"- {entry['name']}")

spots_left = MAX_SPOTS - len(signups.data)
st.caption(f"🪑 {spots_left} spot(s) left for tomorrow.")
