"""
Tests for the API surface: input validation, BMI derivation, session
isolation, and the full screening flow (basic profile -> initial
screening -> follow-up -> prediction -> report).

Run with:  pytest backend/tests -v   (from the project root)
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

VALID_PROFILE = {
    "age": 45,
    "biological_sex": "female",
    "height_cm": 165,
    "weight_kg": 70,
    "systolic_bp": 128,
    "diastolic_bp": 82,
    "resting_heart_rate": 76,
    "smoking_status": "never",
    "alcohol_consumption": "occasional",
    "activity_level": "moderate",
    "family_history": ["diabetes"],
    "existing_conditions": [],
    "current_symptoms": ["fatigue"],
}

DIABETES_FOLLOWUP = {
    "pregnancies": 2, "fasting_glucose": 142, "triceps_skinfold": 30,
    "serum_insulin": 110, "diabetes_pedigree": 0.6,
}


def _new_session():
    return client.post("/screening/basic", json=VALID_PROFILE).json()["session_id"]


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_diseases_all_trained_classical_only():
    resp = client.get("/diseases")
    assert resp.status_code == 200
    by_key = {d["key"]: d for d in resp.json()["diseases"]}
    assert {"diabetes", "heart", "kidney"}.issubset(by_key)
    # All three now have real trained classical models (Phases 4/9);
    # none have a quantum model in this environment (Phase 5 untested
    # here — see README), so all should read "classical_only".
    for key in ("diabetes", "heart", "kidney"):
        assert by_key[key]["model_status"] == "classical_only"


def test_models_endpoint_returns_real_metrics_for_all_three():
    resp = client.get("/models")
    assert resp.status_code == 200
    body = resp.json()
    assert {"diabetes", "heart", "kidney"}.issubset(body.keys())
    diabetes_lr = body["diabetes"]["classical_models"]["logistic_regression"]
    assert 0.0 <= diabetes_lr["accuracy"] <= 1.0
    assert diabetes_lr["confusion_matrix"]


def test_chart_image_served_for_valid_disease_and_filename():
    resp = client.get("/models/diabetes/charts/model_comparison.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_chart_image_rejects_path_traversal():
    resp = client.get("/models/diabetes/charts/..%2F..%2Fmain.py")
    assert resp.status_code == 404


def test_chart_image_rejects_non_allowlisted_filename():
    # joblib model files must never be servable through this endpoint
    resp = client.get("/models/diabetes/charts/random_forest.joblib")
    assert resp.status_code == 404


def test_chart_image_unknown_disease_404():
    resp = client.get("/models/liver/charts/model_comparison.png")
    assert resp.status_code == 404


def test_submit_valid_basic_profile_computes_bmi():
    resp = client.post("/screening/basic", json=VALID_PROFILE)
    assert resp.status_code == 201
    body = resp.json()
    assert body["session_id"]
    # 70kg / (1.65m^2) ~= 25.7
    assert 25.0 <= body["bmi"] <= 26.5
    assert body["bmi_category"] == "overweight"


def test_sessions_are_isolated():
    r1 = client.post("/screening/basic", json=VALID_PROFILE)
    r2 = client.post("/screening/basic", json=VALID_PROFILE)
    assert r1.json()["session_id"] != r2.json()["session_id"]


def test_retrieve_stored_profile_by_session():
    created = client.post("/screening/basic", json=VALID_PROFILE).json()
    fetched = client.get(f"/screening/basic/{created['session_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["profile"]["age"] == 45


def test_unknown_session_returns_404():
    resp = client.get("/screening/basic/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("age", 0),               # below minimum
        ("age", 200),             # above maximum
        ("height_cm", 20),        # implausible height
        ("weight_kg", -5),        # negative weight
        ("systolic_bp", 400),     # above physiological maximum
    ],
)
def test_out_of_range_values_are_rejected(field, bad_value):
    payload = dict(VALID_PROFILE)
    payload[field] = bad_value
    resp = client.post("/screening/basic", json=payload)
    assert resp.status_code == 422


def test_diastolic_must_be_lower_than_systolic():
    payload = dict(VALID_PROFILE)
    payload["systolic_bp"] = 110
    payload["diastolic_bp"] = 120
    resp = client.post("/screening/basic", json=payload)
    assert resp.status_code == 422


def test_missing_required_field_rejected():
    payload = dict(VALID_PROFILE)
    del payload["biological_sex"]
    resp = client.post("/screening/basic", json=payload)
    assert resp.status_code == 422


def test_invalid_enum_value_rejected():
    payload = dict(VALID_PROFILE)
    payload["smoking_status"] = "sometimes"  # not a valid enum member
    resp = client.post("/screening/basic", json=payload)
    assert resp.status_code == 422


def test_implausible_bmi_combo_rejected():
    payload = dict(VALID_PROFILE)
    payload["height_cm"] = 250
    payload["weight_kg"] = 395
    resp = client.post("/screening/basic", json=payload)
    assert resp.status_code == 422


def test_initial_screening_covers_all_diseases():
    session_id = _new_session()
    resp = client.post("/screening/initial", json={"session_id": session_id})
    assert resp.status_code == 200
    keys = {r["disease_key"] for r in resp.json()["results"]}
    assert keys == {"diabetes", "heart", "kidney"}


def test_initial_screening_unknown_session_404():
    resp = client.post("/screening/initial", json={"session_id": "nope"})
    assert resp.status_code == 404


def test_get_followup_questions_for_diabetes():
    resp = client.get("/screening/followup/diabetes")
    assert resp.status_code == 200
    ids = {q["id"] for q in resp.json()["questions"]}
    assert "fasting_glucose" in ids


def test_get_followup_questions_unknown_disease_404():
    resp = client.get("/screening/followup/liver")
    assert resp.status_code == 404


def test_submit_followup_answers_updates_missing_list():
    session_id = _new_session()
    resp = client.post("/screening/followup", json={
        "session_id": session_id, "disease_key": "diabetes",
        "answers": {"fasting_glucose": 130},
    })
    assert resp.status_code == 200
    assert "Number of pregnancies" in resp.json()["still_missing"]


def test_prediction_insufficient_information_without_followup():
    session_id = _new_session()
    resp = client.post("/prediction/diabetes", json={"session_id": session_id})
    assert resp.status_code == 200
    assert resp.json()["status"] == "insufficient_information"


def test_prediction_succeeds_after_followup():
    session_id = _new_session()
    client.post("/screening/followup", json={
        "session_id": session_id, "disease_key": "diabetes",
        "answers": DIABETES_FOLLOWUP,
    })
    resp = client.post("/prediction/diabetes", json={"session_id": session_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "predicted"
    assert 0.0 <= body["risk_probability"] <= 1.0
    assert body["contributing_factors"]


def test_prediction_unknown_disease_404():
    session_id = _new_session()
    resp = client.post("/prediction/liver", json={"session_id": session_id})
    assert resp.status_code == 404


def test_circuit_diagram_honest_501_without_qiskit():
    # This environment has no qiskit installed (see README) — the
    # endpoint must say so plainly rather than fabricate a diagram.
    resp = client.get("/circuit/diabetes")
    assert resp.status_code in (200, 501)  # 200 if qiskit IS installed wherever this runs
    if resp.status_code == 501:
        assert "qiskit" in resp.json()["detail"].lower()
    else:
        assert "diagram_text" in resp.json()


def test_circuit_diagram_unknown_disease_404():
    resp = client.get("/circuit/liver")
    assert resp.status_code == 404


def test_report_reflects_predictions_made_so_far():
    session_id = _new_session()
    client.post("/screening/followup", json={
        "session_id": session_id, "disease_key": "diabetes",
        "answers": DIABETES_FOLLOWUP,
    })
    client.post("/prediction/diabetes", json={"session_id": session_id})

    resp = client.get(f"/screening/report/{session_id}")
    assert resp.status_code == 200
    body = resp.json()
    by_key = {}
    for entry in body["disease_reports"]:
        key = entry.get("disease_key")
        by_key[key] = entry
    # diabetes was predicted; heart/kidney were never touched this session
    diabetes_entry = next(e for e in body["disease_reports"] if e.get("display_name") == "Diabetes")
    assert diabetes_entry["status"] == "predicted"
    not_yet = [e for e in body["disease_reports"] if e.get("status") == "not_yet_assessed"]
    assert len(not_yet) == 2
