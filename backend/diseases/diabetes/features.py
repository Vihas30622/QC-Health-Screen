"""
backend/diseases/diabetes/features.py
========================================
Feature order MUST match ml/common/dataset.py:load_diabetes() exactly:
    pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi,
    diabetes_pedigree, age

Several of these (glucose, skin_thickness, insulin, diabetes_pedigree)
are lab/clinical values most people won't have on hand outside a recent
checkup — that's a real limitation of this dataset for a self-screening
tool, not hidden here. When they're missing, the prediction correctly
comes back "insufficient information" rather than guessing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.core.feature_spec import FeatureSpec


def _pregnancies_extractor(profile: Dict[str, Any], followup: Dict[str, Any]) -> Optional[float]:
    # A value of 0 is a real, known fact for anyone who has never been
    # pregnant — including, factually, anyone not biologically female —
    # so it's safe to default rather than "invented." Biological females
    # still need to answer explicitly.
    if profile.get("biological_sex") != "female":
        return 0.0
    val = followup.get("pregnancies")
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


FEATURE_SPECS = [
    FeatureSpec(
        raw_name="pregnancies",
        label="Number of pregnancies",
        source="followup",
        question_type="number",
        question_id="pregnancies",
        extractor=_pregnancies_extractor,
    ),
    FeatureSpec(
        raw_name="glucose",
        label="Fasting blood glucose",
        source="followup",
        question_type="number",
        unit="mg/dL",
        question_id="fasting_glucose",
        help_text="From a recent blood test, if you have one.",
    ),
    FeatureSpec(
        raw_name="blood_pressure",
        label="Diastolic blood pressure",
        source="profile",
        extractor=lambda profile, followup: profile.get("diastolic_bp"),
    ),
    FeatureSpec(
        raw_name="skin_thickness",
        label="Triceps skinfold thickness",
        source="followup",
        question_type="number",
        unit="mm",
        question_id="triceps_skinfold",
        help_text="A clinical measurement — usually only available from a physical exam.",
    ),
    FeatureSpec(
        raw_name="insulin",
        label="2-hour serum insulin",
        source="followup",
        question_type="number",
        unit="mu U/mL",
        question_id="serum_insulin",
        help_text="From bloodwork, if available.",
    ),
    FeatureSpec(
        raw_name="bmi",
        label="Body mass index",
        source="profile",
        extractor=lambda profile, followup: (
            profile["weight_kg"] / ((profile["height_cm"] / 100) ** 2)
            if profile.get("weight_kg") and profile.get("height_cm")
            else None
        ),
    ),
    FeatureSpec(
        raw_name="diabetes_pedigree",
        label="Diabetes pedigree function score",
        source="followup",
        question_type="number",
        question_id="diabetes_pedigree",
        help_text=(
            "A computed genetic-risk index from a lab or genetic-counseling "
            "report. Most people won't have this — leave blank if unsure."
        ),
    ),
    FeatureSpec(
        raw_name="age",
        label="Age",
        source="profile",
        extractor=lambda profile, followup: profile.get("age"),
    ),
]
