import pandas as pd
import numpy as np
import joblib
from process_garmin_data import load_data, process_sleep_data, process_activity_data, add_lag_features

def predict_latest():
    print("--- Garmin Recovery Predictor ---")
    
    # 1. Load Model
    try:
        model = joblib.load("xgb_bodybattery.pkl")
        print("Model loaded successfully.")
    except FileNotFoundError:
        print("Error: Model file 'xgb_bodybattery.pkl' not found. Run process_garmin_data.py first.")
        return None

    # 2. Load Top-up Data
    # In a real deployed scenario, we would stream this. 
    # Here we reload the CSVs which populate the history including 'today' (if fetched).
    df_summary, df_sleep_raw, df_activities_raw = load_data()
    
    if df_summary.empty:
        print("Error: No data available.")
        return None

    # 3. Process Data (Replicating the pipeline)
    df_sleep = process_sleep_data(df_sleep_raw)
    df_activities = process_activity_data(df_activities_raw)
    
    df_merged = df_summary.copy()
    if not df_sleep.empty:
        df_merged = pd.merge(df_merged, df_sleep, on='date', how='left')
    if not df_activities.empty:
        df_merged = pd.merge(df_merged, df_activities, on='date', how='left')
        
    act_cols = ['workout_minutes', 'workout_calories', 'workout_steps', 'workout_distance', 'activity_count']
    for c in act_cols:
        if c in df_merged.columns:
            df_merged[c] = df_merged[c].fillna(0)
            
    # 4. Feature Engineering (Lags/Rolling)
    # Critical: Use the whole history to calculate the rolling window for the last day
    df_processed = add_lag_features(df_merged)
    
    # 5. Select Latest Day
    # We want the very last row, assuming it represents "Today" (or the latest sync)
    latest_row = df_processed.iloc[-1:].copy()
    latest_date = latest_row['date'].values[0]
    print(f"Predicting for date: {latest_date}")
    
    # 6. Prepare Features for Model
    # We need to ensure columns match training features
    # Get model features from the importance attribute if available, or just align columns
    # XGBoost usually handles extra columns by ignoring them, but missing columns are an issue.
    # Ideally, we should save feature_names with the model.
    # For now, we drop the known non-features.
    
    features = latest_row.drop(columns=['date', 'bodyBatteryChargedValue', 'bodyBatteryDrainedValue'], errors='ignore')
    features = features.select_dtypes(include=[np.number])
    
    # 7. Predict
    prediction = model.predict(features)[0]
    
    print(f"\n> PREDICTED Body Battery Charge: {prediction:.1f}")
    
    # Context for User
    actual = latest_row.get('bodyBatteryChargedValue', np.nan)
    if not isinstance(actual, (int, float)) or np.isnan(actual).any():
        print("(Actual value not yet fully known or missing)")
    else:
        # If the row has the target (e.g. historical day), show it
        actual_val = actual.values[0]
        print(f"> ACTUAL Body Battery Charge:    {actual_val}")
        print(f"> Difference: {prediction - actual_val:.1f}")

    # Return context for AI Coach
    # NOTE: df_merged has columns replaced: e.g. totalSleepSeconds -> totalSleep_minutes
    sleep_col = 'totalSleep_minutes'
    if sleep_col in latest_row:
        sleep_hours = float(latest_row[sleep_col].values[0] / 60.0)
    elif 'totalSleepSeconds' in latest_row:
        sleep_hours = float(latest_row['totalSleepSeconds'].values[0] / 3600.0)
    elif 'sleepingSeconds' in latest_row:
        sleep_hours = float(latest_row['sleepingSeconds'].values[0] / 3600.0)
    else:
        sleep_hours = 0.0

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

if __name__ == "__main__":
    predict_latest()
