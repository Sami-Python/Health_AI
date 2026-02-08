
import os
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR) # .../health_ai/backend
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import firestore_manager
import firestore_garmin_metrics

def migrate_metrics(user_id):
    print(f"Migrating metrics for user: {user_id}")
    
    # Paths to local files
    metrics_path = os.path.join(BACKEND_DIR, "data", user_id, "model_metrics.json")
    fi_path = os.path.join(BACKEND_DIR, "outputs", user_id, "feature_importance.json")
    
    metrics = {}
    fi_data = {}
    
    # Load Metrics
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
            print(f"[SUCCESS] Loaded metrics from {metrics_path}")
        except Exception as e:
             print(f"[ERROR] Error loading metrics: {e}")
             return
    else:
        print(f"[WARNING] Metrics file not found at {metrics_path}")
        
    # Load Feature Importance
    if os.path.exists(fi_path):
        try:
            with open(fi_path, "r") as f:
                fi_data = json.load(f)
                # Ensure top 10 sorted
                fi_data = dict(sorted(fi_data.items(), key=lambda item: item[1], reverse=True)[:10])
            print(f"[SUCCESS] Loaded feature importance from {fi_path}")
        except Exception as e:
             print(f"[ERROR] Error loading feature importance: {e}")
             return
    else:
        print(f"[WARNING] Feature importance file not found at {fi_path}")
        
    # Save to Firestore
    if metrics or fi_data:
        if firestore_garmin_metrics.save_model_performance(user_id, metrics, fi_data):
            print(f"[SUCCESS] Successfully migrated metrics to Firestore for {user_id}")
        else:
            print("[ERROR] Failed to save to Firestore")
    else:
        print("Nothing to migrate.")

if __name__ == "__main__":
    # Default user ID from previous context
    default_uid = "wI0j4s1a9hZtGGaWtNnEn3yqSZC2"
    
    target_uid = default_uid
    if len(sys.argv) > 1:
        target_uid = sys.argv[1]
        
    migrate_metrics(target_uid)
