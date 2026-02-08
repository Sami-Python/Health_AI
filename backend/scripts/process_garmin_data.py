import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import mlflow
import mlflow.sklearn

# Ensure backend path is in sys.path for firestore_manager
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from logger import logger


import firestore_garmin_metrics

def main_process(user_id: str = None):
    # --- Path Configuration ---
    # We need to find the data files regardless of whether we run from backend/ or root/
    # or inside Docker.
    script_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/scripts
    backend_dir = os.path.dirname(script_dir)              # .../backend
    project_root = os.path.dirname(backend_dir)            # .../
    
    # In Docker, project_root might be /app? No, usually it's /app and Health_AI is at /Health_AI
    # Let's check environment or explicit paths.
    
    # Determine path to backend root
    # script: .../backend/scripts/process_garmin_data.py
    # backend: .../backend/
    script_path = os.path.abspath(__file__)
    backend_dir = os.path.dirname(os.path.dirname(script_path))

    def get_path(rel_path):
        """
        Resolves path relative to backend root, handling docker/local differences.
        rel_path should be like "data/garmin.csv" or "models/xgb.pkl"
        """
        # Determine base directory for data/models/outputs
        # In Docker, we might map volumes to /app/data, /app/models
        # Locally, they are in backend/data, backend/models
        
        # Check if we are running in Docker where /app is the workdir
        # Actually, let's just stick to reliable relative paths from backend_dir
        # If /app is the backend dir in Docker, this works
        
        base_dir = backend_dir
        
        # Docker special case: sometimes data is mounted elsewhere?
        # Assuming standard structure:
        # /app/data
        # /app/models
        # /app/outputs
        
        if os.path.exists("/app/data"):
           base_dir = "/app"
           
        # Initial path construction
        full_path = os.path.join(base_dir, rel_path)
        
        # Handle user isolation
        # If user_id is present, inject it into the path
        # e.g., data/UID/file.csv instead of data/file.csv
        
        if user_id:
            directory, filename = os.path.split(full_path)
            # Check if directory already ends with user_id to avoid double nesting
            if os.path.basename(directory) != user_id:
                final_dir = os.path.join(directory, user_id)
            else:
                final_dir = directory
            
            # Ensure directory exists
            os.makedirs(final_dir, exist_ok=True)
            return os.path.join(final_dir, filename)
            
        return full_path

    logger.info("Loading data...")
    try:
        df_summary = pd.read_csv(get_path("data/garmin_daily_summary.csv"))
        df_sleep = pd.read_csv(get_path("data/garmin_sleep_data.csv"))
        df_activities = pd.read_csv(get_path("data/garmin_activities.csv"))
    except FileNotFoundError as e:
        logger.error(f"Error: Missing data file. {e}")
        return

    # --- Preprocessing ---
    # ... (rest of the logic remains same until training) ...

    # Consolidation logic (kept for context)
    df_summary['date'] = pd.to_datetime(df_summary['date'])
    if 'bodyBatteryDuringSleep' in df_summary.columns:
        df_summary['poor_night_flag'] = (df_summary['bodyBatteryDuringSleep'] < 45).astype(int)
    else:
        df_summary['poor_night_flag'] = 0
    
    if 'calendarDate' in df_sleep.columns:
        df_sleep['date'] = pd.to_datetime(df_sleep['calendarDate'])
    elif 'date' in df_sleep.columns:
        df_sleep['date'] = pd.to_datetime(df_sleep['date'])
        
    if 'startTimeLocal' in df_activities.columns:
         df_activities['date'] = pd.to_datetime(df_activities['startTimeLocal']).dt.date
         df_activities['date'] = pd.to_datetime(df_activities['date'])
         
    activity_aggs = df_activities.groupby('date').agg({
        'calories': 'sum',
        'duration': 'sum',
        'averageHR': 'mean'
    }).rename(columns={'calories': 'workout_calories', 'duration': 'workout_duration_seconds', 'averageHR': 'workout_avg_hr'}).reset_index()

    df_merged = pd.merge(df_summary, df_sleep, on='date', how='left', suffixes=('', '_sleep'))
    df_merged = pd.merge(df_merged, activity_aggs, on='date', how='left')
    df_merged['workout_calories'] = df_merged['workout_calories'].fillna(0)
    df_merged['workout_duration_seconds'] = df_merged['workout_duration_seconds'].fillna(0)
    
    if 'totalSleepSeconds' in df_merged.columns:
        df_merged['totalSleep_minutes'] = df_merged['totalSleepSeconds'] / 60
    elif 'sleepingSeconds' in df_merged.columns:
        df_merged['totalSleep_minutes'] = df_merged['sleepingSeconds'] / 60
    else:
        df_merged['totalSleep_minutes'] = 0

    df_merged = df_merged.sort_values('date')
    
    # --- Performance Management Chart (PMC) Calculation ---
    # Using 'workout_calories' as a proxy for TSS (Training Stress Score)
    # Ideally, TSS = (Duration * Intensity / FTP) ... but Calories is a decent proxy for volume+intensity.
    
    # fillna(0) ensures we have valid numbers
    df_merged['workout_calories'] = df_merged['workout_calories'].fillna(0)
    
    # ATL (Acute Training Load) = Fatigue = 7-day exponentially weighted moving average
    df_merged['ATL'] = df_merged['workout_calories'].ewm(span=7, adjust=False).mean()
    
    # CTL (Chronic Training Load) = Fitness = 42-day exponentially weighted moving average
    df_merged['CTL'] = df_merged['workout_calories'].ewm(span=42, adjust=False).mean()
    
    # TSB (Training Stress Balance) = Form = CTL - ATL (Actually usually TSB = CTL_yesterday - ATL_yesterday)
    # But for today's snapshot: TSB = CTL - ATL
    # Positive TSB = Freshness, Negative TSB = Fatigue accumulated
    df_merged['TSB'] = df_merged['CTL'] - df_merged['ATL']
    
    # Roll 7d for simple stats
    df_merged['workout_calories_roll_7d'] = df_merged['workout_calories'].rolling(7, min_periods=1).mean()
    
    lag_cols = ['bodyBatteryChargedValue', 'averageStressLevel', 'totalSteps', 'totalSleep_minutes']
    for col in lag_cols:
        if col in df_merged.columns:
            df_merged[f'{col}_lag_1'] = df_merged[col].shift(1)

    df_merged = df_merged.dropna(subset=['bodyBatteryChargedValue', 'bodyBatteryChargedValue_lag_1'])
    
    features_csv = get_path("data/garmin_merged_features.csv")
    df_merged.to_csv(features_csv, index=False)
    logger.info(f"Saved merged features to {features_csv}")
    
    # --- Sync to Firestore (Multi-User) ---
    if user_id:
        logger.info(f"Syncing processed metrics to Firestore for user {user_id}...")
        try:
            # Prepare metrics list from df_merged
            # We sync ALL columns that map to our schema
            metrics_list = []
            
            # Sync last 120 days to be safe (covering history + retraining range)
            # or sync everything? 400 records is 1 batch. efficient enough.
            # Let's sync everything for now to ensure consistency.
            
            for _, row in df_merged.iterrows():
                # Convert date to string YYYY-MM-DD
                date_str = str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date'])[:10]
                
                metric_doc = {
                    'date': date_str,
                    # Core
                    'bodyBatteryChargedValue': int(row.get('bodyBatteryChargedValue', 0)) if pd.notna(row.get('bodyBatteryChargedValue')) else 0,
                    'bodyBatteryHighestValue': int(row.get('bodyBatteryHighestValue', 0)) if pd.notna(row.get('bodyBatteryHighestValue')) else 0,
                    'bodyBatteryLowestValue': int(row.get('bodyBatteryLowestValue', 0)) if pd.notna(row.get('bodyBatteryLowestValue')) else 0,
                    'averageStressLevel': int(row.get('averageStressLevel', 0)) if pd.notna(row.get('averageStressLevel')) else 0,
                    'totalSteps': int(row.get('totalSteps', 0)) if pd.notna(row.get('totalSteps')) else 0,
                    'totalSleep_minutes': int(row.get('totalSleep_minutes', 0)) if pd.notna(row.get('totalSleep_minutes')) else 0,
                    
                    # Training Load (Calculated)
                    'workout_calories': int(row.get('workout_calories', 0)) if pd.notna(row.get('workout_calories')) else 0,
                    'workout_duration_seconds': int(row.get('workout_duration_seconds', 0)) if pd.notna(row.get('workout_duration_seconds')) else 0,
                    'CTL': float(row.get('CTL', 0)) if pd.notna(row.get('CTL')) else 0.0,
                    'ATL': float(row.get('ATL', 0)) if pd.notna(row.get('ATL')) else 0.0,
                    'TSB': float(row.get('TSB', 0)) if pd.notna(row.get('TSB')) else 0.0,
                }
                
                # Add optional fields if they exist
                if 'averageHR' in row and pd.notna(row['averageHR']): metric_doc['averageHR'] = float(row['averageHR'])
                if 'restingHeartRate' in row and pd.notna(row['restingHeartRate']): metric_doc['restingHeartRate'] = int(row['restingHeartRate'])
                
                metrics_list.append(metric_doc)
            
            # Batch save
            if firestore_garmin_metrics.batch_save_metrics(user_id, metrics_list):
                 logger.info(f"Successfully synced {len(metrics_list)} daily metrics to Firestore")
            else:
                 logger.error("Firestore sync returned false")
                 
        except Exception as e:
            logger.error(f"Failed to sync to Firestore: {e}")
            import traceback
            traceback.print_exc()

    # Set tracking URI to local SQLite database in backend/data
    # For MLflow logic, we keep a shared DB for experiment tracking, 
    # OR we could isolate. Shared DB is usually fine for experiments if we tag run with user_id.
    mlflow_db_path = os.path.join(backend_dir, "data", "mlflow.db")
    os.makedirs(os.path.dirname(mlflow_db_path), exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{mlflow_db_path}")
    mlflow.set_experiment("xgboost_readiness_prediction")
    
    # --- Training with GridSearchCV & Cross-Validation ---
    logger.info("Training XGBoost Model (with Hyperparameter Tuning & TimeSeries CV)...")
    
    target = 'bodyBatteryChargedValue'
    drop_cols = ['date', 'bodyBatteryChargedValue', 'bodyBatteryDrainedValue', 'calendarDate', 'calendarDate_sleep']
    X = df_merged.drop(columns=[c for c in drop_cols if c in df_merged.columns])
    X = X.select_dtypes(include=['number'])
    y = df_merged[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    param_grid = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.01, 0.03, 0.05],
        'max_depth': [3, 4, 5],
        'subsample': [0.8],
        'colsample_bytree': [0.8]
    }
    
    xgb = XGBRegressor(random_state=42)
    tscv = TimeSeriesSplit(n_splits=3)
    
    # ⚠️ Use n_jobs=1 for reliability on shared environments / Windows subprocess issues
    grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, 
                               cv=tscv, n_jobs=1, scoring='r2', verbose=1)
    
    # Start MLflow run
    with mlflow.start_run():
        # Log hyperparameters from grid search
        mlflow.log_params({
            "n_estimators_grid": str(param_grid['n_estimators']),
            "learning_rate_grid": str(param_grid['learning_rate']),
            "max_depth_grid": str(param_grid['max_depth']),
            "subsample": param_grid['subsample'][0],
            "colsample_bytree": param_grid['colsample_bytree'][0],
            "cv_splits": 3,
            "test_size": 0.2,
            "user_id": user_id if user_id else "global"
        })
        
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        logger.info(f"Best Parameters: {grid_search.best_params_}")
        logger.info(f"Best CV Score (R2): {grid_search.best_score_:.2f}")
        
        # Log best parameters
        mlflow.log_params(grid_search.best_params_)
        mlflow.log_metric("best_cv_r2", grid_search.best_score_)

        preds = best_model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        
        print(f"Final Test Model Performance - MAE: {mae:.2f}, R2: {r2:.2f}, RMSE: {rmse:.2f}")
        logger.info(f"Final Test Model Performance", extra={"mae": mae, "r2": r2, "rmse": rmse})
        
        # Log metrics
        mlflow.log_metrics({
            "mae": mae,
            "r2_score": r2,
            "rmse": rmse,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "total_features": X.shape[1]
        })

        # Save Model (traditional way)
        model_path = get_path("models/xgb_model.pkl")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(best_model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Log model to MLflow
        mlflow.sklearn.log_model(best_model, "xgboost_model")
        logger.info("Model logged to MLflow")
    
        # --- Feature Importance ---
        importance = best_model.feature_importances_
        feature_names = X.columns.tolist()
        feat_imp_dict = dict(zip(feature_names, [float(x) for x in importance]))
        feat_imp_dict = dict(sorted(feat_imp_dict.items(), key=lambda item: item[1], reverse=True))
        
        fi_json_path = get_path("outputs/feature_importance.json")
        with open(fi_json_path, "w") as f:
            json.dump(feat_imp_dict, f, indent=4)
            
        logger.info(f"Feature importance saved to {fi_json_path}")
        
        # Log feature importance as MLflow artifact
        mlflow.log_artifact(fi_json_path, "feature_importance")
    
        # Save Metrics to backend/data where API expects it
        metrics = {
            "mae": float(mae),
            "r2": float(r2),
            "last_trained": str(pd.Timestamp.now().date())
        }
        
        # CRITICAL: In Docker, backend is at /app. Locally it might be ./backend
        # Let's ensure we find the backend/data directory.
        if os.path.exists("/app/data"):
            output_metrics_path = "/app/data/model_metrics.json"
        else:
            output_metrics_path = os.path.join(backend_dir, "data", user_id if user_id else "", "model_metrics.json")
        
        os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
        
        with open(output_metrics_path, "w") as f:
            json.dump(metrics, f)
        
        logger.info(f"Model metrics saved to {output_metrics_path}")

        # --- Plotting --- (kept for context)
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(feat_imp_dict.values())[:10], y=list(feat_imp_dict.keys())[:10], palette='viridis')
        plt.title('Top 10 Feature Importance')
        plt.xlabel('Importance')
        plt.tight_layout()
        fi_png_path = get_path('outputs/feature_importance.png')
        os.makedirs(os.path.dirname(fi_png_path), exist_ok=True)
        plt.savefig(fi_png_path)
        plt.close()
        
        # Log to MLflow
        mlflow.log_artifact(fi_png_path, "plots")

        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, preds, alpha=0.5)
        plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
        plt.xlabel('Actual')
        plt.ylabel('Predicted')
        plt.title(f'Actual vs Predicted (R2: {r2:.2f})')
        plt.tight_layout()
        perf_png_path = get_path('outputs/model_performance.png')
        plt.savefig(perf_png_path)
        plt.close()
        
        # Log to MLflow
        mlflow.log_artifact(perf_png_path, "plots")

        logger.info(f"Plots saved to {os.path.dirname(fi_png_path)}")
        logger.info(f"✅ MLflow tracking complete. View experiments at: http://localhost:5000")
        logger.info(f"   Command: mlflow ui --backend-store-uri sqlite:///{mlflow_db_path}")




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-id', help='Firebase UID for Firestore sync')
    args = parser.parse_args()
    
    main_process(user_id=args.user_id)
