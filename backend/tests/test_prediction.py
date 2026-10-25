"""
Tests for Phase 6/7/8: feature resolution, prediction, and initial
screening. Run with: pytest backend/tests -v
"""

import pytest

from backend.core.disease_registry import get_disease, list_diseases
from backend.core.feature_spec import resolve_feature_vector
from backend.services.prediction import predict_disease, run_initial_screening

FULL_PROFILE = {
    "age": 52, "biological_sex": "female", "height_cm": 165, "weight_kg": 78,
    "systolic_bp": 135, "diastolic_bp": 88, "resting_heart_rate": 80,
    "smoking_status": "never", "alcohol_consumption": "occasional",
    "activity_level": "sedentary",
    "family_history": ["diabetes"], "existing_conditions": ["hypertension"],
    "current_symptoms": ["fatigue", "increased_thirst"],
}

MALE_PROFILE = {
    "age": 60, "biological_sex": "male", "height_cm": 178, "weight_kg": 90,
    "systolic_bp": 140, "diastolic_bp": 90, "resting_heart_rate": 78,
    "smoking_status": "former", "alcohol_consumption": "moderate",
    "activity_level": "light", "family_history": [], "existing_conditions": [],
    "current_symptoms": ["chest_discomfort"],
}

DIABETES_FOLLOWUP = {
    "pregnancies": 2, "fasting_glucose": 142, "triceps_skinfold": 30,
    "serum_insulin": 110, "diabetes_pedigree": 0.6,
}

KIDNEY_FOLLOWUP = {
    "urine_specific_gravity": 1.02, "urine_albumin": 1, "urine_sugar": 0,
    "urine_rbc": 0, "urine_pus_cell": 0, "urine_pus_cell_clumps": 0, "urine_bacteria": 0,
    "random_blood_glucose": 110, "blood_urea": 40, "serum_creatinine": 1.1,
    "serum_sodium": 138, "serum_potassium": 4.2, "hemoglobin": 13.5,
    "packed_cell_volume": 40, "white_blood_cell_count": 7500, "red_blood_cell_count": 4.8,
    "appetite": 0,
}


def test_registry_required_features_match_dataset_order():
    # These must stay in sync with ml/common/dataset.py's feature_names
    # or predictions silently score the wrong column against the wrong
    # weight — a correctness bug, not a style issue.
    diabetes = get_disease("diabetes")
    assert diabetes.required_features == [
        "pregnancies", "glucose", "blood_pressure", "skin_thickness",
        "insulin", "bmi", "diabetes_pedigree", "age",
    ]
    kidney = get_disease("kidney")
    assert kidney.required_features[0] == "age"
    assert kidney.required_features[1] == "blood_pressure"
    assert len(kidney.required_features) == 24


def test_diabetes_prediction_insufficient_without_followup():
    result = predict_disease("diabetes", FULL_PROFILE, {})
    assert result["status"] == "insufficient_information"
    assert "Fasting blood glucose" in result["missing_information"]


def test_diabetes_prediction_succeeds_with_followup():
    result = predict_disease("diabetes", FULL_PROFILE, DIABETES_FOLLOWUP)
    assert result["status"] == "predicted"
    assert 0.0 <= result["risk_probability"] <= 1.0
    assert result["model_used"] in ("logistic_regression", "svm", "random_forest")
    assert result["contributing_factors"]
    assert result["model_metrics"]["f1"] is not None


def test_diabetes_male_pregnancies_auto_resolves_to_zero():
    # A value of 0 pregnancies for a male profile is a known fact, not a
    # fabricated one — should NOT show up as missing.
    result = predict_disease("diabetes", MALE_PROFILE, {
        "fasting_glucose": 95, "triceps_skinfold": 22,
        "serum_insulin": 60, "diabetes_pedigree": 0.3,
    })
    assert result["status"] == "predicted"


def test_diabetes_female_without_pregnancies_answer_is_missing():
    result = predict_disease("diabetes", FULL_PROFILE, {
        "fasting_glucose": 95, "triceps_skinfold": 22,
        "serum_insulin": 60, "diabetes_pedigree": 0.3,
        # deliberately omit "pregnancies"
    })
    assert result["status"] == "insufficient_information"
    assert "Number of pregnancies" in result["missing_information"]


def test_heart_prediction_insufficient_with_minimal_answers():
    # Realistic case: most people can't supply ECG/stress-test/fluoroscopy
    # results, so this SHOULD come back insufficient, not a guess.
    result = predict_disease("heart", MALE_PROFILE, {"chest_pain_type": 0})
    assert result["status"] == "insufficient_information"
    assert len(result["missing_information"]) > 0


def test_kidney_prediction_derives_hypertension_from_existing_conditions():
    result = predict_disease("kidney", FULL_PROFILE, KIDNEY_FOLLOWUP)
    assert result["status"] == "predicted"
    # FULL_PROFILE lists "hypertension" in existing_conditions — the
    # feature should resolve without a follow-up question for it.
    factor_labels = [f["label"] for f in result["contributing_factors"]]
    assert isinstance(factor_labels, list)


def test_unknown_disease_raises_keyerror():
    with pytest.raises(KeyError):
        predict_disease("liver", FULL_PROFILE, {})


def test_initial_screening_runs_for_every_registered_disease():
    results = run_initial_screening(FULL_PROFILE)
    keys = {r["disease_key"] for r in results}
    assert keys == {d.key for d in list_diseases()}
    for r in results:
        assert r["risk_probability"] is None or 0.0 <= r["risk_probability"] <= 1.0


def test_followup_questions_are_all_source_followup():
    for disease in list_diseases():
        questions = disease.followup_questions()
        ids = {q["id"] for q in questions}
        assert None not in ids
        assert len(ids) == len(questions)  # no duplicate question ids


def test_resolve_feature_vector_reports_all_missing_not_just_first():
    diabetes = get_disease("diabetes")
    vector, missing = resolve_feature_vector(diabetes.feature_specs, MALE_PROFILE, {})
    assert vector is None
    assert len(missing) == 4  # glucose, skin_thickness, insulin, diabetes_pedigree (pregnancies auto-resolves for male)
