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

def main_process(user_id: str = None, mode: str = "incremental"):
    # --- Path Configuration ---
    # We need to find the data files regardless of whether we run from backend/ or root/
    # or inside Docker.
    # or inside Docker.
    script_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/scripts
    backend_dir = os.path.dirname(script_dir)              # .../backend
    
    # Define metrics/model paths early for mode checking
    # Determine base data dir
    if os.path.exists("/app/data"):
         base_data_dir = "/app/data"
    else:
         base_data_dir = os.path.join(backend_dir, "data")

    # Construct paths
    if user_id:
         output_metrics_path = os.path.join(base_data_dir, user_id, "model_metrics.json")
         model_path_rel = f"models/{user_id}/xgb_model.pkl"
    else:
         output_metrics_path = os.path.join(base_data_dir, "model_metrics.json")
         model_path_rel = "models/xgb_model.pkl"

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
    
    # --- Predictive Lagging & Quality Control ---
    # We want to predict TOMORROW'S recovery (bodyBatteryChargedValue) 
    # based on TODAY'S load, stress, and previous stats.
    
    # QUALITY FILTER: Mark days without watch as NaN.
    # We check for BB Charged=0, Stress=0, or Sleep=0, as these indicate 
    # the watch was not worn or data is invalid for recovery training.
    # threshold 10 for BB caught partial days (e.g. putting watch on mid-day).
    invalid_mask = (df_merged['bodyBatteryChargedValue'] < 10) | \
                   (df_merged['averageStressLevel'] == 0) | \
                   (df_merged['totalSleep_minutes'] == 0)
                   
    if invalid_mask.any():
        logger.info(f"Filtering {invalid_mask.sum()} days with invalid/missing metrics (watch off).")
        cols_to_null = ['bodyBatteryChargedValue', 'averageStressLevel', 'bodyBatteryHighestValue', 
                        'bodyBatteryLowestValue', 'totalSteps', 'totalSleep_minutes',
                        'restingHeartRate', 'averageHR', 'maxHeartRate']
        df_merged.loc[invalid_mask, [c for c in cols_to_null if c in df_merged.columns]] = np.nan

    # Target: Tomorrow's Peak Body Battery (Highest Value)
    # This is more predictive and stable than net charge.
    df_merged['target_recovery'] = df_merged['bodyBatteryHighestValue'].shift(-1)
    
    # CONTINUITY CHECK: Target only valid if next row is today + 1 day
    # and both today and tomorrow have valid data.
    next_is_consecutive = (df_merged['date'].shift(-1) - df_merged['date']).dt.days == 1
    df_merged.loc[~next_is_consecutive, 'target_recovery'] = np.nan

    lag_cols = ['bodyBatteryHighestValue', 'averageStressLevel', 'totalSteps', 'totalSleep_minutes']
    prev_is_consecutive = (df_merged['date'] - df_merged['date'].shift(1)).dt.days == 1
    
    for col in lag_cols:
        if col in df_merged.columns:
            df_merged[f'{col}_lag_1'] = df_merged[col].shift(1)
            # Ensure lag 1 is only from the immediate previous day
            df_merged.loc[~prev_is_consecutive, f'{col}_lag_1'] = np.nan

    # --- Sync to Firestore (Multi-User) ---
    if user_id:
        logger.info(f"Syncing processed metrics to Firestore for user {user_id}...")
        try:
            # Prepare metrics list from df_merged
            int_cols = ['bodyBatteryChargedValue', 'bodyBatteryHighestValue', 'bodyBatteryLowestValue',
                        'averageStressLevel', 'totalSteps', 'totalSleep_minutes',
                        'workout_calories', 'workout_duration_seconds']
            float_cols = ['CTL', 'ATL', 'TSB']
            optional_cols = {'averageHR': float, 'restingHeartRate': int}

            sync_df = df_merged.copy()
            sync_df['date'] = sync_df['date'].apply(
                lambda d: str(d.date()) if hasattr(d, 'date') else str(d)[:10]
            )
            for col in int_cols:
                if col in sync_df.columns:
                    sync_df[col] = sync_df[col].fillna(0).astype(int)
                else:
                    sync_df[col] = 0
            for col in float_cols:
                if col in sync_df.columns:
                    sync_df[col] = sync_df[col].fillna(0.0).astype(float)
                else:
                    sync_df[col] = 0.0
            for col, cast in optional_cols.items():
                if col not in sync_df.columns:
                    sync_df[col] = None

            keep_cols = ['date'] + int_cols + float_cols + list(optional_cols.keys())
            keep_cols = [c for c in keep_cols if c in sync_df.columns]
            metrics_list = sync_df[keep_cols].where(sync_df[keep_cols].notna(), None).to_dict('records')
            
            # Batch save
            if firestore_garmin_metrics.batch_save_metrics(user_id, metrics_list):
                 logger.info(f"Successfully synced {len(metrics_list)} daily metrics to Firestore")
            else:
                 logger.error("Firestore sync returned false")
                 
        except Exception as e:
            logger.error(f"Failed to sync to Firestore: {e}")

    # --- Feature Selection & Data Preparation ---
    # We prioritize averageStressLevel as it has the highest correlation with Peak Recovery.
    top_features = [
        'averageStressLevel', 'bodyBatteryHighestValue', 'totalSleep_minutes',
        'ATL', 'CTL', 'TSB', 'workout_calories', 'totalSteps',
        'restingHeartRate', 'averageHR', 'bodyBatteryHighestValue_lag_1',
        'averageStressLevel_lag_1', 'workout_calories_roll_7d'
    ]
    target = 'target_recovery'
    available_features = [f for f in top_features if f in df_merged.columns]
    
    # Drop rows with NaNs in our selected features + target
    df_train = df_merged.dropna(subset=[target] + available_features)
    logger.info(f"Cleaned data: {len(df_train)} samples available for training (selected {len(available_features)} features).")

    # MLflow Setup - Optional in Production
    mlflow_enabled = os.environ.get("MLFLOW_ENABLED", "false").lower() == "true"
    if mlflow_enabled:
        mlflow_db_path = os.path.join(backend_dir, "data", "mlflow.db")
        os.makedirs(os.path.dirname(mlflow_db_path), exist_ok=True)
        mlflow.set_tracking_uri(f"sqlite:///{mlflow_db_path}")
        mlflow.set_experiment("xgboost_readiness_prediction")

    # --- Training ---
    logger.info("Training XGBoost Model (with Hyperparameter Tuning & TimeSeries CV)...")
    X = df_train[available_features]
    y = df_train[target]

    # --- MINIMUM DATA CHECK ---
    # We need at least 5 samples for TimeSeriesSplit(n_splits=2) + train_test_split(0.2)
    min_samples = 5
    if len(X) < min_samples:
        logger.warning(f"⚠️ Not enough data points ({len(X)}) to train XGBoost model. Need at least {min_samples}.")
        
        # Save placeholder metrics to avoid API 404s/500s
        if not os.path.exists(output_metrics_path):
            placeholder = {
                "mae": 0.0, "r2": 0.0, "rmse": 0.0, "best_cv_score": 0.0,
                "last_trained": str(pd.Timestamp.now().date()),
                "status": "waiting_for_more_data"
            }
            with open(output_metrics_path, 'w') as f:
                json.dump(placeholder, f)
        return

    # --- Mode Selection: Incremental vs Full ---
    # get_path injects user_id into subdir automatically: models/{user_id}/xgb_model.pkl
    model_path = get_path("models/xgb_model.pkl")

    # Check for Last Trained Date
    last_trained_date = None
    if os.path.exists(output_metrics_path):
        try:
            with open(output_metrics_path, 'r') as f:
                m = json.load(f)
                if 'last_trained' in m:
                    last_trained_date = pd.to_datetime(m['last_trained']).date()
        except Exception as e:
            logger.warning(f"Could not read last_trained from metrics: {e}")

    # FORCE FULL if model doesn't exist or no history
    if mode == "incremental" and (not os.path.exists(model_path) or last_trained_date is None):
        logger.info("Incremental mode requested but no existing model/metrics found. Switching to FULL training.")
        mode = "full"
        
    best_model = None
    mae, r2, rmse = 0, 0, 0
    
    if mode == "incremental":
        logger.info(f"--- INCREMENTAL TRAINING (Last trained: {last_trained_date}) ---")
        
        # 1. Access New Data
        # Filter rows where date > last_trained_date
        # Ensure 'date' column is datetime
        new_data = df_merged[df_merged['date'].dt.date > last_trained_date].copy()
        
        if new_data.empty:
            logger.info("✅ No new data found since last training. Model is up to date.")
            return # Exit, nothing to do
            
        logger.info(f"Found {len(new_data)} new data points to learn from.")
        
        # 2. Prepare X_new, y_new
        new_data = new_data.dropna(subset=[target] + available_features)
        if new_data.empty:
            logger.info("No valid new data points after cleaning. Skipping incremental update.")
            return

        X_new = new_data[available_features]
        y_new = new_data[target]
        
        # 3. Load Existing Model
        logger.info(f"Loading existing model from {model_path}...")
        loaded_model = joblib.load(model_path)
        
        # 4. Evaluate (Test on unseen data BEFORE training)
        logger.info("Evaluating model on new data (Pre-update)...")
        preds = loaded_model.predict(X_new)
        mae = mean_absolute_error(y_new, preds)
        r2 = r2_score(y_new, preds)
        rmse = np.sqrt(mean_squared_error(y_new, preds))
        
        logger.info(f"Performance on new batch - MAE: {mae:.2f}, R2: {r2:.2f}")
        
        # SQLite safety check: MLflow crashes on NaN metrics
        mae_log = float(0.0) if pd.isna(mae) else float(mae)
        r2_log = float(0.0) if pd.isna(r2) else float(r2)
        rmse_log = float(0.0) if pd.isna(rmse) else float(rmse)
        
        # 5. Incremental Update
        logger.info("Updating model with new data...")
        # Create new instance with same params
        best_model = XGBRegressor(**loaded_model.get_params())
        
        # BACKUP: Before fitting, we might want to keep the booster if we fail
        # But here we fit and then save. I will add backup call before joblib.dump.
        
        # Fit with xgb_model=loaded_model (uses internal booster)
        best_model.fit(X_new, y_new, xgb_model=loaded_model.get_booster())
        
        logger.info(f"Incremental update complete on {len(X_new)} samples.")
        training_details = {
            "mode": "incremental",
            "samples": len(X_new),
            "pre_update_mae": float(mae),
            "pre_update_r2": float(r2)
        }
        
        # Incremental update complete. MLFlow logging is disabled by default in proc to save IO.
        if mlflow_enabled:
            with mlflow.start_run(run_name=f"incremental_{user_id if user_id else 'global'}"):
                 mlflow.log_metrics({"mae": mae_log, "r2": r2_log, "rmse": rmse_log, "new_samples": len(X_new)})
                 mlflow.sklearn.log_model(best_model, "xgboost_model")
        
    else:
        # --- FULL TRAINING ---
        logger.info("--- FULL TRAINING (GridSearch) ---")
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

        param_grid = {
            'n_estimators': [100, 150], # Added 150
            'learning_rate': [0.05, 0.1], # Added 0.1
            'max_depth': [4, 5], # Added 5
            'subsample': [0.8],
            'colsample_bytree': [0.8]
        }
        
        xgb = XGBRegressor(random_state=42, n_jobs=-1)
        tscv = TimeSeriesSplit(n_splits=2)
        
        # ⚠️ Cloud Run: n_jobs=-1 hyödyntää kaikki ytimet, n_splits=2 nopeuttaa hakua
        grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, 
                                   cv=tscv, n_jobs=-1, scoring='r2', verbose=0)
        
        # 1. Train the model (ALWAYS RUN)
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        logger.info(f"Best Parameters: {grid_search.best_params_}")
        logger.info(f"Best CV Score (R2): {grid_search.best_score_:.2f}")

        preds = best_model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        
        # SQLite safety checks for metrics
        best_cv_r2_log = float(0.0) if pd.isna(grid_search.best_score_) else float(grid_search.best_score_)
        mae_log = float(0.0) if pd.isna(mae) else float(mae)
        r2_log = float(0.0) if pd.isna(r2) else float(r2)
        rmse_log = float(0.0) if pd.isna(rmse) else float(rmse)
        
        print(f"Final Test Model Performance - MAE: {mae:.2f}, R2: {r2:.2f}, RMSE: {rmse:.2f}")
        logger.info(f"Final Test Model Performance", extra={"mae": mae_log, "r2": r2_log, "rmse": rmse_log})
        
        training_details = {
            "mode": "full",
            "samples": len(X_train),
            "test_samples": len(X_test),
            "best_params": grid_search.best_params_
        }
        
        # 2. Log to MLflow (CONDITIONALLY RUN)
        if mlflow_enabled:
            with mlflow.start_run(run_name=f"full_train_{user_id if user_id else 'global'}"):
                mlflow.log_params({
                    "n_estimators_grid": str(param_grid['n_estimators']),
                    "learning_rate_grid": str(param_grid['learning_rate']),
                    "max_depth_grid": str(param_grid['max_depth']),
                    "subsample": param_grid['subsample'][0],
                    "colsample_bytree": param_grid['colsample_bytree'][0],
                    "cv_splits": 2,
                    "test_size": 0.2,
                    "user_id": user_id if user_id else "global"
                })
                mlflow.log_params(grid_search.best_params_)
                mlflow.log_metric("best_cv_r2", best_cv_r2_log)
                mlflow.log_metrics({
                    "mae": mae_log,
                    "r2_score": r2_log,
                    "rmse": rmse_log,
                    "train_samples": len(X_train),
                    "test_samples": len(X_test),
                    "total_features": X.shape[1]
                })
                mlflow.sklearn.log_model(best_model, "xgboost_model")
                logger.info("Model logged to MLflow")
    
    # --- Common Save Logic (for both modes) ---
    if best_model is not None:
        # BACKUP PREVIOUS MODEL
        if os.path.exists(model_path):
            backup_path = model_path.replace(".pkl", "_prev.pkl")
            try:
                import shutil
                shutil.copy2(model_path, backup_path)
                logger.info(f"💾 Backup of previous model saved to {backup_path}")
            except Exception as be:
                logger.warning(f"⚠️ Could not backup model: {be}")

        # Save Model
        # Ensure params are updated for incremental too
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(best_model, model_path)
        logger.info(f"Model saved to {model_path}")

        # Feature Importance (Only availability varies)
        # For incremental, feature importance might shift.
        importance = best_model.feature_importances_
        feature_names = X.columns.tolist()
        feat_imp_dict = dict(zip(feature_names, [float(x) for x in importance]))
        feat_imp_dict = dict(sorted(feat_imp_dict.items(), key=lambda item: item[1], reverse=True))
        
        fi_json_path = get_path("outputs/feature_importance.json")
        with open(fi_json_path, "w") as f:
            json.dump(feat_imp_dict, f, indent=4)

            
        logger.info(f"Feature importance saved to {fi_json_path}")
        
        # Log feature importance as MLflow artifact
        if mlflow_enabled:
            mlflow.log_artifact(fi_json_path, "feature_importance")
    
        # Save Metrics to backend/data where API expects it
        metrics = {
            "mae": float(0.0) if pd.isna(mae) else float(mae),
            "r2": float(0.0) if pd.isna(r2) else float(r2),
            "last_trained": str(pd.Timestamp.now().date()),
            "training_mode": training_details.get("mode", "unknown"),
            "sample_count": training_details.get("samples", 0)
        }
        if "pre_update_r2" in training_details:
            metrics["pre_update_r2"] = training_details["pre_update_r2"]
        
        # CRITICAL: In Docker, backend is at /app. Locally it might be ./backend
        # Let's ensure we find the backend/data directory.
        if os.path.exists("/app/data"):
             base_data_dir = "/app/data"
        else:
             base_data_dir = os.path.join(backend_dir, "data")

        # Construct path with user_id
        if user_id:
             output_metrics_path = os.path.join(base_data_dir, user_id, "model_metrics.json")
        else:
             output_metrics_path = os.path.join(base_data_dir, "model_metrics.json")
        
        os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
        
        with open(output_metrics_path, "w") as f:
            json.dump(metrics, f)
        
        logger.info(f"Model metrics saved to {output_metrics_path}")

    # Indentation fix for the persisted block:
    # Everything below was inside the 'else' block implicitly in original code structure?
    # No, it was main indentation.
    # But wait, 'best_model' availability check is needed.
    
    # ... (Plots and Firestore persist) ...
    # We need to make sure we don't crash if best_model is None (e.g. incremental no data)
    # But we returned early if no data.
    
    # If mode was full, 'metrics', 'mae', 'r2' are defined in the block.
    # If mode was incremental, 'mae' etc are defined.
    # So we can unify.


        # --- Persist to Firestore (Multi-User) ---
        if user_id:
            logger.info(f"Persisting model performance to Firestore for user {user_id}...")
            if firestore_garmin_metrics.save_model_performance(user_id, metrics, feat_imp_dict):
                logger.info("[SUCCESS] Model performance saved to Firestore")
            else:
                logger.error("[ERROR] Failed to save model performance to Firestore")
        # --- Plotting --- (kept for condition when mlflow is enabled)
        if mlflow_enabled:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
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
            if 'preds' in locals() and 'y_test' in locals():
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
            logger.info(f"[SUCCESS] MLflow tracking complete. View experiments at: http://localhost:5000")
            logger.info(f"   Command: mlflow ui --backend-store-uri sqlite:///{mlflow_db_path}")




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-id', help='Firebase UID for Firestore sync')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='incremental', help='Training mode')
    args = parser.parse_args()
    
    main_process(user_id=args.user_id, mode=args.mode)
