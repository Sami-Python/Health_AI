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

def main():
    client = get_garmin_client()

    # Last 90 days including today
    end = date.today()
    start = end - timedelta(days=89)

    # Päiväkohtainen summary-data
    df_summary = fetch_daily_summary(client, start, end)
    if df_summary is not None and not df_summary.empty:
        summary_path = "garmin_daily_summary.csv"
        df_summary.to_csv(summary_path, index=False)
        print(f"Saved {len(df_summary)} rows to {summary_path}")
    else:
        print("No summary data returned from Garmin.")

    # Päivittäinen HR-data
    df_hr = fetch_daily_heart_rate(client, start, end)
    if df_hr is not None and not df_hr.empty:
        hr_path = "garmin_hr_timeseries.csv"
        df_hr.to_csv(hr_path, index=False)
        print(f"Saved {len(df_hr)} rows to {hr_path}")
    else:
        print("No HR data returned from Garmin.")


if __name__ == "__main__":
    main()
