import sys
import os
import asyncio
from datetime import date, timedelta
from dotenv import load_dotenv

# load backend paths
script_dir = os.path.join(os.getcwd(), 'backend', 'scripts')
sys.path.append(script_dir)
import fetch_garmin_data as fgd
print("Loaded fetch_garmin_data correctly.", fgd.__file__)

# simulate logic
today = date.today()
last_sync = today
mode = "incremental"
overlap_days = 1 if mode == "incremental" else 5
start = last_sync - timedelta(days=overlap_days)
print(f"Start: {start}, Today: {today}")

