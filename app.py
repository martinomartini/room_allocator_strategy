import streamlit as st
from datetime import datetime, timedelta, date
from supabase import create_client, Client
import pytz
import pandas as pd

# --- Config ---
ADMIN_PASSWORD = "Verhuizing2025!"
MAX_SPOTS_PER_DAY = 17
WEEK_START = 0  # Monday (0=Monday, 6=Sunday)

# --- Timezone Setup ---
tz = pytz.timezone("Europe/Amsterdam")
now = datetime.now(tz)
today = now.date()

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Page Setup ---
st.set_page_config("📅 Strategy Weekly Planner", page_icon="📍")
st.title("📅 Strategy Office Weekly Signup")

# --- Get this week's weekdays (Mon–Fri) ---
def get_weekdays():
    start = today - timedelta(days=today.weekday())  # start of week
    return [start + timedelta(days=i) for i in range(5)]

weekdays = get_weekdays()

# --- Auth ---
name = st.text_input("Your name (for signup/unsubscribe):")
if not name:
    st.stop()

# --- Admin Panel ---
st.sidebar.title("🔐 Admin Panel")
admin_mode = False
admin_pwd = st.sidebar.text_input("Admin password", type="password")
if admin_pwd == ADMIN_PASSWORD:
    admin_mode = True
    st.sidebar.success("✅ Admin access granted")
    if st.sidebar.button("🧼 Reset all signups (week)"):
        supabase.table("strategy_signups").delete().execute()
        st.sidebar.success("✅ All signups cleared")

# --- Load signups for the week ---
signups = (
    supabase.table("strategy_signups")
    .select("*")
    .gte("day", str(weekdays[0]))
    .lte("day", str(weekdays[-1]))
    .execute()
    .data
)

df = pd.DataFrame(signups)
if not df.empty:
    df["day"] = pd.to_datetime(df["day"]).dt.date
else:
    df = pd.DataFrame(columns=["id", "name", "day", "created_at"])

# --- Render signup table ---
cols = st.columns(len(weekdays))
for i, day in enumerate(weekdays):
    day_signups = df[df["day"] == day]
    user_signed_up = not day_signups[day_signups["name"] == name].empty
    spots_left = MAX_SPOTS_PER_DAY - len(day_signups)

    with cols[i]:
        st.markdown(f"### {day.strftime('%a %d %b')}")
        st.markdown(f"**🪑 {spots_left} spots left**")

        if user_signed_up:
            if st.button(f"❌ Unsubscribe", key=f"uns_{i}"):
                row_id = day_signups[day_signups["name"] == name]["id"].values[0]
                supabase.table("strategy_signups").delete().eq("id", row_id).execute()
                st.experimental_rerun()
        elif spots_left > 0:
            if st.button("✅ Sign up", key=f"sub_{i}"):
                supabase.table("strategy_signups").insert({
                    "name": name.strip(),
                    "day": str(day)
                }).execute()
                st.experimental_rerun()
        else:
            st.warning("Full")

# --- Weekly overview table ---
st.markdown("### 📋 Full Weekly Overview")
if df.empty:
    st.info("No signups yet.")
else:
    pivot = df.pivot_table(index="name", columns="day", aggfunc="size", fill_value=0)
    pivot = pivot.reindex(columns=weekdays, fill_value=0)
    pivot.columns = [d.strftime("%a") for d in weekdays]
    pivot = pivot.replace({1: "✅", 0: ""})
    st.dataframe(pivot)
