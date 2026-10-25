"""
backend/diseases/kidney/features.py
======================================
Feature order MUST match ml/common/dataset.py:load_kidney() exactly:
    age, blood_pressure, specific_gravity, albumin, sugar,
    red_blood_cells, pus_cell, pus_cell_clumps, bacteria,
    blood_glucose_random, blood_urea, serum_creatinine, sodium,
    potassium, hemoglobin, packed_cell_volume, white_blood_cell_count,
    red_blood_cell_count, hypertension, diabetes_mellitus,
    coronary_artery_disease, appetite, pedal_edema, anemia

Unlike diabetes/heart, several of these ARE derivable from what the
basic profile already collects (existing conditions, reported symptoms)
rather than requiring a brand-new follow-up question — used where doing
so is a real fact the user already stated, not an inference.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.feature_spec import FeatureSpec

YES_NO_OPTIONS = [{"value": "1", "label": "Yes"}, {"value": "0", "label": "No"}]
NORMAL_ABNORMAL_OPTIONS = [
    {"value": "0", "label": "Normal"}, {"value": "1", "label": "Abnormal"},
]
PRESENT_OPTIONS = [
    {"value": "1", "label": "Present"}, {"value": "0", "label": "Not present"},
]


def _condition_flag(condition_names: List[str]):
    def _extract(profile: Dict[str, Any], followup: Dict[str, Any]) -> Optional[float]:
        existing = [c.lower() for c in (profile.get("existing_conditions") or [])]
        return 1.0 if any(name in existing for name in condition_names) else 0.0
    return _extract


def _symptom_flag(symptom_names: List[str]):
    def _extract(profile: Dict[str, Any], followup: Dict[str, Any]) -> Optional[float]:
        symptoms = [s.lower() for s in (profile.get("current_symptoms") or [])]
        return 1.0 if any(name in symptoms for name in symptom_names) else 0.0
    return _extract


def _blood_pressure_extractor(profile: Dict[str, Any], followup: Dict[str, Any]) -> Optional[float]:
    if profile.get("diastolic_bp"):
        return profile["diastolic_bp"]
    val = followup.get("resting_diastolic_bp")
    return float(val) if val not in (None, "") else None


FEATURE_SPECS = [
    FeatureSpec(
        raw_name="age", label="Age", source="profile",
        extractor=lambda profile, followup: profile.get("age"),
    ),
    FeatureSpec(
        raw_name="blood_pressure",
        label="Diastolic blood pressure",
        source="profile",
        extractor=_blood_pressure_extractor,
    ),
    FeatureSpec(
        raw_name="specific_gravity",
        label="Urine specific gravity",
        source="followup", question_type="number",
        question_id="urine_specific_gravity",
        help_text="From a urinalysis, if available.",
    ),
    FeatureSpec(
        raw_name="albumin",
        label="Urine albumin level",
        source="followup", question_type="number",
        question_id="urine_albumin", unit="0-5 scale",
        help_text="From a urinalysis report.",
    ),
    FeatureSpec(
        raw_name="sugar",
        label="Urine sugar level",
        source="followup", question_type="number",
        question_id="urine_sugar", unit="0-5 scale",
        help_text="From a urinalysis report.",
    ),
    FeatureSpec(
        raw_name="red_blood_cells",
        label="Urine red blood cells",
        source="followup", question_type="select",
        question_id="urine_rbc", options=NORMAL_ABNORMAL_OPTIONS,
    ),
    FeatureSpec(
        raw_name="pus_cell",
        label="Urine pus cells",
        source="followup", question_type="select",
        question_id="urine_pus_cell", options=NORMAL_ABNORMAL_OPTIONS,
    ),
    FeatureSpec(
        raw_name="pus_cell_clumps",
        label="Urine pus cell clumps",
        source="followup", question_type="select",
        question_id="urine_pus_cell_clumps", options=PRESENT_OPTIONS,
    ),
    FeatureSpec(
        raw_name="bacteria",
        label="Urine bacteria",
        source="followup", question_type="select",
        question_id="urine_bacteria", options=PRESENT_OPTIONS,
    ),
    FeatureSpec(
        raw_name="blood_glucose_random",
        label="Random blood glucose",
        source="followup", question_type="number", unit="mg/dL",
        question_id="random_blood_glucose",
    ),
    FeatureSpec(
        raw_name="blood_urea",
        label="Blood urea",
        source="followup", question_type="number", unit="mg/dL",
        question_id="blood_urea",
    ),
    FeatureSpec(
        raw_name="serum_creatinine",
        label="Serum creatinine",
        source="followup", question_type="number", unit="mg/dL",
        question_id="serum_creatinine",
        help_text="The single most important kidney-function lab value, if you have it.",
    ),
    FeatureSpec(
        raw_name="sodium",
        label="Serum sodium",
        source="followup", question_type="number", unit="mEq/L",
        question_id="serum_sodium",
    ),
    FeatureSpec(
        raw_name="potassium",
        label="Serum potassium",
        source="followup", question_type="number", unit="mEq/L",
        question_id="serum_potassium",
    ),
    FeatureSpec(
        raw_name="hemoglobin",
        label="Hemoglobin",
        source="followup", question_type="number", unit="g/dL",
        question_id="hemoglobin",
    ),
    FeatureSpec(
        raw_name="packed_cell_volume",
        label="Packed cell volume (hematocrit)",
        source="followup", question_type="number", unit="%",
        question_id="packed_cell_volume",
    ),
    FeatureSpec(
        raw_name="white_blood_cell_count",
        label="White blood cell count",
        source="followup", question_type="number", unit="cells/cumm",
        question_id="white_blood_cell_count",
    ),
    FeatureSpec(
        raw_name="red_blood_cell_count",
        label="Red blood cell count",
        source="followup", question_type="number", unit="millions/cmm",
        question_id="red_blood_cell_count",
    ),
    FeatureSpec(
        raw_name="hypertension",
        label="Diagnosed hypertension",
        source="profile",
        extractor=_condition_flag(["hypertension", "high blood pressure"]),
    ),
    FeatureSpec(
        raw_name="diabetes_mellitus",
        label="Diagnosed diabetes",
        source="profile",
        extractor=_condition_flag(["diabetes", "diabetes mellitus"]),
    ),
    FeatureSpec(
        raw_name="coronary_artery_disease",
        label="Diagnosed coronary artery disease",
        source="profile",
        extractor=_condition_flag(["coronary artery disease", "heart disease", "cad"]),
    ),
    FeatureSpec(
        raw_name="appetite",
        label="Appetite",
        source="followup", question_type="select",
        question_id="appetite",
        options=[{"value": "0", "label": "Good"}, {"value": "1", "label": "Poor"}],
    ),
    FeatureSpec(
        raw_name="pedal_edema",
        label="Leg/ankle swelling",
        source="profile",
        extractor=_symptom_flag(["swelling"]),
    ),
    FeatureSpec(
        raw_name="anemia",
        label="Diagnosed anemia",
        source="profile",
        extractor=_condition_flag(["anemia", "anaemia"]),
    ),
]
