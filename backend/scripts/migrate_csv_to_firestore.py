"""
One-time migration script: CSV → Firestore
Migrates existing garmin_merged_features.csv to per-user Firestore storage.

Usage:
    python migrate_csv_to_firestore.py --user-id YOUR_FIREBASE_UID
"""

import pandas as pd
import sys
import os
import argparse

# Add backend to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import firestore_garmin_metrics

def migrate_csv_to_firestore(user_id: str, csv_path: str):
    """
    Migrate existing CSV data to Firestore for a specific user.
    
    Args:
        user_id: Firebase UID
        csv_path: Path to garmin_merged_features.csv or garmin_daily_summary.csv
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    print(f"Reading CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} rows of data")
    
    # **CRITICAL:** Calculate CTL/ATL/TSB first (before converting to list)
    print("Calculating training load metrics (CTL/ATL/TSB)...")
    
    # Use workout_calories as load (or fallback to activeKilocalories)
    if 'workout_calories' in df.columns:
        df['load'] = df['workout_calories'].fillna(0)
    elif 'activeKilocalories' in df.columns:
        df['load'] = df['activeKilocalories'].fillna(0)
    else:
        df['load'] = 0
    
    # Calculate rolling averages
    df['ATL'] = df['load'].rolling(window=7, min_periods=1).mean()  # 7-day acute
    df['CTL'] = df['load'].rolling(window=42, min_periods=1).mean()  # 42-day chronic
    df['TSB'] = df['CTL'] - df['ATL']  # Training Stress Balance
    
    print(f"Training load calculated (Load range: {df['load'].min():.0f}-{df['load'].max():.0f})")
    
    # Prepare metrics list
    metrics_list = []
    
    for _, row in df.iterrows():
        # Extract date (handle both 'calendarDate' and 'date' columns)
        date_str = str(row.get('calendarDate', row.get('date', '')))
        if not date_str or date_str == 'nan':
            continue
        
        # Build metric document with proper NaN handling
        metric_doc = {
            'date': date_str[:10],  # Ensure YYYY-MM-DD format
            
            # Body Battery metrics
            'bodyBatteryChargedValue': int(row.get('bodyBatteryChargedValue', 0)) if pd.notna(row.get('bodyBatteryChargedValue')) else 0,
            'bodyBatteryHighestValue': int(row.get('bodyBatteryHighestValue', 0)) if pd.notna(row.get('bodyBatteryHighestValue')) else 0,
            'bodyBatteryLowestValue': int(row.get('bodyBatteryLowestValue', 0)) if pd.notna(row.get('bodyBatteryLowestValue')) else 0,
            
            # Activity metrics
            'totalSteps': int(row.get('totalSteps', 0)) if pd.notna(row.get('totalSteps')) else 0,
            'totalDistanceMeters': int(row.get('totalDistanceMeters', 0)) if pd.notna(row.get('totalDistanceMeters')) else 0,
            'activeKilocalories': int(row.get('activeKilocalories', 0)) if pd.notna(row.get('activeKilocalories')) else 0,
            
            # Stress metrics
            'averageStressLevel': int(row.get('averageStressLevel', 0)) if pd.notna(row.get('averageStressLevel')) else 0,
            
            # Heart rate metrics
            'restingHeartRate': int(row.get('restingHeartRate', 0)) if pd.notna(row.get('restingHeartRate')) else 0,
            'minHeartRate': int(row.get('minHeartRate', 0)) if pd.notna(row.get('minHeartRate')) else 0,
            'maxHeartRate': int(row.get('maxHeartRate', 0)) if pd.notna(row.get('maxHeartRate')) else 0,
            
            # Sleep metrics
            'totalSleep_minutes': int(row.get('totalSleep_minutes', 0)) if pd.notna(row.get('totalSleep_minutes')) else 0,
            
            # Training Load metrics (CALCULATED above)
            'CTL': float(row.get('CTL', 0)) if pd.notna(row.get('CTL')) else 0,
            'ATL': float(row.get('ATL', 0)) if pd.notna(row.get('ATL')) else 0,
            'TSB': float(row.get('TSB', 0)) if pd.notna(row.get('TSB')) else 0,
            'workout_calories': int(row.get('load', 0)) if pd.notna(row.get('load')) else 0,  # Use calculated load
            'workout_duration_seconds': int(row.get('workout_duration_seconds', 0)) if pd.notna(row.get('workout_duration_seconds')) else 0,
        }
        
        metrics_list.append(metric_doc)
    
    print(f"Prepared {len(metrics_list)} metrics for upload to Firestore...")
    
    # Batch save to Firestore
    success = firestore_garmin_metrics.batch_save_metrics(user_id, metrics_list)
    
    if success:
        print(f"Successfully migrated {len(metrics_list)} records to Firestore for user {user_id}")
        return True
    else:
        print(f"Migration failed for user {user_id}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Migrate CSV Garmin data to Firestore')
    parser.add_argument('--user-id', required=True, help='Firebase UID')
    parser.add_argument('--csv', default='../../Health_AI/data/garmin_merged_features.csv', 
                        help='Path to CSV file (default: ../../Health_AI/data/garmin_merged_features.csv)')
    
    args = parser.parse_args()
    
    # Normalize CSV path
    csv_path = os.path.abspath(os.path.join(SCRIPT_DIR, args.csv))
    
    print("=" * 60)
    print("  CSV -> Firestore Migration Tool")
    print("=" * 60)
    print(f"User ID: {args.user_id}")
    print(f"CSV Path: {csv_path}")
    print("=" * 60)
    
    # Confirm
    confirm = input("[!] This will upload data to Firestore. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Migration cancelled")
        return
    
    # Run migration
    success = migrate_csv_to_firestore(args.user_id, csv_path)
    
    if success:
        print("\nMigration complete! Your dashboard should now show historical data.")
    else:
        print("\nMigration failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
