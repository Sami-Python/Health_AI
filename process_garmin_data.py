import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score
import json
import ast
import joblib

# aja -> python process_garmin_data.py

def load_data():
    """Lataa kaikki Garmin-datat CSV-tiedostoista."""
    print("Loading data...")
    df_summary = pd.read_csv("garmin_daily_summary.csv")
    df_summary["date"] = pd.to_datetime(df_summary["date"]).dt.date
    
    try:
        df_sleep = pd.read_csv("garmin_sleep_data.csv")
        # Sleep data might need day adjustment if the sleep date refers to the night before or morning of
        # Usually Garmin sleep date is the day you woke up.
        if 'calendarDate' in df_sleep.columns:
             df_sleep['date'] = pd.to_datetime(df_sleep['calendarDate']).dt.date
        elif 'date' in df_sleep.columns:
             df_sleep['date'] = pd.to_datetime(df_sleep['date']).dt.date
    except FileNotFoundError:
        print("Warning: Sleep data not found.")
        df_sleep = pd.DataFrame()

    try:
        df_activities = pd.read_csv("garmin_activities.csv")
        # Activity start time
        if 'startTimeLocal' in df_activities.columns:
            df_activities['date'] = pd.to_datetime(df_activities['startTimeLocal']).dt.date
    except FileNotFoundError:
        print("Warning: Activity data not found.")
        df_activities = pd.DataFrame()
        
    try:
        df_hr = pd.read_csv("garmin_hr_timeseries.csv")
    except FileNotFoundError:
        df_hr = pd.DataFrame()
        
    return df_summary, df_sleep, df_activities

def process_sleep_data(df_sleep):
    """Prosessoi unidata päivittäisiksi tunnusluvuiksi."""
    if df_sleep.empty:
        return pd.DataFrame()
    
    print("Processing sleep data...")
    df_sleep_daily = df_sleep.copy()
    
    # Muunnetaan sekunnit minuuteiksi
    time_cols = ['totalSleepSeconds', 'deepSleepSeconds', 'lightSleepSeconds', 'remSleepSeconds', 'awakeSleepSeconds', 'unmeasurableSleepSeconds']
    
    for col in time_cols:
        if col in df_sleep_daily.columns:
            df_sleep_daily[col.replace('Seconds', '_minutes')] = df_sleep_daily[col] / 60.0
    
    features = ['date']
    features += [c.replace('Seconds', '_minutes') for c in time_cols if c in df_sleep_daily.columns]
    if 'sleepScoreFeedback' in df_sleep_daily.columns:
        features.append('sleepScoreFeedback')
        
    possible_score_cols = ['sleepScore', 'overallSleepScore', 'quality'] 
    for c in possible_score_cols:
        if c in df_sleep_daily.columns:
            features.append(c)
            
    df_sleep_agg = df_sleep_daily[features].groupby('date').first().reset_index()
    return df_sleep_agg

def process_activity_data(df_activities):
    """Prosessoi aktiviteettidata päivittäisiksi tunnusluvuiksi."""
    if df_activities.empty:
        return pd.DataFrame()

    print("Processing activity data...")
    aggs = {}
    if 'duration' in df_activities.columns:
        aggs['duration'] = 'sum'
    if 'calories' in df_activities.columns:
        aggs['calories'] = 'sum'
    if 'averageHeartRate' in df_activities.columns:
        aggs['averageHeartRate'] = 'mean'
    if 'maxHeartRate' in df_activities.columns:
        aggs['maxHeartRate'] = 'max'
    if 'steps' in df_activities.columns:
        aggs['steps'] = 'sum'
    if 'distance' in df_activities.columns:
        aggs['distance'] = 'sum'
        
    if not aggs:
        return pd.DataFrame()

    df_act_daily = df_activities.groupby('date').agg(aggs).reset_index()
    
    rename_map = {
        'duration': 'workout_duration_seconds',
        'calories': 'workout_calories',
        'averageHeartRate': 'workout_avg_hr',
        'maxHeartRate': 'workout_max_hr',
        'steps': 'workout_steps',
        'distance': 'workout_distance'
    }
    df_act_daily.rename(columns=rename_map, inplace=True)
    
    if 'workout_duration_seconds' in df_act_daily.columns:
         df_act_daily['workout_minutes'] = df_act_daily['workout_duration_seconds'] / 60.0
    
    df_count = df_activities.groupby('date').size().reset_index(name='activity_count')
    df_act_daily = pd.merge(df_act_daily, df_count, on='date', how='left')
    
    return df_act_daily

