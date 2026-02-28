import os
from datetime import date, timedelta

from garminconnect import Garmin
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict, Any, Optional
import sys

# Ensure backend path is in sys.path for firestore_manager
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from logger import logger


def get_garmin_client(user_id: Optional[str] = None) -> Garmin:
    """
    Authenticate to Garmin using credentials.
    
    Args:
        user_id: Firebase UID. If provided, uses encrypted credentials from Firestore.
                 If None, falls back to GARMIN_EMAIL/GARMIN_PASSWORD from .env (legacy).
    
    Returns:
        Authenticated Garmin client
        
    Raises:
        ValueError: If credentials not found or authentication fails
    """
    email = None
    password = None
    
    if user_id:
        # NEW: Per-user credentials from Firestore
        try:
            # Import here to avoid circular dependency issues
            import firestore_manager
            
            creds = firestore_manager.get_garmin_credentials(user_id)
            if creds:
                email = creds['username']
                password = creds['password']
                logger.info(f"✅ Using Garmin credentials for user: {user_id}")
            else:
                raise ValueError(f"No Garmin credentials found for user: {user_id}. Please connect your Garmin account in Profile settings.")
        except Exception as e:
            logger.error(f"❌ Failed to load Garmin credentials for user {user_id}: {e}")
            raise ValueError(f"Could not load Garmin credentials: {str(e)}")
    else:
        # LEGACY: Environment variables (for backward compatibility)
        load_dotenv()
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")
        
        if not email or not password:
            raise ValueError("No user_id provided and GARMIN_EMAIL/GARMIN_PASSWORD not set in environment. Please provide user_id or configure legacy credentials.")
        
        logger.warning(f"⚠️  Using legacy GARMIN_EMAIL from environment: {email}")

    # Authenticate
    try:
        client = Garmin(email, password)
        client.login()
        logger.info(f"✅ Garmin login successful for: {email}")
        return client
    except Exception as e:
        logger.error(f"❌ Garmin authentication failed: {e}")
        raise ValueError(f"Garmin login failed. Please check your credentials. Error: {str(e)}")




