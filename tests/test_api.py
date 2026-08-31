import pytest
import requests

BASE = "http://localhost:8000"

VALID_PAYLOAD = {
    "country":                "Nigeria",
    "disease_type":           "Foot and mouth disease",
    "species":                "Cattle",
    "year":                   2026,
    "month":                  7,
    "livestock_density":      42.5,
    "rainfall_mm":            145.0,
    "temp_celsuis":           28.5,
    "rolling_outbreak_count": 4,
    "season":                 "Wet",
    "source":                 "react"
}

# ── Test 1: Health endpoint ───────────────────────────────────────
def test_health_endpoint():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] == True
    assert "model_name" in data
    assert "threshold" in data

# ── Test 2: Predict endpoint returns valid response ───────────────
def test_predict_returns_valid_response():
    r = requests.post(f"{BASE}/predict", json=VALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert "predicted_class" in data
    assert "outbreak_probability" in data
    assert "risk_level" in data
    assert "message" in data

# ── Test 3: Predicted class is binary ────────────────────────────
def test_predicted_class_is_binary():
    r = requests.post(f"{BASE}/predict", json=VALID_PAYLOAD)
    data = r.json()
    assert data["predicted_class"] in [0, 1]

# ── Test 4: Probability is between 0 and 1 ───────────────────────
def test_probability_range():
    r = requests.post(f"{BASE}/predict", json=VALID_PAYLOAD)
    data = r.json()
    assert 0.0 <= data["outbreak_probability"] <= 1.0

# ── Test 5: Risk level matches predicted class ────────────────────
def test_risk_level_matches_class():
    r = requests.post(f"{BASE}/predict", json=VALID_PAYLOAD)
    data = r.json()
    if data["predicted_class"] == 1:
        assert data["risk_level"] == "HIGH"
    else:
        assert data["risk_level"] == "LOW"

# ── Test 6: Message is not empty ─────────────────────────────────
def test_message_not_empty():
    r = requests.post(f"{BASE}/predict", json=VALID_PAYLOAD)
    data = r.json()
    assert len(data["message"]) > 10

# ── Test 7: Invalid input returns 422 ────────────────────────────
def test_invalid_input_rejected():
    bad_payload = {"country": "Nigeria"}  # missing required fields
    r = requests.post(f"{BASE}/predict", json=bad_payload)
    assert r.status_code == 422

# ── Test 8: Invalid month rejected ───────────────────────────────
def test_invalid_month_rejected():
    bad = VALID_PAYLOAD.copy()
    bad["month"] = 13  # month 13 does not exist
    r = requests.post(f"{BASE}/predict", json=bad)
    assert r.status_code == 422

# ── Test 9: History endpoint returns a list ───────────────────────
def test_history_returns_list():
    r = requests.get(f"{BASE}/predict_history?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

# ── Test 10: Stats endpoint returns correct keys ──────────────────
def test_stats_returns_correct_keys():
    r = requests.get(f"{BASE}/predict/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_predictions" in data
    assert "high_risk_count" in data
    assert "low_risk_count" in data
    assert "high_risk_rate" in data

# ── Test 11: Model info endpoint works ───────────────────────────
def test_model_info():
    r = requests.get(f"{BASE}/model/info")
    assert r.status_code == 200
    data = r.json()
    assert "model_name" in data
    assert "optimal_threshold" in data

# ── Test 12: USSD source logs correctly ──────────────────────────
def test_ussd_source_accepted():
    ussd_payload = VALID_PAYLOAD.copy()
    ussd_payload["source"] = "ussd"
    r = requests.post(f"{BASE}/predict", json=ussd_payload)
    assert r.status_code == 200