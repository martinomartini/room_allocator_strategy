import streamlit as st
from datetime import datetime, timedelta, date
from supabase import create_client, Client
import pytz
import pandas as pd

# --- Config ---
ADMIN_PASSWORD = "Verhuizing2025!"
MAX_SPOTS = 17

# --- Time Setup ---
tz = pytz.timezone("Europe/Amsterdam")
now = datetime.now(tz)
today = now.date()

# --- Supabase Setup ---
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Get this week's weekdays (Mon–Fri) ---
def get_weekdays():
    start = today - timedelta(days=today.weekday())
    return [start + timedelta(days=i) for i in range(5)]

weekdays = get_weekdays()

# --- User auth ---
st.title("🗓️ Strategy Weekly Office Sign-Up")
name = st.text_input("🤝 Your name:")
if not name.strip():
    st.stop()
name = name.strip()

# --- Admin panel ---
st.sidebar.title("🔐 Admin Panel")
admin_mode = False
if st.sidebar.text_input("Password", type="password") == ADMIN_PASSWORD:
    admin_mode = True
    st.sidebar.success("Admin access granted")
    if st.sidebar.button("🧼 Reset all signups"):
        supabase.table("strategy_signups").delete().execute()
        st.rerun()

# --- Load all signups ---
data = (
    supabase.table("strategy_signups")
    .select("*")
    .gte("day", str(weekdays[0]))
    .lte("day", str(weekdays[-1]))
    .execute()
    .data
)
df = pd.DataFrame(data) if data else pd.DataFrame(columns=["id", "name", "day", "created_at"])
df["day"] = pd.to_datetime(df["day"]).dt.date

# --- Weekly checkbox grid ---
st.markdown("## 🗓️ Select your office days this week")

# Track what user has checked
user_days = set(df[df["name"] == name]["day"])

cols = st.columns(len(weekdays))
new_selection = []

for i, d in enumerate(weekdays):
    with cols[i]:
        day_str = d.strftime("%a %d %b")
        current_signups = df[df["day"] == d]
        spots_left = MAX_SPOTS - len(current_signups)
        st.markdown(f"**{day_str}**")
        st.caption(f"🪑 {spots_left} spots left")
        checked = d in user_days
        if st.checkbox("Going", key=f"chk_{i}", value=checked):
            new_selection.append(d)

# --- Apply changes ---
to_add = set(new_selection) - user_days
to_remove = user_days - set(new_selection)

if to_add or to_remove:
    if st.button("📄 Save changes"):
        for d in to_add:
            if len(df[df["day"] == d]) < MAX_SPOTS:
                supabase.table("strategy_signups").insert({"name": name, "day": str(d)}).execute()
        for d in to_remove:
            row = df[(df["name"] == name) & (df["day"] == d)]
            if not row.empty:
                supabase.table("strategy_signups").delete().eq("id", row.iloc[0]["id"]).execute()
        st.success("✅ Preferences saved!")
        st.rerun()

# --- Overview Table ---
st.markdown("## 📋 Full Weekly Overview")
if df.empty:
    st.info("No one has signed up yet.")
else:
    pivot = df.pivot_table(index="name", columns="day", aggfunc="size", fill_value=0)
    pivot = pivot.reindex(columns=weekdays, fill_value=0)
    pivot.columns = [d.strftime("%a") for d in weekdays]
    pivot = pivot.replace({1: "✅", 0: ""})
    st.dataframe(pivot, use_container_width=True)