import pandas as pd
import os
import json

user_id = "UlO2eH5tfhP9OWcb1lxuLEX7z5L2"
base_dir = r"c:\Users\samih\code\health_ai\backend\data"

def inspect_data(uid):
    summary_path = os.path.join(base_dir, uid, "garmin_daily_summary.csv")
    if not os.path.exists(summary_path):
        print(f"Path not found: {summary_path}")
        return
    
    df = pd.read_csv(summary_path)
    # Convert date
    df['date_parsed'] = pd.to_datetime(df['calendarDate'])
    df = df.sort_values('date_parsed')
    
    cols = ['calendarDate', 'bodyBatteryChargedValue', 'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'averageStressLevel', 'totalSteps', 'activeKilocalories']
    print("--- Last 10 days of raw summary data ---")
    print(df[cols].tail(10))
    
    # Check for NaNs
    print("\n--- Missing values in last 10 days ---")
    print(df[cols].tail(10).isnull().sum())

inspect_data(user_id)
