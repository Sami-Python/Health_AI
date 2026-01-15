import os
from datetime import date, timedelta

from garminconnect import Garmin
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict, Any

def get_garmin_client() -> Garmin:
    """Authenticate to Garmin using credentials from .env."""
    load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    print(f"Using GARMIN_EMAIL={email!r}")  # väliaikainen debug

    if not email or not password:
        raise ValueError("GARMIN_EMAIL or GARMIN_PASSWORD not set in environment/.env")

    client = Garmin(email, password)
    client.login()
    return client


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

def main():
    client = get_garmin_client()

    today = date.today()
    last_sync = get_latest_date("Health_AI/data/garmin_daily_summary.csv")
    
    if last_sync:
        # Start from 5 days ago to ensure we catch any late-syncing activities or missed data
        # Data often settles over a few days.
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
    update_csv(df_summary, "Health_AI/data/garmin_daily_summary.csv")

    # 2. HR
    df_hr = fetch_daily_heart_rate(client, start, today)
    update_csv(df_hr, "Health_AI/data/garmin_hr_timeseries.csv")

    # 3. Sleep
    df_sleep = fetch_sleep_data(client, start, today)
    update_csv(df_sleep, "Health_AI/data/garmin_sleep_data.csv")

    # 4. Activities
    df_activities = fetch_activities(client, start, today)
    # Use 'activityId' as key if available, else 'date' (fallback)
    key = 'activityId' if (df_activities is not None and 'activityId' in df_activities.columns) else 'date'
    update_csv(df_activities, "Health_AI/data/garmin_activities.csv", key_col=key)

if __name__ == "__main__":
    main()
