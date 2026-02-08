import os
import sys
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Ensure backend path is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Load environment variables
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# Configure Firestore
if not firebase_admin._apps:
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.path.join(BACKEND_DIR, 'service_account_key.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

import firestore_garmin_metrics

def check_metrics_response(user_id):
    print(f"Checking metrics for {user_id}...")
    
    # 1. Fetch raw from Firestore
    metrics = firestore_garmin_metrics.get_user_daily_metrics(user_id, days=365)
    print(f"Fetched {len(metrics)} records.")
    
    if not metrics:
        print("No metrics found.")
        return

    # 2. Simulate main.py transformation
    result = []
    try:
        for row in metrics:
            item = {
                "date": row.get('date'),
                "ctl": round(row.get('CTL', 0), 1),
                "atl": round(row.get('ATL', 0), 1),
                "tsb": round(row.get('TSB', 0), 1),
                "load": int(row.get('workout_calories', 0)),
                "readiness": int(row.get('bodyBatteryHighestValue', 0)),
                "sleep_min": int(row.get('totalSleep_minutes', 0))
            }
            result.append(item)
            
            # Check for bad values
            for k, v in item.items():
                if v != v: # NaN check
                    print(f"⚠️ NaN detected in {k} for date {item['date']}")
                if v is None:
                    print(f"⚠️ None detected in {k} for date {item['date']}")

        # Print sample
        print("\nSample Transformed Data (Latest 3):")
        print(json.dumps(result[-3:], indent=2))
        
        print("\n✅ Transformation successful. Data looks valid JSON.")
        
    except Exception as e:
        print(f"❌ Transformation FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    UID = "wI0j4s1a9hZtGGaWtNnEn3yqSZC2"
    check_metrics_response(UID)
