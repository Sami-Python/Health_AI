import pandas as pd
import numpy as np
import joblib
import os
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error

user_id = "UlO2eH5tfhP9OWcb1lxuLEX7z5L2"
data_path = f"backend/data/{user_id}/garmin_daily_summary.csv" # Simplified path for testing

def test_model():
    if not os.path.exists(data_path):
        print("Data not found")
        return

    df = pd.read_csv(data_path)
    # Basic preprocessing (mimicking process_garmin_data.py)
    df['date'] = pd.to_datetime(df['calendarDate'])
    df = df.sort_values('date')
    
    # Target: Tomorrow's recovery
    df['target_recovery'] = df['bodyBatteryChargedValue'].shift(-1)
    
    # Features
    drop_cols = ['date', 'calendarDate', 'target_recovery', 'bodyBatteryDrainedValue', 'userDailySummaryId', 'uuid', 'wellnessStartTimeGmt', 'wellnessStartTimeLocal', 'wellnessEndTimeGmt', 'wellnessEndTimeLocal', 'lastSyncTimestampGMT', 'latestRespirationTimeGMT', 'latestSpo2ReadingTimeGmt', 'latestSpo2ReadingTimeLocal', 'bodyBatteryDynamicFeedbackEvent', 'endOfDayBodyBatteryDynamicFeedbackEvent', 'bodyBatteryActivityEventList']
    
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    X = X.select_dtypes(include=['number'])
    y = df['target_recovery']
    
    # Drop rows where target is NaN (last row)
    mask = y.notna() & X.notna().all(axis=1)
    X = X[mask]
    y = y[mask]
    
    # Feature Selection: Top 10 from previously observed importance
    top_features = ["bodyBatteryChargedValue", "averageStressLevel", "totalSteps", "workout_calories", "CTL", "ATL", "TSB", "restingHeartRate", "totalSleep_minutes", "bodyBatteryHighestValue"]
    X_subset = X[[f for f in top_features if f in X.columns]]
    
    # Split
    split_idx = int(len(X_subset) * 0.8)
    X_train, X_test = X_subset.iloc[:split_idx], X_subset.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)}")
    
    # Simple model
    model = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    
    print(f"Simple Model (Top 10 features) - R2: {r2:.2f}, MAE: {mae:.2f}")

if __name__ == "__main__":
    test_model()