def run_feature_analysis(df, target='bodyBatteryChargedValue'):
    """Ajaa feature importance -analyysin XGBoostilla ja optimoi hyperparametrit."""
    print("Running feature analysis with optimization...")
    
    X = df.drop(columns=['date', target, 'bodyBatteryDrainedValue'], errors='ignore')
    X = X.select_dtypes(include=[np.number])
    y = df[target]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Define Parameter Grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1, 0.2],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }
    
    xgb = XGBRegressor(random_state=42)
    
    # Grid Search
    print("Tuning hyperparameters (this might take a moment)...")
    grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    
    print(f"Best Parameters: {grid_search.best_params_}")
    
    # Use best model
    model = grid_search.best_estimator_
    
    # Eval
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    
    print(f"Model Performance: MAE={mae:.2f}, R2={r2:.2f}")
    
    # Save Metrics
    metrics = {"mae": mae, "r2": r2, "last_trained": str(pd.Timestamp.now().date())}
    with open("model_metrics.json", "w") as f:
        json.dump(metrics, f)
    
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values(by='importance', ascending=False)
    
    print("\nTop 10 Features impacting Body Battery Charging:")
    print(importance.head(10))
    
    return model, importance

def add_lag_features(df):
    """Calculates lag and rolling average features."""
    if df.empty:
        return df
        
    print("Adding lag features...")
    df = df.sort_values(by='date')
    
    rolling_cols = ['totalSleepSeconds', 'activeSeconds', 'averageStressLevel', 'workout_calories', 'totalSteps', 'restingHeartRate']
    rolling_cols = [c for c in rolling_cols if c in df.columns]
    
    for col in rolling_cols:
        df[f'{col}_roll_3d'] = df[col].rolling(window=3, min_periods=1).mean()
        df[f'{col}_roll_7d'] = df[col].rolling(window=7, min_periods=1).mean()
        
    lag_cols = ['bodyBatteryChargedValue', 'totalSleepSeconds', 'totalSteps', 'averageStressLevel', 'bodyBatteryMostRecentValue']
    lag_cols = [c for c in lag_cols if c in df.columns]
    
    for col in lag_cols:
        df[f'{col}_lag_1'] = df[col].shift(1)
        
    return df

def main_process():
    df_summary, df_sleep_raw, df_activities_raw = load_data()
    
    if df_summary.empty:
        print("No summary data, cannot proceed.")
        return

    df_sleep = process_sleep_data(df_sleep_raw)
    df_activities = process_activity_data(df_activities_raw)
    
    print("Merging data...")
    df_merged = df_summary.copy()
    
    if not df_sleep.empty:
        df_merged = pd.merge(df_merged, df_sleep, on='date', how='left')
        
    if not df_activities.empty:
        df_merged = pd.merge(df_merged, df_activities, on='date', how='left')
        
    act_cols = ['workout_minutes', 'workout_calories', 'workout_steps', 'workout_distance', 'activity_count']
    for c in act_cols:
        if c in df_merged.columns:
            df_merged[c] = df_merged[c].fillna(0)
    
    df_merged = add_lag_features(df_merged)
            
    df_merged = df_merged.dropna(subset=['bodyBatteryChargedValue'])
    df_merged = df_merged.iloc[1:] 
    
    model, importance = run_feature_analysis(df_merged)
    
    df_merged.to_csv("garmin_merged_features.csv", index=False)
    print("Saved merged dataset to garmin_merged_features.csv")
    
    joblib.dump(model, "xgb_bodybattery.pkl")
    print("Saved trained model to xgb_bodybattery.pkl")

if __name__ == "__main__":
    main_process()
