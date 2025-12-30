import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import json
import os
import numpy as np

def main_process():
    print("Loading data...")
    try:
        df_summary = pd.read_csv("Health_AI/data/garmin_daily_summary.csv")
        df_sleep = pd.read_csv("Health_AI/data/garmin_sleep_data.csv")
        df_activities = pd.read_csv("Health_AI/data/garmin_activities.csv")
    except FileNotFoundError as e:
        print(f"Error: Missing data file. {e}")
        return

    # --- Preprocessing ---
    # Convert dates
    df_summary['date'] = pd.to_datetime(df_summary['date'])
    
    # Consolidate Sleep (handle differing column names from API)
    if 'calendarDate' in df_sleep.columns:
        df_sleep['date'] = pd.to_datetime(df_sleep['calendarDate'])
    elif 'date' in df_sleep.columns:
        df_sleep['date'] = pd.to_datetime(df_sleep['date'])
        
    # Consolidate Activities (Aggregate per day)
    # Check if 'startTimeLocal' exists
    if 'startTimeLocal' in df_activities.columns:
         df_activities['date'] = pd.to_datetime(df_activities['startTimeLocal']).dt.date
         df_activities['date'] = pd.to_datetime(df_activities['date'])
         
    # Group activities by date
    # Sum calories, duration
    activity_aggs = df_activities.groupby('date').agg({
        'calories': 'sum',
        'duration': 'sum', # seconds
        'averageHR': 'mean'
    }).rename(columns={'calories': 'workout_calories', 'duration': 'workout_duration_seconds', 'averageHR': 'workout_avg_hr'}).reset_index()

    # --- Merging ---
    df_merged = pd.merge(df_summary, df_sleep, on='date', how='left', suffixes=('', '_sleep'))
    df_merged = pd.merge(df_merged, activity_aggs, on='date', how='left')

    # Fill NaNs where appropriate
    df_merged['workout_calories'] = df_merged['workout_calories'].fillna(0)
    df_merged['workout_duration_seconds'] = df_merged['workout_duration_seconds'].fillna(0)
    
    # Feature Engineering: Sleep Minutes
    if 'totalSleepSeconds' in df_merged.columns:
        df_merged['totalSleep_minutes'] = df_merged['totalSleepSeconds'] / 60
    elif 'sleepingSeconds' in df_merged.columns:
        df_merged['totalSleep_minutes'] = df_merged['sleepingSeconds'] / 60
    else:
        df_merged['totalSleep_minutes'] = 0

    # Sort
    df_merged = df_merged.sort_values('date')

    # --- Rolling Averages & Lags ---
    # 7-day Load
    df_merged['workout_calories_roll_7d'] = df_merged['workout_calories'].rolling(7, min_periods=1).mean()
    
    # Lags (Previous Day)
    lag_cols = ['bodyBatteryChargedValue', 'averageStressLevel', 'totalSteps', 'totalSleep_minutes']
    for col in lag_cols:
        if col in df_merged.columns:
            df_merged[f'{col}_lag_1'] = df_merged[col].shift(1)

    # Clean
    df_merged = df_merged.dropna(subset=['bodyBatteryChargedValue', 'bodyBatteryChargedValue_lag_1'])
    
    # Save Features
    df_merged.to_csv("Health_AI/data/garmin_merged_features.csv", index=False)
    print("Saved merged features.")

    # --- Training with GridSearchCV & Cross-Validation ---
    print("Training XGBoost Model (with Hyperparameter Tuning & TimeSeries CV)...")
    
    target = 'bodyBatteryChargedValue'
    
    # Drop non-numeric for X
    drop_cols = ['date', 'bodyBatteryChargedValue', 'bodyBatteryDrainedValue', 'calendarDate', 'calendarDate_sleep']
    
    X = df_merged.drop(columns=[c for c in drop_cols if c in df_merged.columns])
    X = X.select_dtypes(include=['number'])
    y = df_merged[target]

    # TimeSeries Split for "Time-Aware" Validation
    # We don't shuffle because order matters in time series
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    # Parameter Grid (Focused for speed but effective)
    param_grid = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.01, 0.03, 0.05],
        'max_depth': [3, 4, 5],
        'subsample': [0.8],
        'colsample_bytree': [0.8]
    }
    
    xgb = XGBRegressor(random_state=42)
    
    # Use TimeSeriesSplit for CV (folds respect time order)
    tscv = TimeSeriesSplit(n_splits=3)
    
    grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, 
                               cv=tscv, n_jobs=-1, scoring='r2', verbose=1)
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    print(f"Best Parameters: {grid_search.best_params_}")
    print(f"Best CV Score (R2): {grid_search.best_score_:.2f}")

    preds = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    
    print(f"Final Test Model Performance - MAE: {mae:.2f}, R2: {r2:.2f}")

    # Save Model
    joblib.dump(best_model, "Health_AI/models/xgb_model.pkl")
    
    # --- Feature Importance ---
    importance = best_model.feature_importances_
    feature_names = X.columns.tolist()
    feat_imp_dict = dict(zip(feature_names, [float(x) for x in importance]))
    
    # Sort by importance
    feat_imp_dict = dict(sorted(feat_imp_dict.items(), key=lambda item: item[1], reverse=True))
    
    with open("feature_importance.json", "w") as f:
        json.dump(feat_imp_dict, f, indent=4)
        
    print("Feature importance saved.")
    print("Top 3 Features:", list(feat_imp_dict.keys())[:3])
    
    # Save Metrics
    metrics = {
        "mae": mae,
        "r2": r2,
        "last_trained": str(pd.Timestamp.now().date())
    }
    with open("model_metrics.json", "w") as f:
        json.dump(metrics, f)
    
    print("Model and metrics saved.")

if __name__ == "__main__":
    main_process()
