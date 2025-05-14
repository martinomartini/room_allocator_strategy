import streamlit as st
from datetime import datetime, date
from supabase import create_client, Client
import pytz
import pandas as pd

# --- Constants ---
ADMIN_PASSWORD = "Verhuizing2025!"
MAX_SPOTS = 17

# --- Timezone Setup ---
tz = pytz.timezone("Europe/Amsterdam")
now = datetime.now(tz)
today = now.date()

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Page Config ---
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

    if st.sidebar.button("🧼 Reset today's submissions"):
        try:
            supabase.table("strategy_signups").delete().eq("date", str(today)).execute()
            st.sidebar.success("✅ Submissions cleared")
        except Exception as e:
            st.sidebar.error(f"❌ Reset failed: {e}")

    open_votes_override = st.sidebar.toggle("🟢 Force-open voting window", value=False)

# --- Submission Form ---
if now.hour >= 17 or open_votes_override:
    name = st.text_input("Enter your name to sign up:")

    if name:
        try:
            # Check if already signed up
            existing = supabase.table("strategy_signups") \
                .select("*") \
                .eq("date", str(today)) \
                .eq("name", name.strip()) \
                .execute()

            # Count total signups
            total = supabase.table("strategy_signups") \
                .select("*", count="exact") \
                .eq("date", str(today)) \
                .execute()

            if existing.data:
                st.info("✅ You already signed up.")
            elif total.count >= MAX_SPOTS:
                st.warning("🚫 All 17 spots are full.")
            else:
                response = supabase.table("strategy_signups").insert({
                    "name": name.strip(),
                    "date": str(today)
                }).execute()
                st.success("🎉 You're signed up!")

        except Exception as e:
            st.error(f"❌ Submission failed: {e}")
else:
    st.info("🕔 Submissions open daily after 17:00 (Dutch time).")

# --- Display Signups Table ---
st.subheader("Confirmed for tomorrow:")

try:
    response = supabase.table("strategy_signups") \
        .select("*") \
        .eq("date", str(today)) \
        .order("created_at", desc=False) \
        .execute()

    signups = response.data

    if not signups:
        st.info("🙁 No one has signed up yet.")
    else:
        df = pd.DataFrame(signups)
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%H:%M:%S")

        df_display = df[["name", "created_at"]].rename(columns={
            "name": "Name",
            "created_at": "Submitted at"
        })

        st.dataframe(df_display, use_container_width=True)

        spots_left = MAX_SPOTS - len(df_display)
        st.markdown(f"🪑 **{spots_left} spot(s)** left for tomorrow")

except Exception as e:
    st.error(f"❌ Failed to load signups: {e}")
