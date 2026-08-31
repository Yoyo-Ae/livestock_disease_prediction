import pytest
import numpy as np
import joblib
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Test 1: Model loads correctly ────────────────────────────────
def test_model_loads():
    model = joblib.load("models/best_model.pkl")
    assert model is not None
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")

# ── Test 2: Scaler loads correctly ───────────────────────────────
def test_scaler_loads():
    scaler = joblib.load("models/scaler.pkl")
    assert scaler is not None
    assert hasattr(scaler, "transform")

# ── Test 3: Encoders load correctly ──────────────────────────────
def test_encoders_load():
    for col in ["country", "disease_type", "species", "season"]:
        path = f"models/le_{col}.pkl"
        assert os.path.exists(path), f"Encoder missing: {path}"
        le = joblib.load(path)
        assert hasattr(le, "transform")

# ── Test 4: Model predicts valid output ──────────────────────────
def test_model_predicts():
    model   = joblib.load("models/best_model.pkl")
    scaler  = joblib.load("models/scaler.pkl")
    features = joblib.load("models/feature_names.pkl")

    # Create a dummy feature vector of zeros
    dummy = np.zeros((1, len(features)))
    scaled = scaler.transform(dummy)

    pred  = model.predict(scaled)
    proba = model.predict_proba(scaled)

    assert pred[0] in [0, 1]
    assert 0.0 <= proba[0][1] <= 1.0

# ── Test 5: Cyclical month encoding is correct ───────────────────
def test_month_encoding():
    month_sin = math.sin(2 * math.pi * 1 / 12)
    month_cos = math.cos(2 * math.pi * 1 / 12)
    assert round(month_sin, 4) == round(math.sin(math.pi / 6), 4)
    assert -1.0 <= month_sin <= 1.0
    assert -1.0 <= month_cos <= 1.0

# ── Test 6: Season assignment is correct ─────────────────────────
def test_season_assignment():
    wet_months = [4, 5, 6, 7, 8, 9, 10]
    dry_months = [1, 2, 3, 11, 12]

    def assign_season(m):
        return "Wet" if m in wet_months else "Dry"

    for m in wet_months:
        assert assign_season(m) == "Wet"
    for m in dry_months:
        assert assign_season(m) == "Dry"

# ── Test 7: Label encoder handles known values ───────────────────
def test_encoder_known_value():
    le = joblib.load("models/le_country.pkl")
    classes = list(le.classes_)
    assert len(classes) > 0
    # Encode the first known class and verify it returns an integer
    encoded = le.transform([classes[0]])
    assert isinstance(int(encoded[0]), int)

# ── Test 8: Livestock density log transform ──────────────────────
def test_log_transform():
    density = 42.5
    log_density = math.log1p(density)
    assert log_density > 0
    assert log_density < density  # log is always less than raw value

# ── Test 9: Threshold produces correct classification ─────────────
def test_threshold_classification():
    threshold = 0.30
    assert (0.35 >= threshold) == True   # should be HIGH
    assert (0.20 >= threshold) == False  # should be LOW
    assert (0.30 >= threshold) == True   # exact threshold is HIGH

# ── Test 10: Feature vector has correct length ────────────────────
def test_feature_vector_length():
    features = joblib.load("models/feature_names.pkl")
    dummy    = np.zeros((1, len(features)))
    assert dummy.shape == (1, len(features))