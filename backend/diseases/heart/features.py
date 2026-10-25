"""
backend/diseases/heart/features.py
=====================================
Feature order MUST match ml/common/dataset.py:load_heart() exactly:
    age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak,
    slope, ca, thal

Worth stating plainly: most of these features (cp, restecg, thalach,
oldpeak, slope, ca, thal) come from an ECG, an exercise stress test, or
fluoroscopy — not something a basic questionnaire can collect. This
model will legitimately return "insufficient information" for most
users unless they have recent cardiology records to enter. That's a
real limitation of building on this particular research dataset, not a
bug in the follow-up flow.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.core.feature_spec import FeatureSpec

YES_NO_OPTIONS = [{"value": "1", "label": "Yes"}, {"value": "0", "label": "No"}]


def _sex_extractor(profile: Dict[str, Any], followup: Dict[str, Any]) -> Optional[float]:
    sex = profile.get("biological_sex")
    if sex == "male":
        return 1.0
    if sex == "female":
        return 0.0
    return None  # intersex / prefer_not_to_say: this dataset has no safe encoding for it


def _resting_bp_extractor(profile: Dict[str, Any], followup: Dict[str, Any]) -> Optional[float]:
    if profile.get("systolic_bp"):
        return profile["systolic_bp"]
    val = followup.get("resting_systolic_bp")
    return float(val) if val not in (None, "") else None


FEATURE_SPECS = [
    FeatureSpec(
        raw_name="age", label="Age", source="profile",
        extractor=lambda profile, followup: profile.get("age"),
    ),
    FeatureSpec(
        raw_name="sex", label="Biological sex", source="profile",
        extractor=_sex_extractor,
    ),
    FeatureSpec(
        raw_name="cp",
        label="Chest pain type",
        source="followup",
        question_type="select",
        question_id="chest_pain_type",
        options=[
            {"value": "0", "label": "Typical angina"},
            {"value": "1", "label": "Atypical angina"},
            {"value": "2", "label": "Non-anginal pain"},
            {"value": "3", "label": "Asymptomatic"},
        ],
        help_text="As assessed by a clinician, if you've been evaluated for chest pain.",
    ),
    FeatureSpec(
        raw_name="trestbps",
        label="Resting systolic blood pressure",
        source="followup",
        question_type="number",
        unit="mmHg",
        question_id="resting_systolic_bp",
        extractor=_resting_bp_extractor,
    ),
    FeatureSpec(
        raw_name="chol",
        label="Serum cholesterol",
        source="followup",
        question_type="number",
        unit="mg/dL",
        question_id="cholesterol_mg_dl",
        help_text="From a recent lipid panel, if available.",
    ),
    FeatureSpec(
        raw_name="fbs",
        label="Fasting blood sugar over 120 mg/dL",
        source="followup",
        question_type="boolean",
        question_id="fasting_blood_sugar_over_120",
        options=YES_NO_OPTIONS,
    ),
    FeatureSpec(
        raw_name="restecg",
        label="Resting ECG result",
        source="followup",
        question_type="select",
        question_id="resting_ecg_result",
        options=[
            {"value": "0", "label": "Normal"},
            {"value": "1", "label": "ST-T wave abnormality"},
            {"value": "2", "label": "Probable/definite left ventricular hypertrophy"},
        ],
        help_text="From an ECG report, if you have one.",
    ),
    FeatureSpec(
        raw_name="thalach",
        label="Maximum heart rate achieved (exercise test)",
        source="followup",
        question_type="number",
        unit="bpm",
        question_id="max_heart_rate_achieved",
        help_text="From an exercise/stress test — not the same as resting heart rate.",
    ),
    FeatureSpec(
        raw_name="exang",
        label="Exercise-induced angina",
        source="followup",
        question_type="boolean",
        question_id="exercise_induced_angina",
        options=YES_NO_OPTIONS,
    ),
    FeatureSpec(
        raw_name="oldpeak",
        label="ST depression induced by exercise",
        source="followup",
        question_type="number",
        question_id="st_depression_oldpeak",
        help_text="From an exercise ECG report, if available.",
    ),
    FeatureSpec(
        raw_name="slope",
        label="Slope of the peak exercise ST segment",
        source="followup",
        question_type="select",
        question_id="st_slope",
        options=[
            {"value": "0", "label": "Upsloping"},
            {"value": "1", "label": "Flat"},
            {"value": "2", "label": "Downsloping"},
        ],
    ),
    FeatureSpec(
        raw_name="ca",
        label="Number of major vessels colored by fluoroscopy",
        source="followup",
        question_type="select",
        question_id="num_major_vessels_fluoroscopy",
        options=[{"value": str(i), "label": str(i)} for i in range(5)],
        help_text="From a fluoroscopy/angiogram report.",
    ),
    FeatureSpec(
        raw_name="thal",
        label="Thalassemia test result",
        source="followup",
        question_type="select",
        question_id="thalassemia_result",
        options=[
            {"value": "0", "label": "Category 0 (as coded on your report)"},
            {"value": "1", "label": "Category 1 (as coded on your report)"},
            {"value": "2", "label": "Category 2 (as coded on your report)"},
            {"value": "3", "label": "Category 3 (as coded on your report)"},
        ],
        help_text=(
            "Source datasets for this test aren't fully consistent about which "
            "numeric code means what (normal / fixed defect / reversible "
            "defect), so this asks for the exact code from your report rather "
            "than guessing the label. Leave blank if you don't have this test."
        ),
    ),
]
