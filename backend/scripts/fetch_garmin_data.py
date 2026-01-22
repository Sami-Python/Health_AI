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
                print(f"✅ Using Garmin credentials for user: {user_id}")
            else:
                raise ValueError(f"No Garmin credentials found for user: {user_id}. Please connect your Garmin account in Profile settings.")
        except Exception as e:
            print(f"❌ Failed to load Garmin credentials for user {user_id}: {e}")
            raise ValueError(f"Could not load Garmin credentials: {str(e)}")
    else:
        # LEGACY: Environment variables (for backward compatibility)
        load_dotenv()
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")
        
        if not email or not password:
            raise ValueError("No user_id provided and GARMIN_EMAIL/GARMIN_PASSWORD not set in environment. Please provide user_id or configure legacy credentials.")
        
        print(f"⚠️  Using legacy GARMIN_EMAIL from environment: {email}")

    # Authenticate
    try:
        client = Garmin(email, password)
        client.login()
        print(f"✅ Garmin login successful for: {email}")
        return client
    except Exception as e:
        print(f"❌ Garmin authentication failed: {e}")
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

from typing import List, Dict, Any

def fetch_daily_heart_rate(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch intraday heart rate data between start and end dates."""
    days = (end - start).days + 1
    records: List[Dict[str, Any]] = []

    for i in range(days):
        d = start + timedelta(days=i)
        iso = d.isoformat()
        try:
                hr_data = client.get_heart_rates(iso)
        except Exception as e:
                print(f"Failed to get HR data for {iso}: {e}")
                continue

        if not hr_data:
                continue

        records.append({"date": iso, "raw_hr_data": hr_data})

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def fetch_sleep_data(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch daily sleep data between start and end dates."""
    days = (end - start).days + 1
    records: List[Dict[str, Any]] = []

    for i in range(days):
        d = start + timedelta(days=i)
        iso = d.isoformat()
        try:
            sleep_data = client.get_sleep_data(iso)
        except Exception as e:
            print(f"Failed to get sleep data for {iso}: {e}")
            continue

        if not sleep_data:
            continue

        records.append({"date": iso, "raw_sleep_data": sleep_data})

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def fetch_activities(client: Garmin, start: date, end: date) -> pd.DataFrame:
    """Fetch activities between start and end dates."""
    days = (end - start).days + 1
    records: List[Dict[str, Any]] = []

    for i in range(days):
        d = start + timedelta(days=i)
        iso = d.isoformat()
        try:
            # Get activities for the specific date
            activities = client.get_activities_by_date(iso, iso)
        except Exception as e:
            print(f"Failed to get activities for {iso}: {e}")
            continue

        if not activities:
            continue

        # Store each activity with its date
        for activity in activities:
            activity["fetch_date"] = iso
            records.append(activity)

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
            print(f"Updated {filename}: Added {len(new_df)} new rows (Total: {len(combined)})")
        except Exception as e:
            print(f"Error updating {filename}: {e}. Overwriting...")
            new_df.to_csv(filename, index=False)
    else:
        new_df.to_csv(filename, index=False)
        print(f"Created {filename} with {len(new_df)} rows")

def main(user_id: Optional[str] = None):
    """
    Fetches Garmin data for a specific user or uses legacy mode.
    """
    client = get_garmin_client(user_id)

    today = date.today()
    
    # Determine data directory path robustly
    script_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/scripts
    backend_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(backend_dir)
    
    def get_data_dir():
        # 1. Try local data dir
        local_path = os.path.join(project_root, "Health_AI/data")
        if os.path.exists(local_path):
            return local_path
        # 2. Try Docker path
        if os.path.exists("/Health_AI/data"):
            return "/Health_AI/data"
        # 3. Fallback
        return "Health_AI/data"

    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    print(f"📁 Using data directory: {data_dir}")
    
    last_sync = get_latest_date(f"{data_dir}/garmin_daily_summary.csv")
    
    if last_sync:
        start = last_sync - timedelta(days=5)
        print(f"Found existing data up to {last_sync}. Fetching from {start} (5-day overlap)...")
    else:
        start = today - timedelta(days=360)
        print(f"No existing data. Fetching full history from {start}...")

    if start > today:
        print("Data is already up to date!")
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
    # 5. Sync to Firestore (NEW: To power Weekly Load widget)
    if not df_activities.empty:
        print(f"Syncing {len(df_activities)} activities to Firestore for Weekly Load...")
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
                    print(f"⚠️ Failed to sync activity {activity_id} to Firestore: {sync_err}")
        else:
            print("⚠️ Skipping Firestore sync: No user_id provided (Legacy Mode)")

    print(f"✅ Garmin data fetch completed for {'user: ' + user_id if user_id else 'legacy mode'}")

if __name__ == "__main__":
    main()
