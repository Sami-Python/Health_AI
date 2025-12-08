import pandas as pd
import joblib
import pandas as pd
from datetime import timedelta

def predict_latest():
    # 1. Load Model
    try:
        model = joblib.load("xgb_model.pkl")
    except:
        return None

    # 2. Load latest features
    try:
        df = pd.read_csv("garmin_merged_features.csv")
    except:
        return None
    
    if df.empty:
        return None
        
    # Sort and take last row
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    latest_row = df.tail(1)
    latest_date = latest_row['date'].dt.date.values[0]
    
    # Prepare input X
    X = latest_row.drop(columns=['date', 'bodyBatteryChargedValue', 'bodyBatteryDrainedValue'], errors='ignore')
    X = X.select_dtypes(include=['number'])
    
    # Re-align columns to match model
    # (In a robust prod system we would save column names with model)
    model_booster = model.get_booster()
    model_columns = model_booster.feature_names
    
    # Add missing cols as 0
    for col in model_columns:
        if col not in X.columns:
            X[col] = 0
    
    # Order columns
    X = X[model_columns]
    
    # Predict
    prediction = model.predict(X)[0]
    
    # Extract Sleep duration nicely
    sleep_hours = 0
    if 'totalSleep_minutes' in latest_row:
        sleep_hours = latest_row['totalSleep_minutes'].values[0] / 60.0
    elif 'sleepingSeconds' in latest_row:
        sleep_hours = latest_row['sleepingSeconds'].values[0] / 3600.0

    context = {
        "date": str(latest_date),
        "predicted_charge": float(prediction),
        "sleep_score": float(latest_row['sleepScore'].values[0]) if 'sleepScore' in latest_row else "N/A",
        "sleep_hours": sleep_hours,
        "yesterday_stress": float(latest_row['averageStressLevel_lag_1'].values[0]) if 'averageStressLevel_lag_1' in latest_row else 0,
        "recent_load": float(latest_row['workout_calories_roll_7d'].values[0]) if 'workout_calories_roll_7d' in latest_row else 0,
        "yesterday_steps": float(latest_row['totalSteps_lag_1'].values[0]) if 'totalSteps_lag_1' in latest_row else 0,
        "yesterday_charge": float(latest_row['bodyBatteryChargedValue_lag_1'].values[0]) if 'bodyBatteryChargedValue_lag_1' in latest_row else 0,
    }
    return context
