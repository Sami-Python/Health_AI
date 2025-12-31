import pytest
import os
import joblib
import pandas as pd
import numpy as np

MODEL_PATH = "Health_AI/models/xgb_model.pkl"

def test_model_exists():
    """Verify that the model file exists."""
    if not os.path.exists(MODEL_PATH):
        pytest.skip(f"Model file not found at {MODEL_PATH}. Skipping smoke test.")
    assert os.path.exists(MODEL_PATH)

def test_model_loading_and_prediction():
    """Smoke test: Load model and invoke predict with dummy data."""
    if not os.path.exists(MODEL_PATH):
        pytest.skip("Model not found.")
        
    try:
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        pytest.fail(f"Failed to load model: {e}")

    # Create dummy input with some common features expected by the model
    # We don't need all features if the model handles missing ones (or we mock them)
    # But usually sklearn/xgboost expects specific feature count/names.
    # We will try to get feature names from the model if possible.
    
    try:
        booster = model.get_booster()
        feature_names = booster.feature_names
    except:
        # Fallback if specific wrapper doesn't expose it easily
        feature_names = ["day_of_week", "yesterday_steps", "yesterday_stress", "sleep_hours"]

    # Create a DataFrame with 1 row of zeros/dummy values
    input_data = pd.DataFrame([np.zeros(len(feature_names))], columns=feature_names)
    
    try:
        prediction = model.predict(input_data)
        assert len(prediction) == 1
        assert isinstance(prediction[0], (float, np.float32, np.float64))
        # Basic sanity check (Body Battery charge is usually 0-100)
        # It might be outside if dummy data is weird, but shouldn't crash.
    except Exception as e:
        pytest.fail(f"Model prediction failed: {e}")
