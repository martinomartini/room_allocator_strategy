# reset.py
from datetime import date
from supabase import create_client
import os

# Load credentials from environment variables (set in GitHub Actions)
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supabase = create_client(url, key)

today = str(date.today())

# Delete all signups for today — FIXED to use the correct column "day"
supabase.table("strategy_signups").delete().eq("day", today).execute()
print(f"✅ Reset complete for {today}")
