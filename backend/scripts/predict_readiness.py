import os
import sys
import pandas as pd
import joblib
import logging

# Setup basic logging
logger = logging.getLogger("predict_readiness")
if not logger.handlers:
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(sh)
    logger.setLevel(logging.INFO)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
import firestore_manager as db_manager
import firestore_garmin_metrics

def get_model_path(user_id: str = None) -> str:
    """Resolve the path to the trained XGBoost model."""
    if os.path.exists("/app/models"):
        base_dir = "/app"
    else:
        base_dir = BACKEND_DIR

    rel_path = "models/xgb_model.pkl"
    full_path = os.path.join(base_dir, rel_path)

    if user_id:
        directory, filename = os.path.split(full_path)
        if os.path.basename(directory) != user_id:
             final_dir = os.path.join(directory, user_id)
        else:
             final_dir = directory
             
        user_model_path = os.path.join(final_dir, filename)
        if os.path.exists(user_model_path):
            return user_model_path
        else:
            logger.info(f"User {user_id} model not found. Falling back to global model.")
            return full_path

    return full_path

def load_feature_names(user_id: str = None) -> list:
    """Load the feature names from the JSON saved during training."""
    if os.path.exists("/app/outputs"):
        base_dir = "/app"
    else:
        base_dir = BACKEND_DIR

    rel_path = "outputs/feature_importance.json"
    full_path = os.path.join(base_dir, rel_path)
    
    if user_id:
        # Also check user-specific feature importance if possible
        directory, filename = os.path.split(full_path)
        user_fi_path = os.path.join(directory, user_id, filename)
        if os.path.exists(user_fi_path):
             full_path = user_fi_path
             
    import json
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r') as f:
                data = json.load(f)
                return list(data.keys())
        except Exception as e:
            logger.warning(f"Failed to load feature names from {full_path}: {e}")
            
    # Default fallback
    return [
        'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'averageStressLevel',
        'totalSteps', 'poor_night_flag', 'totalSleep_minutes', 
        'workout_calories', 'workout_duration_seconds', 'workout_avg_hr', 
        'ATL', 'CTL', 'TSB', 'workout_calories_roll_7d',
        'bodyBatteryChargedValue_lag_1', 'averageStressLevel_lag_1', 
        'totalSteps_lag_1', 'totalSleep_minutes_lag_1'
    ]

def predict_tomorrow_readiness(user_id: str) -> float:
    """
    Predicts tomorrow's Body Battery Charged Value (0-100).
    """
    model_path = get_model_path(user_id)
    if not os.path.exists(model_path):
        logger.warning(f"No XGBoost model found for user {user_id}. Path: {model_path}")
        return None
        
    try:
        model = joblib.load(model_path)
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        return None

    # Fetch latest data (Look back up to 90 days to find recent records)
    recent_metrics = firestore_garmin_metrics.get_user_daily_metrics(user_id, days=90)
    
    if not recent_metrics or len(recent_metrics) < 1:
        logger.warning(f"Not enough data to predict readiness for user {user_id}")
        return None
        
    # We only need the last two
    latest_metrics = recent_metrics[-2:] if len(recent_metrics) >= 2 else recent_metrics
        
    today = latest_metrics[-1]
    yesterday = latest_metrics[-2] if len(latest_metrics) >= 2 else today
    
    features = {
        'bodyBatteryHighestValue': today.get('bodyBatteryHighestValue', 100),
        'bodyBatteryLowestValue': today.get('bodyBatteryLowestValue', 5),
        'averageStressLevel': today.get('averageStressLevel', 25),
        'totalSteps': today.get('totalSteps', 5000),
        'poor_night_flag': 1 if today.get('totalSleep_minutes', 480) < 360 else 0,
        'totalSleep_minutes': today.get('totalSleep_minutes', 480),
        'workout_calories': today.get('workout_calories', 0),
        'workout_duration_seconds': today.get('workout_duration_seconds', 0),
        'workout_avg_hr': today.get('averageHR', 0) if 'averageHR' in today else 0,
        'ATL': today.get('ATL', 0),
        'CTL': today.get('CTL', 0),
        'TSB': today.get('TSB', 0),
        'workout_calories_roll_7d': today.get('workout_calories', 0),
        
        'bodyBatteryChargedValue_lag_1': yesterday.get('bodyBatteryChargedValue', 50),
        'averageStressLevel_lag_1': yesterday.get('averageStressLevel', 25),
        'totalSteps_lag_1': yesterday.get('totalSteps', 5000),
        'totalSleep_minutes_lag_1': yesterday.get('totalSleep_minutes', 480)
    }

    feature_names = load_feature_names(user_id)
    
    try:
        df_features = pd.DataFrame([features])
        
        model_booster = model.get_booster()
        model_columns = model_booster.feature_names
        
        for col in model_columns:
            if col not in df_features.columns:
                df_features[col] = 0.0
                
        df_features = df_features[model_columns]
        prediction = model.predict(df_features)[0]
        predicted_readiness = max(5.0, min(100.0, float(prediction)))
        
        logger.info(f"Predicted tomorrow's readiness for {user_id}: {predicted_readiness:.1f}")
        return predicted_readiness
        
    except Exception as e:
        logger.error(f"Error during prediction logic: {e}")
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-id', required=True, help='Firebase UID')
    args = parser.parse_args()
    
    pred = predict_tomorrow_readiness(args.user_id)
    if pred is not None:
         print(f"Prediction for tomorrow: {pred:.1f}/100")
    else:
         print("Failed to generate prediction.")
