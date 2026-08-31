import pytest
import requests

BASE = "http://localhost:8001"

def ussd_post(session_id, phone, text):
    return requests.post(f"{BASE}/ussd", data={
        "sessionId":   session_id,
        "phoneNumber": phone,
        "text":        text
    })

# ── Test 1: Welcome screen ────────────────────────────────────────
def test_welcome_screen():
    r = ussd_post("sys_test_1", "+2348000000001", "")
    assert r.status_code == 200
    assert r.text.startswith("CON")
    assert "1. Check disease risk" in r.text
    assert "2. Report sick animal" in r.text

# ── Test 2: About branch returns END ─────────────────────────────
def test_about_branch():
    ussd_post("sys_test_2", "+2348000000002", "")
    r = ussd_post("sys_test_2", "+2348000000002", "3")
    assert r.text.startswith("END")
    assert "Miva" in r.text

# ── Test 3: Branch A shows country menu ──────────────────────────
def test_branch_a_country_menu():
    ussd_post("sys_test_3", "+2348000000003", "")
    r = ussd_post("sys_test_3", "+2348000000003", "1")
    assert r.text.startswith("CON")
    assert "Nigeria" in r.text

# ── Test 4: Country select shows animal menu ──────────────────────
def test_country_select_shows_animals():
    ussd_post("sys_test_4", "+2348000000004", "")
    ussd_post("sys_test_4", "+2348000000004", "1")
    r = ussd_post("sys_test_4", "+2348000000004", "1*1")
    assert r.text.startswith("CON")
    assert "Cattle" in r.text

# ── Test 5: Animal select shows symptom menu ──────────────────────
def test_animal_select_shows_symptoms():
    ussd_post("sys_test_5", "+2348000000005", "")
    ussd_post("sys_test_5", "+2348000000005", "1")
    ussd_post("sys_test_5", "+2348000000005", "1*1")
    r = ussd_post("sys_test_5", "+2348000000005", "1*1*1")
    assert r.text.startswith("CON")
    assert "Sores" in r.text or "noticed" in r.text.lower()

# ── Test 6: Full flow returns END with risk ───────────────────────
def test_full_flow_returns_risk():
    phone = "+2348000000006"
    ussd_post("sys_test_6", phone, "")
    ussd_post("sys_test_6", phone, "1")
    ussd_post("sys_test_6", phone, "1*1")
    ussd_post("sys_test_6", phone, "1*1*1")
    r = ussd_post("sys_test_6", phone, "1*1*1*1")
    assert r.text.startswith("END")
    assert ("HIGH RISK" in r.text or "LOW RISK" in r.text)

# ── Test 7: Result contains probability ───────────────────────────
def test_result_contains_probability():
    phone = "+2348000000007"
    ussd_post("sys_test_7", phone, "")
    ussd_post("sys_test_7", phone, "1")
    ussd_post("sys_test_7", phone, "1*1")
    ussd_post("sys_test_7", phone, "1*1*1")
    r = ussd_post("sys_test_7", phone, "1*1*1*1")
    assert "%" in r.text

# ── Test 8: Report flow completes ────────────────────────────────
def test_report_flow_completes():
    phone = "+2348000000008"
    ussd_post("sys_test_8", phone, "")
    ussd_post("sys_test_8", phone, "2")
    ussd_post("sys_test_8", phone, "2*1")
    ussd_post("sys_test_8", phone, "2*1*1")
    r = ussd_post("sys_test_8", phone, "2*1*1*3")
    assert r.text.startswith("END")
    assert "logged" in r.text.lower() or "vet" in r.text.lower()

# ── Test 9: Invalid input on branch gets handled ──────────────────
def test_invalid_choice_handled():
    phone = "+2348000000009"
    ussd_post("sys_test_9", phone, "")
    r = ussd_post("sys_test_9", phone, "9")  # invalid main choice
    assert r.status_code == 200
    assert "END" in r.text or "Invalid" in r.text

# ── Test 10: All screens under 182 chars ─────────────────────────
def test_screen_lengths():
    phone = "+2348000000010"
    responses = []
    responses.append(ussd_post("sys_test_10", phone, ""))
    responses.append(ussd_post("sys_test_10", phone, "1"))
    responses.append(ussd_post("sys_test_10", phone, "1*1"))
    responses.append(ussd_post("sys_test_10", phone, "1*1*1"))

    for r in responses:
        # Strip CON/END prefix for character count
        text = r.text.replace("CON ", "").replace("END ", "")
        assert len(text) <= 182, (
            f"Screen too long ({len(text)} chars): {text[:50]}..."
        )