def fetch_daily_summary(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch daily summary data between start and end dates (inclusive)."""
    days = (end - start).days + 1
    records = []

    for i in range(days):
        d = start + timedelta(days=i)
        iso = d.isoformat()
        data = client.get_stats(iso)
        if not data:
            continue
        data["date"] = iso
        records.append(data)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)

import concurrent.futures

def fetch_daily_heart_rate(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch intraday heart rate data between start and end dates (Parallelized)."""
    days = (end - start).days + 1
    records: List[Dict[str, Any]] = []
    
    date_list = [start + timedelta(days=i) for i in range(days)]

    def fetch_single_day_hr(d):
        iso = d.isoformat()
        try:
            hr_data = client.get_heart_rates(iso)
            if hr_data:
                return {"date": iso, "raw_hr_data": hr_data}
        except Exception as e:
            logger.error(f"Failed to get HR data for {iso}: {e}")
        return None

    # Use ThreadPoolExecutor for parallel processing
    # Cap workers to avoid overwhelming Garmin API (unofficial)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_single_day_hr, date_list))
    
    records = [r for r in results if r]

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def fetch_sleep_data(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch daily sleep data between start and end dates (Parallelized)."""
    days = (end - start).days + 1
    records: List[Dict[str, Any]] = []

    date_list = [start + timedelta(days=i) for i in range(days)]

    def fetch_single_day_sleep(d):
        iso = d.isoformat()
        try:
            sleep_data = client.get_sleep_data(iso)
            if sleep_data:
                return {"date": iso, "raw_sleep_data": sleep_data}
        except Exception as e:
            logger.error(f"Failed to get sleep data for {iso}: {e}")
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_single_day_sleep, date_list))
    
    records = [r for r in results if r]

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def fetch_activities(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch activities between start and end dates (Batch mode)."""
    records: List[Dict[str, Any]] = []
    
    start_iso = start.isoformat()
    end_iso = end.isoformat()
    
    try:
        # Optimized: Batch fetch using date range
        logger.info(f"Fetching activities from {start_iso} to {end_iso}...")
        activities = client.get_activities_by_date(start_iso, end_iso, "") # type assumption
        
        if activities:
            for activity in activities:
                # Add fetch_date for consistency, though process_garmin_data uses startTimeLocal
                # Use startTimeLocal as fetch_date proxy or just today's date? 
                # Original code used the loop date. Here we use the activity's actual date.
                if 'startTimeLocal' in activity:
                    activity["fetch_date"] = activity['startTimeLocal'].split(' ')[0]
                else:
                    activity["fetch_date"] = start_iso # Fallback
                records.append(activity)
                
    except Exception as e:
         logger.error(f"Failed to batch fetch activities: {e}")
         # Fallback? No, if batch fails, we likely have bigger issues.

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def get_latest_date(filename):
    """Returns the latest date found in the CSV, or None."""
    if not os.path.exists(filename):
        return None
    try:
        df = pd.read_csv(filename)
        if 'date' in df.columns:
            return pd.to_datetime(df['date']).max().date()
        if 'calendarDate' in df.columns:
            return pd.to_datetime(df['calendarDate']).max().date()
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return None

def update_csv(new_df, filename, key_col='date'):
    """Updates existing CSV with new data, handling duplicates."""
    if new_df is None or new_df.empty:
        return

    if os.path.exists(filename):
        try:
            old_df = pd.read_csv(filename)
            combined = pd.concat([old_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=[key_col], keep='last')
            combined.to_csv(filename, index=False)
            combined.to_csv(filename, index=False)
            logger.info(f"Updated {filename}: Added {len(new_df)} new rows (Total: {len(combined)})")
        except Exception as e:
            logger.error(f"Error updating {filename}: {e}. Overwriting...")
            new_df.to_csv(filename, index=False)
    else:
        new_df.to_csv(filename, index=False)
        logger.info(f"Created {filename} with {len(new_df)} rows")

def main(user_id: Optional[str] = None, mode: str = "incremental"):
    """
    Fetches Garmin data for a specific user or uses legacy mode.
    Mode 'incremental' overlaps 1 day, 'full' overlaps 5 days.
    """
    client = get_garmin_client(user_id)

    today = date.today()
    
    # Determine data directory path robustly
    script_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/scripts
    backend_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(backend_dir)
    
    def get_data_dir(uid: Optional[str] = None):
        # 1. Base data path relative to this script
        # Script is in .../backend/scripts/
        # Data is in .../backend/data/ (or /app/data in Docker)
        
        # Robust path resolution
        if os.path.exists("/app/data"):
            base_path = "/app/data"
        else:
            # Local: .../backend/data
            base_path = os.path.join(backend_dir, "data")
            
        # 2. Append user_id if provided
        if uid:
            user_path = os.path.join(base_path, uid)
            return user_path
        
        return base_path

    data_dir = get_data_dir(user_id)
    os.makedirs(data_dir, exist_ok=True)
    logger.info(f"📁 Using data directory: {data_dir}")
    
    last_sync = get_latest_date(f"{data_dir}/garmin_daily_summary.csv")
    
    if last_sync:
        overlap_days = 1 if mode == "incremental" else 5
        start = last_sync - timedelta(days=overlap_days)
        logger.info(f"Found existing data up to {last_sync}. Fetching from {start} ({overlap_days}-day overlap) [{mode}]...")
    else:
        fallback_days = 7 if mode == "incremental" else 360
        start = today - timedelta(days=fallback_days)
        logger.info(f"No existing data. Fetching from {start} (fallback: {fallback_days} days) [{mode}]...")

    if start > today:
        logger.info("Data is already up to date!")
        return

    # 1. Summary
    df_summary = fetch_daily_summary(client, start, today)
    update_csv(df_summary, f"{data_dir}/garmin_daily_summary.csv")

    # 2. HR
    df_hr = fetch_daily_heart_rate(client, start, today)
    update_csv(df_hr, f"{data_dir}/garmin_hr_timeseries.csv")

    # 3. Sleep
    df_sleep = fetch_sleep_data(client, start, today)
    update_csv(df_sleep, f"{data_dir}/garmin_sleep_data.csv")

    # 4. Activities
    df_activities = fetch_activities(client, start, today)
    # Use 'activityId' as key if available, else 'date' (fallback)
    key = 'activityId' if (df_activities is not None and 'activityId' in df_activities.columns) else 'date'
    update_csv(df_activities, f"{data_dir}/garmin_activities.csv", key_col=key)

    # 5. Sync to Firestore (NEW: To power Weekly Load widget)
    if not df_activities.empty:
        logger.info(f"Syncing {len(df_activities)} activities to Firestore for Weekly Load...")
        import firestore_manager
        
        # Only sync if user_id is provided
        if user_id:
            for _, row in df_activities.iterrows():
                try:
                    activity_id = row.get('activityId')
                    if not activity_id:
                        continue
                    
                    # Map Garmin activity to Firestore workout schema
                    # Use 'activityTrainingLoad' as load_estimate, fallback to 0
                    load_est = row.get('activityTrainingLoad', 0)
                    if pd.isna(load_est):
                        load_est = 0
                        
                    workout_doc = {
                        "date": str(pd.to_datetime(row['startTimeLocal']).date()),
                        "activity": row.get('activityName', 'Garmin Activity'),
                        "duration_min": int(row.get('duration', 0) / 60),
                        "load_estimate": int(round(float(load_est))),
                        "status": "DONE",
                        "source": "GARMIN",
                        "garmin_activity_id": str(activity_id)
                    }
                    
                    firestore_manager.save_garmin_workout(user_id, workout_doc, activity_id)
                except Exception as sync_err:
                    logger.warning(f"⚠️ Failed to sync activity {activity_id} to Firestore: {sync_err}")
        else:
            logger.warning("⚠️ Skipping Firestore sync: No user_id provided (Legacy Mode)")
    
    # 6. NOTE: Daily summary metrics are synced to Firestore by process_garmin_data.py
    # This ensures calculated metrics (CTL/ATL/TSB) are included.

    logger.info(f"✅ Garmin data fetch completed for {'user: ' + user_id if user_id else 'legacy mode'}")

if __name__ == "__main__":
    main()
